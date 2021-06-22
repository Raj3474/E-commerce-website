from flask import Flask, url_for, flash, jsonify, render_template, request, redirect,\
    Response, session
from flask_session import Session

from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError


from tempfile import mkdtemp

import psycopg2.extras


from utils import login_required, send_Email, generateOTP
from config import db_connection, RPAY_KEY, RPAY_SECRET


import razorpay


from admin.admin import admin
from product.product import product
from users.users import users


# Configure application
app = Flask(__name__)
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(product, url_prefix='/product')
app.register_blueprint(users, url_prefix='/users')


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)


""" index page """
@app.route("/")
def index():

    with db_connection:
        with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT product_id, product_name, price FROM products ORDER BY uploaded_on DESC LIMIT 9")
            items = cursor.fetchall()

    offer = []
    if len(items) == 9:
        offer = items.pop(8)

    return render_template("index.html", products=items, offer=offer)


""" My cart """
@app.route("/myCart")
# @login_required
def my_cart():

    with db_connection:
        with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT products.product_id, cart_id, product_name, price, quantity, size FROM cart INNER JOIN products ON cart.product_id=products.product_id WHERE user_id=%s;",(1,)) # session['user_id']
            products = cursor.fetchall()

    grandTotal = 0
    for product in products:
        grandTotal = grandTotal + (product['price'] * product['quantity'])

    return render_template("myCart.html", products=products, grandTotal=grandTotal)


""" to a remove product from the cart """
@app.route("/removeFromCart")
# @login_required
def remove_product():

    p = request.args.get("p") # productid

    if not p:
       flash(u"Something went wrong!", "danger")
       return redirect("/myCart")

    with db_connection:
        with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("DELETE FROM cart WHERE (cart_id=(%s) AND user_id=(%s))", (p, 1,)) #session["user_id"]

    flash(u"product Successfully removed from cart", "success")
    return redirect("/myCart")


""" my orders """
@app.route("/myOrders")
# login_required
def my_orders():

    with db_connection:
        with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM latest_orders WHERE user_id = (%s)", (1,)) #session["user_id"]
            latest_orders = cursor.fetchall()

            cursor.execute("SELECT * FROM completed_orders WHERE user_id = (%s)", (1,)) #session["user_id"]
            completed_orders = cursor.fetchall()


    for order in latest_orders:
        order["products_name"] = order["products_name"].replace(' ','').split(",")
        order["products_id"] = order["products_id"].replace(' ','').split(",")
        order["products_price"] = order["products_price"].replace(' ','').split(",")
        order["quantities"] = order["quantities"].replace(' ','').split(",")
        order["sizes"] = order["sizes"].replace(' ','').split(",")
    if len(latest_orders) > 0:
        latest_orders[0]['status'] = latest_orders[0]['status'].replace(' ', '')


    print(completed_orders)

    for order in completed_orders:
        order["products_name"] = order["products_name"].replace(' ','').split(",")
        order["products_id"] = order["products_id"].replace(' ','').split(",")
        order["products_price"] = order["products_price"].replace(' ','').split(",")
        order["quantities"] = order["quantities"].replace(' ','').split(",")
        order["sizes"] = order["sizes"].replace(' ','').split(",")

    return render_template("myOrders.html", latest_orders=latest_orders, completed_orders=completed_orders)


""" place-order route """
@app.route("/place_order", methods=["GET", "POST"])
# login_required
def place_order():

    if request.method == "POST":

        print("inside place_order post method")


        name = request.form.get("name")
        mob  = request.form.get("mob")
        email = request.form.get("email")
        address = request.form.get("address")
        city = request.form.get("city")
        state = request.form.get("state")
        pincode = request.form.get("pincode")

        full_address = "{}\n{}\n{}\n{} {} {}-{}".format(name, mob, email, address, city, state, pincode)
        print(full_address)


        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT products.product_id, cart_id, product_name, price, quantity, size FROM cart INNER JOIN products ON cart.product_id=products.product_id WHERE user_id = %s",(1,)) #session['user_id']
                products = cursor.fetchall()


        products_id = ""
        products_name = ""
        products_price = ""
        quantities = ""
        sizes = ""

        for product in products:
            products_id = products_id + ", " + str(product["product_id"])
            products_name = products_name + ", " + product["product_name"]
            products_price = products_price + ", " + str(product["price"])
            quantities = quantities + ", " + str(product["quantity"])
            sizes = sizes + ", " + product["size"]

        products_id = products_id.lstrip(', ')
        products_name = products_name.lstrip(', ')
        products_price = products_price.lstrip(', ')
        quantities = quantities.lstrip(', ')
        sizes = sizes.lstrip(', ')


        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("INSERT INTO latest_orders (user_id, products_id, products_name, products_price, quantities, sizes, status, address) VALUES(%s, %s, %s, %s, %s, %s, %s, %s);",
                    (1, products_id, products_name, products_price, quantities, sizes, 'o', full_address,))

                cursor.execute("DELETE FROM cart WHERE user_id=(%s);", (1,)) #session["user_id"]



        """ notify admin about the order """
        message = """\
        Subject:  New Order | Fitkit


        New Order Received."""


        send_Email(message)


        flash(u"Payment Successfull", "success")
        return redirect("/myOrders")

    else:

        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT products.product_id, cart_id, product_name, price, quantity, size FROM cart INNER JOIN products ON cart.product_id=products.product_id WHERE user_id=%s;",(1,)) #session['user_id']
                products = cursor.fetchall()

        grandTotal = 0
        for product in products:
            grandTotal = grandTotal + (product['price'] * product['quantity'])

        if grandTotal == 0:
            flash(u"Cart is Empty", "danger")
            return redirect("/myCart")

        ''' creating order '''
        client = razorpay.Client(auth = (RPAY_KEY, RPAY_SECRET))

        data = {
            'amount': grandTotal * 100,
            "currency" : "INR",
            "receipt" : 'razorpaydemo'
        }
        order = client.order.create(data = data)
        print(order)

        with db_connection:
            with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT email FROM users WHERE user_id=%s;", (1,)) #session['user_id']
                user_email = cursor.fetchall()

        print(user_email)
        return render_template("payment.html", order=order, email=user_email)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("InternalServerError.html", error=e.name, code = e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)