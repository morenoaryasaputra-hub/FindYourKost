from flask import Blueprint
from flask import render_template
from flask import session
from flask import redirect

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