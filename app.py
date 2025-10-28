from flask import Flask, render_template

app = Flask(__name__)

# Página inicial
@app.route('/')
def home():
    return render_template('index.html')

# Catálogo completo de joias
@app.route('/joias')
def joias():
    return render_template('joias.html')

# Subcategoria Anéis
@app.route('/joias/aneis')
def joias_aneis():
    return render_template('joias_aneis.html')

# Produto específico (Anel X)
@app.route('/joias/aneis/anel1')
def produto_anel1():
    return render_template('produto_anel1.html')

if __name__ == '__main__':
    app.run(debug=True)
