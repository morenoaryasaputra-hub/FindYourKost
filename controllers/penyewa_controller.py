from flask import Blueprint
from flask import render_template
from flask import session
from flask import redirect

from extensions import mysql

penyewa_bp = Blueprint(
    "penyewa",
    __name__
)

@penyewa_bp.route("/")
def beranda():

    if "user_id" not in session:
        return redirect("/login")

    cursor = mysql.connection.cursor()

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

    return render_template(
        "penyewa/beranda.html",
        kost_list=kost_list
    )