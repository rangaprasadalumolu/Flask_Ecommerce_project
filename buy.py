from flask import Flask,request,redirect,url_for,render_template,session
import sqlite3

from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename  #To makes the uploaded filename safe.

import os
import uuid  #To generates random unique ID
import random
import string
import datetime


from flask_mail import Mail, Message 

import razorpay



ecom=Flask(__name__)

ecom.secret_key="my secret key"


razorpay_client = razorpay.Client(auth=("rzp_test_SlEQWoA4jQfPpV", "tnVrCOUOjaa7nMTJF3AIMhaX"))


bcrypt=Bcrypt(ecom)
admin_data={"username":"prasad","password":"*****","profile_name":"prasad"}
password="Ch077"
hash=bcrypt.generate_password_hash(password)
admin_data["password"]=hash

# connect_db=mysql.connector.connect(
# host="localhost",user="root",password="root",database="ecom")
connect_db = sqlite3.connect("ecom.db", check_same_thread=False)
cursor = connect_db.cursor()

@ecom.route("/create_tables")
def tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_data (
    sl_no INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT UNIQUE NOT NULL,
    pin TEXT,
    profile_name TEXT,
    email TEXT UNIQUE NOT NULL)""")
   

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
    )""")
    connect_db.commit()

    return redirect(url_for("welcome"))




ecom.config['MAIL_SERVER'] = 'smtp.gmail.com' 
ecom.config['MAIL_PORT'] = 587 
ecom.config['MAIL_USE_TLS'] = True 
ecom.config['MAIL_USERNAME'] = 'rangaprasadalumolu66@gmail.com' 
ecom.config['MAIL_PASSWORD'] = "tbbkymtwepotmrmz"  # Not your login password 
ecom.config['MAIL_DEFAULT_SENDER'] = 'rangaprasadalumolu66@gmail.com' 
 
mail = Mail(ecom) 

# Generate product_id
def generate_product_id():
    date_part = datetime.datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PRD_{date_part}_{random_part}"


# Function to generate a random Order ID 
def generate_order_id(): 
    date_part = datetime.datetime.now().strftime("%Y%m%d%H%M") 
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) 
    return f"ORD_{date_part}_{random_part}" 

# for sending mail to user when this function is called
def send_order_email(user_email, order_id, name, items, total_amount):
    try:
        msg = Message(
            subject=f"Order Confirmed - {order_id}",
            recipients=[user_email]
        )

        # 🔹 Plain text fallback
        item_lines = ""
        for item in items:
            item_lines += f"{item['name']} x {item['qty']} = ₹{item['total']}\n"

        msg.body = f"""
Hello {name},

Your order has been placed successfully.

Order ID: {order_id}

Items:
{item_lines}

Total: ₹{total_amount}

Thank you for shopping with us!
"""

        # 🔹 HTML table rows
        rows = ""
        for item in items:
            rows += f"""
            <tr>
                <td style="padding:10px;">{item['name']}</td>
                <td style="padding:10px; text-align:center;">{item['qty']}</td>
                <td style="padding:10px; text-align:right;">₹{item['price']}</td>
                <td style="padding:10px; text-align:right;">₹{item['total']}</td>
            </tr>
            """

        # 🔹 HTML email
        msg.html = f"""
        <html>
        <body style="font-family: Arial; background:#f4f4f4; padding:20px;">

        <table width="600" align="center" style="background:#fff; padding:20px; border-radius:10px;">
            
            <tr>
                <td align="center">
                    <h2 style="color:#2c3e50;">🛒 Order Confirmation</h2>
                </td>
            </tr>

            <tr>
                <td>
                    <p>Hi <b>{name}</b>,</p>
                    <p>Your order has been placed successfully.</p>
                    <p><b>Order ID:</b> {order_id}</p>
                </td>
            </tr>

            <tr>
                <td>
                    <table width="100%" border="1" cellspacing="0" cellpadding="0" style="border-collapse: collapse;">
                        <tr style="background:#eee;">
                            <th style="padding:10px;">Product</th>
                            <th>Qty</th>
                            <th>Price</th>
                            <th>Total</th>
                        </tr>
                        {rows}
                    </table>
                </td>
            </tr>

            <tr>
                <td style="text-align:right; padding-top:15px;">
                    <h3>Total: ₹{total_amount}</h3>
                </td>
            </tr>

            <tr>
                <td align="center" style="padding-top:20px; color:#888;">
                    <p>Thank you for shopping with us!</p>
                </td>
            </tr>

        </table>

        </body>
        </html>
        """

        mail.send(msg)
        print("✅ Email sent with cart details")

    except Exception as e:
        print("❌ Mail failed:", e)


#getting a single image path from the product id folder in static
def get_product_image(product_id):
    folder_path = os.path.join('static', 'images', product_id)

    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        if files:
            return f"images/{product_id}/{files[0]}"  # first image

    return "images/default.png"  # fallback image


@ecom.route("/")   
def welcome():     

    return render_template("welcome.html")    

@ecom.route("/admin",methods=["GET","POST"])
def admin():
 return render_template("admin_form.html")


@ecom.route("/user",methods=["GET","POST"])
def user():
 return render_template("user_form.html")

@ecom.route("/admin_login",methods=["GET","POST"])
def admin_login():
   if "profile_name" in session:
      return redirect(url_for("user_dashboard"))

   elif "name" in session:  #If already logged in, redirect to dashboard
        return redirect(url_for("admin_dashboard"))
   if request.method=="POST":
      admin_name=request.form["admin_name"]
      a_password=request.form["admin_password"]
      if admin_data["username"]==admin_name:
          #if bcrypt.check_password_hash(admin_data["password"],password):
          if bcrypt.check_password_hash(admin_data["password"], a_password):
             session["name"]=admin_data["profile_name"] #storing of profile name
             return  redirect(url_for("admin_dashboard"))
          else:
             return render_template("admin_form.html",note="password incorrect")
      else:
         return render_template("admin_form.html",note="username incorrect")
      
   return render_template("admin_form.html")

#admin dashboard   
@ecom.route("/admin_dashboard",methods=["GET","POST"])
def admin_dashboard():
   
   if "profile_name" in session:

      return redirect(url_for("user_dashboard"))
   
   elif "name" not in session:
     return redirect(url_for("admin_login"))
    # Fetch products
   cursor.execute("SELECT product_id, product, category, price FROM products;")
   
   db_products = cursor.fetchall()
   # 🔥 Attach images
   products = []
   for p in db_products:
        products.append({
            "id": p[0],
            "name": p[1],
            "category": p[2],
            "price": p[3],
            "image": get_product_image(p[0])
        })
   
   return render_template("admin_dashboard.html",name=session.get("name"),products=products)

@ecom.route("/user_login",methods=["GET","POST"])
def user_login():
   if "name" in session:
      return redirect(url_for("admin_dashboard"))

   elif "profile_name" in session:  #If already logged in, redirect to dashboard
        return redirect(url_for("user_dashboard"))
   
   
   if request.method=="POST":
      user_name=request.form["user_name"]
      user_password=request.form["user_password"]
      cursor.execute("select user from user_data where user=?",(user_name,))
      if cursor.fetchall():
           cursor.execute("select user,pin,profile_name,email from user_data where user=?",(user_name,))
           db_data=cursor.fetchall()#[["prasad","Ch077","prasad","prasad@gmail"]]
           pin=str(db_data[0][1])

           if user_password==pin:
             session["pin"]=str(db_data[0][1])
             session["profile_name"]=str(db_data[0][2])
             session["email"]=str(db_data[0][3])
             return  redirect(url_for("user_dashboard")) 
           else:
              
              return render_template("user_form.html",msg="password is incorrect")


      else:
         
         return render_template("user_form.html",msg="user not registered plz sign-in  ")
    
   return render_template("user_form.html")

#user dashboard
@ecom.route("/user_dashboard")
def user_dashboard():

    if "name" in session:
        return redirect(url_for("admin_dashboard"))
    if "profile_name" not in session:
        return redirect(url_for("user_login"))

    # 🔍 Get values
    search = request.args.get("search")
    category = request.args.get("category")

    # 🔥 Simple conditions
    if search and category:
        cursor.execute(
            "SELECT product_id, product, category, price FROM products WHERE product LIKE ? AND category=?",
            (f"%{search}%", category)
        )

    elif search:
        cursor.execute(
            "SELECT product_id, product, category, price FROM products WHERE product LIKE ?",
            (f"%{search}%",)
        )

    elif category:
        cursor.execute(
            "SELECT product_id, product, category, price FROM products WHERE category=?",
            (category,)
        )

    else:
        cursor.execute(
            "SELECT product_id, product, category, price FROM products"
        )

    db_products = cursor.fetchall()

    # 🔹 Attach images
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

@ecom.route("/logout",methods=["GET","POST"])
def logout():
   session.clear()
   return render_template("welcome.html")

@ecom.route("/user_register_form", methods=["GET", "POST"])
def user_register_form():
    return redirect(url_for("user_register"))

@ecom.route("/user_register", methods=["GET", "POST"])
def user_register():

    # 🔥 clear old session before register
    session.clear()

    if request.method == "POST":

        user = request.form["u_n"]
        pin = request.form["pn"]
        profile_name = request.form["pf_n"]
        email = request.form["eml"]

        cursor.execute(
            "SELECT user FROM user_data WHERE user=?",
            (user,)
        )

        if cursor.fetchall():

            return render_template(
                "user_register.html",
                msg="Username already exists"
            )

        cursor.execute(
            "SELECT email FROM user_data WHERE email=?",
            (email,)
        )

        if cursor.fetchall():

            return render_template(
                "user_register.html",
                msg="Email already exists"
            )

        cursor.execute(
            "INSERT INTO user_data(user,pin,profile_name,email) VALUES(?,?,?,?)",
            (user, pin, profile_name, email)
        )

        connect_db.commit()

        return render_template(
            "user_form.html",
            msg1="Registration successful. Please login."
        )

    return render_template("user_register.html")


   
@ecom.route("/add_details",methods=["GET","POST"])
def add_details():
     if 'name' not in session:
        return redirect(url_for('admin_login'))
     else:
        
      return redirect(url_for("add_details_form"))

     

@ecom.route("/add_details_form",methods=["GET","POST"])
def add_details_form():
      if 'name' not in session:
        return redirect(url_for('admin_login'))
      if request.method == 'POST':

        # 🔹 Form data
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        quantity=request.form["quantity"]
        details = request.form['details']

        # 🔥 Generate product_id
        product_id = generate_product_id()

        # 🔹 Insert into MySQL
        query = """
        INSERT INTO products (product_id, product, category, quantity , price, product_details)
        VALUES (?, ?, ?, ?, ?,?)
        """
        cursor.execute(query, (product_id, name, category,quantity ,price, details))
        connect_db.commit()

        # 🔹 Create folder inside static/images
        folder_name = product_id   #  only product_id
        folder_path = os.path.join('static', 'images', folder_name)

        os.makedirs(folder_path, exist_ok=True)

        

        # 🔹 Save images
        images = request.files.getlist('images[]')

        for image in images:
            if image and image.filename != "":
                filename = secure_filename(image.filename)

                
                unique_name = str(uuid.uuid4()) + "_" + filename

                image.save(os.path.join(folder_path, unique_name))

        return redirect(url_for('admin_dashboard'))
        
      return render_template("add_product_details.html")


@ecom.route('/product/<product_id>')
def product_page(product_id):
    cursor = connect_db.cursor()

    cursor.execute("SELECT * FROM products WHERE product_id=?;", (product_id,))
    row = cursor.fetchone()

    if not row:
        return "Product not found", 404

    product = {
        "sl_no": row[0],
        "product_id": row[1],
        "product": row[2],
        "category": row[3],
        "price": row[4],
        "quantity": row[5],
        "product_details": row[6],
        "product_date": row[7]
    }

    image_folder = os.path.join('static', 'images', product_id)

    images = []
    if os.path.exists(image_folder):
        for file in os.listdir(image_folder):
            images.append(f"images/{product_id}/{file}")

    images.sort()

    return render_template("product_page.html", product=product, images=images)

@ecom.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if "profile_name" not in session:
        return redirect(url_for("user_login"))

    product_id = request.form.get("product_id")

    # Initialize cart if not exists
    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]  #cart={}

    # If product already in cart → increase quantity
    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    session["cart"] = cart  # save back to session

    return redirect(url_for("view_cart"))

@ecom.route("/cart")
def view_cart():
    if "profile_name" not in session:
        return redirect(url_for("user_login"))

    cart = session.get("cart", {})  #cart={"product_id1":1,"product_id2":3}
                      #[(product_id1,1),(product_id2,3)]

    cart_items = []
    total_price_cart = 0

    for product_id, qty in cart.items():
        cursor.execute(
            "SELECT product_id, product, price FROM products WHERE product_id=?",
            (product_id,)
        )
        product = cursor.fetchone()#(p_id,tv,50000)

        if product:
            item_total = product[2] * qty
            total_price_cart += item_total

            cart_items.append({
                "id": product[0],
                "name": product[1],
                "price": product[2],
                "quantity": qty,
                "total": item_total,
                "image": get_product_image(product[0])
            })

    return render_template("cart.html", cart_items=cart_items, total_price=total_price_cart)


@ecom.route("/remove_from_cart/<product_id>")
def remove_from_cart(product_id):

    if "profile_name" not in session:
        return redirect(url_for("user_login"))
    cart = session.get("cart", {}) #cart={"product_id2":3}

    if product_id in cart:
        cart.pop(product_id)

    session["cart"] = cart

    return redirect(url_for("view_cart"))


@ecom.route("/empty_cart")
def empty_cart():
    if "profile_name" not in session:
        return redirect(url_for("user_login"))
    cart=session.get("cart",{})

    if cart:
       cart.clear()

    session["cart"]=cart
    return redirect(url_for("view_cart"))

@ecom.route("/update_product/<product_id>", methods=["GET", "POST"]) 
def update_product_form(product_id): 

    if 'name' not in session: 
        return redirect(url_for('admin_login')) 

    # ✅ SQLite cursor (NO dictionary=True)
    cursor = connect_db.cursor() 
    cursor.execute("SELECT * FROM products WHERE product_id=?", (product_id,)) 
    row = cursor.fetchone() 

    # ✅ Convert row → dictionary manually
    if row:
        product = {
            "sl_no": row[0],
            "product_id": row[1],
            "product": row[2],
            "category": row[3],
            "price": row[4],
            "quantity": row[5],
            "product_details": row[6],
            "product_date": row[7]
        }
    else:
        return "Product not found", 404

    # 🔹 Get existing images 
    image_folder = os.path.join('static', 'images', product_id) 
    images = [] 

    if os.path.exists(image_folder): 
        for file in os.listdir(image_folder): 
            images.append(file) 

    if request.method == "POST": 

        # 🔹 Update price 
        new_price = request.form.get("price") 

        cursor.execute( 
            "UPDATE products SET price=? WHERE product_id=?", 
            (new_price, product_id) 
        ) 
        connect_db.commit() 

        # 🔥 DELETE selected images 
        delete_images = request.form.getlist("delete_images") 

        for img in delete_images: 
            img_path = os.path.join(image_folder, img) 
            if os.path.exists(img_path): 
                os.remove(img_path) 

        # 🔥 ADD new images 
        new_images = request.files.getlist("new_images") 

        for image in new_images: 
            if image and image.filename != "": 
                filename = secure_filename(image.filename) 
                unique_name = str(uuid.uuid4()) + "_" + filename 
                image.save(os.path.join(image_folder, unique_name)) 

        return redirect(url_for("admin_dashboard")) 

    return render_template("update_product.html", product=product, images=images)

#delete a product
@ecom.route("/delete_product/<product_id>", methods=["POST"])
def delete_product(product_id):

    if "name" not in session:
        return redirect(url_for("admin_login"))

    # 🔹 Delete from DB
    cursor.execute("DELETE FROM products WHERE product_id=?", (product_id,))
    connect_db.commit()

    # 🔹 Delete images folder
    folder_path = os.path.join('static', 'images', product_id)

    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            os.remove(os.path.join(folder_path, file))
        os.rmdir(folder_path)

    return redirect(url_for("admin_dashboard"))


@ecom.route("/address", methods=["GET", "POST"])
def address():
    if "profile_name" not in session:
        return redirect(url_for("user_login"))

    if request.method == "POST":
        session["address"] = {
            "name": request.form.get("name"),
            "phone": request.form.get("phone"),
            "address": request.form.get("address"),
            "city": request.form.get("city"),
            "pincode": request.form.get("pincode")
        }

        product_id = request.form.get("product_id")

        if product_id:
            return redirect(url_for("checkout", product_id=product_id))
        else:
            return redirect(url_for("checkout"))

    return render_template("address.html")



@ecom.route("/checkout", methods=["GET", "POST"])
def checkout():

    if "profile_name" not in session:
        return redirect(url_for("user_login"))

    if "address" not in session:
        return redirect(url_for("address"))

    cart = session.get("cart", {})
    buy_now_id = request.form.get("product_id") or request.args.get("product_id")

    # Decide items
    if buy_now_id:
        items_to_purchase = {buy_now_id: 1}
    else:
        items_to_purchase = cart

    if not items_to_purchase:
        return redirect(url_for("user_dashboard"))

    total_amount = 0

    for p_id, qty in items_to_purchase.items():
        cursor.execute("SELECT price FROM products WHERE product_id=?", (p_id,))
        result = cursor.fetchone()
        
        if not result:
            continue

        price = result[0]
        total_amount += price * qty

    # Convert to paise
    amount_in_paise = int(total_amount * 100)

    # Create Razorpay Order
    razorpay_order = razorpay_client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    # Store in session
    session["items_to_purchase"] = items_to_purchase
    session["razorpay_order_id"] = razorpay_order["id"]

    return render_template(
        "payment.html",
        order_id=razorpay_order["id"],
        amount=amount_in_paise,
        key_id="rzp_test_SlEQWoA4jQfPpV",  # 🔥 replace with your real key
        user_email=session.get("email"),
        name=session.get("profile_name")
    )



@ecom.route("/payment_success", methods=["POST"])
def payment_success():

    if "profile_name" not in session:
        return redirect(url_for("user_login"))

    # 🔥 Get Razorpay response from hidden inputs
    razorpay_order_id = request.form.get("razorpay_order_id")
    razorpay_payment_id = request.form.get("razorpay_payment_id")
    razorpay_signature = request.form.get("razorpay_signature")

    try:
        # ✅ Verify payment signature
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })

        # ✅ If verified → process order
        items = session.get("items_to_purchase", {})
        address = session.get("address")
        user_email = session.get("email")
        profile_name = session.get("profile_name")

        final_order_id = None  # to show in success page

        for p_id, qty in items.items():

            # 🔹 Generate custom order ID
            order_id = generate_order_id()
            final_order_id = order_id

            # 🔹 Get product details
            cursor.execute(
                "SELECT product, price FROM products WHERE product_id=?",
                (p_id,)
            )
            result = cursor.fetchone()

            if not result:
                continue

            product_name, price = result

            # 🔥 Insert into orders table
            cursor.execute("""
            INSERT INTO orders 
            (order_id, profile_name, product_id, price, user_email, product_name, quantity, address, payment_id)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, (
            order_id,
                  profile_name,
                         p_id,
                          price,
                       user_email,
                          product_name,
                             qty,
                      str(address),
                             razorpay_payment_id
                              ))
            connect_db.commit()

        items_list = []
        total_amount = 0

        for p_id, qty in items.items():
            cursor.execute(
                "SELECT product, price FROM products WHERE product_id=?",
                (p_id,)
            )
            result = cursor.fetchone()

            if not result:
                continue

            product_name, price = result
            item_total = price * qty
            total_amount += item_total

            items_list.append({
                "name": product_name,
                "qty": qty,
                "price": price,
                "total": item_total
            })

        # ✅ Send confirmation mail
        if user_email and final_order_id:
           send_order_email(user_email, final_order_id, profile_name, items_list, total_amount
)

        # ✅ Clear session
        session.pop("cart", None)
        session.pop("items_to_purchase", None)
        session.pop("address", None)

        # ✅ Redirect to success page
        return render_template("order_success.html", order_no=final_order_id)

    except Exception as e:
        print("Verification Error:", e)
        return redirect(url_for("payment_failed",data=e))


@ecom.route("/payment_failed/<data>")
def payment_failed(data):
   
   return f"payment failed {data} "

if __name__=="__main__":
    ecom.run(debug=True)


