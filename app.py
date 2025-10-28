from flask import Flask, render_template, session
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "uma_chave_secreta"  # necessário para sessões

VISITAS_FILE = "visitas.txt"
usuarios_online = {}

# Função para contar visitas
def incrementar_visita():
    if not os.path.exists(VISITAS_FILE):
        with open(VISITAS_FILE, "w") as f:
            f.write("0")
    with open(VISITAS_FILE, "r") as f:
        try:
            count = int(f.read())
        except:
            count = 0
    count += 1
    with open(VISITAS_FILE, "w") as f:
        f.write(str(count))
    return count

# Atualizar usuários online
@app.before_request
def atualizar_usuarios_online():
    agora = datetime.now()
    if "user_id" not in session:
        session["user_id"] = str(agora.timestamp())
    usuarios_online[session["user_id"]] = agora

# Rotas do site
@app.route('/')
def home():
    visitas = incrementar_visita()

    # Remove sessões antigas (timeout 5 minutos)
    agora = datetime.now()
    timeout = timedelta(minutes=5)
    usuarios_ativos = {user: last for user, last in usuarios_online.items() if agora - last <= timeout}

    # Atualiza o dicionário global
    usuarios_online.clear()
    usuarios_online.update(usuarios_ativos)

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

if __name__ == '__main__':
    app.run(debug=True)
