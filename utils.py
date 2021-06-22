import smtplib, ssl
import io
import math, random

from flask import redirect, render_template, request, session
from functools import wraps # for using decorators


from PIL import Image


from config import ADMIN_EMAIL, ADMIN_EMAIL_PASS
from resources import get_bucket

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("userid") is None:
            return redirect("/product/login")
        return f(*args, **kwargs)
    return decorated_function


''' for sending email using smtp '''
def send_Email(message, receiver_email=ADMIN_EMAIL):

    port = 465
    smtp_server = "smtp.gmail.com"

    sender_email = ADMIN_EMAIL
    password = ADMIN_EMAIL_PASS


    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as smtp:
        smtp.ehlo()


        smtp.login(sender_email, password)
        print(smtp.sendmail(sender_email, receiver_email, message))

    return


""" for the generation otp """
def generateOTP(receiver_email=ADMIN_EMAIL) :


    print(receiver_email)
    # Declare a digits variable
    # which stores all digits
    digits = "0123456789"
    OTP = ""

   # length of password can be chaged
   # by changing value in range
    for i in range(4) :
        OTP += digits[math.floor(random.random() * 10)]


    message = """\
                Subject: Fitkit | Otp

                Your One Time Password(OTP) is:

                {}""".format(OTP)

    send_Email(message, receiver_email)

    return OTP

def upload_img(files, productId):

    my_bucket = get_bucket()

    img_index = ['a', 'b', 'c', 'd']

    i = 0
    for file in files:

        img = Image.open(file.stream)

        # creating thumbnail for the product
        if i == 0:

            thumbnail_img = img.resize((100,150),Image.ANTIALIAS)

            buf = io.BytesIO()
            thumbnail_img.save(buf, format='JPEG', quality=80)
            byte_im = buf.getvalue()

            filename = str(productId)  + '.jpg'
            print("filename: {}".format(filename))
            my_bucket.Object('images/thumbnails/' + filename).put(Body=byte_im)



        img = img.resize((600,900),Image.ANTIALIAS)


        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=80)
        byte_im = buf.getvalue()

        filename = str(productId) + img_index[i] + '.jpg'
        print("filename: {}".format(filename))
        my_bucket.Object('images/' + filename).put(Body=byte_im)

        i = i + 1


def remove_img(productId):

    print(productId)
    my_bucket = get_bucket()

    img_index = ['a', 'b', 'c', 'd']
    for i in img_index:
        filename = str(productId) + i + '.jpg'
        print(filename)
        try:
            my_bucket.Object('images/' + filename).delete()
        except:
            print('object not found')
