from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy, session
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy.orm import relationship
from forms import RegisterForm, LoginForm, AddForm
from PIL import Image
import os
from dotenv import load_dotenv
import stripe

from functools import wraps
load_dotenv()

app = Flask(__name__)


stripe.api_key = os.environ.get('STRIPE_API')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#Create table in DB
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)


class Item(db.Model):
    __tablename__ = "store_items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    img_url_1 = db.Column(db.String, nullable=False)
    img_url_2 = db.Column(db.String, nullable=True)
    price = db.Column(db.Float, nullable=False)
    blurb = db.Column(db.String(250), nullable=True)
    # cart = relationship("Cart", back_populates="store_items")

class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("store_items.id"))
    # store_items = relationship("Item", back_populates="cart")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)


with app.app_context():
    db.create_all()

# all Flask routes below
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    # decorated_function.__name__ = f.__name__
    return decorated_function


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("User already exists. Please try with another email.")
            return redirect(url_for('login'))
        else:
            hashed_pw = generate_password_hash(password=form.password.data, method='pbkdf2:sha256', salt_length=8)
            new_user = User(name=form.name.data, email=form.email.data, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('store'))
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('This email does not exist. Please try again.')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect. Please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('store'))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/add_item", methods=["GET", "POST"])
@admin_only
def add_item():
    form = AddForm()
    if form.validate_on_submit():
        filename_1 = os.path.basename(form.img_url_1.data.filename)
        image = Image.open(form.img_url_1.data)
        image.save(os.path.join(app.static_folder, 'images/items', f'{filename_1}'), quality=100)
        resized_1 = image.resize((149, 200))
        resized_1.save(f"static/images/store/{filename_1}", quality=100)
        resized_2 = image.resize((298, 400))
        resized_2.save(f"static/images/large_size/{filename_1}", quality=100)
        resized_3 = image.resize((74, 100))
        resized_3.save(f"static/images/cart/{filename_1}", quality=100)
        filename_2 = os.path.basename(form.img_url_2.data.filename)
        image = Image.open(form.img_url_2.data)
        image.save(os.path.join(app.static_folder, 'images/items', f'{filename_2}'), quality=100)
        resized_2 = image.resize((298, 400))
        resized_2.save(f"static/images/large_size/{filename_2}", quality=100)
        new_item = Item(
            name=form.name.data,
            img_url_1=filename_1,
            img_url_2=filename_2,
            price=form.price.data,
            blurb=form.blurb.data,
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for("store"))
    return render_template("add_item.html", form=form)


@app.route("/store", methods=["GET", "POST"])
def store():
    items = Item.query.all()
    print(items)
    return render_template("store.html", items=items)


@app.route("/show_item/<int:item_id>", methods=["GET", "POST"])
def show_item(item_id):
    requested_item = Item.query.get(item_id)
    return render_template("item.html", item=requested_item)


@app.route("/add_to_cart/<int:item_id>", methods=["GET", "POST"])
def add_to_cart(item_id):
    item = Item.query.get(item_id)
    if not current_user.is_authenticated:
        flash("You need to login or register to add items to the cart.")
        return redirect(url_for("login"))
    cart_item = Cart(
        item_id = item_id,
        user_id = current_user.id,
        name = item.name,
        img_url = item.img_url_1,
        price = item.price,
    )
    db.session.add(cart_item)
    db.session.commit()
    return redirect(url_for('show_cart'))


@app.route("/show_cart", methods=["GET", "POST"])
def show_cart():
    subtotal = 0
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    for item in cart_items:
        subtotal += item.price
    return render_template("cart.html", items=cart_items, subtotal=subtotal)


@app.route("/delete/<int:item_id>/<delete_from>")
def delete(item_id, delete_from):
    if delete_from == 'store':
        item_to_delete = Item.query.get(item_id)
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect(url_for('store'))
    elif delete_from == 'cart':
        item_to_delete = Cart.query.get(item_id)
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect(url_for('show_cart'))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    cart_list = ""
    cart_list = ', '.join([item.name for item in cart_items])
    payable_amount = 0
    for item in cart_items:
        payable_amount += item.price
    checkout_session = stripe.checkout.Session.create(
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': cart_list,
                },
                'unit_amount': int(payable_amount * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f"http://127.0.0.1:5000/success/",
        cancel_url="http://127.0.0.1:5000/cancel",
    )
    return redirect(checkout_session.url, code=303)


@app.route("/success/")
@login_required
def success():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    for item in cart_items:
        db.session.delete(item)
        db.session.commit()
    return render_template("success.html")


@app.route("/cancel")
@login_required
def cancel():
    return render_template("cancel.html")


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == '__main__':
    app.run(debug=True)



