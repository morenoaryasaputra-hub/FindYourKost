# 🏠 FindYourKost

FindYourKost adalah platform marketplace kos berbasis web yang dirancang untuk mempermudah proses pencarian kos bagi penyewa serta membantu pemilik kos dalam mengelola properti mereka secara efisien. Platform ini memungkinkan penyewa mencari kos dan berkomunikasi langsung dengan pemilik, sekaligus menyediakan berbagai fitur yang mendukung pengelolaan properti.

Proyek ini dikembangkan sebagai bagian dari mata kuliah Pengembangan Aplikasi.

---

## ✨ Fitur

### 🔐 Autentikasi Multi-Role

Sistem autentikasi terpisah untuk penyewa dan pemilik kos.

### 📊 Dashboard Pemilik Kos

Dashboard khusus bagi pemilik kos untuk mengelola properti, memantau pemesanan, dan melihat transaksi.

### 💬 Pesan Real-Time

Komunikasi langsung antara penyewa dan pemilik kos menggunakan **Flask-SocketIO**, sehingga pesan dapat diterima tanpa perlu me-refresh halaman.

### 📁 Berbagi Media

Mendukung pengiriman gambar, file, dan video melalui fitur chat dengan batas ukuran unggahan guna menjaga performa aplikasi dan efisiensi penyimpanan database.

### ⭐ Premium Listing

Pemilik kos dapat meningkatkan visibilitas properti dengan menampilkan iklan di bagian teratas hasil pencarian.

---

## 🛠️ Teknologi yang Digunakan

### Backend

* Python 3
* Flask
* Flask-SocketIO

### Database

* MySQL
* TiDB Cloud

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap
* Font Awesome

### API & Layanan

* Midtrans Snap API (Payment Gateway)

---

## 🚀 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/<username>/FindYourKost.git
cd FindYourKost
```

### 2. Buat Virtual Environment (Disarankan)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instal Dependensi

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment Variables

Buat file `.env` pada direktori utama (root) proyek, kemudian isi dengan kredensial dan API key yang diperlukan sesuai dengan konfigurasi lingkungan Anda.

Contoh:

```env
SECRET_KEY=
MYSQL_HOST=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_NAME=
MYSQL_PORT=
MIDTRANS_SERVER_KEY=
MIDTRANS_CLIENT_KEY=
MIDTRANS_IS_PRODUCTION=False (untuk sandbox mode)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
CLOUDINARY_URL=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
GEOAPIFY_API_KEY=
OCR_API_KEY=
SECRET_KEY=  
RESEND_API_KEY=
EMAIL_FROM=onboarding@resend.dev
MAIL_USERNAME= (kita tidak memiliki domain berbayar untuk resend)
MAIL_PASSWORD=
```

### 5. Jalankan Aplikasi

```bash
python app.py
```

Aplikasi dapat diakses melalui:

```
http://127.0.0.1:5000 (localhost)
```

---

## 📌 Ruang Lingkup Proyek

* Autentikasi multi-role
* Manajemen properti kos
* Pencarian dan penelusuran kos
* Chat real-time
* Berbagi media
* Premium listing
* Integrasi payment gateway
  
---

## 👨‍💻 Kontributor
Moreno Arya Saputra
Agape Dhaniel Wibowo
Vanessa Ruth Walingkas
Yuka Asfwa Atalla

Proyek ini dikembangkan secara berkelompok sebagai bagian dari mata kuliah Pengembangan Perangkat Lunak.
