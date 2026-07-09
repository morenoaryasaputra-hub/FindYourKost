from flask import Blueprint, render_template, session, redirect, request
from extensions import get_db

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
        # GANTI QUERY INI: Tambahkan cm.file_path ke dalam SELECT
        cursor.execute("""
            SELECT 
                cm.id, 
                cm.sender_id, 
                cm.pesan, 
                cm.waktu_kirim, 
                u.nama,
                cm.file_path  -- TAMBAHKAN INI
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

import os
from werkzeug.utils import secure_filename
from flask import request, jsonify

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

    # Simpan file
    filename = secure_filename(file.filename)
    save_path = os.path.join("static/uploads", filename)
    file.save(save_path)

    # Simpan ke DB
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_message (room_id, sender_id, pesan, file_path) VALUES (%s, %s, %s, %s)", 
                   (room_id, session["user_id"], "Mengirim file...", save_path))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True, "file_path": save_path, "type": ext})