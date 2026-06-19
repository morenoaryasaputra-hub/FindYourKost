from flask import Flask

from config import Config

from extensions import mysql
from extensions import bcrypt
from extensions import oauth
from extensions import mail

app = Flask(__name__)

app.config.from_object(Config)

mysql.init_app(app)
bcrypt.init_app(app)
mail.init_app(app)
oauth.init_app(app)

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

app.register_blueprint(auth_bp)
app.register_blueprint(penyewa_bp)

if __name__ == "__main__":

    app.run(debug=True)