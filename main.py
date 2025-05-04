from flask import Flask, request, jsonify
import os
import json
import datetime
import hashlib
import hmac
import requests
import traceback

app = Flask(__name__)

ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
ASSOCIATE_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG")

REGION = "us-east-1"
SERVICE = "ProductAdvertisingAPI"
ENDPOINT = "webservices.amazon.com"
URI = "/paapi5/searchitems"
FULL_URL = f"https://{ENDPOINT}{URI}"

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, regionName, serviceName):
    kDate = sign(("AWS4" + key).encode("utf-8"), date_stamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, "aws4_request")
    return kSigning

@app.route("/")
def home():
    return "API do Cada Dia Um Café rodando. Experimente /search com POST."

@app.route("/search", methods=["POST"])
def search_items():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Corpo da requisição JSON é necessário"}), 400

        keywords = data.get("keywords")
        search_index = data.get("searchIndex", "All")
        item_count = data.get("itemCount", 3)

        if not keywords:
            return jsonify({"error": "O campo 'keywords' é obrigatório"}), 400

        t = datetime.datetime.utcnow()
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        payload = {
            "Keywords": keywords,
            "SearchIndex": search_index,
            "ItemCount": item_count,
            "PartnerTag": ASSOCIATE_TAG,
            "PartnerType": "Associates",
            "Resources": [
                "ItemInfo.Title",
                "Offers.Listings.Price"
            ]
        }

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Host": ENDPOINT,
            "X-Amz-Date": amz_date
        }

        canonical_uri = URI
        canonical_querystring = ""
        canonical_headers = f"content-type:{headers['Content-Type']}\nhost:{ENDPOINT}\nx-amz-date:{amz_date}\n"
        signed_headers = "content-type;host;x-amz-date"
        payload_hash = hashlib.sha256(json.dumps(payload).encode("utf-8")).hexdigest()
        canonical_request = "\n".join([
            "POST", canonical_uri, canonical_querystring,
            canonical_headers, signed_headers, payload_hash
        ])

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{REGION}/{SERVICE}/aws4_request"
        string_to_sign = "\n".join([
            algorithm, amz_date, credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        ])

        signing_key = get_signature_key(SECRET_KEY, date_stamp, REGION, SERVICE)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization_header = (
            f"{algorithm} Credential={ACCESS_KEY}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers["Authorization"] = authorization_header

        response = requests.post(FULL_URL, headers=headers, json=payload)

        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            "error": "Erro interno no servidor",
            "message": str(e),
            "trace": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
