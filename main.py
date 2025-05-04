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
except:
    return jsonify({"error": "Falha ao interpretar JSON"})
    keywords = payload.get("keywords", "café")

    request_body = {
        "Keywords": keywords,
        "Resources": ["ItemInfo.Title"],
        "PartnerTag": ASSOCIATE_TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com.br"
    }

    method = "POST"
    host = ENDPOINT
    content_type = "application/json"
    amz_target = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"

    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')

    payload_json = json.dumps(request_body)
    payload_hash = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()

    canonical_headers = f"content-type:{content_type}\nhost:{host}\nx-amz-date:{amz_date}\nx-amz-target:{amz_target}\n"
    signed_headers = "content-type;host;x-amz-date;x-amz-target"
    canonical_request = f"{method}\n{URI}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{REGION}/{SERVICE}/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def getSignatureKey(key, dateStamp, regionName, serviceName):
        kDate = sign(("AWS4" + key).encode("utf-8"), dateStamp)
        kRegion = sign(kDate, regionName)
        kService = sign(kRegion, serviceName)
        kSigning = sign(kService, "aws4_request")
        return kSigning

    signing_key = getSignatureKey(SECRET_KEY, date_stamp, REGION, SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization_header = (
        f"{algorithm} Credential={ACCESS_KEY}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    headers = {
        "Content-Type": content_type,
        "X-Amz-Date": amz_date,
        "X-Amz-Target": amz_target,
        "Authorization": authorization_header,
        "Host": host
    }

    response = requests.post(FULL_URL, headers=headers, data=payload_json)

    try:
        return jsonify(response.json())
    except Exception:
        return jsonify({"error": "Resposta não formatada como JSON", "raw": response.text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
