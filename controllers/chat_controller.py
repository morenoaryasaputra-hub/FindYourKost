from flask import Blueprint, render_template, session, redirect, request
import socketio
from extensions import get_db
from utils.midtrans import snap
import uuid

chat_bp = Blueprint("chat", __name__)

#-------------------------#
# 1. BUKA HALAMAN CHAT UTAMA
#-------------------------#
#-------------------------#
# 1. BUKA HALAMAN CHAT UTAMA
#-------------------------#
@chat_bp.route("/chat")
@chat_bp.route("/chat/<int:room_id>")
def open_room(room_id=None):
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    role = str(session.get("role", "")).lower() 

    conn = get_db()
    cursor = conn.cursor()

    # ==========================================
    # LOGIKA PINTAR: AMBIL NAMA LAWAN & NAMA KOS
    # ==========================================
    if role == "pemilik":
        cursor.execute("""
            SELECT
                cr.id, u.nama, u.foto_profil, k.nama_kost,
                (SELECT pesan FROM chat_message WHERE room_id=cr.id ORDER BY waktu_kirim DESC LIMIT 1) last_message,
                (SELECT waktu_kirim FROM chat_message WHERE room_id=cr.id ORDER BY waktu_kirim DESC LIMIT 1) last_time
            FROM chat_room cr
            JOIN users u ON u.id = cr.penyewa_id
            JOIN kost k ON k.id = cr.kost_id
            WHERE cr.pemilik_id=%s
            ORDER BY last_time DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT
                cr.id, u.nama, u.foto_profil, k.nama_kost,
                (SELECT pesan FROM chat_message WHERE room_id=cr.id ORDER BY waktu_kirim DESC LIMIT 1) last_message,
                (SELECT waktu_kirim FROM chat_message WHERE room_id=cr.id ORDER BY waktu_kirim DESC LIMIT 1) last_time
            FROM chat_room cr
            JOIN users u ON u.id = cr.pemilik_id
            JOIN kost k ON k.id = cr.kost_id
            WHERE cr.penyewa_id=%s
            ORDER BY last_time DESC
        """, (user_id,))

    rooms = cursor.fetchall()

    active_room = None
    messages = []

    if room_id is None and rooms:
        active_room = rooms[0][0]
    elif room_id:
        active_room = room_id

    if active_room:
        cursor.execute("""
            SELECT 
                cm.id, 
                cm.sender_id, 
                cm.pesan, 
                cm.waktu_kirim, 
                u.nama,
                cm.file_path,       
                cm.is_tagihan,     
                cm.tagihan_amount   
            FROM chat_message cm
            JOIN users u ON u.id = cm.sender_id
            WHERE room_id=%s
            ORDER BY waktu_kirim ASC
        """, (active_room,))
        messages = cursor.fetchall()

    cursor.close()
    conn.close()
    # ====== JEBAKAN BATMAN UNTUK DEBUGGING ======
    print("\n=== CEK RADAR CHAT ===")
    print("ROLE SAYA :", role)
    print("ID SAYA   :", user_id)
    print("TOTAL ROOM:", len(rooms))
    print("DATA ROOM :", rooms)
    print("======================\n")
    # ============================================

    # Pisahkan tampilan HTML-nya
    if role == "pemilik":
        return render_template("pemilik/chat.html", rooms=rooms, messages=messages, active_room=active_room)
    else:
        return render_template("chat/chat.html", rooms=rooms, messages=messages, active_room=active_room)
#-------------------------#
# 2. KIRIM PESAN
#-------------------------#
@chat_bp.route("/chat/send", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return redirect("/login")

    room_id = request.form["room_id"]
    pesan = request.form["pesan"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_message (room_id, sender_id, pesan)
        VALUES (%s, %s, %s)
    """, (room_id, session["user_id"], pesan))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(f"/chat/{room_id}")

#-------------------------#
# 3. PENYEWA MEMULAI CHAT BARU
#-------------------------#
@chat_bp.route("/chat/create/<int:kost_id>")
def create_chat(kost_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Cari siapa pemilik kos ini?
    cursor.execute("SELECT pemilik_id FROM kost WHERE id=%s", (kost_id,))
    kost = cursor.fetchone()

    if not kost:
        cursor.close()
        conn.close()
        return redirect("/")

    pemilik_id = kost[0]

    # Cek apakah room sudah ada
    cursor.execute("""
        SELECT id FROM chat_room
        WHERE penyewa_id=%s AND pemilik_id=%s AND kost_id=%s
    """, (session["user_id"], pemilik_id, kost_id))
    room = cursor.fetchone()

    # Bikin atau Buka
    if room:
        room_id = room[0]
    else:
        cursor.execute("""
            INSERT INTO chat_room (penyewa_id, pemilik_id, kost_id)
            VALUES (%s, %s, %s)
        """, (session["user_id"], pemilik_id, kost_id))
        conn.commit()
        room_id = cursor.lastrowid

    cursor.close()
    conn.close()    
    return redirect(f"/chat/{room_id}")

#############################
##BATAS FILE UNTUK CHAT CONTROLLER##
############################

import cloudinary.uploader
from extensions import get_db, socketio
import os
from flask import request, jsonify, session

# Batasan ukuran (dalam bytes)
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_OTHER_SIZE = 30 * 1024 * 1024  # 5MB

@chat_bp.route("/chat/upload", methods=["POST"])
def upload_file():
    if "user_id" not in session: return jsonify({"error": "Unauthorized"}), 401
    
    file = request.files.get("file")
    room_id = request.form.get("room_id")
    
    if not file: return jsonify({"error": "No file"}), 400

    # Cek ekstensi
    ext = file.filename.rsplit('.', 1)[1].lower()
    
    # Validasi ukuran
    if ext in ['jpg', 'jpeg', 'png'] and len(file.read()) > MAX_IMAGE_SIZE:
        return jsonify({"error": "Gambar max 2MB"}), 400
    file.seek(0) # Reset pointer setelah read()

    # ==========================================
    # LOGIKA BARU: UPLOAD LANGSUNG KE CLOUDINARY
    # ==========================================
    try:
        # resource_type="auto" agar bisa menerima gambar, video, maupun file lain
        upload_result = cloudinary.uploader.upload(file, folder="findyourkost_chat", resource_type="auto")
        file_url = upload_result.get('secure_url')
    except Exception as e:
        return jsonify({"error": f"Gagal upload ke Cloudinary: {str(e)}"}), 500

    # Simpan URL Cloudinary ke DB (bukan path lokal lagi)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_message (room_id, sender_id, pesan, file_path) VALUES (%s, %s, %s, %s)", 
                   (room_id, session["user_id"], "Mengirim file...", file_url))
    conn.commit()
    cursor.close()
    conn.close()

    # Tentukan tipe file
    file_type = f"image/{ext}" if ext in ['jpg', 'jpeg', 'png', 'webp'] else f"video/{ext}" if ext in ['mp4', 'webm'] else "application/pdf"

    # Pancarkan URL Cloudinary ke ruangan secara live!
    socketio.emit(
        "receive_message",
        {
            "sender_id": session["user_id"],
            "message": "Mengirim file...",
            "file_path": file_url,
            "file_type": file_type
        },
        to=str(room_id),
        namespace="/"
    )

    return jsonify({"success": True, "file_path": file_url, "type": ext})

@chat_bp.route("/chat/bayar-tagihan", methods=["POST"])
def bayar_tagihan():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    msg_id = data.get("message_id")
    amount = float(data.get("amount", 0))
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # CEK KEAMANAN: Apakah tagihan sudah lunas?
        cursor.execute("SELECT pesan FROM chat_message WHERE id = %s", (msg_id,))
        chat_data = cursor.fetchone()
        
        if chat_data and "LUNAS" in chat_data[0]:
            return jsonify({"error": "Tagihan ini sudah lunas! Anda tidak perlu membayar lagi."})

        # Generate Order ID khusus Tagihan Bulanan (TAGIHAN-)
        order_id = f"TAGIHAN-{msg_id}-{uuid.uuid4().hex[:8]}"
        
        transaction = {
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": int(amount)
            },
            "customer_details": {
                "first_name": session.get("nama", "Penyewa Sistem")
            }
        }
        
        transaction_result = snap.create_transaction(transaction)
        return jsonify({"token": transaction_result["token"]})
        
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        cursor.close()
        conn.close()
        
@chat_bp.route("/chat/update-lunas", methods=["POST"])
def update_lunas_lokal():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    msg_id = data.get("message_id")
    amount = float(data.get("amount", 0))
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # CEK PENGAMAN 1: Pastikan belum lunas (Biar saldo pemilik nggak nambah dobel)
        cursor.execute("SELECT pesan FROM chat_message WHERE id = %s", (msg_id,))
        cek = cursor.fetchone()
        
        if cek and "LUNAS" in cek[0]:
            return jsonify({"success": True, "message": "Sudah lunas sebelumnya"})

        fee = amount * 0.10
        bersih_ke_pemilik = amount - fee
        
        # Cari Pemilik Kos
        cursor.execute("""
            SELECT cr.pemilik_id 
            FROM chat_message cm 
            JOIN chat_room cr ON cm.room_id = cr.id 
            WHERE cm.id = %s
        """, (msg_id,))
        owner = cursor.fetchone()
        
        if owner:
            # 1. Update Saldo Pemilik
            cursor.execute("UPDATE users SET saldo_dompet = saldo_dompet + %s WHERE id = %s", (bersih_ke_pemilik, owner[0]))
            
            # 2. Update Chat Message jadi LUNAS (Kunci Tombol)
            cursor.execute("UPDATE chat_message SET pesan = 'LUNAS', is_tagihan = 1 WHERE id = %s", (msg_id,))
            
            # 3. Catat Log Admin
            deskripsi_log = f"Pemilik menerima tagihan bersih Rp{int(bersih_ke_pemilik)} via chat."
            cursor.execute("INSERT INTO log_admin (admin_id, kategori, aksi, deskripsi) VALUES (1, 'Keuangan', 'Tagihan Bulanan', %s)", (deskripsi_log,))
            
            conn.commit()
            
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()