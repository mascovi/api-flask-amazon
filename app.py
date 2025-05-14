from flask import Flask, request, jsonify
from amazon_search import buscar_produtos

app = Flask(__name__)

@app.route('/buscar')
def buscar():
    keyword = request.args.get('keyword', 'café')
    resultados = buscar_produtos(keyword)
    return jsonify(resultados)

if __name__ == '__main__':
    app.run(debug=True)
