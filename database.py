from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    area_of_residence = db.Column(db.String(200))
    role = db.Column(db.String(30), default='client')
    customer_type = db.Column(db.String(20), default='pure')
    can_dashboard = db.Column(db.Boolean, default=False)
    can_edit_products = db.Column(db.Boolean, default=False)
    can_manage_inventory = db.Column(db.Boolean, default=False)
    can_record_sales = db.Column(db.Boolean, default=False)
    can_view_orders = db.Column(db.Boolean, default=False)
    can_manage_orders = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_view_reports = db.Column(db.Boolean, default=False)
    can_view_customers = db.Column(db.Boolean, default=False)
    can_meter_readings = db.Column(db.Boolean, default=False)
    is_field_marshal = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(20))
    water_type = db.Column(db.String(20), default='pure')
    price = db.Column(db.Float)
    wholesale_min_qty = db.Column(db.Integer, default=0)
    stock_quantity = db.Column(db.Integer, default=0)
    image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    field_marshal_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    total_amount = db.Column(db.Float)
    mpesa_code = db.Column(db.String(20))
    payment_status = db.Column(db.String(20), default='pending')
    delivery_address = db.Column(db.String(200))
    order_type = db.Column(db.String(20), default='retail')
    source = db.Column(db.String(20), default='online')
    customer = db.relationship('User', foreign_keys=[user_id], backref='customer_orders')
    field_marshal = db.relationship('User', foreign_keys=[field_marshal_id], backref='field_marshal_orders')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Float)
    product = db.relationship('Product', backref='order_items')
    order = db.relationship('Order', backref='items')

class WalkInSale(db.Model):
    __tablename__ = 'walkin_sales'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Float)
    total_amount = db.Column(db.Float)
    payment_method = db.Column(db.String(20))
    mpesa_code = db.Column(db.String(20))
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(15))
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    product = db.relationship('Product', backref='walkin_sales')

class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    stock_in = db.Column(db.Integer, default=0)
    stock_out = db.Column(db.Integer, default=0)
    current_stock = db.Column(db.Integer, default=0)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    product = db.relationship('Product', backref='inventory_records')

class MeterReading(db.Model):
    __tablename__ = 'meter_readings'
    id = db.Column(db.Integer, primary_key=True)
    meter_number = db.Column(db.String(50))
    water_type = db.Column(db.String(20), default='pure')
    reading_value = db.Column(db.Float)
    liters_produced = db.Column(db.Float)
    reading_date = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)

class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    old_price = db.Column(db.Float)
    new_price = db.Column(db.Float)
    changed_date = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))
    amount = db.Column(db.Float)
    description = db.Column(db.String(200))
    expense_date = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
