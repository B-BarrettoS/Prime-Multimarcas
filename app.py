import os
import uuid
import json
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, session, request, redirect,
    url_for, flash, send_from_directory, abort
)
from werkzeug.utils import secure_filename

# --- carregar .env opcionalmente ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # python-dotenv não é obrigatório — apenas útil em desenvolvimento local
    pass

app = Flask(__name__)

# ---------- Configurações via variáveis de ambiente (seguro) ----------
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "uma_chave_secreta_local_troque_ja")

USUARIO_ADMIN = os.environ.get("ADMIN_USER", "Barreto")
SENHA_ADMIN = os.environ.get("ADMIN_PASS", "Bb@96321")

# Flag para ativar/desativar admin (1 = ativado, 0 = desativado)
ENABLE_ADMIN = os.environ.get("ENABLE_ADMIN", "1") == "1"

# ---------- Arquivos e pastas ----------
VISITAS_FILE = "visitas.txt"
PRODUTOS_FILE = "produtos.json"
UPLOAD_FOLDER = os.path.join("static", "images")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- Estado em memória ----------
usuarios_online = {}

# ---------- Helpers ----------
def incrementar_visita():
    if not os.path.exists(VISITAS_FILE):
        with open(VISITAS_FILE, "w", encoding="utf-8") as f:
            f.write("0")
    try:
        with open(VISITAS_FILE, "r", encoding="utf-8") as f:
            count = int(f.read().strip())
    except Exception:
        count = 0
    count += 1
    with open(VISITAS_FILE, "w", encoding="utf-8") as f:
        f.write(str(count))
    return count

@app.before_request
def atualizar_usuarios_online():
    agora = datetime.now()
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    usuarios_online[session["user_id"]] = agora
    timeout = timedelta(minutes=5)
    usuarios_online_copy = {u: t for u, t in usuarios_online.items() if agora - t <= timeout}
    usuarios_online.clear()
    usuarios_online.update(usuarios_online_copy)

def carregar_produtos():
    if os.path.exists(PRODUTOS_FILE):
        with open(PRODUTOS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def salvar_produtos(produtos):
    with open(PRODUTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=4)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def encontrar_produto_por_codigo(produtos, codigo):
    return next((p for p in produtos if p.get("codigo") == codigo), None)

def excluir_arquivo_imagem(caminho_relativo):
    """
    Recebe caminho relativo dentro de static, ex: 'images/categoria/arquivo.jpg'
    """
    if not caminho_relativo:
        return
    caminho_absoluto = os.path.join(app.root_path, "static", caminho_relativo)
    try:
        if os.path.exists(caminho_absoluto):
            os.remove(caminho_absoluto)
    except Exception as e:
        app.logger.warning(f"Não foi possível excluir arquivo {caminho_absoluto}: {e}")

def verificar_admin_ativado():
    """
    Aborta com 404 se o admin estiver desabilitado via ENABLE_ADMIN.
    Use no início das rotas do admin (login, admin, editar, remover).
    """
    if not ENABLE_ADMIN:
        abort(404)

# ---------- Rotas públicas ----------
@app.route("/")
def home():
    visitas = incrementar_visita()
    online = len(usuarios_online)
    return render_template("index.html", visitas=visitas, online=online)

@app.route("/joias")
def joias():
    return render_template("joias.html")

@app.route("/joias/<categoria>")
def joias_categoria(categoria):
    produtos = [p for p in carregar_produtos() if p.get("categoria") == categoria]
    return render_template("categoria.html", produtos=produtos, categoria=categoria)

# ---------- Autenticação Admin ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    # Se admin estiver desabilitado, escondemos também a tela de login
    verificar_admin_ativado()

    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        senha = request.form.get("senha", "")
        if usuario == USUARIO_ADMIN and senha == SENHA_ADMIN:
            session["admin"] = True
            flash("Login realizado com sucesso!", "sucesso")
            return redirect(url_for("admin"))
        else:
            flash("Usuário ou senha incorretos!", "erro")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    # logout disponível apenas quando admin ativo (proteção redundante)
    if not ENABLE_ADMIN:
        return redirect(url_for("home"))
    session.pop("admin", None)
    flash("Logout realizado com sucesso!", "sucesso")
    return redirect(url_for("login"))

# ---------- Painel Admin (criar produto) ----------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    verificar_admin_ativado()

    if not session.get("admin"):
        return redirect(url_for("login"))

    produtos = carregar_produtos()

    if request.method == "POST":
        nome = request.form.get("nome")
        codigo = request.form.get("codigo")
        preco = request.form.get("preco")
        categoria = request.form.get("categoria")
        imagem_file = request.files.get("imagem")

        if not all([nome, codigo, preco, categoria]):
            flash("Todos os campos são obrigatórios!", "erro")
            return redirect(url_for("admin"))

        if not imagem_file or imagem_file.filename == "":
            flash("Imagem é obrigatória!", "erro")
            return redirect(url_for("admin"))

        if not allowed_file(imagem_file.filename):
            flash("Formato de imagem inválido!", "erro")
            return redirect(url_for("admin"))

        filename = secure_filename(imagem_file.filename)
        caminho_rel = f"images/{categoria}/{filename}"
        caminho_abs = os.path.join(app.root_path, "static", "images", categoria, filename)
        os.makedirs(os.path.dirname(caminho_abs), exist_ok=True)
        imagem_file.save(caminho_abs)

        novo_produto = {
            "nome": nome,
            "codigo": codigo,
            "preco": preco,
            "categoria": categoria,
            "imagem": caminho_rel
        }
        produtos.insert(0, novo_produto)
        salvar_produtos(produtos)

        flash(f"Produto '{nome}' adicionado com sucesso!", "sucesso")
        return redirect(url_for("admin"))

    return render_template("admin.html", produtos=produtos)

# ---------- Editar Produto ----------
@app.route("/editar/<codigo>", methods=["GET", "POST"])
def editar_produto(codigo):
    verificar_admin_ativado()

    if not session.get("admin"):
        return redirect(url_for("login"))

    produtos = carregar_produtos()
    produto = encontrar_produto_por_codigo(produtos, codigo)
    if not produto:
        flash("Produto não encontrado!", "erro")
        return redirect(url_for("admin"))

    if request.method == "POST":
        nome = request.form.get("nome")
        preco = request.form.get("preco")
        categoria = request.form.get("categoria")
        imagem_file = request.files.get("imagem")

        if not all([nome, preco, categoria]):
            flash("Nome, preço e categoria são obrigatórios!", "erro")
            return redirect(url_for("editar_produto", codigo=codigo))

        if imagem_file and imagem_file.filename != "":
            if not allowed_file(imagem_file.filename):
                flash("Formato de imagem inválido!", "erro")
                return redirect(url_for("editar_produto", codigo=codigo))

            filename = secure_filename(imagem_file.filename)
            caminho_rel = f"images/{categoria}/{filename}"
            caminho_abs = os.path.join(app.root_path, "static", "images", categoria, filename)
            os.makedirs(os.path.dirname(caminho_abs), exist_ok=True)
            imagem_file.save(caminho_abs)

            # tenta remover a imagem antiga (se for diferente)
            if produto.get("imagem") and produto.get("imagem") != caminho_rel:
                excluir_arquivo_imagem(produto.get("imagem"))

            produto["imagem"] = caminho_rel

        produto["nome"] = nome
        produto["preco"] = preco
        produto["categoria"] = categoria
        salvar_produtos(produtos)
        flash("Produto atualizado com sucesso!", "sucesso")
        return redirect(url_for("admin"))

    return render_template("editar.html", produto=produto)

# ---------- Remover Produto ----------
@app.route("/remover/<codigo>", methods=["POST", "GET"])
def remover_produto(codigo):
    verificar_admin_ativado()

    if not session.get("admin"):
        return redirect(url_for("login"))

    produtos = carregar_produtos()
    produto = encontrar_produto_por_codigo(produtos, codigo)
    if not produto:
        flash("Produto não encontrado!", "erro")
        return redirect(url_for("admin"))

    excluir_arquivo_imagem(produto.get("imagem"))

    produtos = [p for p in produtos if p.get("codigo") != codigo]
    salvar_produtos(produtos)

    flash("Produto removido com sucesso!", "sucesso")
    return redirect(url_for("admin"))

# ---------- Favicon ----------
@app.route("/favicon.ico")
def favicon():
    caminho = os.path.join(app.root_path, "static", "admin")
    return send_from_directory(caminho, "favicon.ico", mimetype="image/vnd.microsoft.icon")

# ---------- Execução ----------
if __name__ == "__main__":
    # debug True só em desenvolvimento local
    app.run(debug=True, host="0.0.0.0", port=5000)
