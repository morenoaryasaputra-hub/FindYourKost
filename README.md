# 🏠 FindYourKost - Platform Pencarian & Manajemen Kos

FindYourKost adalah aplikasi web berbasis platform yang dirancang untuk memudahkan pencarian kos bagi penyewa dan mempermudah manajemen properti bagi pemilik kos. Website ini dilengkapi dengan fitur komunikasi langsung dan sistem pembayaran premium terintegrasi.

Proyek ini dibangun sebagai bagian dari tugas pengembangan perangkat lunak kelompok.

---

## 🚀 Fitur Unggulan

1. **Autentikasi Multi-Role**: Sistem login terpisah untuk **Penyewa** dan **Pemilik Kos**.
2. **Dashboard Pemilik Kos**: Halaman khusus bagi pemilik untuk memantau metrik properti dan transaksi.
3. **Fitur Chat Real-Time (Socket.io)**: Chat interaktif langsung antara penyewa dan pemilik kos tanpa perlu refresh halaman.
4. **Berbagi Media di Chat**: Mendukung pengiriman file, gambar (max 2MB), dan video dengan batasan ukuran aman untuk mencegah pembengkakan database.
5. **Premium Listing Gateway (Midtrans)**: Integrasi pembayaran aman menggunakan Midtrans Snap API bagi pemilik kos yang ingin menaikkan visibilitas propertinya ke baris paling atas.

---

## 🛠️ Teknologi yang Digunakan (Tech Stack)

- **Backend**: Python 3.x, Flask (Framework)
- **Real-Time Communication**: Flask-SocketIO
- **Database**: MySQL / TiDB Cloud
- **Payment Gateway**: Midtrans Snap API
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap, FontAwesome

---

## 💻 Cara Install & Menjalankan Proyek

Ikuti langkah-langkah di bawah ini untuk menjalankan aplikasi di lingkungan lokal (localhost):

### 1. Clone atau Ekstrak Folder Proyek
Pastikan semua file proyek sudah berada di dalam satu folder kerja di komputer Anda.

### 2. Buat & Aktifkan Virtual Environment (Opsional tapi Direkomendasikan)
```bash
# Membuat virtual environment
python -m venv venv

# Mengaktifkan di Windows
venv\Scripts\activate

# Mengaktifkan di Mac/Linux
source venv/bin/activate
