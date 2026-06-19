from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import session

from datetime import datetime
from datetime import timedelta
from flask_mail import Message

import secrets

import os
from werkzeug.utils import secure_filename

from extensions import mysql
from extensions import bcrypt
from extensions import oauth
from extensions import mail

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
    "/lupa-password",
    methods=["GET","POST"]
)
def lupa_password():

    if request.method == "POST":

        email = request.form["email"]

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if user:

            token = secrets.token_urlsafe(
                32
            )

            expired_at = (
                datetime.now()
                +
                timedelta(hours=1)
            )

            cursor.execute(
                """
                INSERT INTO
                password_reset_tokens
                (
                    user_id,
                    token,
                    expired_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    user[0],
                    token,
                    expired_at
                )
            )

            mysql.connection.commit()

            reset_link = (
                f"http://127.0.0.1:5000"
                f"/reset-password/{token}"
            )

            msg = Message(
                "Reset Password FindYourKost",
                recipients=[email]
            )

            msg.body = f"""
Halo,

Klik link berikut untuk
mengatur ulang password:

{reset_link}

Link berlaku selama 1 jam.

Jika Anda tidak meminta
reset password, abaikan email ini.
"""

            mail.send(msg)

        cursor.close()

        flash(
            "Jika email terdaftar, tautan reset password telah dikirim.",
            "success"
        )

        return redirect(
            "/lupa-password"
        )

    return render_template(
        "auth/lupa_password.html"
    )

@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET","POST"]
)
def reset_password(token):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            expired_at,
            is_used
        FROM password_reset_tokens
        WHERE token=%s
        """,
        (token,)
    )

    token_data = cursor.fetchone()

    if not token_data:

        cursor.close()

        return "Token tidak valid"

    if token_data[3] == 1:

        cursor.close()

        return "Token sudah digunakan"

    if token_data[2] < datetime.now():

        cursor.close()

        return "Token sudah kadaluarsa"

    if request.method == "POST":

        password = request.form[
            "password"
        ]

        confirm_password = request.form[
            "confirm_password"
        ]

        if password != confirm_password:

            flash(
                "Konfirmasi password tidak cocok",
                "danger"
            )

            cursor.close()

            return redirect(
                request.url
            )

        password_hash = bcrypt.generate_password_hash(
            password
        ).decode(
            "utf-8"
        )

        cursor.execute(
            """
            UPDATE users
            SET password_hash=%s
            WHERE id=%s
            """,
            (
                password_hash,
                token_data[1]
            )
        )

        cursor.execute(
            """
            UPDATE password_reset_tokens
            SET is_used=1
            WHERE id=%s
            """,
            (
                token_data[0],
            )
        )

        mysql.connection.commit()

        cursor.close()

        flash(
            "Password berhasil diubah. Silakan login.",
            "success"
        )

        return redirect(
            "/login"
        )

    cursor.close()

    return render_template(
        "auth/reset_password.html",
        token=token
    )

@auth_bp.route(
    "/login/google"
)
def login_google():

    google = oauth.create_client(
        "google"
    )

    redirect_uri = url_for(
        "auth.google_callback",
        _external=True
    )

    return google.authorize_redirect(
        redirect_uri
    )

@auth_bp.route(
    "/login/google/callback"
)
def google_callback():

    google = oauth.create_client(
        "google"
    )

    token = google.authorize_access_token()

    user_info = token[
        "userinfo"
    ]

    email = user_info["email"]

    nama = user_info["name"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            nama,
            email,
            role,
            is_profile_complete,
            foto_profil
        FROM users
        WHERE email=%s
        """,
        (email,)
    )

    user = cursor.fetchone()

    if not user:

        cursor.execute(
            """
            INSERT INTO users
            (
                nama,
                email,
                role,
                is_profile_complete
            )
            VALUES
            (
                %s,
                %s,
                'penyewa',
                FALSE
            )
            """,
            (
                nama,
                email
            )
        )

        mysql.connection.commit()

        user_id = cursor.lastrowid

        session["user_id"] = user_id
        session["nama"] = nama
        session["email"] = email
        session["role"] = "penyewa"
        session["is_profile_complete"] = False
        session["foto_profil"] = None

        cursor.close()

        return redirect("/profil")

    session["user_id"] = user[0]
    session["nama"] = user[1]
    session["email"] = user[2]
    session["role"] = user[3]
    session["is_profile_complete"] = bool(
        user[4]
    )
    session["foto_profil"] = user[5]

    cursor.close()

    if not user[4]:

        return redirect("/profil")

    return redirect("/")

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