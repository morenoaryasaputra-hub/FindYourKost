from flask import Blueprint
from flask import render_template
from flask import session
from flask import redirect

pemilik_bp = Blueprint(
    "pemilik",
    __name__,
    url_prefix="/pemilik"
)

# ====================================
# PROTEKSI SEMUA HALAMAN PEMILIK
# ====================================

@pemilik_bp.before_request
def cek_pemilik():

    if "user_id" not in session:

        return redirect("/login")

    if session.get("role") != "pemilik":

        return redirect("/")

# ====================================
# DASHBOARD
# ====================================

@pemilik_bp.route("/")
@pemilik_bp.route("/dashboard")
def dashboard():

    return render_template(
        "pemilik/dashboard.html"
    )

# ====================================
# DATA KOS
# ====================================

@pemilik_bp.route("/data-kos")
def data_kos():

    return render_template(
        "pemilik/data_kos.html"
    )

# ====================================
# TAMBAH KOS
# ====================================

@pemilik_bp.route("/tambah-kos")
def tambah_kos():

    return render_template(
        "pemilik/tambah_kos.html"
    )

# ====================================
# EDIT KOS
# ====================================

@pemilik_bp.route("/edit-kos/<int:id>")
def edit_kos(id):

    return render_template(
        "pemilik/edit_kos.html",
        id=id
    )

# ====================================
# VERIFIKASI
# ====================================

@pemilik_bp.route("/verifikasi")
def verifikasi():

    return render_template(
        "pemilik/verifikasi.html"
    )

# ====================================
# TRANSAKSI
# ====================================

@pemilik_bp.route("/transaksi")
def transaksi():

    return render_template(
        "pemilik/transaksi.html"
    )

# ====================================
# LAPORAN
# ====================================

@pemilik_bp.route("/laporan")
def laporan():

    return render_template(
        "pemilik/laporan.html"
    )

# ====================================
# PREMIUM
# ====================================

@pemilik_bp.route("/premium")
def premium():

    return render_template(
        "pemilik/layanan_premium.html"
    )

# ====================================
# PENGATURAN
# ====================================

@pemilik_bp.route("/pengaturan")
def pengaturan():

    return render_template(
        "pemilik/pengaturan.html"
    )

# ====================================
# PROFIL PEMILIK
# ====================================

@pemilik_bp.route("/profil")
def profil_pemilik():

    return render_template(
        "pemilik/profil.html"
    )