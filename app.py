from flask import Flask

from config import Config

from extensions import mysql
from extensions import bcrypt

app = Flask(__name__)
app.config.from_object(Config)

mysql.init_app(app)
bcrypt.init_app(app)

from controllers.auth_controller import auth_bp
from controllers.penyewa_controller import penyewa_bp

app.register_blueprint(auth_bp)
app.register_blueprint(penyewa_bp)

if __name__ == "__main__":
    app.run(debug=True)