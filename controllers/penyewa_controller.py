from flask import Blueprint, flash
from flask import render_template
from flask import session
from flask import redirect
from flask import request
from flask import jsonify
from decimal import Decimal
from flask import current_app
import hashlib
import os

from utils.midtrans import snap
import uuid

from extensions import get_db

penyewa_bp = Blueprint(
    "penyewa",
    __name__,
)

# ====================================
# PROTEKSI SEMUA HALAMAN PENYEWA
# ====================================

@penyewa_bp.before_request
def cek_penyewa():

    whitelist = {
        "penyewa.midtrans_notification"
    }

    if request.endpoint in whitelist:
        return

    if "user_id" not in session:

        return redirect("/login")

    if session.get("role") != "penyewa":

        return redirect(
            "/pemilik/dashboard"
        )

# ====================================
# BERANDA
# ====================================

@penyewa_bp.route("/")
def beranda():

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            k.id,
            k.nama_kost,
            k.alamat,
            k.harga,
            k.tipe_penghuni,
            k.foto_thumbnail,
            k.status_verifikasi,
            k.sisa_kamar,
            k.tier_listing,

            CASE

                WHEN w.id IS NULL THEN 0
                ELSE 1

            END AS is_wishlist

        FROM kost k

        LEFT JOIN wishlist w

        ON
            w.kost_id = k.id

        AND
            w.user_id = %s

        WHERE
            k.status_verifikasi = 1

        ORDER BY

        CASE

            WHEN k.tier_listing='premium' THEN 3
            WHEN k.tier_listing='gold' THEN 2
            WHEN k.tier_listing='silver' THEN 1
            ELSE 0

        END DESC,

        k.created_at DESC

        LIMIT 12

    """,(
        session["user_id"],
    ))

    kost_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(

        "penyewa/beranda.html",

        kost_list=kost_list

    )

# ====================================
# CARI KOS
# ====================================

@penyewa_bp.route("/cari-kos")
def cari_kos():

    if "user_id" not in session:

        return redirect("/login")

    gender = request.args.get(
        "gender",
        ""
    )

    max_harga = request.args.get(
        "max_harga",
        ""
    )

    sort = request.args.get(
        "sort",
        "premium"
    )

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    conn = get_db()

    cursor = conn.cursor()

    sql = """

        SELECT

            k.id,
            k.nama_kost,
            k.alamat,
            k.harga,
            k.tipe_penghuni,
            k.foto_thumbnail,
            k.sisa_kamar,
            k.status_verifikasi,
            k.tier_listing,

            CASE

                WHEN w.id IS NULL THEN 0
                ELSE 1

            END AS is_wishlist

        FROM kost k

        LEFT JOIN wishlist w

        ON
            w.kost_id = k.id

        AND
            w.user_id = %s

        WHERE

            k.status_verifikasi = 1

    """

    params = [

        session["user_id"]

    ]

    if gender:

        sql += """

            AND
            k.tipe_penghuni = %s

        """

        params.append(
            gender
        )

    if max_harga:

        sql += """

            AND
            k.harga <= %s

        """

        params.append(
            max_harga
        )

    if keyword:

        sql += """

            AND

            (

                k.nama_kost LIKE %s

                OR

                k.alamat LIKE %s

            )

        """

        params.extend(

            [

                f"%{keyword}%",

                f"%{keyword}%"

            ]

        )

    if sort == "murah":

        sql += """

            ORDER BY

            k.harga ASC

        """

    elif sort == "mahal":

        sql += """

            ORDER BY

            k.harga DESC

        """

    elif sort == "baru":

        sql += """

            ORDER BY

            k.created_at DESC

        """

    else:

        sql += """

            ORDER BY

            CASE

                WHEN k.tier_listing = 'premium' THEN 1
                WHEN k.tier_listing = 'gold' THEN 2
                WHEN k.tier_listing = 'silver' THEN 3
                ELSE 4

            END,

            k.created_at DESC

        """

    cursor.execute(

        sql,

        params

    )

    kost_list = cursor.fetchall()

    cursor.close()

    conn.close()

    return render_template(

        "penyewa/cari_kos.html",

        kost_list = kost_list,

        keyword = keyword,

        total = len(kost_list)

    )

import os
import pymysql

# ====================================
# HALAMAN DETAIL KOS (PENYEWA)
# ====================================
@penyewa_bp.route("/detail-kost/<int:kost_id>")
def detail_kost(kost_id):
    if "user_id" not in session or session.get("role") != "penyewa":
        return redirect("/login")
        
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 1. Ambil Data Kos Lengkap (Termasuk Latitude & Longitude)
    cursor.execute("""
        SELECT k.*, u.nama as nama_pemilik, u.foto_profil as foto_pemilik
        FROM kost k
        JOIN users u ON k.pemilik_id = u.id
        WHERE k.id = %s
    """, (kost_id,))
    kost = cursor.fetchone()
    
    if not kost:
        cursor.close()
        conn.close()
        flash("Kos tidak ditemukan.", "danger")
        return redirect("/cari-kos")
        
    # 2. Ambil Galeri Foto (Jika tabelnya ada, jika tidak abaikan/sesuaikan)
    try:
        cursor.execute("SELECT foto_path FROM galeri_kost WHERE kost_id = %s", (kost_id,))
        foto_list = cursor.fetchall()
    except:
        foto_list = [] # Fallback jika tabel belum siap
        
    cursor.close()
    conn.close()
    
    # 3. Kirim Kunci API Geoapify untuk Peta
    geoapify_key = os.environ.get("GEOAPIFY_API_KEY")
    
    return render_template(
        "penyewa/detail_kost.html", 
        kost=kost, 
        foto_list=foto_list, 
        geoapify_key=geoapify_key
    )

# ====================================
# KONFIRMASI BOOKING
# ====================================

# PASTIKAN IMPORT INI ADA DI ATAS FILE
from flask import render_template, redirect, request, jsonify, session, flash
from extensions import get_db
from decimal import Decimal

@penyewa_bp.route("/konfirmasi-booking/<int:kost_id>")
def konfirmasi_booking(kost_id):

    if "user_id" not in session:

        return redirect("/login")

    if session.get("role") != "penyewa":

        return redirect("/")

    conn = get_db()

    cursor = conn.cursor(
        pymysql.cursors.DictCursor
    )

    # ============================
    # DATA USER
    # ============================

    cursor.execute("""

        SELECT

            id,
            nama,
            email,
            no_hp,
            foto_ktp

        FROM users

        WHERE id=%s

    """,(

        session["user_id"],

    ))

    user = cursor.fetchone()

    # ============================
    # DATA KOST
    # ============================

    cursor.execute("""

        SELECT

            k.id,
            k.nama_kost,
            k.harga,
            k.uang_muka,
            k.tier_listing,
            k.foto_thumbnail,

            u.nama
            AS nama_pemilik

        FROM kost k

        JOIN users u

        ON
        u.id=k.pemilik_id

        WHERE

            k.id=%s

        AND

            k.status_verifikasi=1

    """,(

        kost_id,

    ))

    kost = cursor.fetchone()

    cursor.close()
    conn.close()

    if not kost:

        return redirect("/cari-kos")

    harga = int(

        kost["harga"] or 0

    )

    dp = int(

        kost["uang_muka"] or 0

    )

    if dp <= 0:

        dp = harga

    sisa = harga - dp

    return render_template(

        "penyewa/konfirmasi_booking.html",

        user=user,

        kost=kost,

        dp=dp,

        sisa=sisa,

        client_key=current_app.config[
            "MIDTRANS_CLIENT_KEY"
        ]

    )

# ====================================
# BUAT BOOKING
# ====================================

# ====================================
# BUAT BOOKING
# ====================================

@penyewa_bp.route(
    "/booking/buat/<int:kost_id>",
    methods=["POST"]
)
def buat_booking(kost_id):

    if "user_id" not in session:

        return jsonify({

            "success":False,

            "message":"Unauthorized"

        }),401

    conn=get_db()

    cursor=conn.cursor(
        pymysql.cursors.DictCursor
    )

    try:

        # ============================
        # CEK DATA KOST
        # ============================

        cursor.execute("""

            SELECT

                id,
                harga,
                sisa_kamar

            FROM kost

            WHERE

                id=%s

            AND

                status_verifikasi=1

        """,(

            kost_id,

        ))

        kost=cursor.fetchone()

        if not kost:

            return jsonify({

                "success":False,

                "message":"Kos tidak ditemukan."

            }),404

        if kost["sisa_kamar"]<=0:

            return jsonify({

                "success":False,

                "message":"Kamar sudah penuh."

            }),400

        # ============================
        # CEK BOOKING AKTIF
        # ============================

        cursor.execute("""

            SELECT

                id

            FROM booking

            WHERE

                penyewa_id=%s

            AND

                kost_id=%s

            AND

                status_booking
                IN
                (

                    'menunggu_dp',

                    'dp_dibayar',

                    'menunggu_konfirmasi',

                    'menunggu_pelunasan',

                    'aktif'

                )

            LIMIT 1

        """,(

            session["user_id"],

            kost_id

        ))

        if cursor.fetchone():

            return jsonify({

                "success":False,

                "message":"Booking sudah pernah dibuat."

            }),400

        total=int(

            float(

                kost["harga"]

            )

        )

        cursor.execute("""

            INSERT INTO booking
            (

                penyewa_id,
                kost_id,
                tanggal_booking,
                tanggal_masuk,
                durasi_bulan,
                total_harga,
                status_booking,
                status_pembayaran

            )

            VALUES
            (

                %s,
                %s,
                NOW(),
                CURDATE(),
                1,
                %s,
                'menunggu_dp',
                'Belum Bayar'

            )

        """,(

            session["user_id"],

            kost_id,

            total

        ))

        booking_id=cursor.lastrowid

        # ============================
        # INSERT PEMBAYARAN DP
        # ============================

        cursor.execute("""

            INSERT INTO pembayaran
            (

                booking_id,
                jenis_pembayaran,
                jumlah,
                metode_pembayaran,
                status_pembayaran,
                midtrans_order_id,
                snap_token

            )

            VALUES
            (

                %s,
                'dp',
                0,
                'Midtrans',
                'pending',
                NULL,
                NULL

            )

        """,(

            booking_id,

        ))

        conn.commit()

        cursor.close()

        conn.close()

        return jsonify({

            "success":True,

            "booking_id":booking_id

        })

    except Exception as e:

        conn.rollback()

        print("ERROR BUAT BOOKING :",e)

        cursor.close()

        conn.close()

        return jsonify({

            "success":False,

            "message":str(e)

        }),500

# ====================================
# WISHLIST
# ====================================

@penyewa_bp.route("/wishlist")
def wishlist():

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            k.id,
            k.nama_kost,
            k.alamat,
            k.harga,
            k.foto_thumbnail,
            k.tipe_penghuni,
            k.status_verifikasi,
            k.tier_listing,
            k.sisa_kamar

        FROM wishlist w

        JOIN kost k
        ON w.kost_id = k.id

        WHERE

        w.user_id=%s

        ORDER BY w.created_at DESC

    """,(session["user_id"],))

    wishlist = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(

        "penyewa/wishlist.html",

        wishlist=wishlist

    )

# ====================================
# TOGGLE WISHLIST
# ====================================

@penyewa_bp.route("/wishlist/toggle/<int:kost_id>")
def toggle_wishlist(kost_id):

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT id

        FROM wishlist

        WHERE

        user_id=%s

        AND

        kost_id=%s

    """,(
        session["user_id"],
        kost_id
    ))

    data = cursor.fetchone()

    if data:

        cursor.execute("""

            DELETE FROM wishlist

            WHERE

            user_id=%s

            AND

            kost_id=%s

        """,(
            session["user_id"],
            kost_id
        ))

    else:

        cursor.execute("""

            INSERT INTO wishlist
            (
                user_id,
                kost_id
            )

            VALUES
            (
                %s,
                %s
            )

        """,(
            session["user_id"],
            kost_id
        ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(request.referrer or "/wishlist")

# ====================================
# BOOKING
# ====================================

@penyewa_bp.route("/booking-saya")
def booking_saya():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            booking.id,
            kost.nama_kost,
            kost.foto_thumbnail,
            booking.tanggal_booking,
            booking.tanggal_masuk,
            booking.durasi_bulan,
            booking.total_harga,
            booking.status_booking
        FROM booking
        JOIN kost
            ON booking.kost_id = kost.id
        WHERE booking.penyewa_id=%s
        ORDER BY booking.id DESC
    """,(session["user_id"],))

    booking_list = cursor.fetchall()


    cursor.execute("""
        SELECT COUNT(*)
        FROM booking
        WHERE penyewa_id=%s
    """,(session["user_id"],))
    total_booking = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM booking
        WHERE penyewa_id=%s
        AND status_booking='aktif'
    """,(session["user_id"],))
    aktif = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM booking
        WHERE penyewa_id=%s
        AND status_booking IN
        (
            'menunggu_dp',
            'dp_dibayar',
            'menunggu_konfirmasi',
            'menunggu_pelunasan'
        )
    """,(session["user_id"],))
    menunggu = cursor.fetchone()[0]


    cursor.execute("""
        SELECT COUNT(*)
        FROM booking
        WHERE penyewa_id=%s
        AND status_booking='selesai'
    """,(session["user_id"],))
    selesai = cursor.fetchone()[0]


    cursor.close()
    conn.close()

    return render_template(
        "penyewa/booking_saya.html",
        booking_list=booking_list,
        total_booking=total_booking,
        aktif=aktif,
        menunggu=menunggu,
        selesai=selesai
    )

# ====================================
# DETAIL BOOKING
# ====================================

@penyewa_bp.route("/booking/<int:booking_id>")
def detail_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            booking.id,
            booking.tanggal_booking,
            booking.tanggal_masuk,
            booking.durasi_bulan,
            booking.total_harga,
            booking.status_booking,
                   
            kost_id,

            kost.nama_kost,
            kost.alamat,
            kost.foto_thumbnail,
            kost.harga,
            kost.tipe_penghuni,

            users.nama

        FROM booking

        JOIN kost
        ON booking.kost_id = kost.id

        JOIN users
        ON kost.pemilik_id = users.id

        WHERE booking.id=%s
        AND booking.penyewa_id=%s
    """,(booking_id,session["user_id"]))

    booking = cursor.fetchone()
    
    dp = booking[4] * Decimal("0.30")
    pelunasan = booking[4] - dp

    cursor.close()
    conn.close()

    if not booking:
        return redirect("/booking-saya")

    return render_template(
        "penyewa/detail_booking.html",
        booking=booking,
        dp=dp,
        pelunasan=pelunasan
    )

# ====================================
# BAYAR DP
# ====================================

@penyewa_bp.route("/booking/<int:booking_id>/bayar-dp")
def bayar_dp(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            booking.id,
            booking.total_harga,

            users.nama,
            users.email,
            users.no_hp

        FROM booking

        JOIN users
        ON booking.penyewa_id = users.id

        WHERE
            booking.id=%s
        AND
            booking.penyewa_id=%s
    """, (
        booking_id,
        session["user_id"]
    ))

    booking = cursor.fetchone()

    if not booking:

        cursor.close()
        conn.close()

        return redirect("/booking-saya")

    total = float(booking[1])

    dp = int(total * 0.30)

    order_id = f"DP-{booking_id}-{uuid.uuid4().hex[:8]}"
    
    transaction = {

        "transaction_details": {

            "order_id": order_id,

            "gross_amount": dp

        },

        "customer_details": {

            "first_name": booking[2],

            "email": booking[3],

            "phone": booking[4]

        }

    }

# ====================================
# MIDTRANS SNAP TOKEN
# ====================================

@penyewa_bp.route("/booking/<int:booking_id>/snap-token")
def get_snap_token(booking_id):

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            b.id,
            b.total_harga,

            u.nama,
            u.email,
            u.no_hp,

            p.midtrans_order_id,
            p.snap_token,
            p.status_pembayaran

        FROM booking b

        JOIN users u
        ON b.penyewa_id = u.id

        JOIN pembayaran p
        ON p.booking_id = b.id

        WHERE
            b.id=%s
        AND
            b.penyewa_id=%s

    """, (booking_id, session["user_id"]))

    booking = cursor.fetchone()

    if not booking:

        cursor.close()
        conn.close()

        return jsonify({
            "error": "Booking tidak ditemukan"
        }), 404

    dp = int(float(booking[1]) * 0.30)

    # ============================
    # SUDAH BERHASIL BAYAR
    # ============================

    if booking[7] == "success":

        cursor.close()
        conn.close()

        return jsonify({
            "message": "DP sudah dibayar."
        }), 400

    # ============================
    # MASIH PENDING
    # ============================

    if booking[7] == "pending" and booking[6]:

        print("PAKAI SNAP TOKEN LAMA")

        cursor.close()
        conn.close()

        return jsonify({

            "token": booking[6]

        })

    # ============================
    # BUAT TRANSAKSI BARU
    # ============================

    order_id = f"DP-{booking_id}-{uuid.uuid4().hex[:8]}"

    print("ORDER BARU =", order_id)

    transaction = {

        "transaction_details": {

            "order_id": order_id,

            "gross_amount": dp

        },

        "customer_details": {

            "first_name": booking[2],

            "email": booking[3],

            "phone": booking[4]

        }

    }

    transaction_result = snap.create_transaction(transaction)

    snap_token = transaction_result["token"]

    cursor.execute("""

        UPDATE pembayaran

        SET

            midtrans_order_id=%s,

            snap_token=%s,

            jumlah=%s,

            status_pembayaran='pending'

        WHERE booking_id=%s

    """, (

        order_id,

        snap_token,

        dp,

        booking_id

    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({

        "token": snap_token

    })

# ====================================
# WEBHOOK MIDTRANS
# ====================================

@penyewa_bp.route("/midtrans/notification", methods=["POST"])
def midtrans_notification():

    data = request.get_json(silent=True)

    if data is None:
        data = request.form.to_dict()

    print("CONTENT TYPE =", request.content_type)
    print("RAW DATA =", request.data)
    print("FORM =", request.form)
    print("JSON =", request.get_json(silent=True))
    print(data)

    order_id = data["order_id"]
    status_code = data["status_code"]
    gross_amount = data["gross_amount"]
    signature_key = data["signature_key"]
    transaction_status = data["transaction_status"]

    print("======================================")
    print("WEBHOOK MASUK")
    print("ORDER ID =", order_id)
    print("STATUS =", transaction_status)
    print("======================================")

    server_key = current_app.config["MIDTRANS_SERVER_KEY"]

    my_signature = hashlib.sha512(
        (
            order_id +
            status_code +
            gross_amount +
            server_key
        ).encode()
    ).hexdigest()

    if my_signature != signature_key:
        return jsonify({
            "message": "Invalid Signature"
        }), 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT booking_id

        FROM pembayaran

        WHERE midtrans_order_id=%s

    """, (order_id,))

    pembayaran = cursor.fetchone()

    print("HASIL QUERY =", pembayaran)

    if not pembayaran:

        cursor.close()
        conn.close()

        return jsonify({
            "message": "Order tidak ditemukan"
        }), 404

    booking_id = pembayaran[0]

    print("BOOKING =", booking_id)

    # =========================================
    # SETTLEMENT
    # =========================================

    if transaction_status == "settlement":

        cursor.execute("""
            UPDATE pembayaran
            SET status_pembayaran='success'
            WHERE midtrans_order_id=%s
        """, (order_id,))

        print("UPDATE PEMBAYARAN =", cursor.rowcount)

        if order_id.startswith("DP-"):

            cursor.execute("""
                UPDATE booking
                SET status_booking='dp_dibayar'
                WHERE id=%s
            """, (booking_id,))

            print("BOOKING -> DP DIBAYAR")

            # --- TAMBAHAN MODUL 3: OTOMATIS POTONG SISA KAMAR ---
            cursor.execute("""
                SELECT kost_id 
                FROM booking 
                WHERE id=%s
            """, (booking_id,))
            
            kost_data = cursor.fetchone()
            
            if kost_data:
                cursor.execute("""
                    UPDATE kost 
                    SET sisa_kamar = sisa_kamar - 1 
                    WHERE id=%s AND sisa_kamar > 0
                """, (kost_data[0],))
                print("KOST -> SISA KAMAR BERKURANG 1")
            # ----------------------------------------------------

        # (Tambahkan di bawah elif order_id.startswith("PEL-"): ... )
        elif order_id.startswith("TAGIHAN-"):
            # Jika Tagihan Bulanan Berhasil Terbayar
            gross = float(data.get("gross_amount", 0))
            # Potong fee layanan tagihan platform (misal admin ambil 2%)
            fee = gross * 0.02
            bersih_ke_pemilik = gross - fee
            
            # Cari message ID dari Order ID (Format: TAGIHAN-{msg_id}-{random})
            msg_id = order_id.split("-")[1]
            
            # 1. Cari Pemilik Kos dari Chat Room
            cursor.execute("SELECT cr.pemilik_id FROM chat_message cm JOIN chat_room cr ON cm.room_id = cr.id WHERE cm.id = %s", (msg_id,))
            owner = cursor.fetchone()
            
            if owner:
                # 2. Uang langsung masuk ke Dompet Virtual Pemilik
                cursor.execute("UPDATE users SET saldo_dompet = saldo_dompet + %s WHERE id = %s", (bersih_ke_pemilik, owner[0]))
                
                # 3. Ubah pesan tagihan di chat menjadi "LUNAS"
                cursor.execute("UPDATE chat_message SET pesan = 'Tagihan telah LUNAS dibayarkan', is_tagihan = 0 WHERE id = %s", (msg_id,))
                
                # 4. Catat ke Log Admin
                cursor.execute("INSERT INTO log_admin (admin_id, kategori, aksi, deskripsi) VALUES (1, 'Keuangan', 'Tagihan Bulanan', %s)", 
                               (f"Pemilik menerima tagihan bersih Rp{bersih_ke_pemilik} via chat.",))

        elif order_id.startswith("PEL-"):

            cursor.execute("""
                UPDATE booking
                SET status_booking='aktif'
                WHERE id=%s
            """, (booking_id,))

            print("BOOKING -> AKTIF")

        print("UPDATE BOOKING =", cursor.rowcount)
        
        

    # =========================================
    # PENDING
    # =========================================

    elif transaction_status == "pending":

        cursor.execute("""

            UPDATE pembayaran

            SET status_pembayaran='pending'

            WHERE midtrans_order_id=%s

        """, (order_id,))

    # =========================================
    # EXPIRE / CANCEL
    # =========================================

    elif transaction_status in ("expire", "cancel"):

        cursor.execute("""

            UPDATE pembayaran

            SET status_pembayaran='failed'

            WHERE midtrans_order_id=%s

        """, (order_id,))

    print("COMMIT...")
    conn.commit()
    print("UPDATE BERHASIL")

    cursor.close()
    conn.close()

    return jsonify({
        "message": "OK"
    })

# ====================================
# MIDTRANS PELUNASAN
# ====================================

@penyewa_bp.route("/booking/<int:booking_id>/pelunasan")
def get_pelunasan_token(booking_id):

    if "user_id" not in session:
        return jsonify({"error":"Unauthorized"}),401

    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("""

        SELECT

            b.id,
            b.total_harga,

            u.nama,
            u.email,
            u.no_hp

        FROM booking b

        JOIN users u
        ON b.penyewa_id=u.id

        WHERE

            b.id=%s

        AND

            b.penyewa_id=%s

    """,(booking_id,session["user_id"]))

    booking=cursor.fetchone()

    if not booking:

        cursor.close()
        conn.close()

        return jsonify({
            "error":"Booking tidak ditemukan"
        }),404

    total=float(booking[1])

    pelunasan=int(total-(total*0.30))

    # ===============================
    # CEK APAKAH SUDAH ADA PELUNASAN
    # ===============================

    cursor.execute("""

        SELECT

            midtrans_order_id,
            snap_token,
            status_pembayaran

        FROM pembayaran

        WHERE

            booking_id=%s

        AND

            jenis_pembayaran='pelunasan'

        LIMIT 1

    """,(booking_id,))

    pembayaran=cursor.fetchone()

    # ===============================
    # SUDAH SUCCESS
    # ===============================

    if pembayaran and pembayaran[2]=="success":

        cursor.close()
        conn.close()

        return jsonify({

            "message":"Pelunasan sudah dibayar."

        }),400

    # ===============================
    # MASIH PENDING
    # ===============================

    if pembayaran and pembayaran[2]=="pending":

        cursor.close()
        conn.close()

        return jsonify({

            "token":pembayaran[1]

        })

    # ===============================
    # BUAT TRANSAKSI BARU
    # ===============================

    order_id=f"PEL-{booking_id}-{uuid.uuid4().hex[:8]}"

    transaction={

        "transaction_details":{

            "order_id":order_id,

            "gross_amount":pelunasan

        },

        "customer_details":{

            "first_name":booking[2],

            "email":booking[3],

            "phone":booking[4]

        }

    }

    transaction_result=snap.create_transaction(transaction)

    snap_token=transaction_result["token"]

    cursor.execute("""

        INSERT INTO pembayaran
        (

            booking_id,
            jenis_pembayaran,
            jumlah,
            metode_pembayaran,
            status_pembayaran,
            midtrans_order_id,
            snap_token

        )

        VALUES
        (

            %s,
            'pelunasan',
            %s,
            'Midtrans',
            'pending',
            %s,
            %s

        )

    """,(

        booking_id,
        pelunasan,
        order_id,
        snap_token

    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({

        "token":snap_token

    })
    
import cloudinary.uploader

# ====================================
# API UPLOAD KTP (KYC) PENYEWA
# ====================================
@penyewa_bp.route("/upload-ktp-booking", methods=["POST"])
def upload_ktp_booking():
    if "user_id" not in session or session.get("role") != "penyewa":
        return jsonify({"error": "Unauthorized"}), 401
        
    file = request.files.get("ktp_file")
    if not file: return jsonify({"error": "File KTP tidak ditemukan"}), 400
        
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'webp']:
        return jsonify({"error": "Hanya format JPG, PNG, atau WEBP yang diperbolehkan"}), 400
        
    file.seek(0, 2)
    if file.tell() > 5 * 1024 * 1024:
        return jsonify({"error": "Ukuran KTP maksimal 5MB"}), 400
    file.seek(0)
    
    try:
        # Upload ke Cloudinary
        upload_result = cloudinary.uploader.upload(file, folder="findyourkost_ktp", resource_type="image")
        ktp_url = upload_result.get('secure_url')
        
        # Simpan ke DB (Hanya update foto_ktp, hindari error status_verifikasi)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET foto_ktp = %s WHERE id = %s", (ktp_url, session["user_id"]))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "ktp_url": ktp_url})
    except Exception as e:
        print(f"Error Upload KTP Cloudinary: {e}")
        return jsonify({"error": str(e)}), 500


# ====================================
# FORM LAPORAN PEMILIK
# ====================================
@penyewa_bp.route("/laporkan-pemilik/<int:kost_id>")
def form_laporan_pemilik(kost_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""

        SELECT
            k.id,
            k.nama_kost,
            u.nama AS nama_pemilik

        FROM kost k

        JOIN users u
        ON k.pemilik_id=u.id

        WHERE k.id=%s

    """,(kost_id,))

    kost=cursor.fetchone()

    cursor.close()
    conn.close()

    if not kost:
        flash("Data kos tidak ditemukan.","danger")
        return redirect("/cari-kos")

    return render_template(
        "penyewa/laporan_pemilik.html",
        kost=kost
    )

# ====================================
# KIRIM LAPORAN
# ====================================

@penyewa_bp.route("/laporkan-pemilik/<int:kost_id>",methods=["POST"])
def kirim_laporan_pemilik(kost_id):

    if "user_id" not in session:
        return redirect("/login")

    alasan=request.form.get("alasan")

    conn=get_db()
    cursor=conn.cursor()

    cursor.execute("""

        INSERT INTO laporan
        (

            pelapor_id,
            kost_id,
            alasan

        )

        VALUES
        (

            %s,
            %s,
            %s

        )

    """,(

        session["user_id"],
        kost_id,
        alasan

    ))

    conn.commit()

    cursor.close()
    conn.close()

    flash(
        "Laporan berhasil dikirim ke Administrator.",
        "success"
    )

    return redirect("/booking-saya")