from flask import Flask, render_template

app = Flask(__name__)

products = [
    {"id": 1, "name": "Tênis Classic", "price": 199.90, "desc": "Conforto diário"},
    {"id": 2, "name": "Relógio Sport", "price": 349.00, "desc": "Resistente à água"},
]

@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product(product_id):
    p = next((x for x in products if x['id'] == product_id), None)
    if not p:
        return "Produto não encontrado", 404
    return render_template('product.html', product=p)

if __name__ == '__main__':
    app.run(debug=True)
