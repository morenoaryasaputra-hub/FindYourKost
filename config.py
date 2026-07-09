import os
from dotenv import load_dotenv

# Memuat file .env tempat menyimpan data credential rahasia
load_dotenv()

class Config:
    # ==========================================
    # 1. DATABASE TIDB CONFIGURATION
    # ==========================================
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DB = os.getenv("MYSQL_DB")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 4000))
    
    # Koneksi string ORM Flask-SQLAlchemy (Fitur Utama Database)
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================
    # 2. FLASK CORE CONFIGURATION
    # ==========================================
    SECRET_KEY = os.getenv("SECRET_KEY")

    # ==========================================
    # 3. GOOGLE OAUTH CONFIGURATION
    # ==========================================
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # ==========================================
    # 4. GMAIL SMTP CONFIGURATION
    # ==========================================
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")

    # ==========================================
    # 5. CLOUDINARY CONFIGURATION (UPLOAD FOTO)
    # ==========================================
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # ==========================================
    # 6. RESEND API CONFIGURATION (EMAIL SERVICE)
    # ==========================================
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")

    # ==========================================
    # 7. MIDTRANS API CONFIGURATION (PAYMENT GATEWAY)
    # ==========================================
    MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
    MIDTRANS_CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY")
    MIDTRANS_IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION") == "True"