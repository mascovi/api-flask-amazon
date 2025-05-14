import os
from flask import Flask, request, jsonify
from amazon_signed_request import buscar_produtos_amazon

app = Flask(__name__)

@app.route('/buscar')
def buscar():
    keyword = request.args.get('keyword', 'café')
    resultado = buscar_produtos_amazon(keyword)
    return jsonify(resultado)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Porta dinâmica para o Render
    app.run(host='0.0.0.0', port=port)
