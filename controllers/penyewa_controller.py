from flask import Blueprint
from flask import render_template
from flask import session
from flask import redirect
from flask import request
from flask import jsonify
from decimal import Decimal
from flask import current_app
import hashlib

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

# ====================================
# DETAIL KOS
# ====================================

@penyewa_bp.route("/detail-kost/<int:kost_id>")
def detail_kost(kost_id):

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
            k.deskripsi,
            k.foto_thumbnail,
            k.sisa_kamar,
            k.status_verifikasi,
            k.tier_listing,

            u.id,
            u.nama,
            u.foto_profil,
            u.no_hp,

            (
                SELECT COUNT(*)
                FROM review r
                WHERE r.kost_id=k.id
            ) AS total_review,

            (
                SELECT ROUND(AVG(r.rating),1)
                FROM review r
                WHERE r.kost_id=k.id
            ) AS rating,

            CASE

                WHEN w.id IS NULL THEN 0
                ELSE 1

            END AS is_wishlist

        FROM kost k

        JOIN users u

        ON
            u.id=k.pemilik_id

        LEFT JOIN wishlist w

        ON
            w.kost_id=k.id

        AND
            w.user_id=%s

        WHERE

            k.id=%s

        AND

            k.status_verifikasi=1

    """,(

        session["user_id"],
        kost_id

    ))

    kost = cursor.fetchone()

    cursor.execute("""

        SELECT

            url_foto

        FROM foto_kost

        WHERE

            kost_id=%s

        ORDER BY

            created_at ASC

    """,(kost_id,))

    foto_list = cursor.fetchall()

    cursor.close()
    conn.close()

    if not kost:

        return redirect("/cari-kos")

    return render_template(

        "penyewa/detail_kost.html",

        kost=kost,
        foto_list=foto_list

    )

# ====================================
# KONFIRMASI BOOKING
# ====================================

@penyewa_bp.route("/konfirmasi-booking/<int:kost_id>")
def konfirmasi_booking(kost_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            id,
            nama_kost,
            alamat,
            harga,
            foto_thumbnail,
            tipe_penghuni

        FROM kost

        WHERE

            id=%s

        AND

            status_verifikasi=1

    """,(kost_id,))

    kost = cursor.fetchone()

    cursor.close()
    conn.close()

    if not kost:

        return redirect("/cari-kos")

    return render_template(

        "penyewa/konfirmasi_booking.html",

        kost=kost

    )

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