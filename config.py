import os
import psycopg2

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_EMAIL_PASS = os.environ.get("ADMIN_EMAIL_PASS")


ADMIN_LOGIN_ID = os.environ.get("ADMIN_LOGIN_ID")
ADMIN_LOGIN_PASS= os.environ.get("ADMIN_LOGIN_PASS")


RPAY_KEY = os.environ.get("RPAY_KEY")
RPAY_SECRET = os.environ.get("RPAY_SECRET")


S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("S3_KEY")
S3_SECRET = os.environ.get("S3_SECRET")


DBNAME = os.environ.get("DBNAME")
USER = os.environ.get("USER")
PASSWORD = os.environ.get("PASSWORD")
HOST = os.environ.get("HOST")



db_connection = psycopg2.connect(
    dbname=DBNAME,
    user=USER,
    password=PASSWORD,
    host=HOST,
    port=5432
)