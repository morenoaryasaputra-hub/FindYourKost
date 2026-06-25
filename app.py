from flask import Flask

from config import Config
import socket_events
import cloudinary
from extensions import bcrypt
from extensions import oauth
from extensions import socketio

app = Flask(__name__)


app.config.from_object(Config)

app.secret_key = app.config[
    "SECRET_KEY"
]

cloudinary.config(
    cloud_name=app.config[
        "CLOUDINARY_CLOUD_NAME"
    ],
    api_key=app.config[
        "CLOUDINARY_API_KEY"
    ],
    api_secret=app.config[
        "CLOUDINARY_API_SECRET"
    ],
    secure=True
)

bcrypt.init_app(app)
oauth.init_app(app)
socketio.init_app(app)

oauth.register(
    name="google",

    client_id=app.config[
        "GOOGLE_CLIENT_ID"
    ],

    client_secret=app.config[
        "GOOGLE_CLIENT_SECRET"
    ],

    server_metadata_url=
    "https://accounts.google.com/.well-known/openid-configuration",

    client_kwargs={
        "scope":
        "openid email profile"
    }
)

from controllers.auth_controller import auth_bp
from controllers.penyewa_controller import penyewa_bp
from controllers.pemilik_controller import pemilik_bp
from controllers.chat_controller import chat_bp

app.register_blueprint(auth_bp)
app.register_blueprint(penyewa_bp)
app.register_blueprint(pemilik_bp)
app.register_blueprint(chat_bp)

if __name__ == "__main__":

    socketio.run(app, debug=True)