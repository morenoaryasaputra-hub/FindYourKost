import os

from dotenv import load_dotenv

load_dotenv()


class Config:

    # DATABASE TIDB

    MYSQL_HOST = os.getenv(
        "MYSQL_HOST"
    )

    MYSQL_USER = os.getenv(
        "MYSQL_USER"
    )

    MYSQL_PASSWORD = os.getenv(
        "MYSQL_PASSWORD"
    )

    MYSQL_DB = os.getenv(
        "MYSQL_DB"
    )

    MYSQL_PORT = int(
        os.getenv(
            "MYSQL_PORT",
            4000
        )
    )

    # FLASK

    SECRET_KEY = os.getenv(
        "SECRET_KEY"
    )

    # GOOGLE LOGIN

    GOOGLE_CLIENT_ID = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    GOOGLE_CLIENT_SECRET = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    # GMAIL SMTP

    MAIL_SERVER = "smtp.gmail.com"

    MAIL_PORT = 587

    MAIL_USE_TLS = True

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME"
    )

    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD"
    )

    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_USERNAME"
    )

    # CLOUDINARY

    CLOUDINARY_CLOUD_NAME = os.getenv(
        "CLOUDINARY_CLOUD_NAME"
    )

    CLOUDINARY_API_KEY = os.getenv(
        "CLOUDINARY_API_KEY"
    )

    CLOUDINARY_API_SECRET = os.getenv(
        "CLOUDINARY_API_SECRET"
    )

    # RESEND

    RESEND_API_KEY = os.getenv(
        "RESEND_API_KEY"
    )

    MIDTRANS_SERVER_KEY = os.getenv(
        "MIDTRANS_SERVER_KEY"
    )

    MIDTRANS_CLIENT_KEY = os.getenv(
        "MIDTRANS_CLIENT_KEY"
    )

    MIDTRANS_IS_PRODUCTION = os.getenv(
        "MIDTRANS_IS_PRODUCTION"
    ) == "True"