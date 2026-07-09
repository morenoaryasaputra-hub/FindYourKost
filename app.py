import os
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES (Wajib Paling Atas Sekali!)
load_dotenv()

from flask import Flask
from config import Config
import cloudinary
from extensions import bcrypt, oauth, socketio
import socket_events

app = Flask(__name__)

# 2. CONFIGURATION LOGIC
app.config.from_object(Config)
print("SQLALCHEMY_DATABASE_URI =", app.config.get("SQLALCHEMY_DATABASE_URI"))

# Amankan pemanggilan secret key dari config atau .env
app.secret_key = app.config.get("SECRET_KEY", os.environ.get("SECRET_KEY"))

# 3. INITIALIZE DATABASE CONNECTION
from models import db
db.init_app(app)

# 4. CONTEXT PROCESSOR FOR JINJA TEMPLATE
@app.context_processor
def inject_config():
    return dict(config=app.config)

# 5. CLOUDINARY CONFIGURATION (Fitur Unggah Foto)
cloudinary.config(
    cloud_name=app.config.get("CLOUDINARY_CLOUD_NAME"),
    api_key=app.config.get("CLOUDINARY_API_KEY"),
    api_secret=app.config.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# 6. INITIALIZE FLASK EXTENSIONS
bcrypt.init_app(app)
oauth.init_app(app)
socketio.init_app(app)

# 7. GOOGLE OAUTH REGISTRATION
oauth.register(
    name="google",
    client_id=app.config.get("GOOGLE_CLIENT_ID"),
    client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

# 8. IMPORT ALL BLUEPRINTS (Gabungan Fitur Kamu & Temanmu)
# Import controller dilakukan DI SINI agar .env ke-load duluan
from controllers.auth_controller import auth_bp
from controllers.penyewa_controller import penyewa_bp
from controllers.pemilik_controller import pemilik_bp
from controllers.admin_controller import admin_bp 
from controllers.chat_controller import chat_bp
from controllers.payment_controller import payment_bp

# 9. REGISTER ALL BLUEPRINTS TO FLASK
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(penyewa_bp)
app.register_blueprint(pemilik_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(payment_bp)

# 10. RUN APPLICATION VIA SOCKETIO (Wajib agar Chat Real-time Berjalan)
if __name__ == "__main__":
    socketio.run(app, debug=True)