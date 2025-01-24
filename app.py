from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import stripe

app = Flask(__name__)
   # configuring postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://owner:password@localhost/your_database_name'
app.config['SECRET_KEY'] = 'your secret key'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

stripe.api_key = ' your api key'

  # Creating three tables for storing data of user , product and orders using postgresql

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)

   # creating routes 

@app.route('/', methods=['GET'])
def index():
    products = Product.query.all()
    return render_template('index.html')
    #return redirect(url_for('product'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'cart' not in session:
        session['cart'] = {}
        return redirect(url_for('checkout'))
    return render_template('cart.html', cart=session['cart'])

@app.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    product = Product.query.get_or_404(id)
    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']
    if str(id) in cart:
        cart[str(id)]['quantity'] += 1
    else:
        cart[str(id)] = {'name': product.name, 'price': product.price, 'quantity': 1}

    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:id>', methods=['POST'])
def remove_from_cart(id):
    # Check if cart exists in session
    if 'cart' not in session:
        return redirect(url_for('cart'))

    cart = session['cart']
    
    # Check if the product is in the cart
    if str(id) in cart:
        # Remove the product from the cart
        #cart[str(id)]['quantity'] -= 1
        del cart[str(id)]
        session['cart'] = cart

    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        cart = session.get('cart', {})
        total = sum(item['price'] * item['quantity'] for item in cart.values())

        # Stripe payment
        session['cart'] = {}
        return render_template('checkout.html', total=total, success=True)
    except Exception as e:
        return render_template('checkout.html', error=str(e))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

