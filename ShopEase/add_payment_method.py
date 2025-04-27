from app import app, db
from sqlalchemy import Column, String

def add_payment_method_column():
    with app.app_context():
        # Check if the column exists first to avoid errors
        try:
            # Add the payment_method column to the order table
            db.engine.execute('ALTER TABLE "order" ADD COLUMN payment_method VARCHAR(20) DEFAULT \'Cash on Delivery\'')
            print("Successfully added payment_method column to order table")
        except Exception as e:
            print(f"Error adding column: {e}")
            # If there's an error, it might be because the column already exists
            # or there's another issue with the database

if __name__ == "__main__":
    add_payment_method_column()
