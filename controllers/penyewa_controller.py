from flask import Blueprint
from flask import render_template
from flask import session
from flask import redirect
from flask import request
from decimal import Decimal

from extensions import get_db

penyewa_bp = Blueprint(
    "penyewa",
    __name__
)

# ====================================
# PROTEKSI SEMUA HALAMAN PENYEWA
# ====================================

@penyewa_bp.before_request
def cek_penyewa():

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

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            nama_kost,
            alamat,
            harga,
            tipe_penghuni,
            foto_thumbnail,
            status_verifikasi,
            sisa_kamar
        FROM kost
        WHERE status_verifikasi = 1
        ORDER BY created_at DESC
        LIMIT 8
    """)

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

@penyewa_bp.route(
    "/cari-kos"
)
def cari_kos():

    return render_template(
        "penyewa/cari_kos.html"
    )

# ====================================
# DETAIL KOS
# ====================================

@penyewa_bp.route(
    "/detail-kost"
)
def detail_kost():

    return render_template(
        "penyewa/detail_kost.html"
    )

# ====================================
# KONFIRMASI BOOKING
# ====================================

@penyewa_bp.route(
    "/konfirmasi-booking"
)
def konfirmasi_booking():

    return render_template(
        "penyewa/konfirmasi_booking.html"
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

    cursor.execute(
        """
        SELECT

            kost.id,
            kost.nama_kost,
            kost.alamat,
            kost.harga,
            kost.foto_thumbnail,
            kost.tipe_penghuni

        FROM wishlist

        INNER JOIN kost
        ON wishlist.kost_id = kost.id

        WHERE wishlist.user_id = %s

        ORDER BY wishlist.created_at DESC
        """,
        (session["user_id"],)
    )

    wishlist = cursor.fetchall()

    cursor.close()

    conn.close()

    return render_template(
        "penyewa/wishlist.html",
        wishlist=wishlist
    )

# ====================================
# TAMBAH WISHLIST
# ====================================

@penyewa_bp.route("/wishlist/tambah/<int:kost_id>")
def tambah_wishlist(kost_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

        INSERT IGNORE INTO wishlist
        (
            user_id,
            kost_id
        )

        VALUES
        (
            %s,
            %s
        )

    """,(session["user_id"],kost_id))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(request.referrer or "/")

# ====================================
# HAPUS WISHLIST
# ====================================

@penyewa_bp.route("/wishlist/hapus/<int:kost_id>")
def hapus_wishlist(kost_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

        DELETE FROM wishlist

        WHERE

        user_id=%s

        AND

        kost_id=%s

    """,(session["user_id"],kost_id))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/wishlist")

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