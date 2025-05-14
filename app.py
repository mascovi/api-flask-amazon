from flask import Flask, request, jsonify
from amazon_signed_request import buscar_produtos_amazon

app = Flask(__name__)

@app.route('/buscar')
def buscar():
    keyword = request.args.get('keyword', 'café')
    resultado = buscar_produtos_amazon(keyword)
    return jsonify(resultado)
