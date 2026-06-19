from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import session
import os
from werkzeug.utils import secure_filename

from extensions import mysql
from extensions import bcrypt

auth_bp = Blueprint(
    "auth",
    __name__
)

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if "user_id" in session:

        return redirect("/")

    if request.method == "POST":

        nama = request.form["nama"]

        email = request.form["email"]

        no_hp = request.form["no_hp"]

        password = request.form["password"]

        confirm_password = request.form[
            "confirm_password"
        ]

        role = request.form["role"]

        if password != confirm_password:

            flash(
                "Konfirmasi password tidak cocok",
                "danger"
            )

            return redirect("/register")

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()

            flash(
                "Email sudah digunakan",
                "danger"
            )

            return redirect("/register")

        password_hash = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO users
            (
                nama,
                email,
                no_hp,
                password_hash,
                role,
                is_profile_complete
            )
            VALUES
            (
                %s,%s,%s,%s,%s,FALSE
            )
            """,
            (
                nama,
                email,
                no_hp,
                password_hash,
                role
            )
        )

        mysql.connection.commit()

        user_id = cursor.lastrowid

        cursor.close()

        session["user_id"] = user_id
        session["nama"] = nama
        session["email"] = email
        session["role"] = role
        session["is_profile_complete"] = False

        flash(
            "Registrasi berhasil",
            "success"
        )

        return redirect("/profil")

    return render_template(
        "auth/register.html"
    )

@auth_bp.route(
    "/login",
    methods=["GET","POST"]
)
def login():

    if "user_id" in session:

        return redirect("/")

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nama,
                email,
                password_hash,
                role,
                is_profile_complete,
                foto_profil
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()

        if not user:

            flash(
                "Email tidak ditemukan",
                "danger"
            )

            return redirect("/login")

        if not bcrypt.check_password_hash(
            user[3],
            password
        ):

            flash(
                "Password salah",
                "danger"
            )

            return redirect("/login")

        session["user_id"] = user[0]
        session["nama"] = user[1]
        session["email"] = user[2]
        session["role"] = user[4]

        session["is_profile_complete"] = bool(
            user[5]
        )
        session["foto_profil"] = user[6]

        return redirect("/")

    return render_template(
        "auth/login.html"
    )

@auth_bp.route(
    "/profil",
    methods=["GET", "POST"]
)
def profil():

    if "user_id" not in session:

        return redirect("/login")

    cursor = mysql.connection.cursor()

    if request.method == "POST":

        nama = request.form["nama"]

        no_hp = request.form["no_hp"]

        jenis_kelamin = request.form[
            "jenis_kelamin"
        ]

        tanggal_lahir = request.form[
            "tanggal_lahir"
        ]

        pekerjaan = request.form[
            "pekerjaan"
        ]

        instansi = request.form[
            "instansi"
        ]

        alamat = request.form[
            "alamat"
        ]

        foto = request.files.get(
            "foto_profil"
        )

        nama_file = None

        if foto and foto.filename != "":

            nama_file = secure_filename(
                foto.filename
            )

            upload_folder = os.path.join(
                "static",
                "uploads"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            foto.save(
                os.path.join(
                    upload_folder,
                    nama_file
                )
            )

        is_profile_complete = all([
            nama,
            no_hp,
            jenis_kelamin,
            tanggal_lahir,
            pekerjaan,
            alamat
        ])

        if nama_file:

            session["foto_profil"] = nama_file

            cursor.execute(
                """
                UPDATE users
                SET

                nama=%s,
                no_hp=%s,
                jenis_kelamin=%s,
                tanggal_lahir=%s,
                pekerjaan=%s,
                instansi=%s,
                alamat=%s,
                foto_profil=%s,
                is_profile_complete=%s

                WHERE id=%s
                """,
                (
                    nama,
                    no_hp,
                    jenis_kelamin,
                    tanggal_lahir,
                    pekerjaan,
                    instansi,
                    alamat,
                    nama_file,
                    is_profile_complete,
                    session["user_id"]
                )
            )

        else:

            cursor.execute(
                """
                UPDATE users
                SET

                nama=%s,
                no_hp=%s,
                jenis_kelamin=%s,
                tanggal_lahir=%s,
                pekerjaan=%s,
                instansi=%s,
                alamat=%s,
                is_profile_complete=%s

                WHERE id=%s
                """,
                (
                    nama,
                    no_hp,
                    jenis_kelamin,
                    tanggal_lahir,
                    pekerjaan,
                    instansi,
                    alamat,
                    is_profile_complete,
                    session["user_id"]
                )
            )

        mysql.connection.commit()

        session["nama"] = nama

        session[
            "is_profile_complete"
        ] = is_profile_complete

        flash(
            "Profil berhasil diperbarui",
            "success"
        )

        cursor.close()

        return redirect("/profil")

    cursor.execute(
        """
        SELECT

            nama,
            email,
            no_hp,

            jenis_kelamin,
            tanggal_lahir,

            pekerjaan,
            instansi,

            alamat,

            foto_profil

        FROM users

        WHERE id=%s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()
    
    if user:
        session["foto_profil"] = user[8]
    
    cursor.close()

    return render_template(
        "auth/edit_profil.html",
        user=user
    )

@auth_bp.route("/akun")
def akun():

    if "user_id" not in session:

        return redirect("/login")

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT
            nama,
            email,
            no_hp,
            jenis_kelamin,
            tanggal_lahir,
            pekerjaan,
            instansi,
            alamat,
            is_profile_complete,
            foto_profil
        FROM users
        WHERE id=%s
        """,
        (
            session["user_id"],
        )
    )

    user = cursor.fetchone()

    cursor.close()

    return render_template(
        "auth/akun.html",
        user=user
    )

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/login")