from flask import Flask, request, redirect, url_for, render_template, session
import sqlite3
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import uuid
import random
import string
import datetime
from flask_mail import Mail, Message
import razorpay

# ---------------- APP ----------------
ecom = Flask(__name__)

# ---------------- ENV VARIABLES ----------------
ecom.secret_key = os.environ.get("SECRET_KEY")

RAZORPAY_KEY = os.environ.get("RAZORPAY_KEY")
RAZORPAY_SECRET = os.environ.get("RAZORPAY_SECRET")

MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

# ---------------- RAZORPAY ----------------
razorpay_client = razorpay.Client(
    auth=(RAZORPAY_KEY, RAZORPAY_SECRET)
)

# ---------------- BCRYPT ----------------
bcrypt = Bcrypt(ecom)

# ---------------- ADMIN ----------------
admin_data = {
    "username": "prasad",
    "password": "",
    "profile_name": "prasad"
}

password = "Ch077"
hash_password = bcrypt.generate_password_hash(password)
admin_data["password"] = hash_password

# ---------------- DATABASE ----------------
connect_db = sqlite3.connect("ecom.db", check_same_thread=False)
cursor = connect_db.cursor()

# ---------------- MAIL CONFIG ----------------
ecom.config['MAIL_SERVER'] = 'smtp.gmail.com'
ecom.config['MAIL_PORT'] = 587
ecom.config['MAIL_USE_TLS'] = True
ecom.config['MAIL_USERNAME'] = MAIL_USERNAME
ecom.config['MAIL_PASSWORD'] = MAIL_PASSWORD
ecom.config['MAIL_DEFAULT_SENDER'] = MAIL_USERNAME

mail = Mail(ecom)

# ---------------- CREATE TABLES ----------------
@ecom.route("/create_tables")
def tables():

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_data (
    sl_no INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT UNIQUE NOT NULL,
    pin TEXT,
    profile_name TEXT,
    email TEXT UNIQUE NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
    sl_no INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT UNIQUE,
    product TEXT NOT NULL,
    category TEXT,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    product_details TEXT,
    product_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    profile_name TEXT NOT NULL,
    product_id TEXT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price REAL NOT NULL,
    user_email TEXT NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    address TEXT,
    payment_id TEXT
    )
    """)

    connect_db.commit()

    return redirect(url_for("welcome"))

# ---------------- PRODUCT ID ----------------
def generate_product_id():

    date_part = datetime.datetime.now().strftime("%Y%m%d")

    random_part = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )

    return f"PRD_{date_part}_{random_part}"

# ---------------- ORDER ID ----------------
def generate_order_id():

    date_part = datetime.datetime.now().strftime("%Y%m%d%H%M")

    random_part = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )

    return f"ORD_{date_part}_{random_part}"

# ---------------- SEND EMAIL ----------------
def send_order_email(user_email, order_id, name, items, total_amount):

    try:

        msg = Message(
            subject=f"Order Confirmed - {order_id}",
            recipients=[user_email]
        )

        item_lines = ""

        for item in items:

            item_lines += (
                f"{item['name']} x "
                f"{item['qty']} = ₹{item['total']}\n"
            )

        msg.body = f"""
Hello {name},

Your order has been placed successfully.

Order ID: {order_id}

Items:
{item_lines}

Total: ₹{total_amount}

Thank you for shopping with us!
"""

        mail.send(msg)

        print("Email Sent Successfully")

    except Exception as e:

        print("Mail Failed:", e)

# ---------------- PRODUCT IMAGE ----------------
def get_product_image(product_id):

    folder_path = os.path.join('static', 'images', product_id)

    if os.path.exists(folder_path):

        files = os.listdir(folder_path)

        if files:
            return f"images/{product_id}/{files[0]}"

    return "images/default.png"

# ---------------- HOME ----------------
@ecom.route("/")
def welcome():

    return render_template("welcome.html")

# ---------------- ADMIN ----------------
@ecom.route("/admin")
def admin():

    return render_template("admin_form.html")

# ---------------- USER ----------------
@ecom.route("/user")
def user():

    return render_template("user_form.html")

# ---------------- ADMIN LOGIN ----------------
@ecom.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        admin_name = request.form["admin_name"]

        a_password = request.form["admin_password"]

        if admin_data["username"] == admin_name:

            if bcrypt.check_password_hash(
                admin_data["password"],
                a_password
            ):

                session["name"] = admin_data["profile_name"]

                return redirect(url_for("admin_dashboard"))

            else:

                return render_template(
                    "admin_form.html",
                    note="Password Incorrect"
                )

        else:

            return render_template(
                "admin_form.html",
                note="Username Incorrect"
            )

    return render_template("admin_form.html")

# ---------------- ADMIN DASHBOARD ----------------
@ecom.route("/admin_dashboard")
def admin_dashboard():

    if "name" not in session:
        return redirect(url_for("admin_login"))

    cursor.execute(
        "SELECT product_id, product, category, price FROM products"
    )

    db_products = cursor.fetchall()

    products = []

    for p in db_products:

        products.append({
            "id": p[0],
            "name": p[1],
            "category": p[2],
            "price": p[3],
            "image": get_product_image(p[0])
        })

    return render_template(
        "admin_dashboard.html",
        name=session.get("name"),
        products=products
    )

# ---------------- LOGOUT ----------------
@ecom.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return redirect(url_for("welcome"))

# ---------------- ADD PRODUCT ----------------
@ecom.route("/add_details_form", methods=["GET", "POST"])
def add_details_form():

    if 'name' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':

        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        quantity = request.form["quantity"]
        details = request.form['details']

        product_id = generate_product_id()

        query = """
        INSERT INTO products
        (product_id, product, category, quantity, price, product_details)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        cursor.execute(
            query,
            (
                product_id,
                name,
                category,
                quantity,
                price,
                details
            )
        )

        connect_db.commit()

        folder_path = os.path.join(
            'static',
            'images',
            product_id
        )

        os.makedirs(folder_path, exist_ok=True)

        images = request.files.getlist('images[]')

        for image in images:

            if image and image.filename != "":

                filename = secure_filename(image.filename)

                unique_name = (
                    str(uuid.uuid4()) + "_" + filename
                )

                image.save(
                    os.path.join(folder_path, unique_name)
                )

        return redirect(url_for('admin_dashboard'))

    return render_template("add_product_details.html")

# ---------------- USER DASHBOARD ----------------
@ecom.route("/user_dashboard")
def user_dashboard():

    if "profile_name" not in session:
        return redirect(url_for("user_login"))

    cursor.execute(
        "SELECT product_id, product, category, price FROM products"
    )

    db_products = cursor.fetchall()

    products = []

    for p in db_products:

        products.append({
            "id": p[0],
            "name": p[1],
            "category": p[2],
            "price": p[3],
            "image": get_product_image(p[0])
        })

    return render_template(
        "user_dashboard.html",
        name=session.get("profile_name"),
        products=products
    )

# ---------------- PAYMENT ----------------
@ecom.route("/checkout")
def checkout():

    amount = 50000

    razorpay_order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return render_template(
        "payment.html",
        order_id=razorpay_order["id"],
        amount=amount,
        key_id=RAZORPAY_KEY,
        user_email=session.get("email"),
        name=session.get("profile_name")
    )

# ---------------- PAYMENT SUCCESS ----------------
@ecom.route("/payment_success", methods=["POST"])
def payment_success():

    return render_template(
        "order_success.html",
        order_no=generate_order_id()
    )

# ---------------- RUN ----------------
if __name__ == "__main__":

    ecom.run(debug=True, port=5000)