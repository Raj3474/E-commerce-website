from flask import Blueprint, flash, jsonify, render_template, request, url_for, redirect, session

from werkzeug.security import check_password_hash, generate_password_hash


import psycopg2.extras

from utils import generateOTP, send_Email
from config import db_connection


users = Blueprint('users', __name__,
                        template_folder='templates', static_folder='static')


""" login """
@users.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Forget any user_id
        session.clear()

        # Ensure email is submitted
        if not request.form.get("email"):
            return jsonify(
            {
                "status" : "error",
                "message" : "Email Missing!"
            })


        if not request.form.get("pass"):
            return jsonify(
            {
                "status" : "error",
                "message" : "Password Missing!"
            })

        print( request.form.get("email"),  request.form.get("pass"))

        # Query database for the user
        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s",(request.form.get("email"),))
                rows = cursor.fetchall()

        print(rows)
        # Ensure user exists and password is correct
        if len(rows) == 0:
            return jsonify(
            {
                "status" : "error",
                "message" : "Invalid Email!"
            })

        if not check_password_hash(rows[0]["hash"], request.form.get("pass")):
            return jsonify(
            {
                "status" : "error",
                "message" : "Incorrect Password!"
            })

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]


        flash(u"Successfully Login", "success")

        return jsonify(
            {
                "status" : "success",
                "message" : "Login Successfully"
            })

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/users/login.html", loginForm=True)




""" new user registration """
@users.route("/registration", methods=["POST", "GET"])
def registration():

    if request.method == 'POST':

        email = request.form.get("email")
        password = request.form.get("pass")
        confpassword = request.form.get("confpass")


        if not email:
            return jsonify(
            {
                "status" : "error",
                "message" : "Email Missing"
            })


        if not password:
            return jsonify(
            {
                "status" : "error",
                "message" : "Password Missing!"
            })

        if not confpassword:
            return jsonify(
            {
                "status" : "error",
                "message" : "Please confirm your Password!"
            })

        if password != confpassword:
            return jsonify(
            {
                "status" : "error",
                "message" : "Password Doesn't Matched!"
            })



        # checking if the email is already registered or not, if not registered then the 'result list' will be empty
        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
                resultEmail = cursor.fetchall()

        print(resultEmail)
        if resultEmail:
            return jsonify(
                {
                    "status" : "error",
                    "message" : "Email is already linked to an existing Account"
                })

        session['email'] = email
        session['otp'] = generateOTP(session['email'])
        return jsonify(
            {
                "status" : "success",
                "message" : ""
            })


    return render_template("/users/login.html")


@users.route("/registerUser", methods=["POST"])
def registerUser():

    email = request.form.get("email")
    password = request.form.get("pass")


    # hashing the password
    hash = generate_password_hash(password)

    # insert the data into database
    with db_connection:
        with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("INSERT INTO users (email, hash) VALUES (%s, %s)",(email, hash))


    session.clear()

    # Query database for the user
    with db_connection:
        with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT user_id FROM users WHERE email = %s;", (request.form.get("email"),))
            rows = cursor.fetchall()


    # Remember which user has logged in
    session["user_id"] = rows[0]["user_id"]

    # flashing the success message to the next route with category as 'success'
    flash(u"User Successfully Registered!", "success")

    # Redirect user to home page
    return redirect("/")


@users.route("/forgotPassword", methods=["GET", "POST"])
def forogtpassword():
    """changing user's password"""

    # if request '/changepassword' via post method
    if request.method == "POST":

        # Ensure old password is submitted
        if not request.form.get("email"):

            return jsonify(
            {
                "status" : "error",
                "message" : "Email Missing"
            })

        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (request.form.get("email"),))
                users = cursor.fetchall()


        print(user)

        if not user:

            return jsonify(
                {
                    "status" : "error",
                    "message" : "Invalid Email"
                })

        else:

            session['email'] = request.form.get("email")
            session['otp'] = generateOTP(session['email'])

            return jsonify(
                {
                    "status" : "success",
                    "message" : "user found"
                })

    else:

        return render_template("/users/forgot_password.html")



@users.route("/otp", methods=["POST"])
def otp():

    if not request.form.get('otp'):

        return jsonify(
                {
                    "status" : "error",
                    "message" : "Otp Missing"
                })

    elif session["otp"] != request.form.get('otp'):

        session['otp'] = generateOTP(session["email"])
        return jsonify(
                {
                    "status" : "error",
                    "message" : "Invalid Otp!"
                })

    else:
        session.pop('otp')
        return jsonify(
                {
                    "status" : "success",
                    "message" : "Otp Matched"
                })


@users.route("/reset_password", methods=["POST"])
def reset_password():

    if not request.form.get('newPassword'):

        return jsonify(
                {
                    "status" : "error",
                    "message" : "password missing!"
                })

    if not request.form.get('confirmPassword'):

        return jsonify(
                {
                    "status" : "error",
                    "message" : "confirm your password!"
                })

    if not request.form.get('newPassword') == request.form.get('confirmPassword'):

        return jsonify(
                {
                    "status" : "error",
                    "message" : "password didn't matched!"
                })

    else:
        # hashing the new password
        hash = generate_password_hash(request.form.get("newPassword"))

        # update the new hashed password into database
        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("UPDATE users SET hash = %s WHERE email = %s", (hash, session["email"],))
                users = cursor.fetchall()


        # forget the user's logging
        session.clear()

        # flashing the message of successful changed password
        flash(u"Password successfully changed!", "success")

        return jsonify(
                {
                    "status" : "success",
                    "message" : ""
                })




""" route for loggin out """
@users.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")