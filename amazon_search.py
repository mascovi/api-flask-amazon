import os
from amazon.paapi import AmazonApi

def buscar_produtos(keyword):
    amazon = AmazonApi(
        access_key=os.getenv("ACCESS_KEY"),
        secret_key=os.getenv("SECRET_KEY"),
        partner_tag=os.getenv("ASSOCIATE_TAG"),
        country='BR'
    )

    result = amazon.search_items(keywords=keyword, search_index='Kitchen')
    produtos = []

    for item in result.items:
        produtos.append({
            "titulo": item.title,
            "link_afiliado": item.detail_page_url,
            "imagem": item.image,
            "preco": item.price
        })

    return produtos
