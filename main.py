from flask import Flask, request, jsonify
from app.db import DB, InventoryItem
from app.services import reserve_item

app = Flask(__name__)
db = DB()
db.inventory["widget"] = InventoryItem("widget", available=20)


@app.route("/")
def index():
    return "Hello, World!"


@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.get_json()
    body, status = reserve_item(db, data["sku"], data["user_id"], data["qty"])
    return jsonify(body), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)