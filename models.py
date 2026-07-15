from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# =================================------------------------
# 1. TABEL PENGGUNA (Aktor Sistem)
# =================================------------------------
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(255), nullable=True)
    no_hp = db.Column(db.String(20), nullable=True)
    foto_profil = db.Column(db.String(255), nullable=True)
    role = db.Column(db.Enum('penyewa', 'pemilik', 'admin'), default='penyewa', nullable=False)
    is_profile_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    alamat = db.Column(db.Text, nullable=True)
    tanggal_lahir = db.Column(db.Date, nullable=True)
    jenis_kelamin = db.Column(db.Enum('L', 'P'), nullable=True)
    foto_ktp = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    pekerjaan = db.Column(db.String(100), nullable=True)
    instansi = db.Column(db.String(150), nullable=True)
    nama_bank = db.Column(db.String(50), nullable=True)
    no_rekening = db.Column(db.String(50), nullable=True)
    atas_nama_rekening = db.Column(db.String(100), nullable=True)
    is_premium = db.Column(db.Boolean, default=False)
    nik = db.Column(db.String(20), nullable=True)
    nama_ktp = db.Column(db.String(100), nullable=True)
    foto_ktp = db.Column(db.String(200), nullable=True)
    is_ktp_verified = db.Column(db.Boolean, default=False)
    status_akun = db.Column(db.String(20), default='aktif')
    alasan_status = db.Column(db.Text, nullable=True)
    
 

    # Hubungan Relasi (Relationship) balik untuk mempermudah pemanggilan data
    kosts = db.relationship('Kost', backref='pemilik', lazy=True, cascade="all, delete-orphan")
    rekening_bank = db.relationship('RekeningBank', backref='user', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='penyewa', foreign_keys='Booking.penyewa_id', lazy=True)
    subscriptions = db.relationship('PremiumSubscription', backref='user', lazy=True, cascade="all, delete-orphan")


# =================================------------------------
# 2. TABEL KOST (Data Properti Utama)
# =================================------------------------
class Kost(db.Model):
    __tablename__ = 'kost'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pemilik_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    nama_kost = db.Column(db.String(150), nullable=False)
    alamat = db.Column(db.Text, nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    harga = db.Column(db.Numeric(12, 2), nullable=False)
    tipe_penghuni = db.Column(db.Enum('putra', 'putri', 'campur'), default='campur')
    total_kamar = db.Column(db.Integer, default=1, nullable=False)
    sisa_kamar = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    status_verifikasi = db.Column(db.Boolean, default=False)
    tier_listing = db.Column(db.Enum('none', 'silver', 'gold', 'premium'), default='none')
    foto_thumbnail = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    uang_muka = db.Column(db.Integer, default=0)

    # Relasi anak tabel
    galeri_foto = db.relationship('FotoKost', backref='kost', lazy=True, cascade="all, delete-orphan")
    buku_kas = db.relationship('BukuKas', backref='kost', lazy=True, cascade="all, delete-orphan")


# =================================------------------------
# 3. TABEL GALERI FOTO KOST
# =================================------------------------
class FotoKost(db.Model):
    __tablename__ = 'foto_kost'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kost_id = db.Column(db.Integer, db.ForeignKey('kost.id', ondelete="CASCADE"), nullable=False)
    url_foto = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 4. TABEL REKENING BANK PEMILIK
# =================================------------------------
class RekeningBank(db.Model):
    __tablename__ = 'rekening_bank'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    nama_bank = db.Column(db.String(50), nullable=False)
    nomor_rekening = db.Column(db.String(50), nullable=False)
    atas_nama = db.Column(db.String(100), nullable=False)
    is_utama = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 5. TABEL BOOKING (Transaksi Pemesanan Kamar)
# =================================------------------------
class Booking(db.Model):
    __tablename__ = 'booking'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    penyewa_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    kost_id = db.Column(db.Integer, db.ForeignKey('kost.id'), nullable=False)
    tanggal_booking = db.Column(db.DateTime, default=db.func.current_timestamp())
    tanggal_masuk = db.Column(db.Date, nullable=True)
    durasi_bulan = db.Column(db.Integer, nullable=True)
    total_harga = db.Column(db.Numeric(12, 2), nullable=True)
    status_booking = db.Column(
        db.Enum('menunggu_dp', 'dp_dibayar', 'menunggu_konfirmasi', 'menunggu_pelunasan', 'aktif', 'selesai', 'dibatalkan'), 
        default='menunggu_dp'
    )
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relasi
    pembayaran = db.relationship('Pembayaran', backref='booking', lazy=True, cascade="all, delete-orphan")
    tagihan = db.relationship('TagihanPenghuni', backref='booking', lazy=True, cascade="all, delete-orphan")
    escrows = db.relationship('Escrow', backref='booking', lazy=True, cascade="all, delete-orphan")


# =================================------------------------
# 6. TABEL PEMBAYARAN (Integrasi Midtrans)
# =================================------------------------
class Pembayaran(db.Model):
    __tablename__ = 'pembayaran'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id', ondelete="CASCADE"), nullable=False)
    midtrans_order_id = db.Column(db.String(100), nullable=True)
    jumlah = db.Column(db.Numeric(12, 2), nullable=True)
    metode_pembayaran = db.Column(db.String(100), nullable=True)
    status_pembayaran = db.Column(db.Enum('pending', 'success', 'failed', 'expired'), default='pending')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 8. TABEL PREMIUM SUBSCRIPTION (Langganan Akun SaaS)
# =================================------------------------
class PremiumSubscription(db.Model):
    __tablename__ = 'premium_subscription'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    tier = db.Column(db.Enum('silver', 'gold', 'premium'), default='silver')
    tanggal_mulai = db.Column(db.Date, nullable=True)
    tanggal_akhir = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('aktif', 'expired'), default='aktif')
    
# =================================------------------------
# 8. TABEL PREMIUM SUBSCRIPTION NEW
# =================================------------------------
class PaketPremium(db.Model):
    __tablename__ = 'paket_premium'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_paket = db.Column(db.String(50), nullable=False, default='Premium')
    harga = db.Column(db.Numeric(12, 2), nullable=False, default=99000.00)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =================================------------------------
# 9. TABEL BUKU KAS (Fitur Keuangan Premium Pemilik)
# =================================------------------------
class BukuKas(db.Model):
    __tablename__ = 'buku_kas'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kost_id = db.Column(db.Integer, db.ForeignKey('kost.id', ondelete="CASCADE"), nullable=False)
    jenis_transaksi = db.Column(db.Enum('pemasukan', 'pengeluaran'), nullable=False)
    kategori = db.Column(db.String(50), nullable=True)
    nominal = db.Column(db.Numeric(12, 2), nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    tanggal_transaksi = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 10. TABEL TAGIHAN PENGHUNI (Fitur Keuangan Premium Pemilik)
# =================================------------------------
class TagihanPenghuni(db.Model):
    __tablename__ = 'tagihan_penghuni'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id', ondelete="CASCADE"), nullable=False)
    bulan_tagihan = db.Column(db.Date, nullable=False)
    nominal = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.Enum('belum_bayar', 'lunas'), default='belum_bayar')
    tanggal_jatuh_tempo = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 11. TABEL CHAT ROOM & CHAT MESSAGE (Komunikasi Privat)
# =================================------------------------
class ChatRoom(db.Model):
    __tablename__ = 'chat_room'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    penyewa_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pemilik_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    kost_id = db.Column(db.Integer, db.ForeignKey('kost.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    messages = db.relationship('ChatMessage', backref='room', lazy=True, cascade="all, delete-orphan")


class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id', ondelete="CASCADE"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pesan = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    waktu_kirim = db.Column(db.DateTime, default=db.func.current_timestamp())
    file_path = db.Column(db.String(255), nullable=True)
    is_tagihan = db.Column(db.Boolean, default=False)
    tagihan_amount = db.Column(db.Numeric(12, 2), nullable=True)


# =================================------------------------
# 12. TABEL REVIEW (Ulasan Terverifikasi)
# =================================------------------------
class Review(db.Model):
    __tablename__ = 'review'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    kost_id = db.Column(db.Integer, db.ForeignKey('kost.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    ulasan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 13. TABEL WISHLIST (Kos Favorit)
# =================================------------------------
class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    kost_id = db.Column(db.Integer, db.ForeignKey('kost.id', ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 14. TABEL LAPORAN (Pengaduan Kos Bermasalah)
# =================================------------------------
class Laporan(db.Model):
    __tablename__ = 'laporan'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pelapor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    kost_id = db.Column(db.Integer, db.ForeignKey('kost.id'), nullable=False)
    alasan = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('pending', 'diproses', 'selesai'), default='pending')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 15. TABEL VERIFIKASI KOST (Persetujuan Admin)
# =================================------------------------
class VerifikasiKost(db.Model):
    __tablename__ = 'verifikasi_kost'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kost_id = db.Column(db.Integer, db.ForeignKey('kost.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Enum('pending', 'diterima', 'ditolak'), default='pending')
    catatan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 16. PASSWORD RESET TOKEN
# =================================------------------------
class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    token = db.Column(db.String(255), nullable=False)
    expired_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =================================------------------------
# 7. TABEL ESCROW (Manajemen Dana DP & Komisi)
# =================================------------------------
class Escrow(db.Model):
    __tablename__ = 'escrow'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id', ondelete="CASCADE"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rekening_tujuan_id = db.Column(db.Integer, db.ForeignKey('rekening_bank.id'), nullable=True)
    jumlah_dp = db.Column(db.Numeric(12, 2), nullable=True)
    potongan_komisi = db.Column(db.Numeric(12, 2), default=0.00)
    nominal_bersih = db.Column(db.Numeric(12, 2), nullable=True)
    status = db.Column(db.Enum('ditahan', 'released', 'refund'), default='ditahan')
    bukti_transfer = db.Column(db.String(255), nullable=True)
    tanggal_release = db.Column(db.DateTime, nullable=True)
    tanggal_refund = db.Column(db.DateTime, nullable=True)