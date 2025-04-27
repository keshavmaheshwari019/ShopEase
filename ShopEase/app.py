from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta  # Add timedelta to the import
import json
import os
from werkzeug.utils import secure_filename
from functools import wraps
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:9950@localhost/t-6'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add this after creating the Flask app
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images', 'products')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='customer', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add the missing columns
    discount = db.Column(db.Float, nullable=True, default=0.0)
    brand = db.Column(db.String(100), nullable=True)
    rating = db.Column(db.Float, nullable=True, default=0.0)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'), nullable=False)  # Fixed this line
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product')

class Order(db.Model):
    __tablename__ = 'customer_order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='Pending')
    order_status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_delivery = db.Column(db.DateTime)
    shipping_address = db.Column(db.String(200))
    payment_method = db.Column(db.String(50))
    items = db.relationship('OrderItem', backref='order', lazy=True)

# Function to update database schema
def update_database_schema():
    with app.app_context():
        # Check if the columns exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('product')]
        
        # Add missing columns if they don't exist
        if 'brand' not in columns:
            db.session.execute(text("ALTER TABLE product ADD COLUMN brand VARCHAR(100)"))
        if 'discount' not in columns:
            db.session.execute(text("ALTER TABLE product ADD COLUMN discount FLOAT DEFAULT 0.0"))
        if 'rating' not in columns:
            db.session.execute(text("ALTER TABLE product ADD COLUMN rating FLOAT DEFAULT 0.0"))
        
        # Update existing products with default values
        db.session.execute(text("UPDATE product SET brand = '' WHERE brand IS NULL"))
        db.session.execute(text("UPDATE product SET discount = 0.0 WHERE discount IS NULL"))
        db.session.execute(text("UPDATE product SET rating = 0.0 WHERE rating IS NULL"))
        db.session.commit()
        print("Database schema updated successfully!")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    # Use a try-except block to handle potential database errors
    try:
        products = Product.query.limit(8).all()
        return render_template('index.html', products=products)
    except Exception as e:
        flash(f'Error loading products: {str(e)}', 'danger')
        return render_template('index.html', products=[])

@app.route('/products')
def products():
    category = request.args.get('category')
    search = request.args.get('search')
    
    try:
        if category:
            products = Product.query.filter_by(category=category).all()
        elif search:
            products = Product.query.filter(Product.name.ilike(f'%{search}%')).all()
        else:
            products = Product.query.all()
            
        return render_template('products.html', products=products)
    except Exception as e:
        flash(f'Error loading products: {str(e)}', 'danger')
        return render_template('products.html', products=[])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page if next_page else url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/cart')
def cart():
    cart_items = []
    cart = session.get('cart', {})
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            item_total = product.price * quantity
            total += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'item_total': item_total
            })
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cancel_order/<int:order_id>', methods=['POST', 'GET'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Allow only the user who placed the order or admin to cancel
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('home'))
    
    # Update order status to 'Cancelled'
    order.order_status = 'Cancelled'
    db.session.commit()
    
    flash('Order has been cancelled successfully.', 'success')
    return redirect(url_for('orders'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' not in session:
        session['cart'] = {}
        
    cart = session['cart']
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        cart[product_id_str] += quantity
    else:
        cart[product_id_str] = quantity
        
    session['cart'] = cart
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity'))
    
    if 'cart' in session:
        cart = session['cart']
        if quantity > 0:
            cart[product_id] = quantity
        else:
            cart.pop(product_id, None)
        session['cart'] = cart
        
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        cart = session['cart']
        if product_id in cart:
            cart.pop(product_id)
            session['cart'] = cart
            flash('Item removed from cart', 'success')
            
    return redirect(url_for('cart'))
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'info')
        return redirect(url_for('cart'))
        
    cart_items = []
    cart = session.get('cart', {})
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            item_total = product.price * quantity
            total += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'item_total': item_total
            })
    
    if request.method == 'POST':
        estimated_delivery = datetime.utcnow() + timedelta(days=3)
        new_order = Order(
            user_id=current_user.id,
            total_amount=total,
            payment_status='Pending',
            order_status='Pending',
            estimated_delivery=estimated_delivery,
            shipping_address=request.form.get('shipping_address', ''),
            payment_method=request.form.get('payment_method', 'Credit Card')
        )
        db.session.add(new_order)
        db.session.flush()
        
        # Save ordered items
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item['product'].id,
                quantity=item['quantity']
            )
            db.session.add(order_item)

        db.session.commit()

        # Clear the cart after successful checkout
        session.pop('cart', None)

        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=new_order.id))
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/payment/<int:order_id>')
@login_required
def payment(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure user can only access their own orders
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
        
    return render_template('payment.html', order=order)

@app.route('/process_payment/<int:order_id>', methods=['POST'])
@login_required
def process_payment(order_id):
    order = Order.query.get_or_404(order_id)
    
    # In a real app, you would integrate with a payment gateway here
    # For this example, we'll just mark the payment as successful
    
    order.payment_status = 'Paid'
    db.session.commit()
    
    flash('Payment successful!', 'success')
    return redirect(url_for('order_confirmation', order_id=order.id))

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure user can only access their own orders
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
        
    return render_template('order_confirmation.html', order=order)

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure user can only access their own orders
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
        
    return render_template('order_detail.html', order=order)

# Admin routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                        total_users=total_users,
                        total_products=total_products,
                        total_orders=total_orders,
                        recent_orders=recent_orders)

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)



@app.route('/admin/products/add-multiple', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_multiple_products():
    if request.method == 'POST':
        products_data = request.form.getlist('products')
        
        # Process each product
        for product_data in products_data:
            new_product = Product(
                name=product_data['name'],
                price=float(product_data['price']),
                category=product_data['category'],
                description=product_data['description'],
                image_url=product_data['image_url'],
                stock=int(product_data['stock']),
                brand=product_data.get('brand', ''),
                discount=float(product_data.get('discount', 0)),
                rating=float(product_data.get('rating', 0))
            )
            db.session.add(new_product)
        
        db.session.commit()
        flash('Products added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/add_multiple_products.html')


@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            price = float(request.form.get('price'))
            category = request.form.get('category')
            description = request.form.get('description')
            stock = int(request.form.get('stock'))
            brand = request.form.get('brand', '')
            discount = float(request.form.get('discount', 0))
            rating = float(request.form.get('rating', 0))
            
            # Handle image upload
            image_url = request.form.get('image_url')
            uploaded_file = request.files.get('product_image')
            
            if uploaded_file and allowed_file(uploaded_file.filename):
                filename = secure_filename(uploaded_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(file_path)
                image_url = f'/static/images/products/{filename}'
            
            if not image_url:
                flash('Please provide either an image URL or upload an image', 'danger')
                return redirect(url_for('admin_add_product'))
            
            new_product = Product(
                name=name,
                price=price,
                category=category,
                description=description,
                image_url=image_url,
                stock=stock,
                brand=brand,
                discount=discount,
                rating=rating
            )
            
            db.session.add(new_product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
            return redirect(url_for('admin_add_product'))
        
    return render_template('admin/add_product.html')


@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.price = float(request.form.get('price'))
        product.category = request.form.get('category')
        product.description = request.form.get('description')
        product.image_url = request.form.get('image_url')
        product.stock = int(request.form.get('stock'))
        product.brand = request.form.get('brand', '')
        product.discount = float(request.form.get('discount', 0))
        product.rating = float(request.form.get('rating', 0))
        
        db.session.commit()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
        
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/product/delete/<int:product_id>')
@login_required
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/product/upload', methods=['POST'])
@login_required
@admin_required
def admin_upload_product_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({'success': True, 'image_url': f'/static/images/products/{filename}'})
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
@login_required
@admin_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/order/update/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    order_status = request.form.get('order_status')
    if order_status:
        order.order_status = order_status
        db.session.commit()
        flash('Order status updated successfully!', 'success')
        
    return redirect(url_for('admin_order_detail', order_id=order.id))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    user_orders = Order.query.filter_by(user_id=user.id).all()
    return render_template('admin/user_detail.html', user=user, orders=user_orders)

@app.route('/admin/user/toggle/<int:user_id>')
@login_required
@admin_required
def admin_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Toggle user active status (in a real app, you'd have an is_active field)
    # For this example, we'll just show a message
    flash(f'User status toggled for {user.name}', 'success')
    return redirect(url_for('admin_users'))


@app.route('/clothing', methods=['GET'])
def clothing():
    # You can add logic to fetch clothing products if needed
    products = Product.query.filter_by(category='Clothing').all()
    return render_template('clothing.html', products=products)

@app.route('/favorites', methods=['GET'])
@login_required
def favorites():
    # Logic to fetch favorite products for the current user
    # Assuming you have a way to track favorites in your database
    favorite_products = []  # Replace with actual logic to get favorite products
    return render_template('favorites.html', products=favorite_products)

@app.route('/admin/settings')
@login_required
@admin_required
def admin_settings():
    return render_template('admin/settings.html')

@app.route('/init-db')
def initialize_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if products already exist
        if Product.query.count() == 0:
            # Add sample products
            products = [
                {
                    'name': 'Smartphone X',
                    'price': 699.99,
                    'category': 'Electronics',
                    'description': 'Latest smartphone with advanced features, high-resolution camera, and long battery life.',
                    'image_url': '/static/images/products/smartphone.jpg',
                    'stock': 50,
                    'discount': 5.0,
                    'brand': 'TechX',
                    'rating': 4.5
                },
                {
                    'name': 'Laptop Pro',
                    'price': 1299.99,
                    'category': 'Electronics',
                    'description': 'Powerful laptop with high-performance processor, ample storage, and stunning display.',
                    'image_url': '/static/images/products/laptop.jpg',
                    'stock': 30,
                    'discount': 10.0,
                    'brand': 'TechBook',
                    'rating': 4.8
                },
                {
                    'name': 'Wireless Headphones',
                    'price': 149.99,
                    'category': 'Electronics',
                    'description': 'Premium wireless headphones with noise cancellation and exceptional sound quality.',
                    'image_url': '/static/images/products/headphones.jpg',
                    'stock': 100,
                    'discount': 0.0,
                    'brand': 'AudioMax',
                    'rating': 4.3
                },
                {
                    'name': 'Men\'s Casual Shirt',
                    'price': 39.99,
                    'category': 'Clothing',
                    'description': 'Comfortable casual shirt made from high-quality cotton, perfect for everyday wear.',
                    'image_url': '/static/images/products/mens_shirt.jpg',
                    'stock': 200,
                    'discount': 15.0,
                    'brand': 'FashionStyle',
                    'rating': 4.0
                },
                {
                    'name': 'Women\'s Summer Dress',
                    'price': 59.99,
                    'category': 'Clothing',
                    'description': 'Elegant summer dress with floral pattern, lightweight and comfortable for warm weather.',
                    'image_url': '/static/images/products/womens_dress.jpg',
                    'stock': 150,
                    'discount': 20.0,
                    'brand': 'ElegantWear',
                    'rating': 4.6
                },
                {
                    'name': 'Coffee Table',
                    'price': 199.99,
                    'category': 'Home',
                    'description': 'Modern coffee table with sleek design, perfect for any living room.',
                    'image_url': '/static/images/products/coffee_table.jpg',
                    'stock': 25,
                    'discount': 0.0,
                    'brand': 'HomeDecor',
                    'rating': 4.2
                },
                {
                    'name': 'Bedside Lamp',
                    'price': 49.99,
                    'category': 'Home',
                    'description': 'Stylish bedside lamp with adjustable brightness, creates a cozy atmosphere.',
                    'image_url': '/static/images/products/lamp.jpg',
                    'stock': 75,
                    'discount': 5.0,
                    'brand': 'LightCraft',
                    'rating': 3.9
                },
                {
                    'name': 'Bestselling Novel',
                    'price': 24.99,
                    'category': 'Books',
                    'description': 'Award-winning novel that has captivated readers worldwide with its compelling story.',
                    'image_url': '/static/images/products/novel.jpg',
                    'stock': 120,
                    'discount': 0.0,
                    'brand': 'LiteraryPress',
                    'rating': 4.7
                }
            ]
            
            for product_data in products:
                product = Product(**product_data)
                db.session.add(product)
            
            # Create admin user if not exists
            if User.query.filter_by(email='admin@shopease.com').first() is None:
                hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
                admin = User(
                    name='Admin User',
                    email='admin@shopease.com',
                    password=hashed_password,
                    is_admin=True
                )
                db.session.add(admin)
            
            db.session.commit()
            flash('Database initialized with sample data!', 'success')
    
    return redirect(url_for('home'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

if __name__ == '__main__':
    # Update database schema before starting the app
    try:
        update_database_schema()
    except Exception as e:
        print(f"Error updating database schema: {str(e)}")
        print("You may need to run /init-db route to initialize the database properly.")
    
    with app.app_context():
        db.create_all()
    app.run(debug=True)