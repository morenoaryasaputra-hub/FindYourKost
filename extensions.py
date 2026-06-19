from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_mail import Mail

from authlib.integrations.flask_client import OAuth

mysql = MySQL()

bcrypt = Bcrypt()

mail = Mail()

oauth = OAuth()
