import os
import json
import uuid
import hashlib
import hmac
import datetime
import requests

ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
PARTNER_TAG = os.getenv("ASSOCIATE_TAG")
REGION = "us-east-1"
SERVICE = "ProductAdvertisingAPI"
HOST = "webservices.amazon.com.br"
ENDPOINT = f"https://{HOST}/paapi5/searchitems"

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region, service):
    kDate = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = sign(kDate, region)
    kService = sign(kRegion, service)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

def build_signed_headers(keyword):
    payload = {
        "Keywords": keyword,
        "SearchIndex": "All",
        "PartnerTag": PARTNER_TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com.br",
        "Resources": [
            "Images.Primary.Medium",
            "ItemInfo.Title",
            "Offers.Listings.Price"
        ]
    }

    request_payload = json.dumps(payload)

    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')

    canonical_uri = "/paapi5/searchitems"
    canonical_querystring = ""
    canonical_headers = (
        f"content-encoding:amz-1.0\n"
        f"content-type:application/json; charset=utf-8\n"
        f"host:{HOST}\n"
        f"x-amz-date:{amz_date}\n"
        f"x-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems\n"
    )
    signed_headers = "content-encoding;content-type;host;x-amz-date;x-amz-target"
    payload_hash = hashlib.sha256(request_payload.encode('utf-8')).hexdigest()

    canonical_request = f"POST\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{date_stamp}/{REGION}/{SERVICE}/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    signing_key = get_signature_key(SECRET_KEY, date_stamp, REGION, SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = (
        f"{algorithm} Credential={ACCESS_KEY}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    headers = {
        "Content-Encoding": "amz-1.0",
        "Content-Type": "application/json; charset=utf-8",
        "Host": HOST,
        "X-Amz-Date": amz_date,
        "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
        "Authorization": authorization_header
    }

    return request_payload, headers

def buscar_produtos_amazon(keyword):
    payload, headers = build_signed_headers(keyword)
    response = requests.post(ENDPOINT, data=payload, headers=headers)

    try:
        data = response.json()
        items = data.get("SearchResult", {}).get("Items", [])
        resultados = []

        for item in items:
            offers = item.get("Offers", {}).get("Listings", [])
            if not offers:
                continue

            resultados.append({
                "titulo": item["ItemInfo"]["Title"]["DisplayValue"],
                "preco": offers[0]["Price"]["DisplayAmount"],
                "imagem": item["Images"]["Primary"]["Medium"]["URL"],
                "link_afiliado": item["DetailPageURL"]
            })

        return resultados

    except Exception as e:
        return {"erro": str(e), "resposta_bruta": response.text}
