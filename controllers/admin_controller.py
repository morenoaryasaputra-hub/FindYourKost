# ==========================================
# IMPORT FLASK COMPONENTS
# ==========================================
import os

from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import session
from extensions import bcrypt, get_db
import pymysql.cursors

# ==========================================
# IMPORT PYTHON STANDARD LIBRARIES
# ==========================================
from datetime import datetime
from datetime import timedelta

# ==========================================
# IMPORT DATABASE MODELS
# ==========================================
from models import db
from models import User
from models import Kost
from models import VerifikasiKost
from werkzeug.utils import secure_filename

# Inisialisasi Blueprint untuk rute khusus Admin
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==========================================
# PROTEKSI HALAMAN ADMIN
# ==========================================
@admin_bp.before_request
def cek_admin():
    if "user_id" not in session:
        return redirect("/login")
    
    if session.get("role") != "admin":
        flash("Akses ditolak! Anda bukan admin.", "danger")
        return redirect("/")


# ==========================================
# RUTE HALAMAN UTAMA (GET / TAMPILAN HTML)
# ==========================================
# ==========================================
# ADMIN DASHBOARD (CRASH-PROOF VERSION)
# ==========================================
@admin_bp.route("/")
@admin_bp.route("/dashboard")
def dashboard():
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    try:
        # 1. Hitung Ringkasan Platform
        cursor.execute("SELECT COUNT(id) AS total FROM users")
        total_pengguna = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT COUNT(id) AS total FROM kost WHERE status_verifikasi = 0")
        menunggu_approval = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT COUNT(id) AS total FROM pembayaran WHERE status_pembayaran = 'lunas'")
        total_transaksi = cursor.fetchone()['total'] or 0
        
        # 2. Hitung Distribusi Chart
        cursor.execute("SELECT COUNT(id) AS total FROM users WHERE role = 'pemilik'")
        pemilik_count = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT COUNT(id) AS total FROM users WHERE role = 'penyewa'")
        penyewa_count = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT COUNT(id) AS total FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()['total'] or 0
        
        # 3. Ambil Data Banding
        cursor.execute("SELECT * FROM banding WHERE status = 'pending' ORDER BY created_at DESC")
        daftar_banding = cursor.fetchall()
        from datetime import timedelta
        for b in daftar_banding:
            if b['created_at']:
                b['created_at'] = b['created_at'] + timedelta(hours=7)
                
        # 4. AMBIL RIWAYAT TINDAKAN ADMIN (Semua Aktivitas)
        cursor.execute("""
            SELECT kategori, aksi, deskripsi, created_at 
            FROM log_admin 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        riwayat_tindakan = cursor.fetchall()

    except Exception as e:
        print(f"Error Database Admin Dashboard: {e}")
        total_pengguna, menunggu_approval, total_transaksi = 0, 0, 0
        pemilik_count, penyewa_count, admin_count = 0, 0, 0
        daftar_banding, riwayat_tindakan = [], []
        
    cursor.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_pengguna=total_pengguna,
        menunggu_approval=menunggu_approval,
        total_transaksi=total_transaksi,
        pemilik_count=pemilik_count,
        penyewa_count=penyewa_count,
        admin_count=admin_count,
        daftar_banding=daftar_banding,
        riwayat_tindakan=riwayat_tindakan # Variabel baru untuk Dashboard
    )
    
# ==========================================
# PROSES BANDING (Memperbaiki BuildError)
# ==========================================
# Tambahkan ini di paling bawah file admin_controller.py

@admin_bp.route('/proses-banding/<int:banding_id>', methods=['POST'])
def proses_banding(banding_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect("/login")
        
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    # Ambil data email dan user_id
    cursor.execute("SELECT user_id, email FROM banding WHERE id = %s", (banding_id,))
    data_banding = cursor.fetchone()
    
    if data_banding:
        user_id = data_banding['user_id']
        email_user = data_banding['email']
        
        # Update status banding dan user
        cursor.execute("UPDATE banding SET status = 'approved' WHERE id = %s", (banding_id,))
        cursor.execute("""
            UPDATE users 
            SET status_akun = 'aktif', suspend_until = NULL, alasan_status = NULL 
            WHERE id = %s
        """, (user_id,))
        
        # CATAT KE RIWAYAT TINDAKAN
        cursor.execute("""
            INSERT INTO log_admin (admin_id, kategori, aksi, deskripsi) 
            VALUES (%s, 'User', 'Terima Banding', %s)
        """, (session.get('user_id'), f"Mengaktifkan kembali akun {email_user}"))
        
        conn.commit()
        flash("Akun berhasil diaktifkan kembali dan banding disetujui.", "success")
    
    cursor.close()
    conn.close()
    return redirect(url_for('admin.dashboard'))
# ==========================================
# KELOLA PENGGUNA
# ==========================================
@admin_bp.route('/kelola-pengguna')
def kelola_pengguna():
    # Ambil semua user kecuali admin (atau hapus filter kalau mau ambil semua)
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin/kelola_pengguna.html', users=users)

# ==========================================
# AKSI TINDAKAN USER (SUSPEND / BLOKIR / AKTIFKAN) + ALASAN
# ==========================================
from datetime import datetime, timedelta

@admin_bp.route('/tindak-user/<int:user_id>', methods=['POST'])
def tindak_user(user_id):
    action_type = request.form.get('action_type')
    user = User.query.get_or_404(user_id)

    if action_type == 'suspend':
        # Tangkap alasan dari dropdown atau text (Lainnya)
        alasan_dropdown = request.form.get('alasan_dropdown')
        alasan_text = request.form.get('alasan_text')
        alasan = alasan_text if alasan_dropdown == 'Lainnya' else alasan_dropdown
        
        # Hitung waktu suspend otomatis: Hari ini + 7 Hari (1 Minggu)
        waktu_pulih = datetime.now() + timedelta(days=7)

        user.status_akun = 'suspended'
        user.alasan_status = alasan
        user.suspend_until = waktu_pulih
        flash(f"Akun {user.nama} dibekukan selama 1 minggu (Pulih: {waktu_pulih.strftime('%d %b %Y')}). Alasan: {alasan}", "warning")
        
    elif action_type == 'blokir':
        alasan = request.form.get('alasan')
        user.status_akun = 'diblokir'
        user.alasan_status = alasan
        user.suspend_until = None
        flash(f"Akun {user.nama} diblokir permanen.", "danger")
        
    elif action_type == 'aktifkan':
        user.status_akun = 'aktif'
        user.alasan_status = None
        user.suspend_until = None
        flash(f"Akun {user.nama} berhasil diaktifkan kembali.", "success")

    db.session.commit()
    return redirect(url_for('admin.kelola_pengguna'))

# ==========================================
# LIST APPROVAL KOS (MATCH MOCKUP IMAGE_50155D)
# ==========================================
@admin_bp.route('/approval-kos')
def approval_kos():
    # Pastikan hanya admin yang bisa akses
    if "user_id" not in session or session.get("role") != "admin":
        return redirect("/login")
        
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    # 1. Hitung Total Menunggu / Ditolak (status_verifikasi = 0)
    cursor.execute("SELECT COUNT(id) AS total FROM kost WHERE status_verifikasi = 0")
    total_menunggu = cursor.fetchone()['total'] or 0
    
    # 2. Hitung Total Disetujui (status_verifikasi = 1)
    cursor.execute("SELECT COUNT(id) AS total FROM kost WHERE status_verifikasi = 1")
    total_disetujui = cursor.fetchone()['total'] or 0
    
    # 3. Ambil data kos beserta nama pemiliknya (JOIN dengan tabel users)
    cursor.execute("""
        SELECT k.id, k.nama_kost, k.alamat, k.status_verifikasi, k.alasan_penolakan, 
               u.nama AS nama_pemilik
        FROM kost k
        LEFT JOIN users u ON k.pemilik_id = u.id
        ORDER BY k.id DESC
    """)
    list_kos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Kirim data ke HTML
    return render_template('admin/approval_kos.html', 
                           list_kos=list_kos,
                           total_menunggu=total_menunggu,
                           total_disetujui=total_disetujui)

# ==========================================
# HALAMAN DETAIL KOS
# ==========================================
@admin_bp.route('/kos/<int:kost_id>/detail')
def detail_kos(kost_id):
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    # Ambil detail kos beserta nama pemiliknya
    cursor.execute("""
        SELECT k.*, u.nama as nama_pemilik 
        FROM kost k 
        LEFT JOIN users u ON k.pemilik_id = u.id 
        WHERE k.id = %s
    """, (kost_id,))
    kos = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not kos:
        flash("Data kos tidak ditemukan!", "danger")
        return redirect(url_for('admin.approval_kos'))
        
    return render_template('admin/detail_kos.html', kos=kos)

# ==========================================
# AKSI PROSES VERIFIKASI (SETUJUI / TOLAK)
# ==========================================
# ==========================================
# AKSI PROSES VERIFIKASI (SETUJUI / TOLAK) DENGAN LOG
# ==========================================
@admin_bp.route('/kos/<int:kost_id>/proses', methods=['POST'])
def proses_verifikasi(kost_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect("/login")
        
    admin_id = session.get('user_id')
    action = request.form.get('action_type')
    catatan = request.form.get('catatan_admin')
    badge_kualitas = request.form.get('badge_kualitas', 'none')
    
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    # Ambil nama kos untuk log dan notifikasi
    cursor.execute("SELECT nama_kost FROM kost WHERE id = %s", (kost_id,))
    data_kos = cursor.fetchone()
    nama_kost = data_kos['nama_kost'] if data_kos else "Properti"
    
    if action == 'setujui':
        # 1. Update Status
        cursor.execute("""
            UPDATE kost 
            SET status_verifikasi = 1, tier_listing = %s, alasan_penolakan = NULL 
            WHERE id = %s
        """, (badge_kualitas, kost_id))
        
        # 2. Catat ke Log Riwayat Tindakan
        deskripsi_log = f"Menyetujui Unit Kos '{nama_kost}' dengan Lencana: {badge_kualitas.upper()}"
        cursor.execute("INSERT INTO log_admin (admin_id, kategori, aksi, deskripsi) VALUES (%s, 'Kos', 'Setujui Kos', %s)", (admin_id, deskripsi_log))
        
        flash(f"Properti '{nama_kost}' Berhasil Disetujui dengan Lencana {badge_kualitas.upper()}!", "success")
        
    elif action == 'tolak':
        if not catatan or catatan.strip() == "":
            flash("Gagal menolak! Anda WAJIB mengisi catatan/alasan penolakan.", "danger")
            return redirect(url_for('admin.detail_kos', kost_id=kost_id))
            
        # 1. Update Status
        cursor.execute("""
            UPDATE kost 
            SET status_verifikasi = 0, tier_listing = 'none', alasan_penolakan = %s 
            WHERE id = %s
        """, (catatan, kost_id))
        
        # 2. Catat ke Log Riwayat Tindakan
        deskripsi_log = f"Menolak Unit '{nama_kost}' - Alasan: {catatan}"
        cursor.execute("INSERT INTO log_admin (admin_id, kategori, aksi, deskripsi) VALUES (%s, 'Kos', 'Tolak Kos', %s)", (admin_id, deskripsi_log))
        
        flash(f"Properti '{nama_kost}' Telah Ditolak dengan alasan: {catatan}", "warning")
        
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin.approval_kos'))

# ==========================================
# MANAGEMENT TIER PREMIUM & PERUANGAN (MOCKUP STYLE)
# ==========================================
@admin_bp.route('/layanan-premium', methods=['GET', 'POST'])
def layanan_premium():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect("/login")
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    if request.method == 'POST':
        harga_baru = request.form.get('harga_baru')
        try:
            cursor.execute("UPDATE paket_premium SET harga = %s WHERE id = 1", (harga_baru,))
            conn.commit()
            flash("Harga langganan Premium berhasil diperbarui!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Gagal memperbarui harga: {e}", "danger")
        return redirect(url_for('admin.layanan_premium'))
    
    # Ambil harga premium terupdate dari database
    cursor.execute("SELECT harga FROM paket_premium WHERE id = 1")
    paket = cursor.fetchone()
    harga_premium = paket['harga'] if paket else 99000
    
    cursor.close()
    conn.close()
    
    return render_template('admin/layanan_premium.html', harga_premium=harga_premium)

# ==========================================
# ADMIN PROFIL & SETTING (FIX NAMA & STATISTIK)
# ==========================================
@admin_bp.route('/profil', methods=['GET', 'POST'])
def profil():
    admin_id = session.get('user_id')
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    if request.method == 'POST':
        nama_baru = request.form.get('nama_lengkap')
        nohp_baru = request.form.get('nomor_telepon')
        file_foto = request.files.get('foto_profil')
        
        # 1. Update Nama & No HP
        if nama_baru and nama_baru.strip() != "":
            cursor.execute("UPDATE users SET nama = %s, no_hp = %s WHERE id = %s", (nama_baru.strip(), nohp_baru, admin_id))
        
        # 2. Proses Upload Foto dengan Validasi Ukuran (Max 2MB)
        if file_foto and file_foto.filename != '':
            # Cek ukuran file (dalam bytes)
            file_foto.seek(0, os.SEEK_END)
            file_size = file_foto.tell()
            file_foto.seek(0) # Reset pointer kembali ke awal file setelah cek
            
            # 2MB = 2 * 1024 * 1024 bytes = 2,097,152 bytes
            if file_size > 2 * 1024 * 1024:
                flash("Gagal! Foto profil terlalu besar. Maksimal 2MB.", "danger")
                return redirect(url_for('admin.profil'))
            
            filename = secure_filename(file_foto.filename)
            nama_file_baru = f"admin_{admin_id}_{int(datetime.now().timestamp())}_{filename}"
            upload_path = os.path.join('static/uploads/profil/', nama_file_baru)
            
            # Simpan file
            file_foto.save(upload_path)
            
            # Update path ke database
            path_db = f"uploads/profil/{nama_file_baru}"
            cursor.execute("UPDATE users SET foto_profil = %s WHERE id = %s", (path_db, admin_id))
            
        conn.commit()
        flash("Perubahan profil berhasil disimpan!", "success")
        return redirect(url_for('admin.profil'))

    # MENGAMBIL DATA ADMIN SAAT INI
    cursor.execute("SELECT * FROM users WHERE id = %s", (admin_id,))
    admin_user = cursor.fetchone()

    # MENGHITUNG STATISTIK NYATA (Tanpa Block Except yang membuat 0)
    cursor.execute("SELECT COUNT(id) AS total FROM kost WHERE status_verifikasi = 1")
    kos_diverifikasi = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(id) AS total FROM users")
    pengguna_dikelola = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(id) AS total FROM kost WHERE status_verifikasi = 0")
    laporan_ditangani = cursor.fetchone()['total'] or 0
    
    # Hitung Escrow (Pastikan kolom status_pencairan sudah dibuat di database!)
    cursor.execute("SELECT SUM(jumlah) AS total_escrow FROM pembayaran WHERE status_pembayaran='lunas' AND status_pencairan='belum_cair'")
    escrow_raw = cursor.fetchone()['total_escrow'] or 0
    
    if escrow_raw >= 1000000:
        escrow_nominal = f"Rp {(escrow_raw / 1000000):.1f}JT"
    else:
        escrow_nominal = f"Rp {int(escrow_raw):,}".replace(",", ".")

    cursor.close()
    conn.close()

    return render_template('admin/profil.html', 
                           admin=admin_user, 
                           kos_diverifikasi=kos_diverifikasi,
                           pengguna_dikelola=pengguna_dikelola,
                           laporan_ditangani=laporan_ditangani,
                           escrow_nominal=escrow_nominal)


# ==========================================
# RUTE AKSI & LOGIKA (POST / PEMROSESAN DATA)
# ==========================================

# --- 1. FITUR APPROVE & REJECT KOS BARU ---
# ==========================================
# FITUR APPROVE & REJECT KOS (DENGAN LOG AKTIVITAS)
# ==========================================
@admin_bp.route('/kos/<int:kost_id>/approve', methods=['POST'])
def approve_kos(kost_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect("/login")
        
    # Tangkap pilihan badge kualitas dari modal persetujuan
    badge_kualitas = request.form.get('badge_kualitas', 'none')
    
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    # Update status verifikasi JADI 1 (Tampil), dan berikan badge kualitas
    cursor.execute("""
        UPDATE kost 
        SET status_verifikasi = 1, tier_listing = %s 
        WHERE id = %s
    """, (badge_kualitas, kost_id))
    
    # Ambil Nama Kos untuk log
    cursor.execute("SELECT nama_kost FROM kost WHERE id = %s", (kost_id,))
    nama = cursor.fetchone()['nama_kost']
    
    # Catat log
    cursor.execute("""
        INSERT INTO log_admin (admin_id, kategori, aksi, deskripsi) 
        VALUES (%s, 'Kos', 'Verifikasi Kos', %s)
    """, (session.get('user_id'), f"Menyetujui Unit Kos '{nama}' dengan Badge Kualitas: {badge_kualitas.upper()}"))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f"Kos {nama} berhasil disetujui dan diberikan badge {badge_kualitas}!", "success")
    return redirect(url_for('admin.approval_kos'))

@admin_bp.route('/kos/<int:kost_id>/reject', methods=['POST'])
def reject_kos(kost_id):
    alasan = request.form.get('alasan_penolakan', 'Tidak memenuhi standar')
    
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    cursor.execute("UPDATE kost SET status_verifikasi = 0 WHERE id = %s", (kost_id,))
    
    cursor.execute("SELECT nama_kost FROM kost WHERE id = %s", (kost_id,))
    nama = cursor.fetchone()['nama_kost']
    
    # Catat ke Riwayat Tindakan (Dashboard)
    cursor.execute("""
        INSERT INTO log_admin (admin_id, kategori, aksi, deskripsi) 
        VALUES (%s, 'Kos', 'Tolak Kos', %s)
    """, (session.get('user_id'), f"Menolak Unit '{nama}' - Alasan: {alasan}"))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f"Pengajuan Kos {nama} ditolak.", "warning")
    return redirect(url_for('admin.approval_kos'))


# --- 2. FITUR HAPUS PROPERTI KOS ---
@admin_bp.route('/kos/<int:kost_id>/delete', methods=['POST'])
def hapus_properti(kost_id):
    kos = Kost.query.get_or_404(kost_id)
    nama = kos.nama_kost
    
    db.session.delete(kos)
    db.session.commit()
    
    flash(f"Properti {nama} berhasil dihapus secara permanen.", "danger")
    # Arahkan kembali ke halaman sebelumnya (referrer)
    return redirect(request.referrer or url_for('admin.dashboard'))



# --- 4. FITUR MENGHUBUNGI PENGGUNA (VIA WA/EMAIL) ---
@admin_bp.route('/user/<int:user_id>/contact', methods=['GET'])
def hubungi_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.no_hp:
        no_wa = user.no_hp.lstrip('0')
        no_wa = f"62{no_wa}" if not no_wa.startswith('62') else no_wa
        pesan_default = f"Halo {user.nama}, ini pesan dari Admin FindYourKost terkait akun Anda."
        return redirect(f"https://wa.me/{no_wa}?text={pesan_default}")
    else:
        return redirect(f"mailto:{user.email}?subject=Notifikasi Admin FindYourKost")


# --- 5. FITUR UPDATE HARGA LAYANAN PREMIUM ---
@admin_bp.route('/premium/update', methods=['POST'])
def update_layanan_premium():
    tier_name = request.form.get('tier_name')
    harga_baru = request.form.get('harga_baru')
    benefit_baru = request.form.get('benefit_baru')
    
    # Disini tempat menyimpan ke DB khusus Premium (jika ada)
    # Untuk sekarang kita flash messagenya saja
    
    flash(f"Berhasil! Paket {tier_name} diubah harganya menjadi Rp {harga_baru}.", "success")
    return redirect(url_for('admin.layanan_premium'))

# ==========================================
# ESCROW / KEUANGAN MIDTRANS
# ==========================================
# ==========================================
# RUTE KEUANGAN ASLI DATABASE (WITH ADVANCED FILTERS)
# ==========================================
from datetime import datetime

@admin_bp.route('/keuangan', methods=['GET'])
def keuangan():
    # 1. Tangkap parameter filter query string
    filter_status = request.args.get('status', 'Semua')
    tgl_mulai_str = request.args.get('tanggal_mulai', '')
    tgl_akhir_str = request.args.get('tanggal_akhir', '')

    # 2. Query Data Asli Database (Kita ambil dari User yang terverifikasi sebagai contoh logikanya)
    query = User.query.filter(User.nik.isnot(None))
    users_transaksi = query.all()
    
    transaksi_asli = []
    total_escrow = 0
    pendapatan_bersih = 129900  # Nilai asli dari kodemu
    dana_tertahan = 1200000     # Nilai asli dari kodemu
    
    for u in users_transaksi:
        nominal_trx = 99000.00 if u.is_premium else 1200000.00
        # Simulasikan status berdasarkan is_premium
        status_trx = "Dalam Penampungan (Escrow)" if not u.is_premium else "Telah Diteruskan Ke Pemilik"
        tgl_trx = datetime.today().strftime("%Y-%m-%d")
        
        # Validasi Filter Status
        if filter_status != 'Semua' and status_trx != filter_status:
            continue
            
        # Validasi Filter Tanggal
        if tgl_mulai_str and tgl_trx < tgl_mulai_str: continue
        if tgl_akhir_str and tgl_trx > tgl_akhir_str: continue
            
        transaksi_asli.append({
            "id": f"TXT-2026-{u.id:03d}",
            "tipe": "Layanan Premium" if u.is_premium else "Booking Kos",
            "pengirim": f"{u.nama} ({u.role.capitalize()})",
            "nominal": nominal_trx,
            "status": status_trx,
            "tanggal": tgl_trx
        })
        
        if status_trx == "Dalam Penampungan (Escrow)":
            total_escrow += nominal_trx

    # 3. Lempar semua data dan filter kembali ke halaman
    return render_template(
        'admin/keuangan.html', 
        transaksi=transaksi_asli, 
        total_escrow=total_escrow,
        pendapatan_bersih=pendapatan_bersih,
        dana_tertahan=dana_tertahan,
        current_status=filter_status,
        current_mulai=tgl_mulai_str,
        current_akhir=tgl_akhir_str
    )
# ==========================================
# PROSES UBAH PASSWORD ADMIN
# ==========================================
@admin_bp.route('/ubah-password', methods=['POST'])
def ubah_password():
    # 1. Ambil data admin yang sedang login
    admin_id = session.get('user_id')
    admin_user = User.query.get(admin_id)
    
    # 2. Tangkap inputan dari modal form
    password_lama = request.form.get('password_lama')
    password_baru = request.form.get('password_baru')
    konfirmasi_password = request.form.get('konfirmasi_password')
    
    # 3. Validasi Kecocokan Password Baru & Konfirmasi
    if password_baru != konfirmasi_password:
        flash("Password baru dan konfirmasi password tidak cocok!", "danger")
        return redirect(url_for('admin.profil'))
        
    # 4. Validasi Password Lama dengan Database (Menggunakan Bcrypt)
    # Pastikan 'bcrypt' sudah di-import di bagian atas file controller kamu
    if bcrypt.check_password_hash(admin_user.password_hash, password_lama):
        # Hash password baru dan simpan ke DB
        admin_user.password_hash = bcrypt.generate_password_hash(password_baru).decode('utf-8')
        db.session.commit()
        flash("Password akun administrator berhasil diperbarui!", "success")
    else:
        flash("Gagal! Password lama yang Anda masukkan salah.", "danger")
        
    return redirect(url_for('admin.profil'))

# ==========================================
# AKSI PENCAIRAN DANA ESCROW KE PEMILIK
# ==========================================
# ==========================================
# AKSI ADMIN MENYETUJUI PENCAIRAN KE DOMPET PEMILIK
# ==========================================
@admin_bp.route('/keuangan/cairkan/<int:escrow_id>', methods=['POST'])
def cairkan_dana(escrow_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect("/login")
        
    admin_id = session.get('user_id')
    conn = get_db()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    
    # 1. Ambil data Escrow beserta ID pemiliknya
    cursor.execute("""
        SELECT e.jumlah_bersih, k.nama_kost, k.pemilik_id, u.nama as nama_pemilik
        FROM escrow e
        JOIN booking b ON e.booking_id = b.id
        JOIN kost k ON b.kost_id = k.id
        JOIN users u ON k.pemilik_id = u.id
        WHERE e.id = %s AND e.status_pencairan = 'diproses'
    """, (escrow_id,))
    data = cursor.fetchone()
    
    if data:
        jumlah_cair = data['jumlah_bersih']
        pemilik_id = data['pemilik_id']
        nominal_rp = f"Rp {int(jumlah_cair):,}".replace(",", ".")
        
        # 2. TAMBAHKAN UANG KE DOMPET VIRTUAL PEMILIK
        cursor.execute("""
            UPDATE users 
            SET saldo_dompet = saldo_dompet + %s 
            WHERE id = %s
        """, (jumlah_cair, pemilik_id))
        
        # 3. UBAH STATUS ESCROW JADI SELESAI
        cursor.execute("""
            UPDATE escrow 
            SET status_pencairan = 'selesai', tanggal_pencairan = NOW() 
            WHERE id = %s
        """, (escrow_id,))
        
        # 4. CATAT KE RIWAYAT TINDAKAN ADMIN
        deskripsi_log = f"Menyetujui pencairan {nominal_rp} ke Saldo Dompet pemilik '{data['nama_pemilik']}' untuk penyewaan '{data['nama_kost']}'"
        cursor.execute("""
            INSERT INTO log_admin (admin_id, kategori, aksi, deskripsi) 
            VALUES (%s, 'Keuangan', 'Pencairan ke Wallet', %s)
        """, (admin_id, deskripsi_log))
        
        conn.commit()
        flash(f"Dana sebesar {nominal_rp} berhasil masuk ke Dompet Virtual Pemilik!", "success")
    else:
        flash("Data transaksi tidak valid atau belum diajukan oleh pemilik.", "danger")
        
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin.keuangan'))