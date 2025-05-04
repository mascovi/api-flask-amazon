from flask import Flask, request, jsonify
import os
import json
import datetime
import hashlib
import hmac
import requests

app = Flask(__name__)

ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
ASSOCIATE_TAG = os.environ.get("AMAZON_ASSOCIATE_TAG")
REGION = "us-east-1"
SERVICE = "ProductAdvertisingAPI"
ENDPOINT = "webservices.amazon.com.br"
URI = "/paapi5/searchitems"
FULL_URL = f"https://{ENDPOINT}{URI}"

@app.route("/")
def home():
    return "API do Cada Dia Um Café rodando. Experimente /search com POST."

@app.route("/search", methods=["POST"])
def search():
    try:
        payload = request.get_json(force=True)
        keywords = payload.get("keywords", "")

        if not keywords:
            return jsonify({"error": "Campo 'keywords' é obrigatório"}), 400

        now = datetime.datetime.utcnow()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        headers = {
            "Content-Encoding": "amz-1.0",
            "Content-Type": "application/json; charset=utf-8",
            "Host": ENDPOINT,
            "X-Amz-Date": amz_date
        }

        body = {
            "Keywords": keywords,
            "Resources": [
                "ItemInfo.Title",
                "Offers.Listings.Price"
            ],
            "PartnerTag": ASSOCIATE_TAG,
            "PartnerType": "Associates",
            "Marketplace": "www.amazon.com.br"
        }

        request_payload = json.dumps(body)
        canonical_uri = URI
        canonical_querystring = ""
        canonical_headers = f"content-encoding:amz-1.0\ncontent-type:application/json; charset=utf-8\nhost:{ENDPOINT}\nx-amz-date:{amz_date}\n"
        signed_headers = "content-encoding;content-type;host;x-amz-date"
        payload_hash = hashlib.sha256(request_payload.encode("utf-8")).hexdigest()
        canonical_request = f"POST\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{REGION}/{SERVICE}/aws4_request"
        string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

        def sign(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        k_date = sign(("AWS4" + SECRET_KEY).encode("utf-8"), date_stamp)
        k_region = sign(k_date, REGION)
        k_service = sign(k_region, SERVICE)
        k_signing = sign(k_service, "aws4_request")

        signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization_header = (
            f"{algorithm} Credential={ACCESS_KEY}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers["Authorization"] = authorization_header

        response = requests.post(FULL_URL, headers=headers, data=request_payload)
        return jsonify(response.json())

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
