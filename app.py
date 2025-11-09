import os
import json
import uuid
from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, flash, session
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "chave-secreta-prime-multimarcas"

# Caminhos
ARQUIVO_PRODUTOS = 'produtos.json'
UPLOAD_FOLDER = 'static/images/piercings'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- CONTADOR DE VISITAS ----------
visitas_total = 0
usuarios_online = set()


@app.before_request
def contar_visitas():
    global visitas_total
    user_id = session.get('user_id')
    if not user_id:
        session['user_id'] = os.urandom(8).hex()
        visitas_total += 1
    usuarios_online.add(session['user_id'])

# ---------- FUNÇÕES AUXILIARES ----------


def carregar_produtos():
    if not os.path.exists(ARQUIVO_PRODUTOS):
        return []
    with open(ARQUIVO_PRODUTOS, 'r', encoding='utf-8') as f:
        try:
            produtos = json.load(f)
            # Garantir que preço seja float
            for p in produtos:
                p['preco'] = float(p['preco'])
            return produtos
        except json.JSONDecodeError:
            return []


def salvar_produtos(produtos):
    with open(ARQUIVO_PRODUTOS, 'w', encoding='utf-8') as f:
        json.dump(produtos, f, ensure_ascii=False, indent=4)

# ---------- LOGIN ----------


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        if usuario == "Barreto" and senha == "Bb@96321":
            session['logado'] = True
            flash("Login realizado com sucesso!", "sucesso")
            return redirect(url_for('admin'))
        else:
            flash("Usuário ou senha incorretos.", "erro")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logado', None)
    flash("Você saiu do painel.", "sucesso")
    return redirect(url_for('login'))

# ---------- ROTAS PRINCIPAIS ----------


@app.route('/')
def home():
    global visitas_total, usuarios_online
    online = len(usuarios_online)
    return render_template('index.html', visitas=visitas_total, online=online)


@app.route('/joias')
def joias():
    produtos = carregar_produtos()
    categorias = sorted(set(p['categoria'] for p in produtos))
    return render_template('joias.html', categorias=categorias)


@app.route('/joias/<categoria>')
def joias_categoria(categoria):
    produtos_por_pagina = 35
    page = int(request.args.get('page', 1))
    query = request.args.get('q', '').lower()

    produtos = carregar_produtos()
    produtos_categoria = [
        p for p in produtos if p.get('categoria') == categoria]

    # Não ordena por código, mantém sequência do cadastro
    if query:
        produtos_categoria = [
            p for p in produtos_categoria
            if query in p.get('nome', '').lower() or query in p.get('codigo', '').lower()
        ]

    total_produtos = len(produtos_categoria)
    total_paginas = (total_produtos + produtos_por_pagina -
                     1) // produtos_por_pagina

    inicio = (page - 1) * produtos_por_pagina
    fim = inicio + produtos_por_pagina
    produtos_pagina = produtos_categoria[inicio:fim]

    return render_template(
        'categoria.html',
        categoria=categoria,
        produtos=produtos_pagina,
        pagina=page,
        total_paginas=total_paginas
    )

# ---------- ROTAS ADMIN ----------


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logado'):
        return redirect(url_for('login'))

    produtos = carregar_produtos()
    produto_edit = None
    mensagem = None
    sucesso = True

    if request.method == 'POST':
        modo = request.form.get('modo')
        codigo = request.form.get('codigo').strip()
        nome = request.form.get('nome').strip()
        preco = request.form.get('preco').strip().replace(',', '.')
        categoria = request.form.get('categoria').strip()
        imagem = request.files.get('imagem')

        if not codigo or not nome or not preco or not categoria:
            mensagem = "Preencha todos os campos obrigatórios."
            sucesso = False
        else:
            if modo == 'novo':
                if any(p['codigo'] == codigo for p in produtos):
                    mensagem = "Produto já cadastrado!"
                    sucesso = False
                else:
                    filename = "sem-imagem.jpg"
                    if imagem and imagem.filename:
                        ext = imagem.filename.rsplit('.', 1)[1].lower()
                        filename = f"{codigo}.{ext}"  # Mantendo nome do código
                        imagem.save(os.path.join(UPLOAD_FOLDER, filename))

                    novo = {
                        "codigo": codigo,
                        "nome": nome,
                        "preco": float(preco),
                        "categoria": categoria,
                        "imagem": f"images/piercings/{filename}"
                    }

                    # Adiciona no topo
                    produtos.insert(0, novo)
                    salvar_produtos(produtos)
                    mensagem = "Produto cadastrado com sucesso!"
                    sucesso = True

            elif modo == 'editar':
                codigo_original = request.form.get('codigo_original')
                for i, p in enumerate(produtos):
                    if p['codigo'] == codigo_original:
                        produtos[i]['codigo'] = codigo
                        produtos[i]['nome'] = nome
                        produtos[i]['preco'] = float(preco)
                        produtos[i]['categoria'] = categoria
                        if imagem and imagem.filename:
                            ext = imagem.filename.rsplit('.', 1)[1].lower()
                            filename = f"{codigo}.{ext}"
                            imagem.save(os.path.join(UPLOAD_FOLDER, filename))
                            produtos[i]['imagem'] = f"piercings/{filename}"
                        salvar_produtos(produtos)
                        mensagem = "Produto atualizado com sucesso!"
                        sucesso = True
                        break

    return render_template('admin.html', produtos=carregar_produtos(), produto_edit=produto_edit, mensagem=mensagem, sucesso=sucesso)


@app.route('/editar/<codigo>')
def editar_produto(codigo):
    if not session.get('logado'):
        return redirect(url_for('login'))

    produtos = carregar_produtos()
    produto = next((p for p in produtos if p['codigo'] == codigo), None)
    return render_template('admin.html', produtos=produtos, produto_edit=produto)


@app.route('/remover/<codigo>')
def remover_produto(codigo):
    if not session.get('logado'):
        return redirect(url_for('login'))

    produtos = carregar_produtos()
    produtos = [p for p in produtos if p['codigo'] != codigo]
    salvar_produtos(produtos)
    flash("Produto removido com sucesso!", "sucesso")
    return redirect(url_for('admin'))


@app.route('/verificar_codigo/<codigo>')
def verificar_codigo(codigo):
    produtos = carregar_produtos()
    existe = any(p['codigo'].lower() == codigo.lower() for p in produtos)
    return jsonify({'existe': existe})


# ---------- EXECUÇÃO ----------
if __name__ == '__main__':
    app.run(debug=True)
