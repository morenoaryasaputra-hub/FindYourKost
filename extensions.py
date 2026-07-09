import os
import pymysql
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
from flask_socketio import SocketIO

# 1. INISIALISASI UTAS EXTENSION CORE
bcrypt = Bcrypt()
oauth = OAuth()

# 2. INISIALISASI WEBSOCKET SOCKETIO (Fitur Chat & Real-time Temanmu)
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    logger=True,
    engineio_logger=True
)

# 3. FUNGSI KONEKSI DATABASE (Gabungan Fitur Log & SSL TiDB)
def get_db():
    # Menampilkan log credential di terminal saat fungsi dipanggil (Fitur Kamu)
    print("MYSQL_HOST =", os.getenv("MYSQL_HOST"))
    print("MYSQL_USER =", os.getenv("MYSQL_USER"))
    print("MYSQL_PORT =", os.getenv("MYSQL_PORT"))

    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
        port=int(os.getenv("MYSQL_PORT", 4000)),
        ssl={
            "ssl": {}
        },
        cursorclass=pymysql.cursors.Cursor
    )