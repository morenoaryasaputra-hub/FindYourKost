# 🏠 FindYourKost - Platform Pencarian & Manajemen Kos

FindYourKost adalah aplikasi web berbasis platform yang dirancang untuk memudahkan pencarian kos bagi penyewa dan mempermudah manajemen properti bagi pemilik kos. Website ini dilengkapi dengan fitur komunikasi langsung dan sistem pembayaran premium terintegrasi.

Proyek ini dibangun sebagai bagian dari tugas pengembangan perangkat lunak kelompok.

---

## 🚀 Fitur Unggulan

1. **Autentikasi Multi-Role**: Sistem login terpisah untuk **Penyewa** dan **Pemilik Kos**.
2. **Dashboard Pemilik Kos**: Halaman khusus bagi pemilik untuk memantau metrik properti dan transaksi.
3. **Fitur Chat Real-Time (Socket.io)**: Chat interaktif langsung antara penyewa dan pemilik kos tanpa perlu refresh halaman.
4. **Berbagi Media di Chat**: Mendukung pengiriman file, gambar (max 2MB), dan video dengan batasan ukuran aman untuk mencegah pembengkakan database.
5. **Premium Listing**: Bemilik bisa menaikkan visibilitas propertinya ke baris paling atas dengan mengupgrade plan mereka.
6. **Integrasi Payment Gateway**: Terintegrasi dengan Midtrans Snap API untuk memproses pembayaran kos.

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
```

### 3. Instal Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment Variables

Buat file `.env` di direktori utama (root) project anda, kemudian isi dengan kredensial dan *API key* yang diperlukan sesuai dengan konfigurasi lingkungan Anda.

Contoh:

```env
SECRET_KEY=your_secret_key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=findyourkost
MIDTRANS_SERVER_KEY=your_midtrans_server_key
MIDTRANS_CLIENT_KEY=your_midtrans_client_key
```

### 5. Jalankan Aplikasi

```bash
python app.py
```

---

## 👨‍💻 Contributors
- Moreno Arya Saputra 
- Agape Dhaniel Wibowo
- Vanessa Ruth Walingkas
- Yuka Asfwa Atalla

Dikembangkan sebagai projek akademik untuk mata kuliah Pengembangan Aplikasi.
