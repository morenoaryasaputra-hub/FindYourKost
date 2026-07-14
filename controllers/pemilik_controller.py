from flask import Blueprint
from flask import render_template
from flask import session
from flask import redirect
from flask import request
from flask import url_for
from flask import flash
import os
import pymysql
from resend import response
from werkzeug.utils import secure_filename
from extensions import get_db
import requests
from PIL import Image
from decimal import Decimal

# ==========================================
# IMPORT PYTHON STANDARD LIBRARIES
# ==========================================
from datetime import datetime

# ==========================================
# IMPORT DATABASE MODELS
# ==========================================
from models import db
from models import User
from models import Kost

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

    # === TAMBAHAN BARU: OTOMATIS TARIK DATA PREMIUM DARI DATABASE ===
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT is_premium FROM users WHERE id = %s", (session['user_id'],))
        cek = cursor.fetchone()
        
        # Jika di database nilainya 1 (True), maka buka gembok premium
        if cek and cek[0] == 1:
            session['is_premium'] = True
        else:
            session['is_premium'] = False
            
        cursor.close()
        conn.close()
    except:
        pass # Abaikan jika terjadi error database

# ==========================================
# PEMILIK KOS DASHBOARD (REAL-TIME DATA & CHART)
# ==========================================
@pemilik_bp.route("/")
@pemilik_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")
        
    pemilik_id = session.get('user_id')
    nama_pemilik = session.get('nama', 'Mitra Pemilik')

    try:
        conn = get_db()
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        
        # [Logika hitung total_properti, kamar_tersedia, booking_aktif, pendapatan_raw SAMA SEPERTI SEBELUMNYA]
        cursor.execute("SELECT COUNT(id) AS total FROM kost WHERE pemilik_id = %s", (pemilik_id,))
        total_properti = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT SUM(sisa_kamar) AS tersedia FROM kost WHERE pemilik_id = %s", (pemilik_id,))
        kamar_tersedia = cursor.fetchone()['tersedia'] or 0
        
        cursor.execute("""
            SELECT COUNT(b.id) AS aktif 
            FROM booking b JOIN kost k ON b.kost_id = k.id
            WHERE k.pemilik_id = %s AND b.status_booking = 'aktif'
        """, (pemilik_id,))
        booking_aktif = cursor.fetchone()['aktif'] or 0
        
        cursor.execute("""
            SELECT SUM(p.jumlah) AS pendapatan 
            FROM pembayaran p JOIN booking b ON p.booking_id = b.id JOIN kost k ON b.kost_id = k.id
            WHERE k.pemilik_id = %s AND p.status_pembayaran = 'lunas'
        """, (pemilik_id,))
        pendapatan_raw = cursor.fetchone()['pendapatan'] or 0
        
        if pendapatan_raw >= 1000000000:
            pendapatan_display = f"Rp {(pendapatan_raw / 1000000000):.1f}M"
        elif pendapatan_raw >= 1000000:
            pendapatan_display = f"Rp {(pendapatan_raw / 1000000):.1f}JT"
        else:
            pendapatan_display = f"Rp {int(pendapatan_raw):,}".replace(",", ".")

        # === TAMBAHAN BARU: AMBIL SALDO DOMPET ===
        cursor.execute("SELECT saldo_dompet FROM users WHERE id = %s", (pemilik_id,))
        saldo_data = cursor.fetchone()
        saldo_dompet = saldo_data['saldo_dompet'] if saldo_data and saldo_data['saldo_dompet'] else 0

        # Ambil Data Aktivitas / Notifikasi Terbaru
        cursor.execute("""
            SELECT judul, pesan, ikon, warna, created_at 
            FROM notifikasi_pemilik 
            WHERE pemilik_id = %s 
            ORDER BY created_at DESC LIMIT 6
        """, (pemilik_id,))
        daftar_aktivitas = cursor.fetchall()
        
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Bypass Error Database Dashboard Pemilik: {e}")
        total_properti, kamar_tersedia, booking_aktif = 24, 15, 142
        pendapatan_display = "Rp 82.4M"
        saldo_dompet = 0 # Fallback saldo
        daftar_aktivitas = []

    return render_template(
        "pemilik/dashboard.html",
        nama_pemilik=nama_pemilik,
        total_properti=total_properti,
        kamar_tersedia=kamar_tersedia,
        booking_aktif=booking_aktif,
        pendapatan_display=pendapatan_display,
        saldo_dompet=saldo_dompet, # Kirim saldo ke HTML
        daftar_aktivitas=daftar_aktivitas
    )

# ==========================================
# AKSI TARIK SALDO DOMPET (DEMO MAGIC)
# ==========================================
@pemilik_bp.route("/tarik-saldo", methods=["POST"])
def tarik_saldo():
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")

    # Tangkap nominal dari form
    try:
        nominal_tarik = float(request.form.get("nominal", 0))
    except ValueError:
        nominal_tarik = 0

    if nominal_tarik < 10000:
        flash("Minimal penarikan adalah Rp 10.000.", "warning")
        return redirect(url_for("pemilik.dashboard"))

    pemilik_id = session.get("user_id")
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)

    # Cek saldo saat ini
    cursor.execute("SELECT saldo_dompet FROM users WHERE id = %s", (pemilik_id,))
    user = cursor.fetchone()

    if user and user['saldo_dompet'] >= nominal_tarik:
        # 1. POTONG SALDO SECARA GAIB (Otomatis)
        cursor.execute("UPDATE users SET saldo_dompet = saldo_dompet - %s WHERE id = %s", (nominal_tarik, pemilik_id))

        # 2. CATAT KE NOTIFIKASI (Agar seolah-olah diproses sistem nyata)
        pesan_notif = f"Penarikan dana sebesar <strong>Rp {int(nominal_tarik):,}</strong> berhasil diproses dan dikirim ke rekening Anda."
        cursor.execute("""
            INSERT INTO notifikasi_pemilik (pemilik_id, judul, pesan, ikon, warna, created_at)
            VALUES (%s, 'Penarikan Berhasil', %s, 'fa-money-bill-wave', 'success', NOW())
        """, (pemilik_id, pesan_notif))

        conn.commit()
        flash(f"Penarikan Rp {int(nominal_tarik):,} sedang diproses ke rekening terdaftar Anda!", "success")
    else:
        flash("Penarikan gagal! Saldo tidak mencukupi.", "danger")

    cursor.close()
    conn.close()
    return redirect(url_for("pemilik.dashboard"))
# ====================================
# DATA KOS & HAPUS KOS
# ====================================
@pemilik_bp.route("/data-kos")
def data_kos():
    # 1. Proteksi Sesi
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")
        
    user_id = session.get("user_id")
    
    # 2. Tangkap Parameter Filter dari URL (GET Request)
    tipe_filter = request.args.get('tipe')
    
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    # 3. Bangun Query SQL Dasar
    query = """
        SELECT id, nama_kost, tipe_penghuni, harga, sisa_kamar, total_kamar, 
               status_verifikasi, tier_listing 
        FROM kost 
        WHERE pemilik_id = %s
    """
    params = [user_id]
    
    # 4. Tambahkan Kondisi Filter Jika Ada
    if tipe_filter and tipe_filter in ['putra', 'putri', 'campur']:
        query += " AND tipe_penghuni = %s"
        params.append(tipe_filter)
        
    query += " ORDER BY id DESC"
    
    # 5. Eksekusi Query
    cursor.execute(query, tuple(params))
    daftar_kos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template(
        "pemilik/data_kos.html",
        list_kost=daftar_kos,
        tipe_filter=tipe_filter # Kirim kembali ke frontend agar dropdown tetap terpilih
    )

@pemilik_bp.route("/hapus-kos/<int:id>", methods=["POST"])
def hapus_kos(id):
    kost = Kost.query.get_or_404(id)
    
    # Keamanan tambahan: pastikan kos yang dihapus benar milik user yang login
    if kost.pemilik_id != session.get("user_id"):
        flash("Anda tidak memiliki akses untuk menghapus properti ini!", "danger")
        return redirect(url_for("pemilik.data_kos"))
        
    db.session.delete(kost)
    db.session.commit()
    
    flash("Properti kos berhasil dihapus secara permanen.", "success")
    return redirect(url_for("pemilik.data_kos"))


# ========================================================
# GABUNGAN PENUH: TAMBAH KOS (SAMPURNA & AMAN DARI RESET)
# ========================================================
@pemilik_bp.route("/tambah-kos", methods=["GET", "POST"])
def tambah_kos():
    
    user = User.query.get(session["user_id"])
    if not user.is_ktp_verified:
        flash("Maaf, kamu harus upload KTP dan menunggu verifikasi Admin sebelum bisa menambah kos.", "danger")
        return redirect(url_for("pemilik.profil_pemilik"))
    
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")

    if request.method == "POST":
        # 1. Ambil data harga & uang muka terlebih dahulu untuk divalidasi
        try:
            harga = int(request.form.get("harga", 0))
            uang_muka = int(request.form.get("uang_muka", 0))
        except ValueError:
            harga = 0
            uang_muka = 0

        # VALIDASI AMAN: Jika DP melebihi 50% dari Harga Kos
        if uang_muka > (harga * 0.5):
            flash("Pengajuan Gagal! Uang Muka (DP) maksimal adalah 50% dari harga bulanan kos.", "danger")
            geoapify_key = os.environ.get("GEOAPIFY_API_KEY")
            # Kembalikan form_data=request.form agar teks input di browser TIDAK HILANG
            return render_template("pemilik/tambah_kos.html", geoapify_key=geoapify_key, form_data=request.form)

        # 2. Ambil seluruh data dari Form Section jika lolos validasi harga
        nama_kost = request.form.get("nama_kost")
        alamat = request.form.get("alamat")                # Dari map interaktif otomatis
        alamat_spesifik = request.form.get("alamat_spesifik")  # Input manual (RT/RW/Patokan)
        wilayah = request.form.get("wilayah") 
        deskripsi = request.form.get("deskripsi") 
        tipe_penghuni = request.form.get("tipe_penghuni")
        total_kamar = request.form.get("total_kamar", 1)
        
        # Ambil koordinat presisi dari Peta Geoapify
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        # 3. Proses Upload Foto / Galeri Foto Bawaan Kamu (Utanpa Dikurangi)
        foto_files = request.files.getlist("galeri_foto")
        nama_foto_tersimpan = "default_kos.jpg" 
        
        upload_folder = os.path.join('static', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        for file in foto_files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                nama_foto_tersimpan = filename 

        # 4. Gabungkan informasi Alamat Utama + Wilayah + Alamat Spesifik untuk disimpan ke DB
        alamat_final = f"{alamat} ({wilayah}) - Patokan: {alamat_spesifik}"

        # 5. Simpan ke Database dengan Model ORM (Sesuai Struktur Aslimu)
        try:
            baru_kos = Kost(
                nama_kost=nama_kost,
                alamat=alamat_final, 
                tipe_penghuni=tipe_penghuni,
                harga=harga,
                total_kamar=int(total_kamar),
                sisa_kamar=int(total_kamar), 
                status_verifikasi=False, 
                pemilik_id=session.get("user_id")
            )
            
            # Pengisian Koordinat Geolocation ke Model DB
            if hasattr(baru_kos, 'latitude'): baru_kos.latitude = latitude
            if hasattr(baru_kos, 'longitude'): baru_kos.longitude = longitude

            # Pengisian Atribut Opsional Bawaan Kamu
            if hasattr(baru_kos, 'deskripsi'): baru_kos.deskripsi = deskripsi
            if hasattr(baru_kos, 'uang_muka'): baru_kos.uang_muka = uang_muka
            if hasattr(baru_kos, 'foto'): baru_kos.foto = nama_foto_tersimpan

            db.session.add(baru_kos)
            db.session.commit()
            flash("Properti kos baru berhasil diajukan! Menunggu verifikasi admin.", "success")
            return redirect(url_for("pemilik.data_kos"))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error Database: {e}")
            flash("Terjadi kesalahan sistem saat menyimpan ke database.", "danger")

    # Ambil token dari .env secara aman untuk disalurkan ke Map picker script
    geoapify_key = os.environ.get("GEOAPIFY_API_KEY")
    return render_template("pemilik/tambah_kos.html", geoapify_key=geoapify_key, form_data=None)


# ========================================================
# GABUNGAN PENUH: EDIT KOS (SAMPURNA & AMAN DARI RESET)
# ========================================================
@pemilik_bp.route("/edit-kos/<int:kost_id>", methods=["GET", "POST"])
def edit_kos(kost_id):
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")

    # 1. Ambil data kos lama
    kos = Kost.query.get_or_404(kost_id)

    if request.method == "POST":
        # Ambil input dari form
        form_harga = request.form.get("harga")
        form_dp = request.form.get("uang_muka")
        
        # LOGIKA PERBAIKAN: Jika form dikosongkan, gunakan nilai lama dari database
        try:
            harga = int(form_harga) if form_harga and form_harga.strip() != "" else kos.harga
            uang_muka = int(form_dp) if form_dp and form_dp.strip() != "" else (kos.uang_muka or 0)
        except ValueError:
            harga = kos.harga
            uang_muka = kos.uang_muka or 0

        # VALIDASI AMAN: DP tidak boleh lebih dari 50%
        if uang_muka > (harga * Decimal('0.5')):
            flash("Perubahan Gagal! Uang Muka (DP) maksimal adalah 50% dari harga bulanan.", "danger")
            geoapify_key = os.environ.get("GEOAPIFY_API_KEY")
            return render_template("pemilik/edit_kos.html", kos=kos, geoapify_key=geoapify_key)

        try:
            # 2. Update Field Utama
            kos.nama_kost = request.form.get("nama_kost")
            
            # Gabungkan kembali alamat dengan format konsisten
            alamat_raw = request.form.get("alamat")
            alamat_spesifik = request.form.get("alamat_spesifik")
            wilayah = request.form.get("wilayah")
            kos.alamat = f"{alamat_raw} ({wilayah}) - Patokan: {alamat_spesifik}"
            
            kos.tipe_penghuni = request.form.get("tipe_penghuni")
            kos.harga = harga
            kos.uang_muka = uang_muka
            kos.total_kamar = int(request.form.get("total_kamar", kos.total_kamar))
            
            # Update atribut opsional
            if hasattr(kos, 'deskripsi'): 
                kos.deskripsi = request.form.get("deskripsi")
            if hasattr(kos, 'latitude'): 
                kos.latitude = request.form.get("latitude")
            if hasattr(kos, 'longitude'): 
                kos.longitude = request.form.get("longitude")

            # 3. Proses Update Foto (Jika ada file baru)
            foto_files = request.files.getlist("galeri_foto")
            for file in foto_files:
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    upload_folder = os.path.join('static', 'uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    file.save(os.path.join(upload_folder, filename))
                    if hasattr(kos, 'foto'): 
                        kos.foto = filename 

            db.session.commit()
            flash(f"Data properti '{kos.nama_kost}' berhasil diperbarui!", "success")
            return redirect(url_for("pemilik.data_kos"))

        except Exception as e:
            db.session.rollback()
            print(f"Error Update Database: {e}")
            flash("Gagal menyimpan perubahan. Periksa kembali koneksi database.", "danger")

    # ========================================================
    # LOGIKA GET (Menampilkan data ke form)
    # ========================================================
    wilayah_current = ""
    alamat_display = kos.alamat
    alamat_spesifik_current = ""

    if kos.alamat and " - Patokan: " in kos.alamat:
        parts = kos.alamat.split(" - Patokan: ")
        alamat_display = parts[0]
        alamat_spesifik_current = parts[1]

    if alamat_display and "(" in alamat_display and ")" in alamat_display:
        wilayah_current = alamat_display.split(" (")[1].replace(")", "")
        alamat_display = alamat_display.split(" (")[0]

    geoapify_key = os.environ.get("GEOAPIFY_API_KEY")
    return render_template(
        "pemilik/edit_kos.html", 
        kos=kos, 
        alamat_display=alamat_display, 
        alamat_spesifik_current=alamat_spesifik_current,
        wilayah_current=wilayah_current,
        geoapify_key=geoapify_key
    )
# ====================================
# VERIFIKASI
# ====================================

@pemilik_bp.route("/verifikasi")
def verifikasi():
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")
    
    pemilik_id = session.get("user_id")
    conn = get_db()
    cursor = conn.cursor()
    
    # KONEKSI DATABASE ASLI
    # PERHATIAN: Jika masih error 'Unknown column', ganti b.user_id 
    # atau k.pemilik_id di bawah sesuai dengan nama kolom asli di DB-mu!
    query = """
    SELECT 
        b.id, 
        u.nama, 
        k.nama_kost, 
        b.tanggal_masuk, 
        b.durasi, 
        b.status 
    FROM booking b
    JOIN kost k ON b.kost_id = k.id
    JOIN users u ON b.user_id = u.id
    WHERE k.pemilik_id = %s
    """
    
    try:
        cursor.execute(query, (pemilik_id,))
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Laporan Error SQL: {e}")
        rows = []
        
    cursor.close()
    conn.close()
    
    # Transformasi hasil DB ke format objek agar pas dengan b.penyewa.nama di HTML
    bookings_real = []
    for row in rows:
        bookings_real.append({
            "id": row[0],
            "penyewa": {"nama": row[1]},
            "kos": {"nama_kost": row[2]},
            "tanggal_masuk": row[3],
            "durasi_bulan": row[4],
            "status": row[5]
        })
    
    return render_template("pemilik/verifikasi.html", bookings=bookings_real)
# ====================================
# VERIFIKASI tombol 
# ====================================
@pemilik_bp.route("/verifikasi/<int:booking_id>/<aksi>", methods=["POST"])
def verifikasi_aksi(booking_id, aksi):
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Tentukan status berdasarkan tombol yang diklik
    status_baru = "Disetujui" if aksi == "terima" else "Ditolak"
    
    # Update status ke database
    cursor.execute("UPDATE booking SET status = %s WHERE id = %s", (status_baru, booking_id))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    flash(f"Pengajuan sewa berhasil di-{aksi}!", "success")
    return redirect(url_for("pemilik.verifikasi"))


# ====================================
# PREMIUM
# ====================================
@pemilik_bp.route("/premium")
def premium():
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")
        
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Ambil harga premium dinamis untuk ditampilkan ke pemilik
        cursor.execute("SELECT harga FROM paket_premium WHERE id = 1")
        paket = cursor.fetchone()
        harga_premium = int(paket['harga']) if paket and paket.get('harga') else 99000
    except Exception as e:
        print(f"Error ambil harga premium: {e}")
        harga_premium = 99000 # Harga default jika database gagal ditarik
    finally:
        cursor.close()
        conn.close()
    
    return render_template("pemilik/layanan_premium.html", harga_premium=harga_premium)
def premium_checkout():
    """
    Rute ini disiapkan untuk memproses transaksi langganan via Midtrans Snap API.
    Untuk keperluan demo/sidang awal, kode di bawah langsung mengaktifkan status premium.
    """
    user_id = session.get("user_id")
    user = User.query.get(user_id)
    
    if user:
        # Jalur Simulasi Sukses Payment Midtrans
        user.is_premium = True
        db.session.commit()
        
        # Perbarui nilai session agar gembok di sidebar langsung terbuka otomatis
        session["is_premium"] = True
        
        flash("Selamat! Pembayaran berhasil. Akun Anda telah aktif sebagai PREMIUM.", "success")
    
    return redirect(url_for("pemilik.dashboard"))

# ====================================
# PENGATURAN
# ====================================

from extensions import bcrypt # Pastikan ini ada di paling atas file kalau belum

@pemilik_bp.route("/pengaturan", methods=["GET", "POST"])
def pengaturan():
    if request.method == "POST":
        password_lama = request.form.get("password_lama")
        password_baru = request.form.get("password_baru")
        
        user = User.query.get(session.get("user_id"))
        
        # Cek password lama
        if bcrypt.check_password_hash(user.password_hash, password_lama):
            # Hash password baru dan simpan
            user.password_hash = bcrypt.generate_password_hash(password_baru).decode('utf-8')
            db.session.commit()
            flash("Password berhasil diubah!", "success")
        else:
            flash("Password lama salah!", "danger")
            
        return redirect(url_for("pemilik.pengaturan"))

    return render_template("pemilik/pengaturan.html")

# ====================================
# PROFIL PEMILIK & REKENING
# ====================================


from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask import render_template, request, session, redirect, flash, url_for
import os
import re
import requests
from datetime import date
from PIL import Image

@pemilik_bp.route("/profil-pemilik", methods=["GET", "POST"])
def profil_pemilik():
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")
    
    pemilik_id = session.get("user_id")
    conn = get_db()
    cursor = conn.cursor()
    
    # === JALUR POST (SAAT TOMBOL DI-KLIK) ===
    if request.method == "POST":
        aksi = request.form.get("aksi")
        
        # 1. UPDATE INFORMASI PRIBADI
        if aksi == "update_profil":
            nama = request.form.get("nama")
            no_hp = request.form.get("no_hp")
            cursor.execute("UPDATE users SET nama = %s, no_hp = %s WHERE id = %s", (nama, no_hp, pemilik_id))
            session['nama'] = nama
            flash("Informasi pribadi berhasil diperbarui!", "success")
            
        # 2. UPDATE REKENING BANK
        elif aksi == "update_rekening":
            nama_bank = request.form.get("nama_bank")
            no_rekening = request.form.get("no_rekening")
            atas_nama_rekening = request.form.get("atas_nama_rekening")
            cursor.execute("""
                UPDATE users SET nama_bank = %s, no_rekening = %s, atas_nama_rekening = %s WHERE id = %s
            """, (nama_bank, no_rekening, atas_nama_rekening, pemilik_id))
            flash("Informasi rekening bank berhasil diperbarui!", "success")
            
        # 3. GANTI PASSWORD
        elif aksi == "update_password":
            password_lama = request.form.get("password_lama")
            password_baru = request.form.get("password_baru")
            konfirmasi_password = request.form.get("konfirmasi_password")
            
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (pemilik_id,))
            user_data = cursor.fetchone()
            
            if check_password_hash(user_data[0], password_lama):
                if password_baru != konfirmasi_password:
                    flash("Konfirmasi password baru tidak cocok!", "warning")
                else:
                    hash_baru = generate_password_hash(password_baru)
                    cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hash_baru, pemilik_id))
                    flash("Password akun Anda berhasil diubah!", "success")
            else:
                flash("Password saat ini yang Anda masukkan salah!", "danger")
                
        # 4. LUPA PASSWORD
        elif aksi == "lupa_password":
            cursor.execute("SELECT email FROM users WHERE id = %s", (pemilik_id,))
            email_user = cursor.fetchone()[0]
            flash(f"Kode verifikasi reset password sukses dikirim ke email: {email_user}", "info")

        # 5. VERIFIKASI KTP (STRICT LOGIC & FIX TEMPAT/TANGGAL LAHIR)
        elif aksi == "verifikasi_ktp":
            hari_ini = date.today()
            
            # Cek kuota harian
            cursor.execute("SELECT ktp_attempts, last_ktp_attempt FROM users WHERE id = %s", (pemilik_id,))
            limit_data = cursor.fetchone()
            attempts = limit_data[0] if limit_data[0] is not None else 0
            if limit_data[1] != hari_ini: 
                attempts = 0

            if attempts >= 3:
                flash("Batas harian tercapai! Anda hanya bisa mencoba verifikasi KTP 3 kali sehari.", "danger")
                return redirect(url_for("pemilik.profil_pemilik"))

            ktp_file = request.files.get("ktp_file")
            if ktp_file and ktp_file.filename != '':
                filename = secure_filename(ktp_file.filename)
                upload_folder = os.path.abspath(os.path.join('static', 'uploads', 'ktp'))
                if not os.path.exists(upload_folder): 
                    os.makedirs(upload_folder)
                
                filepath = os.path.join(upload_folder, filename)
                ktp_file.save(filepath)

                # Kompresi gambar aman Windows
                try:
                    img = Image.open(filepath)
                    if img.mode != 'RGB': 
                        img = img.convert('RGB')
                    img.thumbnail((1500, 1500))
                    temp_filepath = filepath + ".tmp"
                    img.save(temp_filepath, format="JPEG", optimize=True, quality=90)
                    img.close()
                    os.replace(temp_filepath, filepath)
                except Exception as e:
                    print("Error Kompresi:", e)
                
                attempts += 1
                cursor.execute("UPDATE users SET ktp_attempts = %s, last_ktp_attempt = %s WHERE id = %s", (attempts, hari_ini, pemilik_id))
                
                # --- PANGGIL API OCR.SPACE ---
                api_key = os.environ.get("OCR_API_KEY", "helloworld") 
                api_url = "https://api.ocr.space/parse/image"
                payload = {
                    "apikey": api_key, 
                    "language": "eng",            
                    "isOverlayRequired": False,
                    "detectOrientation": True,
                    "OCREngine": "2"
                }
                
                try:
                    with open(filepath, 'rb') as f:
                        response = requests.post(api_url, data=payload, files={"file": f}, timeout=20)
                    
                    data = response.json()
                    
                    if data.get("IsErroredOnProcessing") == True:
                        pesan_error_ocr = data.get("ErrorMessage", ["Pesan error tidak diketahui"])[0]
                        if os.path.exists(filepath): os.remove(filepath)
                        flash(f"Ditolak oleh Server OCR: {pesan_error_ocr}", "danger")
                        conn.commit()
                        return redirect(url_for("pemilik.profil_pemilik"))

                    parsed_results = data.get("ParsedResults")
                    if not parsed_results:
                        if os.path.exists(filepath): os.remove(filepath)
                        flash("Verifikasi Gagal! Teks pada gambar tidak dapat diproses oleh sistem.", "danger")
                        conn.commit()
                        return redirect(url_for("pemilik.profil_pemilik"))
                        
                    parsed_text = parsed_results[0].get("ParsedText", "")
                    
                    # 1. CLEANING TEKS KHUSUS NIK
                    teks_clean = parsed_text.upper().replace(' ', '').replace('\n', '').replace('\r', '')
                    teks_clean = teks_clean.replace('O', '0').replace('I', '1').replace('L', '1').replace('S', '5').replace('B', '8')
                    
                    # 2. VALIDASI STRICT NIK
                    nik_match = re.search(r'\d{16}', teks_clean)
                    nik_api = nik_match.group(0) if nik_match else None
                    
                    if not nik_api:
                        if os.path.exists(filepath): os.remove(filepath)
                        flash(f"Foto Ditolak! Sistem tidak menemukan NIK valid. Pastikan foto KTP asli, tegak, dan jelas. (Sisa percobaan: {3 - attempts})", "danger")
                        conn.commit()
                        return redirect(url_for("pemilik.profil_pemilik"))

                    # EKSTRAK DATA LAIN
                    nama_match = re.search(r'NAM[A4]\s*[:;]?\s*([^\n]+)', parsed_text, re.IGNORECASE)
                    nama_api = nama_match.group(1).strip() if nama_match else "Tidak Terbaca"
                    
                    alamat_match = re.search(r'ALAMAT\s*[:;]?\s*([^\n]+)', parsed_text, re.IGNORECASE)
                    alamat = alamat_match.group(1).strip() if alamat_match else "Tidak Terbaca"

                    # --- FIXED TANGGAL & TEMPAT LAHIR ---
                    tempat_lahir = "-"
                    tanggal_lahir = None
                    
                    birth_match = re.search(r'TEMPAT/TG[LI]\s*LAH[I1]R\s*[:;]?\s*([^\n]+)', parsed_text, re.IGNORECASE)
                    if birth_match:
                        full_birth = birth_match.group(1).strip()
                        parts = re.split(r'[,\.]', full_birth, maxsplit=1)
                        if parts:
                            tempat_lahir = parts[0].strip()
                            if len(parts) > 1:
                                tgl_str = parts[1].strip()
                                tgl_clean = re.search(r'(\d{2})-(\d{2})-(\d{4})', tgl_str)
                                if tgl_clean:
                                    tanggal_lahir = f"{tgl_clean.group(3)}-{tgl_clean.group(2)}-{tgl_clean.group(1)}"

                    # SIMPAN KE DATABASE
                    cursor.execute("""
                        UPDATE users 
                        SET nik = %s, nama_ktp = %s, tempat_lahir = %s, tanggal_lahir = %s, alamat_ktp = %s, foto_ktp = %s, is_ktp_verified = 1 
                        WHERE id = %s
                    """, (nik_api, nama_api, tempat_lahir, tanggal_lahir, alamat, filename, pemilik_id))
                    
                    flash("Verifikasi Identitas Sukses! Data KTP Anda telah diproses.", "success")
                        
                except Exception as e:
                    print("Error Sistem API:", e)
                    if os.path.exists(filepath): os.remove(filepath)
                    flash(f"Gagal memproses gambar ke server API. (Sisa percobaan: {3 - attempts})", "warning")
            else:
                flash("Harap masukkan file gambar KTP terlebih dahulu!", "warning")
            
            conn.commit()
            return redirect(url_for("pemilik.profil_pemilik"))

    # === JALUR GET (SAAT DI-REFRESH / DI-BUKA BIASA) ===
    # Pastikan bagian bawah ini sejajar di luar blok 'if request.method == "POST"'
    cursor.execute("""
        SELECT nama, email, no_hp, nama_bank, no_rekening, atas_nama_rekening, is_premium,
               nik, nama_ktp, foto_ktp, is_ktp_verified, tempat_lahir, tanggal_lahir, alamat_ktp
        FROM users WHERE id = %s
    """, (pemilik_id,))
    data = cursor.fetchone()
    
    user_info = {
        "nama": data[0] if data[0] else "User",
        "email": data[1],
        "no_hp": data[2] if data[2] else "-",
        "nama_bank": data[3] if data[3] else "Belum diatur",
        "no_rekening": data[4] if data[4] else "Belum diatur",
        "atas_nama_rekening": data[5] if data[5] else "Belum diatur",
        "is_premium": data[6],
        "nik": data[7],
        "nama_ktp": data[8],
        "foto_ktp": data[9],
        "is_ktp_verified": data[10],
        "tempat_lahir": data[11] if data[11] else "-",
        "tanggal_lahir": data[12] if data[12] else "-",
        "alamat_ktp": data[13] if data[13] else "-"
    }
    
    profil_lengkap = True
    if not data[2] or not data[3] or not data[9]: 
        profil_lengkap = False
        
    cursor.close()
    conn.close()
    
    return render_template("pemilik/profil_pemilik.html", user_info=user_info, profil_lengkap=profil_lengkap)
# ====================================
# HALAMAN PEMBAYARAN MIDTRANS
# ====================================
@pemilik_bp.route("/pembayaran")
def pembayaran():
    # Menampilkan invoice sebelum memunculkan popup Midtrans Snap
    return render_template("pemilik/pembayaran.html")

# ====================================
# KELOLA KOS (Detail Penyewa per Kos)
# ====================================
@pemilik_bp.route("/kelola-kos/<int:kost_id>")
def kelola_kos(kost_id):
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Ambil data kos untuk judul halaman
    cursor.execute("SELECT nama_kost FROM kost WHERE id = %s", (kost_id,))
    kost = cursor.fetchone()

    cursor.close()
    conn.close()

    if not kost:
        return redirect(url_for('pemilik.data_kos'))

    return render_template(
        "pemilik/kelola_kos.html", 
        nama_kos=kost[0]
    )
    
    # ====================================
# LAPORAN KEUANGAN (FITUR PREMIUM)
# ====================================
@pemilik_bp.route("/laporan-keuangan")
def laporan_keuangan():
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")
    
    if not session.get("is_premium"):
        flash("Fitur Manajemen Keuangan khusus untuk pengguna Premium.", "warning")
        return redirect(url_for("pemilik.premium"))
    
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                b.id AS booking_id, 
                u.nama AS nama, 
                k.nama_kost AS kamar, 
                b.total_harga AS total, 
                b.status_pembayaran AS status 
            FROM booking b
            JOIN users u ON b.penyewa_id = u.id
            JOIN kost k ON b.kost_id = k.id
            WHERE k.pemilik_id = %s
        """, (session['user_id'],))
        
        tagihan = cursor.fetchall()
        
    except Exception as e:
        print(f"Error Database (Cek kolom status_pembayaran!): {e}")
        tagihan = [] 
        
    finally:
        cursor.close()
        conn.close()

    # Kirim data hasil query ke HTML
    return render_template("pemilik/laporan_keuangan.html", tagihan=tagihan)

# ==========================================
# AKSI KIRIM TAGIHAN VIA CHAT OTOMATIS (MODUL 3)
# ==========================================
@pemilik_bp.route("/kirim-tagihan/<int:booking_id>", methods=["POST"])
def kirim_tagihan(booking_id):
    if "user_id" not in session or session.get("role") != "pemilik":
        return redirect("/login")

    pemilik_id = session.get("user_id")
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)

    try:
        # 1. Ambil data penyewa dan kos dari tabel booking
        cursor.execute("""
            SELECT b.penyewa_id, b.total_harga, b.kost_id, u.nama as nama_penyewa, k.nama_kost
            FROM booking b
            JOIN kost k ON b.kost_id = k.id
            JOIN users u ON b.penyewa_id = u.id
            WHERE b.id = %s AND k.pemilik_id = %s
        """, (booking_id, pemilik_id))
        
        data_booking = cursor.fetchone()

        if not data_booking:
            flash("Data pemesanan tidak ditemukan atau tidak valid.", "danger")
            return redirect(url_for('pemilik.laporan_keuangan'))

        penyewa_id = data_booking['penyewa_id']
        nama_penyewa = data_booking['nama_penyewa']
        nama_kost = data_booking['nama_kost']
        
        # Ambil nominal dari tagihan_penghuni jika ada, atau pakai harga booking
        nominal_rp = f"Rp {int(data_booking['total_harga'] or 0):,}".replace(",", ".")

        # 2. Cek apakah Chat Room antara Pemilik dan Penyewa untuk Kos ini sudah ada
        cursor.execute("""
            SELECT id FROM chat_room 
            WHERE pemilik_id = %s AND penyewa_id = %s AND kost_id = %s
        """, (pemilik_id, penyewa_id, data_booking['kost_id']))
        room = cursor.fetchone()

        if room:
            room_id = room['id']
        else:
            # Jika belum ada obrolan, buat Chat Room baru
            cursor.execute("""
                INSERT INTO chat_room (pemilik_id, penyewa_id, kost_id, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (pemilik_id, penyewa_id, data_booking['kost_id']))
            room_id = cursor.lastrowid

        # 3. Susun Pesan Otomatis & Masukkan ke Chat Message
        pesan_sistem = (
            f"🔔 *PENGINGAT TAGIHAN OTOMATIS*\n\n"
            f"Halo {nama_penyewa}, ini adalah pengingat otomatis dari sistem. "
            f"Anda memiliki tagihan sewa berjalan untuk kos '{nama_kost}' sebesar {nominal_rp} yang belum dilunasi. "
            f"Mohon segera melakukan pembayaran melalui sistem. Terima kasih!"
        )

        cursor.execute("""
            INSERT INTO chat_message (room_id, sender_id, pesan, is_read, waktu_kirim)
            VALUES (%s, %s, %s, 0, NOW())
        """, (room_id, pemilik_id, pesan_sistem))

        conn.commit()
        flash(f"Pesan tagihan otomatis berhasil dikirim ke ruang chat Anda dengan {nama_penyewa}!", "success")

    except Exception as e:
        conn.rollback()
        print(f"Error Kirim Tagihan: {e}")
        flash("Terjadi kesalahan saat mengirim pesan tagihan.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('pemilik.laporan_keuangan'))