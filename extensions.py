import os
import pymysql

from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
from flask_socketio import SocketIO

bcrypt = Bcrypt()
oauth = OAuth()

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    logger=True,
    engineio_logger=True
)

def get_db():

    return pymysql.connect(
        host=os.getenv(
            "MYSQL_HOST"
        ),
        user=os.getenv(
            "MYSQL_USER"
        ),
        password=os.getenv(
            "MYSQL_PASSWORD"
        ),
        database=os.getenv(
            "MYSQL_DB"
        ),
        port=int(
            os.getenv(
                "MYSQL_PORT",
                4000
            )
        ),
        ssl={
            "ssl": {}
        },
        cursorclass=
        pymysql.cursors.Cursor
    )