from flask import Flask, render_template, session
from datetime import datetime, timedelta
import os
import uuid

app = Flask(__name__)
app.secret_key = "uma_chave_secreta"  # Necessário para sessões

VISITAS_FILE = "visitas.txt"
usuarios_online = {}

# ---------- Função para contar visitas ----------
def incrementar_visita():
    """Incrementa e retorna o total de visitas do site."""
    if not os.path.exists(VISITAS_FILE):
        with open(VISITAS_FILE, "w", encoding="utf-8") as f:
            f.write("0")

    try:
        with open(VISITAS_FILE, "r", encoding="utf-8") as f:
            count = int(f.read().strip())
    except (ValueError, FileNotFoundError):
        count = 0

    count += 1
    with open(VISITAS_FILE, "w", encoding="utf-8") as f:
        f.write(str(count))

    return count

# ---------- Atualiza usuários online ----------
@app.before_request
def atualizar_usuarios_online():
    agora = datetime.now()
    
    # Gera user_id único se não existir na sessão
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())

    # Atualiza último acesso do usuário
    usuarios_online[session["user_id"]] = agora

    # Remove usuários inativos há mais de 5 minutos
    timeout = timedelta(minutes=5)
    usuarios_online_copy = {u: t for u, t in usuarios_online.items() if agora - t <= timeout}
    usuarios_online.clear()
    usuarios_online.update(usuarios_online_copy)

# ---------- Rotas ----------
@app.route('/')
def home():
    visitas = incrementar_visita()
    online = len(usuarios_online)
    return render_template('index.html', visitas=visitas, online=online)

@app.route('/joias')
def joias():
    return render_template('joias.html')

@app.route('/joias/aneis')
def joias_aneis():
    return render_template('aneis.html')

@app.route('/joias/pulseiras')
def joias_pulseiras():
    return render_template('pulseiras.html')

@app.route('/joias/correntes')
def joias_correntes():
    return render_template('correntes.html')

@app.route('/joias/gargantilhas')
def joias_gargantilhas():
    return render_template('gargantilhas.html')

@app.route("/joias/brincos")
def joias_brincos():
    incrementar_visita()
    return render_template("brincos.html")

@app.route("/joias/piercings")
def joias_piercings():
    incrementar_visita()
    return render_template("piercings.html")


# ---------- Execução ----------
if __name__ == '__main__':
    # host='0.0.0.0' permite rodar no Render
    app.run(debug=True, host='0.0.0.0', port=5000)
