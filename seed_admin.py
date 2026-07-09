from app import app
from extensions import bcrypt, get_db
from dotenv import load_dotenv

# Load .env biar koneksi database otomatis diambil dari situ
load_dotenv()

def create_admin():
    # Data Admin
    nama_admin = "Admin FindYourKost"
    email_admin = "admin@findyourkost.com" 
    password_raw = "admin123" # Ganti password-nya!
    
    # Hash password pakai bcrypt yang sudah ada di app
    with app.app_context():
        hashed_password = bcrypt.generate_password_hash(password_raw).decode('utf-8')
    
    # Koneksi ke Database TiDB menggunakan helper kamu
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # SQL untuk insert
        query = """
        INSERT INTO users (nama, email, password_hash, role, is_profile_complete, is_verified)
        VALUES (%s, %s, %s, 'admin', 1, 1)
        """
        cursor.execute(query, (nama_admin, email_admin, hashed_password))
        conn.commit()
        print(f"✅ Sukses! Admin {email_admin} berhasil ditanam ke database TiDB.")
    except Exception as e:
        print(f"❌ Gagal: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_admin()