from flask_mysqldb import MySQL

class Config:

    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = ""
    MYSQL_DB = "findyourkost_test"

    SECRET_KEY = "findyourkost_secret_key"