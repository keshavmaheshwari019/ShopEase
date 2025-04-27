from app import app, db, Product, User, bcrypt
from datetime import datetime

def init_db():
    with app.app_context():
        # Create tables
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
                    'stock': 50
                },
                {
                    'name': 'Laptop Pro',
                    'price': 1299.99,
                    'category': 'Electronics',
                    'description': 'Powerful laptop with high-performance processor, ample storage, and stunning display.',
                    'image_url': '/static/images/products/laptop.jpg',
                    'stock': 30
                },
                {
                    'name': 'Wireless Headphones',
                    'price': 149.99,
                    'category': 'Electronics',
                    'description': 'Premium wireless headphones with noise cancellation and exceptional sound quality.',
                    'image_url': '/static/images/products/headphones.jpg',
                    'stock': 100
                },
                {
                    'name': 'Men\'s Casual Shirt',
                    'price': 39.99,
                    'category': 'Clothing',
                    'description': 'Comfortable casual shirt made from high-quality cotton, perfect for everyday wear.',
                    'image_url': '/static/images/products/mens_shirt.jpg',
                    'stock': 200
                },
                {
                    'name': 'Women\'s Summer Dress',
                    'price': 59.99,
                    'category': 'Clothing',
                    'description': 'Elegant summer dress with floral pattern, lightweight and comfortable for warm weather.',
                    'image_url': '/static/images/products/womens_dress.jpg',
                    'stock': 150
                },
                {
                    'name': 'Coffee Table',
                    'price': 199.99,
                    'category': 'Home',
                    'description': 'Modern coffee table with sleek design, perfect for any living room.',
                    'image_url': '/static/images/products/coffee_table.jpg',
                    'stock': 25
                },
                {
                    'name': 'Bedside Lamp',
                    'price': 49.99,
                    'category': 'Home',
                    'description': 'Stylish bedside lamp with adjustable brightness, creates a cozy atmosphere.',
                    'image_url': '/static/images/products/lamp.jpg',
                    'stock': 75
                },
                {
                    'name': 'Bestselling Novel',
                    'price': 24.99,
                    'category': 'Books',
                    'description': 'Award-winning novel that has captivated readers worldwide with its compelling story.',
                    'image_url': '/static/images/products/novel.jpg',
                    'stock': 120
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
            print("Database initialized with sample data!")

if __name__ == '__main__':
    init_db()
