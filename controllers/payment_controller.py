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
    data = request.json
    
    # Ambil tipe pembayaran dari frontend (misal: dikirim via fetch JS saat sukses)
    tipe_pembayaran = data.get("tipe", "premium") # Default ke premium jika kosong
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if tipe_pembayaran == "premium":
            # LOGIKA LAMA: Update status premium
            cursor.execute("UPDATE users SET is_premium = 1 WHERE id = %s", (user_id,))
            session['is_premium'] = True
            pesan = "Berhasil berlangganan Premium!"
            
        elif tipe_pembayaran == "sewa":
            # LOGIKA BARU: Bayar sewa kos, uang masuk ke Escrow
            booking_id = data.get("booking_id") 
            jumlah_bayar = data.get("amount")
            
            # Masukkan data ke tabel escrow dengan status 'tertahan'
            cursor.execute("""
                INSERT INTO escrow (booking_id, jumlah_bersih, status_pencairan, created_at)
                VALUES (%s, %s, 'tertahan', NOW())
            """, (booking_id, jumlah_bayar))
            
            # Update status booking menjadi 'dibayar' (asumsi kolomnya status_booking)
            cursor.execute("UPDATE booking SET status_booking = 'dibayar' WHERE id = %s", (booking_id,))
            pesan = "Pembayaran sewa berhasil dan masuk ke Penampungan Aman (Escrow)."

        conn.commit()
        return jsonify({"message": pesan, "status": "success"})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
        
    finally:
        cursor.close()
        conn.close()