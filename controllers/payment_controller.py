import os
import midtransclient
import uuid
from flask import Blueprint, request, jsonify, session

from extensions import get_db


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

@payment_bp.route("/payment-success", methods=["POST"])
def payment_success():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session["user_id"]
    
    # Update status user menjadi premium di database
    conn = get_db() # Pastikan fungsi get_db() sudah di-import di atas
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = 1 WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    # Update session agar sistem langsung mengenali tanpa perlu login ulang
    session['is_premium'] = True
    
    return jsonify({"success": True, "message": "Akun berhasil di-upgrade ke Premium!"})