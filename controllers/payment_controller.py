import os
import midtransclient
import uuid
from flask import Blueprint, request, jsonify, session

payment_bp = Blueprint("payment", __name__)

# Konfigurasi Midtrans
snap = midtransclient.Snap(
    is_production=False, # Ubah ke True jika sudah live
    server_key=os.getenv('MIDTRANS_SERVER_KEY'),
    client_key=os.getenv('MIDTRANS_CLIENT_KEY')
)

@payment_bp.route("/create-transaction", methods=["POST"])
def create_transaction():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    # Gunakan ID unik
    order_id = f"ORDER-{uuid.uuid4().hex[:8].upper()}"
    
    param = {
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": int(data['amount'])
        },
        "customer_details": {
            "first_name": session.get('nama', 'User'),
            "email": session.get('email', 'user@example.com')
        }
    }

    transaction = snap.create_transaction(param)
    return jsonify({"token": transaction['token']})