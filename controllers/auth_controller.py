from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import session

from datetime import datetime
from datetime import timedelta

import pymysql
from resend import Emails
import os
import secrets
import cloudinary.uploader

from extensions import get_db

from extensions import bcrypt
from extensions import oauth

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

        if session.get("role") == "pemilik":

            return redirect(
                "/pemilik/dashboard"
            )

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

        conn = get_db()

        cursor = conn.cursor()

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
            conn.close()

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

        conn.commit()

        user_id = cursor.lastrowid

        cursor.close()
        conn.close()

        session["user_id"] = user_id
        session["nama"] = nama
        session["email"] = email
        session["role"] = role
        session["is_profile_complete"] = False
        session["foto_profil"] = None

        flash(
            "Registrasi berhasil",
            "success"
        )

        if role == "pemilik":

            return redirect(
                "/pemilik/dashboard"
            )

        return redirect(
            "/profil"
        )

    return render_template(
        "auth/register.html"
    )

# ==========================================
# LOGIN PENYEWA & PEMILIK
# ==========================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. Jika sudah login, teruskan ke dashboard masing-masing
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect("/admin/dashboard")
        elif session.get("role") == "pemilik":
            return redirect("/pemilik/dashboard")
        else:
            return redirect("/penyewa/dashboard")

    # 2. Proses POST
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nama, email, password_hash, role, foto_profil, status_akun, alasan_status, suspend_until
            FROM users WHERE email = %s
        """, (email,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            # =======================================================
            # 🚧 GERBANG ADMIN: BLOKIR ADMIN DI PORTAL USER 🚧
            # =======================================================
            if user[4] == 'admin': # user[4] adalah kolom 'role'
                flash("Akses ditolak! Akun Admin hanya dapat masuk melalui portal khusus Admin.", "danger")
                return redirect('/login')

            # =======================================================
            # 3. VERIFIKASI PASSWORD
            # =======================================================
            if bcrypt.check_password_hash(user[3], password):
                
                status_akun = user[6] if len(user) > 6 and user[6] else 'aktif'
                alasan_status = user[7] if len(user) > 7 and user[7] else ''
                suspend_until = user[8] if len(user) > 8 else None

                # 🚧 GERBANG BANNED & SUSPEND 🚧
                if status_akun == 'diblokir':
                    pesan = alasan_status if alasan_status else "Pelanggaran berat terhadap kebijakan platform."
                    flash(f"AKSES DITOLAK: Akun Anda diblokir permanen! Alasan: {pesan}", "danger")
                    return redirect('/login')
                
                elif status_akun == 'suspended':
                    from datetime import datetime
                    if suspend_until and datetime.now() >= suspend_until:
                        # Hukuman selesai, aktifkan otomatis
                        conn = get_db()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET status_akun='aktif', alasan_status=NULL, suspend_until=NULL WHERE id=%s", (user[0],))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        status_akun = 'aktif'
                    else:
                        tgl_pulih = suspend_until.strftime('%d-%m-%Y %H:%M') if suspend_until else "1 Minggu"
                        # PASTIKAN BAGIAN INI BENAR: {email} harus ada di sini
                        pesan_flash = f"AKUN DIBEKUKAN HINGGA {tgl_pulih}. Alasan: {alasan_status}. <a href='/ajukan-banding?email={email}' class='alert-link text-decoration-underline'>Klik di sini untuk Ajukan Banding</a>"
                        flash(pesan_flash, "warning")
                        return redirect('/login')

                # JIKA LOLOS, BUAT SESSION
                session['user_id'] = user[0]
                session['role'] = user[4]
                session['nama'] = user[1]
                session['foto_profil'] = user[5]

                if user[4] == 'admin':
                    return redirect('/admin/dashboard')
                elif user[4] == 'pemilik':
                    return redirect('/pemilik/dashboard')
                else:
                    return redirect('/penyewa/dashboard')
            else:
                flash("Password yang Anda masukkan salah!", "danger")
                return redirect('/login')
        else:
            flash("Alamat email tidak ditemukan di sistem!", "danger")
            return redirect('/login')

    return render_template('auth/login.html')

@auth_bp.route('/ajukan-banding', methods=['GET', 'POST'])
def ajukan_banding():
    # --- LOGIKA POST (Saat Tombol Kirim Ditekan) ---
    if request.method == 'POST':
        # AMBIL DATA DARI FORM, BUKAN URL
        email_form = request.form.get('email', '').strip()
        alasan = request.form.get('alasan_banding', '').strip()
        
        print(f"DEBUG: Email diterima dari FORM: '{email_form}'") # Cek ini di terminal!

        conn = get_db()
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        
        # 1. Cari user berdasarkan email form
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (email_form,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            flash("Email tidak terdaftar di sistem.", "danger")
            return redirect('/login')

        user_id = user['id']
        
        # 2. Cek apakah sudah ada banding pending
        cursor.execute("SELECT id FROM banding WHERE user_id = %s AND LOWER(status) = 'pending'", (user_id,))
        cek_banding = cursor.fetchone()
        
        if cek_banding:
            flash("Anda sudah memiliki pengajuan banding yang sedang diproses. Mohon tunggu.", "warning")
            cursor.close()
            conn.close()
            return redirect('/login')
            
        # 3. Simpan banding baru
        cursor.execute("INSERT INTO banding (user_id, email, alasan, status) VALUES (%s, %s, %s, 'pending')", 
                       (user_id, email_form, alasan))
        conn.commit()
        
        cursor.close()
        conn.close()
        flash("Pengajuan banding berhasil dikirim. Harap menunggu proses peninjauan.", "success")
        return redirect('/login')

    # --- LOGIKA GET (Saat Halaman Dibuka) ---
    email_url = request.args.get('email', '').strip()
    return render_template('auth/banding.html', email_params=email_url)


# ==========================================
# LOGIN KHUSUS ADMIN (PINTU RAHASIA)
# ==========================================
@auth_bp.route("/login/admin", methods=["GET","POST"])
def login_admin():
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect("/admin/dashboard")
        return redirect("/")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        # AMBIL DATA HANYA JIKA ROLENYA ADMIN
        cursor.execute(
            """
            SELECT id, nama, email, password_hash, role 
            FROM users 
            WHERE email=%s AND role='admin'
            """,
            (email,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            flash("Akses ditolak! Anda bukan admin.", "danger")
            return redirect("/login/admin")

        if not bcrypt.check_password_hash(user[3], password):
            flash("Password salah", "danger")
            return redirect("/login/admin")

        # Set Session Admin
        session["user_id"] = user[0]
        session["nama"] = user[1]
        session["email"] = user[2]
        session["role"] = user[4]

        flash("Selamat datang, Admin Pusat!", "success")
        return redirect("/admin/dashboard")

    # Pastikan kalian bikin file login_admin.html di folder templates/auth/
    return render_template("auth/login_admin.html")

@auth_bp.route(
    "/lupa-password",
    methods=["GET", "POST"]
)
def lupa_password():

    if request.method == "POST":

        email = request.form["email"]

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s
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

            conn.commit()

            reset_link = (
                request.host_url.rstrip("/")
                   +
                    f"/reset-password/{token}"
            )

            try:

                Emails.send({

                    "from": os.getenv(
                        "EMAIL_FROM"
                    ),

                    "to": [
                        "morenoaryasaputra@gmail.com"
                    ],

                    "subject":
                    "Reset Password FindYourKost",

                    "html": f"""
                    <h2>Reset Password</h2>

                    <p>
                        Klik tombol berikut
                        untuk reset password:
                    </p>

                    <p>
                        <a href="{reset_link}">
                            Reset Password
                        </a>
                    </p>

                    <p>
                        Link berlaku selama
                        1 jam.
                    </p>
                    """
                })

            except Exception as e:

                print(
                    "RESEND ERROR:",
                    e
                )

        cursor.close()

        conn.close()

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

    conn = get_db()
    cursor = conn.cursor()

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
        conn.close()

        return "Token tidak valid"

    if token_data[3] == 1:

        cursor.close()
        conn.close()

        return "Token sudah digunakan"

    if token_data[2] < datetime.now():

        cursor.close()
        conn.close()

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
            conn.close()

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

        conn.commit()

        cursor.close()
        conn.close()

        flash(
            "Password berhasil diubah. Silakan login.",
            "success"
        )

        return redirect(
            "/login"
        )

    cursor.close()
    conn.close()

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

    conn = get_db()
    cursor = conn.cursor()

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

        conn.commit()

        user_id = cursor.lastrowid

        session["user_id"] = user_id
        session["nama"] = nama
        session["email"] = email
        session["role"] = "penyewa"
        session["is_profile_complete"] = False
        session["foto_profil"] = None

        cursor.close()
        conn.close()

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
    conn.close()

    if not user[4]:

        return redirect("/profil")
    
    if user[3] == "pemilik":

        return redirect(
            "/pemilik"
        )

    return redirect("/")

@auth_bp.route(
    "/profil",
    methods=["GET", "POST"]
)
def profil():

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

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

        foto_url = None

        if foto and foto.filename != "":

            result = cloudinary.uploader.upload(
                foto,
                folder="findyourkost/profile"
            )

            foto_url = result[
                "secure_url"
            ]

        is_profile_complete = all([
            nama,
            no_hp,
            jenis_kelamin,
            tanggal_lahir,
            pekerjaan,
            alamat
        ])

        if foto_url:

            session["foto_profil"] = foto_url

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
                    foto_url,
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

        conn.commit()

        session["nama"] = nama

        session[
            "is_profile_complete"
        ] = is_profile_complete

        flash(
            "Profil berhasil diperbarui",
            "success"
        )

        cursor.close()
        conn.close()

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
    conn.close()

    return render_template(
        "auth/edit_profil.html",
        user=user
    )

@auth_bp.route("/akun")
def akun():

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

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
    conn.close()

    return render_template(
        "auth/akun.html",
        user=user
    )

@auth_bp.route("/test-resend")
def test_resend():

    try:

        email = Emails.send({

            "from": os.getenv("EMAIL_FROM"),

            "to": ["emailkamu@gmail.com"],

            "subject": "Test Resend",

            "html": """
            <h2>FindYourKost</h2>
            <p>Email berhasil dikirim dari Resend.</p>
            """
        })

        return str(email)

    except Exception as e:

        return str(e)

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/login")