from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

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

    from flask import Flask, render_template, session
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "uma_chave_secreta"

# Arquivo para contar visitas totais
VISITAS_FILE = "visitas.txt"

# Dicionário em memória para usuários online
usuarios_online = {}

# Função para incrementar visitas
def incrementar_visita():
    if not os.path.exists(VISITAS_FILE):
        with open(VISITAS_FILE, "w") as f:
            f.write("0")
    with open(VISITAS_FILE, "r") as f:
        count = int(f.read())
    count += 1
    with open(VISITAS_FILE, "w") as f:
        f.write(str(count))
    return count

# Atualiza usuários online
@app.before_request
def atualizar_usuarios_online():
    agora = datetime.now()
    session_id = session.get("user_id")
    if not session_id:
        session["user_id"] = str(agora.timestamp())
        session_id = session["user_id"]
    usuarios_online[session_id] = agora

@app.route('/')
def home():
    # Contador de visitas
    visitas = incrementar_visita()

    # Remove sessões antigas (timeout 5 minutos)
    agora = datetime.now()
    timeout = timedelta(minutes=5)
    for user, last in list(usuarios_online.items()):
        if agora - last > timeout:
            del usuarios_online[user]
    online = len(usuarios_online)

    return render_template('index.html', visitas=visitas, online=online)

if __name__ == '__main__':
    app.run(debug=True)

