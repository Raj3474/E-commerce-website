from flask import Blueprint, flash, jsonify, render_template, request, url_for, redirect, session


import psycopg2.extras

from utils import generateOTP, send_Email, upload_img, remove_img
from config import db_connection, ADMIN_LOGIN_ID, ADMIN_LOGIN_PASS

admin = Blueprint('admin', __name__,
                        template_folder='templates', static_folder='static')


""" admin dashboard """
@admin.route("/dashboard", methods=["GET", "POST"])
@admin.route("/", methods=["GET", "POST"])
def dashboard():

    if request.method == 'POST':
        if True:# session.get('admin'):
            print("Inside dashboard route")

            with db_connection:
                with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("SELECT order_id, products_id, products_name, quantities, sizes, status, address, email FROM latest_orders INNER JOIN users ON latest_orders.user_id = users.user_id WHERE (users.user_id = %s AND status = 'o');", (1,))
                    latest_orders = cursor.fetchall()

                    cursor.execute("SELECT order_id, products_id, products_name, quantities, sizes, status, address, email FROM latest_orders INNER JOIN users ON latest_orders.user_id = users.user_id WHERE (users.user_id = %s AND status = 'd');", (1,))
                    dispatched_orders = cursor.fetchall()

            for order in latest_orders:
                order["products_id"] = order["products_id"].replace(' ','').split(",")
                order["products_name"] = order["products_name"].replace(' ','').split(",")
                order["quantities"] = order["quantities"].replace(' ','').split(",")
                order["sizes"] = order["sizes"].replace(' ','').split(",")


            for order in dispatched_orders:
                order["products_id"] = order["products_id"].replace(' ','').split(",")
                order["products_name"] = order["products_name"].replace(' ','').split(",")
                order["quantities"] = order["quantities"].replace(' ','').split(",")
                order["sizes"] = order["sizes"].replace(' ','').split(",")


            print(latest_orders)
            return render_template("/admin/dashboard.html", latest_orders=latest_orders, dispatched_orders=dispatched_orders)

    return redirect('/admin/login')



@admin.route("/login", methods=["GET", "POST"])
def index():

    session.clear()

    if request.method == "POST":

        admin = request.form.get("admin")
        password = request.form.get("password")

        if not admin:
            return jsonify(
            {
                "status" : "error",
                "message" : "Admin Name Missing"
            })

        elif not password:
            return jsonify(
            {
                "status" : "error",
                "message" : "Password Missing"
            })

        elif ADMIN_LOGIN_ID != admin or ADMIN_LOGIN_PASS != password:
            return jsonify(
            {
                "status" : "error",
                "message" : "Incorrect Admin Info"
            })

        else:

            session['otp'] = generateOTP()
            return jsonify(
            {
                "status" : "success",
                "message" : ""
            })



    return render_template("/admin/login.html")


@admin.route("/otp", methods=["POST"])
def otp():

    if not request.form.get('otp'):

        return jsonify(
                {
                    "status" : "error",
                    "message" : "Otp Missing"
                })

    elif not session.get("otp") == request.form.get('otp'):

        session['otp'] = generateOTP()
        return jsonify(
                {
                    "status" : "error",
                    "message" : "Invalid Otp!"
                })

    else:
        session.clear()
        session['admin'] = True
        return jsonify(
                {
                    "status" : "success",
                    "message" : "Otp Matched"
                })


""" all products """
@admin.route("/products")
def products():

    if True: # session.get('admin')

        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT product_id, product_name, price, sizes_available FROM products;")
                products = cursor.fetchall()

        return render_template("/admin/products.html", products=products)

""" remove a product """
@admin.route("/removeProduct")
def remove_product():

    if True: # session.get('admin')

        p = request.args.get('p')

        # do the database deletion
        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("DELETE FROM products WHERE (product_id=(%s))", (p,))

        remove_img(productId=p)
        return jsonify(True)
    else:
        return "Method Not allowed"


""" update order """
@admin.route("/updateOrder/<update>")
def updateOrder(update):

    p = request.args.get('p')

    if update == 'dispatched':

        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("UPDATE latest_orders SET status = 'd' WHERE order_id=%s;", (p,))

        flash(u"Order updated", "success")
        return redirect('/admin/dashboard')

    if update == 'completed':

        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM latest_orders WHERE order_id=%s;", (p,))
                product = cursor.fetchall()

                cursor.execute("INSERT INTO completed_orders (user_id, products_id, products_name, products_price, quantities, sizes, address) VALUES (%s, %s, %s, %s, %s, %s, %s);", (product[0]['user_id'], product[0]['products_id'], product[0]['products_name'], product[0]['products_price'], product[0]['quantities'], product[0]['sizes'], product[0]['address'],))

        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("DELETE FROM latest_orders WHERE order_id=%s;", (p,))

        flash(u"Order updated", "success")
        return redirect('/admin/dashboard')



""" adding a new product """
@admin.route("/add_product", methods=["POST"])
def add_product():

    if True: # session.get('admin')

        if 'file' not in request.files:
            flash(u"No file part", "danger")
            return redirect(request.url)

        prodname = request.form.get("product")
        price = request.form.get("price")
        proddesc = request.form.get("productdesc")

        sizes = request.form.getlist("size")  # taking all the sizes input by the user via form.getlist
        sizes_available = ""
        for size in sizes:
            sizes_available = sizes_available + ", " + size
        sizes_available = sizes_available.lstrip(', ')

        files = request.files.getlist("file")

        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("INSERT INTO products (product_name, product_desc, price, sizes_available) VALUES (%s, %s, %s, %s)", (prodname, proddesc, price, sizes_available,))
                product_id

        upload_img(files, product_id)

        return redirect('/admin/dashboard')

    return redirect("/admin")



""" admin loggin out """
@admin.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/admin")