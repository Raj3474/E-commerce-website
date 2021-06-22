from flask import Blueprint, flash, render_template, request, url_for, redirect, session

import psycopg2.extras

from config import db_connection
from utils import login_required

product = Blueprint('product', __name__,
                        template_folder='templates', static_folder='static')


""" All Products Page """
@product.route("/")
@product.route("/<page>")
def products(page='1'):

    sort = request.args.get("sort")

    num_prods_in_single_page = 8
    offset = (int(page) - 1) * num_prods_in_single_page

    print(offset, num_prods_in_single_page)
    with db_connection:
        with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if sort == 'lth':
                cursor.execute("SELECT product_id, product_name, price FROM products ORDER BY price LIMIT %s OFFSET %s;", (num_prods_in_single_page, offset,))
            elif sort == 'htl':
                cursor.execute("SELECT product_id, product_name, price FROM products ORDER BY price DESC LIMIT %s OFFSET %s;", (num_prods_in_single_page, offset,))
            elif sort == 'nf':
                cursor.execute("SELECT product_id, product_name, price FROM products ORDER BY uploaded_on DESC LIMIT %s OFFSET %s;", (num_prods_in_single_page, offset,))
            else:
                cursor.execute("SELECT product_id, product_name, price FROM products LIMIT %s OFFSET %s;", (num_prods_in_single_page, offset,))

            products = cursor.fetchall()

            cursor.execute("SELECT count(product_id) FROM products;")
            count = cursor.fetchall()

    count = count[0]['count']

    total_pages = count // num_prods_in_single_page
    if count % num_prods_in_single_page != 0:
        total_pages = total_pages + 1

    return render_template("/product/products.html", products=products, sort=sort, page=str(page), total_pages=str(total_pages))


""" single product detail """
@product.route("/detail")
def product_detail():

    p = request.args.get("p")


    with db_connection:
        with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT product_id, product_desc, product_name, price, sizes_available FROM products WHERE product_id = %s;", (p,))
            single_product = cursor.fetchall()

            cursor.execute("SELECT product_id, product_name, price FROM products WHERE product_id != %s ORDER BY uploaded_on DESC LIMIT 4", (p,))
            related_products = cursor.fetchall()

    print(single_product)
    if len(single_product) == 0:
        flash(u"Product not found or may be removed", "danger")
        return render_template(url_for('products'))
    single_product[0]["sizes_available"] = single_product[0]["sizes_available"].replace(' ', '').split(',')
    print(single_product)

    return render_template("/product/productDetail.html", product=single_product[0], related_products=related_products)



""" Add to cart """
@product.route("/addToCart")
# @login_required
def add_to_cart():

    # user id saved in session
    # session['userid']


    p = request.args.get("p") # product_id
    s = request.args.get("s") # size selected
    q = request.args.get("q") # quantity


    if not p:
        flash(u"Product is required!", "danger")
        return redirect ("/product")

    if not s:
        flash(u"Select Size!", "danger")
        return redirect("/product/detail?p={}".format(p))

    if not q:
        print("q not found")
        flash(u"Quantity Missing!", "danger")
        return redirect(request.url)


    """ after validation of all the required fields
        insert into database """
    with db_connection:
        with db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("INSERT INTO cart (user_id, product_id, size, quantity) VALUES(%s, %s, %s, %s);", (1, p, s, q,)) #user_id=session["userid"]


    flash(u"Item successfully added to the cart!", "success")
    return redirect("/myCart")