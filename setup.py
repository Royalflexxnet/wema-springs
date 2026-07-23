import os

base_dir = "."

directories = [
    "static/css",
    "static/js",
    "static/uploads",
    "templates/dashboard"
]

for directory in directories:
    os.makedirs(os.path.join(base_dir, directory), exist_ok=True)

print("✅ Directories created!")

with open("requirements.txt", "w") as f:
    f.write("""Flask==2.3.2
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
Werkzeug==2.3.6
reportlab==4.0.0
""")
print("✅ requirements.txt")

with open("database.py", "w", encoding="utf-8") as f:
    f.write("""from flask_sqlalchemy import SQLAlchemy
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
""")
print("✅ database.py")

with open("app.py", "w", encoding="utf-8") as f:
    f.write("""from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_user, login_required, logout_user, current_user
from database import db, login_manager, User, Product, Order, OrderItem, Inventory, MeterReading, PriceHistory, WalkInSale, Expense
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func, or_
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wema-springs-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wema_springs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

def user_has_permission(permission):
    if not current_user.is_authenticated: return False
    if current_user.role == 'admin': return True
    return getattr(current_user, permission, False)

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not user_has_permission(permission):
                flash('Permission denied.', 'danger')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role == 'client':
            flash('Staff access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    pure_retail = Product.query.filter_by(category='retail', water_type='pure').limit(4).all()
    salt_retail = Product.query.filter_by(category='retail', water_type='salt').limit(4).all()
    pure_wholesale = Product.query.filter_by(category='wholesale', water_type='pure').limit(4).all()
    salt_wholesale = Product.query.filter_by(category='wholesale', water_type='salt').limit(4).all()
    return render_template('index.html', pure_retail=pure_retail, salt_retail=salt_retail,
                           pure_wholesale=pure_wholesale, salt_wholesale=salt_wholesale)

@app.route('/shop/retail')
def shop_retail():
    water_type = request.args.get('type', 'pure')
    products = Product.query.filter_by(category='retail', water_type=water_type).all()
    return render_template('shop_retail.html', products=products, water_type=water_type)

@app.route('/shop/wholesale')
def shop_wholesale():
    water_type = request.args.get('type', 'pure')
    products = Product.query.filter_by(category='wholesale', water_type=water_type).all()
    return render_template('shop_wholesale.html', products=products, water_type=water_type)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone_number', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        email = request.form.get('email')
        area = request.form.get('area_of_residence')
        customer_type = request.form.get('customer_type', 'pure')
        if not phone or not password or not name:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(phone_number=phone).first():
            flash('Phone number already registered!', 'danger')
            return redirect(url_for('login'))
        user = User(phone_number=phone, name=name, email=email, area_of_residence=area,
                    role='client', customer_type=customer_type)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')
        if not login_id or not password:
            flash('Please enter your login details.', 'danger')
            return render_template('login.html')
        user = User.query.filter(or_(User.username == login_id, User.phone_number == login_id)).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome, {user.name}!', 'success')
            if user.role != 'client':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('client_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard/client')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        return redirect(url_for('admin_dashboard'))
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('dashboard/client_dashboard.html', orders=orders)

@app.route('/place-order', methods=['POST'])
@login_required
def place_order():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    mpesa_code = request.form.get('mpesa_code', '')
    delivery_address = request.form.get('delivery_address', current_user.area_of_residence)
    product = Product.query.get_or_404(product_id)
    if product.stock_quantity < quantity:
        flash('Insufficient stock!', 'danger')
        return redirect(request.referrer or url_for('shop_retail'))
    total = product.price * quantity
    order = Order(user_id=current_user.id, total_amount=total, mpesa_code=mpesa_code,
                  payment_status='paid' if mpesa_code else 'pending',
                  delivery_address=delivery_address, order_type=product.category, source='online')
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=quantity, unit_price=product.price))
    product.stock_quantity -= quantity
    db.session.add(Inventory(product_id=product.id, stock_out=quantity, current_stock=product.stock_quantity,
                   recorded_by=current_user.id, notes=f'Order #{order.id}'))
    db.session.commit()
    flash(f'Order placed! KES {total:.2f}', 'success')
    return redirect(url_for('client_dashboard'))

@app.route('/track-order/<int:order_id>')
@login_required
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and current_user.role == 'client':
        flash('Access denied.', 'danger')
        return redirect(url_for('client_dashboard'))
    return render_template('dashboard/track_order.html', order=order)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_pw = request.form.get('old_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')
        if not current_user.check_password(old_pw):
            flash('Current password is incorrect.', 'danger')
        elif new_pw != confirm_pw:
            flash('New passwords do not match.', 'danger')
        elif len(new_pw) < 4:
            flash('Password too short.', 'danger')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash('Password updated!', 'success')
            return redirect(url_for('client_dashboard') if current_user.role == 'client' else url_for('admin_dashboard'))
    return render_template('change_password.html')

@app.route('/dashboard/admin')
@login_required
@staff_required
def admin_dashboard():
    if current_user.is_field_marshal:
        total_orders = Order.query.filter_by(field_marshal_id=current_user.id).count()
        recent_orders = Order.query.filter_by(field_marshal_id=current_user.id).order_by(Order.order_date.desc()).limit(5).all()
    else:
        total_orders = Order.query.count()
        recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    total_walkins = db.session.query(func.sum(WalkInSale.total_amount)).scalar() or 0
    online_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.payment_status == 'paid').scalar() or 0
    total_revenue = online_sales + total_walkins
    total_customers = User.query.filter_by(role='client').count()
    total_products = Product.query.count()
    recent_walkins = WalkInSale.query.order_by(WalkInSale.sale_date.desc()).limit(5).all()
    low_stock = Product.query.filter(Product.stock_quantity < 10).all()
    return render_template('dashboard/admin_dashboard.html',
                         total_orders=total_orders, total_revenue=total_revenue,
                         total_customers=total_customers, total_products=total_products,
                         recent_orders=recent_orders, recent_walkins=recent_walkins, low_stock=low_stock)

@app.route('/admin/clients/add', methods=['POST'])
@login_required
@staff_required
def add_client():
    if not current_user.is_field_marshal and current_user.role != 'admin':
        flash('Only admins and field marshals can add clients.', 'danger')
        return redirect(url_for('admin_dashboard'))
    phone = request.form.get('phone_number', '').strip()
    name = request.form.get('name')
    area = request.form.get('area', '')
    customer_type = request.form.get('customer_type', 'pure')
    password = request.form.get('password', '1234')
    if not phone or not name:
        flash('Phone and name required.', 'danger')
        return redirect(url_for('manage_customers'))
    if User.query.filter_by(phone_number=phone).first():
        flash('Client exists.', 'danger')
        return redirect(url_for('manage_customers'))
    client = User(phone_number=phone, name=name, area_of_residence=area, role='client', customer_type=customer_type)
    client.set_password(password)
    db.session.add(client)
    db.session.commit()
    flash(f'Client {name} added!', 'success')
    return redirect(url_for('manage_customers'))

@app.route('/admin/clients/delete/<int:user_id>')
@login_required
@staff_required
def delete_client(user_id):
    if not current_user.is_field_marshal and current_user.role != 'admin':
        flash('Only admins and field marshals.', 'danger')
        return redirect(url_for('admin_dashboard'))
    client = User.query.get_or_404(user_id)
    if client.role != 'client':
        flash('Can only delete clients.', 'danger')
        return redirect(url_for('manage_customers'))
    db.session.delete(client)
    db.session.commit()
    flash('Client removed.', 'success')
    return redirect(url_for('manage_customers'))

@app.route('/admin/walkin-sale')
@login_required
@permission_required('can_record_sales')
def walkin_sale():
    products = Product.query.all()
    today_sales = WalkInSale.query.filter(func.date(WalkInSale.sale_date) == datetime.now().date()).order_by(WalkInSale.sale_date.desc()).all()
    return render_template('dashboard/walkin_sale.html', products=products, today_sales=today_sales)

@app.route('/admin/walkin-sale/record', methods=['POST'])
@login_required
@permission_required('can_record_sales')
def record_walkin_sale():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    payment_method = request.form.get('payment_method', 'cash')
    mpesa_code = request.form.get('mpesa_code', '')
    customer_name = request.form.get('customer_name', 'Walk-in')
    product = Product.query.get_or_404(product_id)
    if product.stock_quantity < quantity:
        flash('Insufficient stock!', 'danger')
        return redirect(url_for('walkin_sale'))
    total = product.price * quantity
    db.session.add(WalkInSale(product_id=product.id, quantity=quantity, unit_price=product.price,
                   total_amount=total, payment_method=payment_method,
                   mpesa_code=mpesa_code if payment_method=='mpesa' else None,
                   customer_name=customer_name, recorded_by=current_user.id))
    product.stock_quantity -= quantity
    db.session.add(Inventory(product_id=product.id, stock_out=quantity, current_stock=product.stock_quantity,
                   recorded_by=current_user.id, notes='Walk-in sale'))
    db.session.commit()
    flash(f'Sale recorded! KES {total:.2f}', 'success')
    return redirect(url_for('walkin_sale'))

@app.route('/admin/customers')
@login_required
@permission_required('can_view_customers')
def manage_customers():
    customer_type_filter = request.args.get('type', 'all')
    if customer_type_filter == 'all':
        customers = User.query.filter_by(role='client').order_by(User.created_at.desc()).all()
    else:
        customers = User.query.filter_by(role='client', customer_type=customer_type_filter).order_by(User.created_at.desc()).all()
    return render_template('dashboard/customers.html', customers=customers, current_filter=customer_type_filter)

@app.route('/admin/customers/view/<int:user_id>')
@login_required
def view_customer(user_id):
    customer = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()
    return render_template('dashboard/customer_detail.html', customer=customer, orders=orders)

@app.route('/admin/users')
@login_required
@permission_required('can_manage_users')
def manage_users():
    staff = User.query.filter(User.role != 'client').order_by(User.created_at.desc()).all()
    return render_template('dashboard/users.html', staff=staff)

@app.route('/admin/users/add', methods=['POST'])
@login_required
@permission_required('can_manage_users')
def add_user():
    role = request.form.get('role', 'cashier')
    user = User(username=request.form.get('username'), phone_number=request.form.get('phone_number') or None,
                name=request.form.get('name'), role=role, email=request.form.get('email'),
                is_field_marshal=(role=='field_marshal'), can_dashboard=True,
                can_edit_products=bool(request.form.get('can_edit_products')),
                can_manage_inventory=bool(request.form.get('can_manage_inventory')),
                can_record_sales=bool(request.form.get('can_record_sales')),
                can_view_orders=bool(request.form.get('can_view_orders')),
                can_manage_orders=bool(request.form.get('can_manage_orders')),
                can_manage_users=bool(request.form.get('can_manage_users')),
                can_view_reports=bool(request.form.get('can_view_reports')),
                can_view_customers=bool(request.form.get('can_view_customers')),
                can_meter_readings=bool(request.form.get('can_meter_readings')))
    user.set_password(request.form.get('password'))
    db.session.add(user)
    db.session.commit()
    flash(f'Staff {user.name} created!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
@login_required
@permission_required('can_manage_users')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    user.name = request.form.get('name', user.name)
    user.role = request.form.get('role', user.role)
    user.email = request.form.get('email', user.email)
    user.username = request.form.get('username') or user.username
    user.is_field_marshal = (user.role == 'field_marshal')
    user.can_edit_products = bool(request.form.get('can_edit_products'))
    user.can_manage_inventory = bool(request.form.get('can_manage_inventory'))
    user.can_record_sales = bool(request.form.get('can_record_sales'))
    user.can_view_orders = bool(request.form.get('can_view_orders'))
    user.can_manage_orders = bool(request.form.get('can_manage_orders'))
    user.can_manage_users = bool(request.form.get('can_manage_users'))
    user.can_view_reports = bool(request.form.get('can_view_reports'))
    user.can_view_customers = bool(request.form.get('can_view_customers'))
    user.can_meter_readings = bool(request.form.get('can_meter_readings'))
    db.session.commit()
    flash('Staff updated!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/users/delete/<int:user_id>')
@login_required
@permission_required('can_manage_users')
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Cannot delete yourself.', 'danger')
        return redirect(url_for('manage_users'))
    db.session.delete(User.query.get_or_404(user_id))
    db.session.commit()
    flash('Staff deleted!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/prices')
@login_required
@permission_required('can_edit_products')
def manage_prices():
    pure_retail = Product.query.filter_by(category='retail', water_type='pure').all()
    salt_retail = Product.query.filter_by(category='retail', water_type='salt').all()
    pure_wholesale = Product.query.filter_by(category='wholesale', water_type='pure').all()
    salt_wholesale = Product.query.filter_by(category='wholesale', water_type='salt').all()
    return render_template('dashboard/prices.html', pure_retail=pure_retail, salt_retail=salt_retail,
                           pure_wholesale=pure_wholesale, salt_wholesale=salt_wholesale)

@app.route('/admin/products/add', methods=['POST'])
@login_required
@permission_required('can_edit_products')
def add_product():
    category = request.form.get('category')
    water_type = request.form.get('water_type', 'pure')
    product = Product(name=request.form.get('name'), category=category, water_type=water_type,
                      price=float(request.form.get('price', 0)),
                      wholesale_min_qty=int(request.form.get('wholesale_min_qty', 0)) if category=='wholesale' else 0)
    db.session.add(product)
    db.session.flush()
    if 'image' in request.files and request.files['image'].filename:
        img = request.files['image']
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], f"product_{product.id}_{img.filename}"))
        product.image = f"product_{product.id}_{img.filename}"
    db.session.commit()
    flash('Product added!', 'success')
    return redirect(url_for('manage_prices'))

@app.route('/admin/prices/update', methods=['POST'])
@login_required
@permission_required('can_edit_products')
def update_price():
    product = Product.query.get_or_404(request.form.get('product_id'))
    new_price = float(request.form.get('price', 0))
    new_stock = int(request.form.get('stock_quantity', -1))

    if product.price != new_price:
        db.session.add(PriceHistory(product_id=product.id, old_price=product.price or 0, new_price=new_price, changed_by=current_user.id))

    product.name = request.form.get('name', product.name)
    product.category = request.form.get('category', product.category)
    product.water_type = request.form.get('water_type', product.water_type)
    product.price = new_price if new_price > 0 else product.price

    if product.category == 'wholesale':
        product.wholesale_min_qty = int(request.form.get('wholesale_min_qty', product.wholesale_min_qty))

    if new_stock >= 0:
        old_stock = product.stock_quantity
        product.stock_quantity = new_stock
        if new_stock > old_stock:
            db.session.add(Inventory(product_id=product.id, stock_in=new_stock - old_stock, current_stock=new_stock,
                           recorded_by=current_user.id, notes='Stock adjusted (increase)'))
        elif new_stock < old_stock:
            db.session.add(Inventory(product_id=product.id, stock_out=old_stock - new_stock, current_stock=new_stock,
                           recorded_by=current_user.id, notes='Stock adjusted (decrease)'))

    if 'image' in request.files and request.files['image'].filename:
        img = request.files['image']
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], f"product_{product.id}_{img.filename}"))
        product.image = f"product_{product.id}_{img.filename}"

    db.session.commit()
    flash('Product updated!', 'success')
    return redirect(url_for('manage_prices'))

@app.route('/admin/inventory')
@login_required
@permission_required('can_manage_inventory')
def inventory():
    products = Product.query.all()
    records = Inventory.query.order_by(Inventory.date_recorded.desc()).limit(50).all()
    return render_template('dashboard/inventory.html', products=products, inventory_records=records)

@app.route('/admin/inventory/add-stock', methods=['POST'])
@login_required
@permission_required('can_manage_inventory')
def add_stock():
    product = Product.query.get_or_404(request.form.get('product_id'))
    qty = int(request.form.get('quantity'))
    product.stock_quantity += qty
    db.session.add(Inventory(product_id=product.id, stock_in=qty, current_stock=product.stock_quantity,
                   recorded_by=current_user.id, notes=request.form.get('notes', '')))
    db.session.commit()
    flash(f'Added {qty} units!', 'success')
    return redirect(url_for('inventory'))

@app.route('/admin/inventory/edit/<int:record_id>', methods=['POST'])
@login_required
@permission_required('can_manage_inventory')
def edit_inventory(record_id):
    r = Inventory.query.get_or_404(record_id)
    p = Product.query.get(r.product_id)
    oi, oo = r.stock_in, r.stock_out
    ni, no = int(request.form.get('stock_in',0)), int(request.form.get('stock_out',0))
    p.stock_quantity = p.stock_quantity - oi + oo + ni - no
    r.stock_in, r.stock_out, r.current_stock = ni, no, p.stock_quantity
    r.notes = request.form.get('notes', r.notes)
    db.session.commit()
    flash('Updated!', 'success')
    return redirect(url_for('inventory'))

@app.route('/admin/expenses')
@login_required
@permission_required('can_view_reports')
def manage_expenses():
    expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0
    return render_template('dashboard/expenses.html', expenses=expenses, total_expenses=total_expenses)

@app.route('/admin/expenses/add', methods=['POST'])
@login_required
@permission_required('can_view_reports')
def add_expense():
    db.session.add(Expense(category=request.form.get('category'),
                          amount=float(request.form.get('amount')),
                          description=request.form.get('description'),
                          recorded_by=current_user.id))
    db.session.commit()
    flash('Expense recorded!', 'success')
    return redirect(url_for('manage_expenses'))

@app.route('/admin/expenses/delete/<int:expense_id>')
@login_required
@permission_required('can_view_reports')
def delete_expense(expense_id):
    Expense.query.get_or_404(expense_id)
    db.session.delete(Expense.query.get(expense_id))
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('manage_expenses'))

@app.route('/admin/meter-readings')
@login_required
@permission_required('can_meter_readings')
def meter_readings():
    water_type = request.args.get('type', 'pure')
    readings = MeterReading.query.filter_by(water_type=water_type).order_by(MeterReading.reading_date.desc()).all()
    return render_template('dashboard/meter_reading.html', readings=readings, water_type=water_type)

@app.route('/admin/meter-readings/add', methods=['POST'])
@login_required
@permission_required('can_meter_readings')
def add_meter_reading():
    db.session.add(MeterReading(meter_number=request.form.get('meter_number'),
                                water_type=request.form.get('water_type', 'pure'),
                                reading_value=float(request.form.get('reading_value')),
                                liters_produced=float(request.form.get('liters_produced')),
                                recorded_by=current_user.id, notes=request.form.get('notes', '')))
    db.session.commit()
    flash('Reading recorded!', 'success')
    return redirect(url_for('meter_readings', type=request.form.get('water_type', 'pure')))

@app.route('/admin/orders')
@login_required
@permission_required('can_view_orders')
def manage_orders():
    if current_user.is_field_marshal:
        orders = Order.query.filter_by(field_marshal_id=current_user.id).order_by(Order.order_date.desc()).all()
    else:
        orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('dashboard/orders.html', orders=orders)

@app.route('/admin/orders/update/<int:order_id>', methods=['POST'])
@login_required
@permission_required('can_manage_orders')
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status')
    if order.status == 'delivered': order.payment_status = 'paid'
    db.session.commit()
    flash('Order updated!', 'success')
    return redirect(url_for('manage_orders'))

@app.route('/admin/field-order')
@login_required
def field_order():
    if not current_user.is_field_marshal and current_user.role != 'admin':
        flash('Only Field Marshals.', 'danger')
        return redirect(url_for('admin_dashboard'))
    products = Product.query.filter(Product.stock_quantity > 0).all()
    clients = User.query.filter_by(role='client').order_by(User.name).all()
    my_orders = Order.query.filter_by(field_marshal_id=current_user.id).order_by(Order.order_date.desc()).limit(20).all()
    return render_template('dashboard/field_order.html', products=products, clients=clients, my_orders=my_orders)

@app.route('/admin/field-order/place', methods=['POST'])
@login_required
def place_field_order():
    if not current_user.is_field_marshal and current_user.role != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('admin_dashboard'))
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity',1))
    client_id = request.form.get('client_id')
    mpesa_code = request.form.get('mpesa_code','')
    delivery_address = request.form.get('delivery_address','')
    product = Product.query.get_or_404(product_id)
    if product.stock_quantity < quantity:
        flash('Insufficient stock!', 'danger')
        return redirect(url_for('field_order'))
    total = product.price * quantity
    order = Order(user_id=client_id, field_marshal_id=current_user.id, total_amount=total,
                  mpesa_code=mpesa_code, payment_status='paid' if mpesa_code else 'pending',
                  delivery_address=delivery_address, order_type=product.category, source='field_marshal')
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=quantity, unit_price=product.price))
    product.stock_quantity -= quantity
    db.session.add(Inventory(product_id=product.id, stock_out=quantity, current_stock=product.stock_quantity,
                   recorded_by=current_user.id, notes=f'Field order #{order.id}'))
    db.session.commit()
    flash(f'Order placed! KES {total:.2f}', 'success')
    return redirect(url_for('field_order'))

@app.route('/admin/reports')
@login_required
@permission_required('can_view_reports')
def reports():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    online_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.order_date.between(start_dt, end_dt), Order.payment_status=='paid').scalar() or 0
    total_walkins = db.session.query(func.sum(WalkInSale.total_amount)).filter(WalkInSale.sale_date.between(start_dt, end_dt)).scalar() or 0
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(Expense.expense_date.between(start_dt, end_dt)).scalar() or 0
    pure_produced = db.session.query(func.sum(MeterReading.liters_produced)).filter(MeterReading.water_type=='pure', MeterReading.reading_date.between(start_dt, end_dt)).scalar() or 0
    salt_produced = db.session.query(func.sum(MeterReading.liters_produced)).filter(MeterReading.water_type=='salt', MeterReading.reading_date.between(start_dt, end_dt)).scalar() or 0
    total_revenue = online_sales + total_walkins
    profit = total_revenue - total_expenses
    total_orders = Order.query.filter(Order.order_date.between(start_dt, end_dt)).count()
    fm_stats = []
    for fm in User.query.filter_by(is_field_marshal=True).all():
        cnt = Order.query.filter_by(field_marshal_id=fm.id).filter(Order.order_date.between(start_dt, end_dt)).count()
        rev = db.session.query(func.sum(Order.total_amount)).filter_by(field_marshal_id=fm.id).filter(Order.order_date.between(start_dt, end_dt), Order.payment_status=='paid').scalar() or 0
        fm_stats.append({'name':fm.name,'orders':cnt,'revenue':rev})
    return render_template('dashboard/reports.html', start_date=start_date, end_date=end_date,
                         online_sales=online_sales, total_walkins=total_walkins,
                         total_revenue=total_revenue, total_expenses=total_expenses,
                         profit=profit, total_orders=total_orders, fm_stats=fm_stats,
                         pure_produced=pure_produced, salt_produced=salt_produced)

@app.route('/admin/reports/pdf')
@login_required
@permission_required('can_view_reports')
def reports_pdf():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    online_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.order_date.between(start_dt, end_dt), Order.payment_status=='paid').scalar() or 0
    total_walkins = db.session.query(func.sum(WalkInSale.total_amount)).filter(WalkInSale.sale_date.between(start_dt, end_dt)).scalar() or 0
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(Expense.expense_date.between(start_dt, end_dt)).scalar() or 0
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30)
    styles = getSampleStyleSheet()
    elements = [Paragraph("WEMA SPRINGS - REPORT", styles['Title']), Paragraph(f"{start_date} to {end_date}", styles['Normal']), Spacer(1,20)]
    sd = [['SUMMARY',''],['Online Sales',f'KES {online_sales:,.2f}'],['Walk-in',f'KES {total_walkins:,.2f}'],['Expenses',f'KES {total_expenses:,.2f}'],['Profit',f'KES {online_sales+total_walkins-total_expenses:,.2f}']]
    st = Table(sd, colWidths=[200,200])
    st.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1e40af')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('SPAN',(0,0),(-1,0)),('GRID',(0,0),(-1,-1),1,colors.black)]))
    elements.append(st)
    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Wema_Report_{start_date}.pdf'
    return response

with app.app_context():
    db.drop_all()
    db.create_all()
    admin = User(username='admin', name='Administrator', role='admin',
                 can_dashboard=True, can_edit_products=True, can_manage_inventory=True,
                 can_record_sales=True, can_view_orders=True, can_manage_orders=True,
                 can_manage_users=True, can_view_reports=True, can_view_customers=True, can_meter_readings=True)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin: admin / admin123")
    print("✅ System ready.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
""")
print("✅ app.py")

# ---- TEMPLATES (all modals have tabindex="-1") ----
templates = {
    'base.html': '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>{% block title %}Wema Springs{% endblock %}</title>\n<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">\n<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">\n<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/style.css\') }}">\n</head>\n<body>\n<nav class="navbar navbar-expand-lg navbar-dark"><div class="container">\n<a class="navbar-brand" href="{{ url_for(\'index\') }}" style="color:#fff!important;"><i class="bi bi-droplet-fill"></i> WEMA SPRINGS</a>\n<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button>\n<div class="collapse navbar-collapse" id="navbarNav"><ul class="navbar-nav ms-auto">\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'index\') }}">Home</a></li>\n<li class="nav-item dropdown"><a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Retail</a><ul class="dropdown-menu"><li><a class="dropdown-item" href="{{ url_for(\'shop_retail\', type=\'pure\') }}">Pure Water</a></li><li><a class="dropdown-item" href="{{ url_for(\'shop_retail\', type=\'salt\') }}">Salt Water</a></li></ul></li>\n<li class="nav-item dropdown"><a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Wholesale</a><ul class="dropdown-menu"><li><a class="dropdown-item" href="{{ url_for(\'shop_wholesale\', type=\'pure\') }}">Pure Water</a></li><li><a class="dropdown-item" href="{{ url_for(\'shop_wholesale\', type=\'salt\') }}">Salt Water</a></li></ul></li>\n{% if current_user.is_authenticated %}\n<li class="nav-item dropdown"><a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">{{ current_user.name }}</a><ul class="dropdown-menu"><li><a class="dropdown-item" href="{{ url_for(\'change_password\') }}"><i class="bi bi-key"></i> Change Password</a></li><li><a class="dropdown-item" href="{{ url_for(\'logout\') }}">Logout</a></li></ul></li>\n{% if current_user.role == \'client\' %}<li class="nav-item"><a class="nav-link" href="{{ url_for(\'client_dashboard\') }}">Dashboard</a></li>\n{% else %}<li class="nav-item"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a></li>\n{% endif %}\n{% else %}\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'login\') }}">Login</a></li>\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'register\') }}">Register</a></li>\n{% endif %}\n</ul></div></div></nav>\n{% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}<div class="container mt-3">{% for c,m in messages %}<div class="alert alert-{{ c }} alert-dismissible fade show">{{ m }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>{% endfor %}</div>{% endif %}{% endwith %}\n<main>{% block content %}{% endblock %}</main>\n<footer class="footer"><div class="container"><div class="row"><div class="col-md-6"><h5>Wema Springs</h5></div></div></div></footer>\n<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>\n</body>\n</html>',
    'index.html': '{% extends "base.html" %}\n{% block title %}Home{% endblock %}\n{% block content %}\n<section class="hero-section"><div class="container"><div class="row"><div class="col-lg-6"><h1 class="hero-title">Pure Water, Pure Life</h1><p class="text-white">Get fresh spring water and salt water delivered.</p><a href="{{ url_for(\'shop_retail\') }}" class="btn btn-gold btn-lg">Shop Now</a></div></div></div></section>\n{% endblock %}',
    'login.html': '{% extends "base.html" %}\n{% block title %}Login{% endblock %}\n{% block content %}\n<div class="container py-5"><div class="row justify-content-center"><div class="col-md-5"><div class="card"><div class="card-header"><h3>Login</h3></div><div class="card-body"><form method="POST"><div class="mb-3"><label>Phone or Username</label><input type="text" name="login_id" class="form-control" required></div><div class="mb-3"><label>Password</label><input type="password" name="password" class="form-control" required></div><button type="submit" class="btn btn-primary w-100">Login</button></form><div class="mt-3"><a href="{{ url_for(\'register\') }}">Register</a></div></div></div></div></div></div>\n{% endblock %}',
    'register.html': '{% extends "base.html" %}\n{% block title %}Register{% endblock %}\n{% block content %}\n<div class="container py-5"><div class="row justify-content-center"><div class="col-md-6"><div class="card"><div class="card-header"><h3>Create Account</h3></div><div class="card-body"><form method="POST"><div class="mb-3"><label>Full Name *</label><input type="text" name="name" class="form-control" required></div><div class="mb-3"><label>Phone *</label><input type="text" name="phone_number" class="form-control" required></div><div class="mb-3"><label>Email</label><input type="email" name="email" class="form-control"></div><div class="mb-3"><label>Area *</label><input type="text" name="area_of_residence" class="form-control" required></div><div class="mb-3"><label>Customer Type</label><select name="customer_type" class="form-control"><option value="pure">Pure</option><option value="salt">Salt</option><option value="both">Both</option></select></div><div class="mb-3"><label>Password *</label><input type="password" name="password" class="form-control" required></div><div class="mb-3"><label>Confirm *</label><input type="password" name="confirm_password" class="form-control" required></div><button type="submit" class="btn btn-primary w-100">Register</button></form></div></div></div></div></div>\n{% endblock %}',
    'change_password.html': '{% extends "base.html" %}\n{% block title %}Change Password{% endblock %}\n{% block content %}\n<div class="container py-5"><div class="row justify-content-center"><div class="col-md-5"><div class="card"><div class="card-header"><h3>Change Password</h3></div><div class="card-body"><form method="POST"><div class="mb-3"><label>Current</label><input type="password" name="old_password" class="form-control" required></div><div class="mb-3"><label>New</label><input type="password" name="new_password" class="form-control" required></div><div class="mb-3"><label>Confirm</label><input type="password" name="confirm_password" class="form-control" required></div><button type="submit" class="btn btn-primary w-100">Update</button></form></div></div></div></div></div>\n{% endblock %}',
    'shop_retail.html': '{% extends "base.html" %}\n{% block title %}Retail - {{ water_type|title }} Water{% endblock %}\n{% block content %}\n<div class="container py-5"><h2>Retail Shop - {{ water_type|title }} Water</h2><div class="row">{% for p in products %}<div class="col-md-4 mb-4"><div class="card"><div class="card-body text-center"><h4>{{ p.name }}</h4><h3>KES {{ "%.2f"|format(p.price) }}</h3>{% if current_user.is_authenticated and current_user.role==\'client\' and p.stock_quantity>0 %}<button class="btn btn-gold" data-bs-toggle="modal" data-bs-target="#om{{ p.id }}">Order</button>{% elif not current_user.is_authenticated %}<a href="{{ url_for(\'login\') }}" class="btn btn-primary">Login</a>{% endif %}</div></div></div>{% endfor %}</div></div>\n{% for p in products %}{% if current_user.is_authenticated and p.stock_quantity>0 %}<div class="modal fade" id="om{{ p.id }}" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5>Order {{ p.name }}</h5></div><form action="{{ url_for(\'place_order\') }}" method="POST"><div class="modal-body"><input type="hidden" name="product_id" value="{{ p.id }}"><div class="mb-3"><label>Quantity</label><input type="number" name="quantity" class="form-control" value="1" min="1" max="{{ p.stock_quantity }}" required></div><div class="mb-3"><label>Delivery Address</label><input type="text" name="delivery_address" class="form-control" value="{{ current_user.area_of_residence }}"></div><div class="mb-3"><label>M-Pesa Code</label><input type="text" name="mpesa_code" class="form-control"></div></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Confirm</button></div></form></div></div></div>{% endif %}{% endfor %}\n{% endblock %}',
    'shop_wholesale.html': '{% extends "base.html" %}\n{% block title %}Wholesale - {{ water_type|title }} Water{% endblock %}\n{% block content %}\n<div class="container py-5"><h2>Wholesale - {{ water_type|title }} Water</h2><div class="row">{% for p in products %}<div class="col-md-4 mb-4"><div class="card"><div class="card-body text-center"><h4>{{ p.name }}</h4><h3>KES {{ "%.2f"|format(p.price) }}</h3><p>Min: {{ p.wholesale_min_qty }}</p>{% if current_user.is_authenticated and current_user.role==\'client\' and p.stock_quantity>=p.wholesale_min_qty %}<button class="btn btn-gold" data-bs-toggle="modal" data-bs-target="#om{{ p.id }}">Order</button>{% elif not current_user.is_authenticated %}<a href="{{ url_for(\'login\') }}" class="btn btn-primary">Login</a>{% endif %}</div></div></div>{% endfor %}</div></div>\n{% for p in products %}{% if current_user.is_authenticated and p.stock_quantity>=p.wholesale_min_qty %}<div class="modal fade" id="om{{ p.id }}" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5>Order {{ p.name }}</h5></div><form action="{{ url_for(\'place_order\') }}" method="POST"><div class="modal-body"><input type="hidden" name="product_id" value="{{ p.id }}"><div class="mb-3"><label>Quantity (Min {{ p.wholesale_min_qty }})</label><input type="number" name="quantity" class="form-control" value="{{ p.wholesale_min_qty }}" min="{{ p.wholesale_min_qty }}" max="{{ p.stock_quantity }}" required></div><div class="mb-3"><label>Delivery Address</label><input type="text" name="delivery_address" class="form-control" value="{{ current_user.area_of_residence }}"></div><div class="mb-3"><label>M-Pesa Code</label><input type="text" name="mpesa_code" class="form-control"></div></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Confirm</button></div></form></div></div></div>{% endif %}{% endfor %}\n{% endblock %}',
    'dashboard/client_dashboard.html': '{% extends "base.html" %}\n{% block title %}My Dashboard{% endblock %}\n{% block content %}\n<div class="container py-4"><h2>Welcome, {{ current_user.name }}!</h2><div class="card mt-4"><div class="card-header"><h5>My Orders</h5></div><div class="card-body">{% if orders %}<table class="table"><thead><tr><th>ID</th><th>Date</th><th>Total</th><th>Status</th><th>Track</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.order_date.strftime(\'%Y-%m-%d\') }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td>{{ o.status }}</td><td><a href="{{ url_for(\'track_order\', order_id=o.id) }}" class="btn btn-sm btn-info">Track</a></td></tr>{% endfor %}</tbody></table>{% else %}<p>No orders. <a href="{{ url_for(\'shop_retail\') }}">Shop</a></p>{% endif %}</div></div></div>\n{% endblock %}',
    'dashboard/track_order.html': '{% extends "base.html" %}\n{% block title %}Track Order{% endblock %}\n{% block content %}\n<div class="container py-4"><h2>Order #{{ order.id }}</h2><p>Status: {{ order.status }} | Payment: {{ order.payment_status }}</p><a href="{{ url_for(\'client_dashboard\') }}" class="btn btn-primary">Back</a></div>\n{% endblock %}',
    'dashboard/admin_dashboard.html': '{% extends "base.html" %}\n{% block title %}Dashboard{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav class="nav flex-column"><a class="nav-link active" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a>\n{% if current_user.role==\'admin\' or current_user.can_record_sales %}<a class="nav-link" href="{{ url_for(\'walkin_sale\') }}">Walk-in Sale</a>{% endif %}\n{% if current_user.is_field_marshal or current_user.role==\'admin\' %}<a class="nav-link" href="{{ url_for(\'field_order\') }}">Field Orders</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_orders %}<a class="nav-link" href="{{ url_for(\'manage_orders\') }}">Orders</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_customers %}<a class="nav-link" href="{{ url_for(\'manage_customers\') }}">Customers</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_manage_inventory %}<a class="nav-link" href="{{ url_for(\'inventory\') }}">Inventory</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_edit_products %}<a class="nav-link" href="{{ url_for(\'manage_prices\') }}">Products</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_manage_users %}<a class="nav-link" href="{{ url_for(\'manage_users\') }}">Staff</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_reports %}<a class="nav-link" href="{{ url_for(\'manage_expenses\') }}">Expenses</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_meter_readings %}<a class="nav-link" href="{{ url_for(\'meter_readings\') }}">Meter</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_reports %}<a class="nav-link" href="{{ url_for(\'reports\') }}">Reports</a>{% endif %}\n</nav></div><div class="col-md-10 py-4"><h2>Dashboard</h2><div class="row"><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Orders</h6><div class="stats-number">{{ total_orders }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Revenue</h6><div class="stats-number">KES {{ "%.0f"|format(total_revenue) }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Customers</h6><div class="stats-number">{{ total_customers }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Products</h6><div class="stats-number">{{ total_products }}</div></div></div></div></div></div></div></div>\n{% endblock %}',
    'dashboard/customers.html': '{% extends "base.html" %}\n{% block title %}Customers{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_customers\') }}">Customers</a></nav></div><div class="col-md-10 py-4"><h2>Customers</h2>\n<div class="mb-3"><a href="?type=all" class="btn btn-sm btn-outline-primary">All</a> <a href="?type=pure" class="btn btn-sm btn-outline-primary">Pure</a> <a href="?type=salt" class="btn btn-sm btn-outline-primary">Salt</a> <a href="?type=both" class="btn btn-sm btn-outline-primary">Both</a></div>\n{% if current_user.is_field_marshal or current_user.role==\'admin\' %}<button class="btn btn-gold mb-3" data-bs-toggle="modal" data-bs-target="#addClientModal">Add Client</button>{% endif %}\n<table class="table"><thead><tr><th>Name</th><th>Phone</th><th>Type</th><th>Area</th><th>Actions</th></tr></thead><tbody>{% for c in customers %}<tr><td>{{ c.name }}</td><td>{{ c.phone_number }}</td><td>{{ c.customer_type }}</td><td>{{ c.area_of_residence or \'-\' }}</td><td><a href="{{ url_for(\'view_customer\', user_id=c.id) }}" class="btn btn-sm btn-primary">View</a>{% if current_user.is_field_marshal or current_user.role==\'admin\' %}<a href="{{ url_for(\'delete_client\', user_id=c.id) }}" class="btn btn-sm btn-danger">Del</a>{% endif %}</td></tr>{% endfor %}</tbody></table></div></div></div>\n{% if current_user.is_field_marshal or current_user.role==\'admin\' %}<div class="modal fade" id="addClientModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5>Add Client</h5></div><form action="{{ url_for(\'add_client\') }}" method="POST"><div class="modal-body"><div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" required></div><div class="mb-3"><label>Phone</label><input type="text" name="phone_number" class="form-control" required></div><div class="mb-3"><label>Area</label><input type="text" name="area" class="form-control"></div><div class="mb-3"><label>Type</label><select name="customer_type" class="form-control"><option value="pure">Pure</option><option value="salt">Salt</option><option value="both">Both</option></select></div><div class="mb-3"><label>Password</label><input type="text" name="password" class="form-control" value="1234"></div></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Add Client</button></div></form></div></div></div>{% endif %}\n{% endblock %}',
    'dashboard/customer_detail.html': '{% extends "base.html" %}\n{% block title %}Customer{% endblock %}\n{% block content %}\n<div class="container py-4"><h2>{{ customer.name }}</h2><p>Type: {{ customer.customer_type }} | Phone: {{ customer.phone_number }}</p><div class="card"><div class="card-header"><h5>Orders</h5></div><table class="table"><thead><tr><th>ID</th><th>Date</th><th>Total</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.order_date.strftime(\'%Y-%m-%d\') }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td></tr>{% endfor %}</tbody></table></div></div>\n{% endblock %}',
    'dashboard/expenses.html': '{% extends "base.html" %}\n{% block title %}Expenses{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_expenses\') }}">Expenses</a></nav></div><div class="col-md-10 py-4"><h2>Expenses <small>Total: KES {{ "%.2f"|format(total_expenses) }}</small></h2>\n<button class="btn btn-gold mb-3" data-bs-toggle="modal" data-bs-target="#addExpenseModal">Add Expense</button>\n<table class="table"><thead><tr><th>Date</th><th>Category</th><th>Amount</th><th>Description</th><th>Action</th></tr></thead><tbody>\n{% for e in expenses %}<tr><td>{{ e.expense_date.strftime(\'%Y-%m-%d\') }}</td><td>{{ e.category }}</td><td>KES {{ "%.2f"|format(e.amount) }}</td><td>{{ e.description }}</td><td><a href="{{ url_for(\'delete_expense\', expense_id=e.id) }}" class="btn btn-sm btn-danger" onclick="return confirm(\'Delete?\')">Del</a></td></tr>{% endfor %}\n</tbody></table></div></div></div>\n\n<div class="modal fade" id="addExpenseModal" tabindex="-1" aria-hidden="true">\n  <div class="modal-dialog">\n    <div class="modal-content">\n      <div class="modal-header" style="background:#1e40af;color:white;">\n        <h5>Add Expense</h5>\n        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>\n      </div>\n      <form action="{{ url_for(\'add_expense\') }}" method="POST">\n        <div class="modal-body">\n          <div class="mb-3"><label>Category</label><select name="category" class="form-control"><option>Fuel</option><option>Bottles</option><option>Salaries</option><option>Maintenance</option><option>Other</option></select></div>\n          <div class="mb-3"><label>Amount (KES)</label><input type="number" step="0.01" name="amount" class="form-control" required></div>\n          <div class="mb-3"><label>Description</label><input type="text" name="description" class="form-control"></div>\n        </div>\n        <div class="modal-footer">\n          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>\n          <button type="submit" class="btn btn-gold">Save Expense</button>\n        </div>\n      </form>\n    </div>\n  </div>\n</div>\n{% endblock %}',
    'dashboard/field_order.html': '{% extends "base.html" %}\n{% block title %}Field Orders{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'field_order\') }}">Field Orders</a></nav></div><div class="col-md-10 py-4"><div class="row"><div class="col-md-5"><div class="card"><div class="card-header" style="background:#8b5cf6;"><h5>Place Order</h5></div><form action="{{ url_for(\'place_field_order\') }}" method="POST"><div class="mb-3"><label>Client</label><select name="client_id" class="form-control" required>{% for c in clients %}<option value="{{ c.id }}">{{ c.name }} ({{ c.customer_type }})</option>{% endfor %}</select></div><div class="mb-3"><label>Product</label><select name="product_id" class="form-control" required>{% for p in products %}<option value="{{ p.id }}">{{ p.name }} ({{ p.water_type }}) KES {{ "%.2f"|format(p.price) }}</option>{% endfor %}</select></div><div class="mb-3"><label>Qty</label><input type="number" name="quantity" class="form-control" value="1" required></div><div class="mb-3"><label>Address</label><input type="text" name="delivery_address" class="form-control"></div><div class="mb-3"><label>Payment</label><select name="payment_method" class="form-control"><option>cash</option><option>mpesa</option></select></div><div class="mb-3"><label>M-Pesa Code</label><input type="text" name="mpesa_code" class="form-control"></div><button type="submit" class="btn text-white w-100" style="background:#8b5cf6;">Place Order</button></form></div></div></div><div class="col-md-7"><div class="card"><div class="card-header"><h5>My Orders</h5></div><table class="table table-sm"><thead><tr><th>ID</th><th>Client</th><th>Total</th></tr></thead><tbody>{% for o in my_orders %}<tr><td>#{{ o.id }}</td><td>{{ o.customer.name }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td></tr>{% endfor %}</tbody></table></div></div></div></div></div>\n{% endblock %}',
    'dashboard/walkin_sale.html': '{% extends "base.html" %}\n{% block title %}Walk-in Sale{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'walkin_sale\') }}">Walk-in</a></nav></div><div class="col-md-10 py-4"><div class="row"><div class="col-md-5"><div class="card"><div class="card-header" style="background:#059669;"><h5>Record Sale</h5></div><form action="{{ url_for(\'record_walkin_sale\') }}" method="POST"><select name="product_id" class="form-control mb-2">{% for p in products %}<option value="{{ p.id }}">{{ p.name }} ({{ p.water_type }}) KES {{ "%.2f"|format(p.price) }}</option>{% endfor %}</select><input type="number" name="quantity" value="1" class="form-control mb-2"><select name="payment_method" class="form-control mb-2"><option>cash</option><option>mpesa</option></select><input type="text" name="mpesa_code" class="form-control mb-2" placeholder="M-Pesa"><input type="text" name="customer_name" class="form-control mb-2" value="Walk-in"><button type="submit" class="btn btn-success w-100">Record</button></form></div></div></div><div class="col-md-7"><div class="card"><div class="card-header"><h5>Today</h5></div><table class="table table-sm"><thead><tr><th>Time</th><th>Product</th><th>Total</th></tr></thead><tbody>{% for s in today_sales %}<tr><td>{{ s.sale_date.strftime(\'%H:%M\') }}</td><td>{{ s.product.name }}</td><td>KES {{ "%.2f"|format(s.total_amount) }}</td></tr>{% endfor %}</tbody></table></div></div></div></div></div>\n{% endblock %}',
    'dashboard/orders.html': '{% extends "base.html" %}\n{% block title %}Orders{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_orders\') }}">Orders</a></nav></div><div class="col-md-10 py-4"><h2>Orders</h2><table class="table"><thead><tr><th>ID</th><th>Customer</th><th>Total</th><th>Status</th><th>Action</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.customer.name }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td>{{ o.status }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#upd{{ o.id }}">Update</button></td></tr>{% endfor %}</tbody></table></div></div></div>\n{% for o in orders %}<div class="modal fade" id="upd{{ o.id }}" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h5>Update #{{ o.id }}</h5></div><form action="{{ url_for(\'update_order\', order_id=o.id) }}" method="POST"><div class="modal-body"><select name="status" class="form-control"><option>pending</option><option>confirmed</option><option>delivered</option><option>cancelled</option></select></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Update</button></div></form></div></div></div>{% endfor %}\n{% endblock %}',
    'dashboard/prices.html': '{% extends "base.html" %}\n{% block title %}Products{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_prices\') }}">Products</a></nav></div><div class="col-md-10 py-4"><div class="d-flex justify-content-between"><h2>Products</h2><button class="btn btn-gold" data-bs-toggle="modal" data-bs-target="#addProductModal">Add</button></div>\n<div class="card mb-4"><div class="card-header">Pure Retail</div><table class="table"><tr><th>Name</th><th>Price</th><th>Stock</th><th></th></tr>{% for p in pure_retail %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.stock_quantity }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#edit{{ p.id }}">Edit</button></td></tr>{% endfor %}</table></div>\n<div class="card mb-4"><div class="card-header">Salt Retail</div><table class="table"><tr><th>Name</th><th>Price</th><th>Stock</th><th></th></tr>{% for p in salt_retail %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.stock_quantity }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#edit{{ p.id }}">Edit</button></td></tr>{% endfor %}</table></div>\n<div class="card mb-4"><div class="card-header">Pure Wholesale</div><table class="table"><tr><th>Name</th><th>Price</th><th>Min Qty</th><th>Stock</th><th></th></tr>{% for p in pure_wholesale %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.wholesale_min_qty }}</td><td>{{ p.stock_quantity }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#edit{{ p.id }}">Edit</button></td></tr>{% endfor %}</table></div>\n<div class="card"><div class="card-header">Salt Wholesale</div><table class="table"><tr><th>Name</th><th>Price</th><th>Min Qty</th><th>Stock</th><th></th></tr>{% for p in salt_wholesale %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.wholesale_min_qty }}</td><td>{{ p.stock_quantity }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#edit{{ p.id }}">Edit</button></td></tr>{% endfor %}</table></div></div></div></div>\n<div class="modal fade" id="addProductModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h5>Add Product</h5></div><form action="{{ url_for(\'add_product\') }}" method="POST" enctype="multipart/form-data"><div class="modal-body"><input name="name" placeholder="Name" class="form-control mb-2" required><select name="category" class="form-control mb-2"><option value="retail">Retail</option><option value="wholesale">Wholesale</option></select><select name="water_type" class="form-control mb-2"><option value="pure">Pure</option><option value="salt">Salt</option></select><input name="price" type="number" step="0.01" class="form-control mb-2" required><input name="wholesale_min_qty" type="number" value="0" class="form-control mb-2"><input type="file" name="image" class="form-control"></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Add</button></div></form></div></div></div>\n{% for p in pure_retail + salt_retail + pure_wholesale + salt_wholesale %}\n<div class="modal fade" id="edit{{ p.id }}" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5>Edit {{ p.name }}</h5></div><form action="{{ url_for(\'update_price\') }}" method="POST" enctype="multipart/form-data"><input type="hidden" name="product_id" value="{{ p.id }}"><div class="modal-body"><div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" value="{{ p.name }}"></div><div class="mb-3"><label>Category</label><select name="category" class="form-control"><option value="retail" {% if p.category==\'retail\' %}selected{% endif %}>Retail</option><option value="wholesale" {% if p.category==\'wholesale\' %}selected{% endif %}>Wholesale</option></select></div><div class="mb-3"><label>Water Type</label><select name="water_type" class="form-control"><option value="pure" {% if p.water_type==\'pure\' %}selected{% endif %}>Pure</option><option value="salt" {% if p.water_type==\'salt\' %}selected{% endif %}>Salt</option></select></div><div class="mb-3"><label>Price (KES)</label><input type="number" step="0.01" name="price" class="form-control" value="{{ "%.2f"|format(p.price) }}"></div><div class="mb-3"><label>Stock Quantity</label><input type="number" name="stock_quantity" class="form-control" value="{{ p.stock_quantity }}"></div>{% if p.category==\'wholesale\' %}<div class="mb-3"><label>Min Wholesale Qty</label><input type="number" name="wholesale_min_qty" class="form-control" value="{{ p.wholesale_min_qty }}"></div>{% endif %}<div class="mb-3"><label>Image</label><input type="file" name="image" class="form-control"></div></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Update</button></div></form></div></div></div>\n{% endfor %}\n{% endblock %}',
    'dashboard/users.html': '{% extends "base.html" %}\n{% block title %}Staff{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_users\') }}">Staff</a></nav></div><div class="col-md-10 py-4"><div class="d-flex justify-content-between"><h2>Staff</h2><button class="btn btn-gold" data-bs-toggle="modal" data-bs-target="#addUserModal">Add</button></div><table class="table"><thead><tr><th>Name</th><th>Role</th><th>Actions</th></tr></thead><tbody>{% for u in staff %}<tr><td>{{ u.name }}</td><td>{{ u.role }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#editUser{{ u.id }}">Edit</button>{% if u.id!=current_user.id %}<a href="{{ url_for(\'delete_user\', user_id=u.id) }}" class="btn btn-sm btn-danger">Del</a>{% endif %}</td></tr>{% endfor %}</tbody></table></div></div></div>\n{% endblock %}',
    'dashboard/inventory.html': '{% extends "base.html" %}\n{% block title %}Inventory{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'inventory\') }}">Inventory</a></nav></div><div class="col-md-10 py-4"><div class="d-flex justify-content-between"><h2>Inventory</h2><button class="btn btn-gold" data-bs-toggle="modal" data-bs-target="#addStockModal">Add Stock</button></div><table class="table"><thead><tr><th>Product</th><th>Type</th><th>Price</th><th>Stock</th></tr></thead><tbody>{% for p in products %}<tr><td>{{ p.name }}</td><td>{{ p.water_type }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.stock_quantity }}</td></tr>{% endfor %}</tbody></table></div></div></div>\n{% endblock %}',
    'dashboard/meter_reading.html': '{% extends "base.html" %}\n{% block title %}Meter{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'meter_readings\') }}">Meter</a></nav></div><div class="col-md-10 py-4"><h2>Meter Readings</h2>\n<div class="mb-3"><a href="?type=pure" class="btn btn-sm btn-outline-primary">Pure</a> <a href="?type=salt" class="btn btn-sm btn-outline-primary">Salt</a></div>\n<button class="btn btn-gold mb-3" data-bs-toggle="modal" data-bs-target="#addReadingModal">Add</button>\n<table class="table"><thead><tr><th>Date</th><th>Meter</th><th>Type</th><th>Reading</th><th>Liters</th></tr></thead><tbody>{% for r in readings %}<tr><td>{{ r.reading_date.strftime(\'%Y-%m-%d\') }}</td><td>{{ r.meter_number }}</td><td>{{ r.water_type }}</td><td>{{ r.reading_value }}</td><td>{{ r.liters_produced }}</td></tr>{% endfor %}</tbody></table></div></div></div>\n<div class="modal fade" id="addReadingModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h5>Add Reading</h5></div><form action="{{ url_for(\'add_meter_reading\') }}" method="POST"><div class="modal-body"><input name="meter_number" class="form-control mb-2" placeholder="Meter Number" required><select name="water_type" class="form-control mb-2"><option value="pure">Pure</option><option value="salt">Salt</option></select><input name="reading_value" type="number" step="0.01" class="form-control mb-2" required><input name="liters_produced" type="number" step="0.01" class="form-control mb-2" required><textarea name="notes" class="form-control" placeholder="Notes"></textarea></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Save</button></div></form></div></div></div>\n{% endblock %}',
    'dashboard/reports.html': '{% extends "base.html" %}\n{% block title %}Reports{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar"><nav><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'reports\') }}">Reports</a></nav></div><div class="col-md-10 py-4"><h2>Reports</h2><form method="GET" class="row mb-4"><div class="col-md-4"><input type="date" name="start_date" value="{{ start_date }}" class="form-control"></div><div class="col-md-4"><input type="date" name="end_date" value="{{ end_date }}" class="form-control"></div><div class="col-md-4"><button type="submit" class="btn btn-primary w-100">Generate</button></div></form>\n<div class="row"><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Online Sales</h6><div class="stats-number">KES {{ "%.0f"|format(online_sales) }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Walk-in</h6><div class="stats-number">KES {{ "%.0f"|format(total_walkins) }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Expenses</h6><div class="stats-number">KES {{ "%.0f"|format(total_expenses) }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Profit</h6><div class="stats-number">KES {{ "%.0f"|format(profit) }}</div></div></div></div></div>\n<div class="row mt-4"><div class="col-md-6"><div class="card stats-card"><div class="card-body"><h6>Pure Water Produced</h6><div class="stats-number">{{ "%.0f"|format(pure_produced) }} L</div></div></div></div><div class="col-md-6"><div class="card stats-card"><div class="card-body"><h6>Salt Water Produced</h6><div class="stats-number">{{ "%.0f"|format(salt_produced) }} L</div></div></div></div></div>\n<a href="{{ url_for(\'reports_pdf\', start_date=start_date, end_date=end_date) }}" class="btn btn-danger mt-3">PDF</a></div></div></div>\n{% endblock %}',
}

for filename, content in templates.items():
    filepath = os.path.join("templates", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ All templates created!")

with open("static/css/style.css", "w") as f:
    f.write(""":root{--primary-blue:#1e40af;--secondary-blue:#3b82f6;--gold:#f59e0b;--light-gold:#fbbf24;--white:#ffffff}*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#f0f9ff,#e0f2fe);min-height:100vh}.navbar{background:linear-gradient(135deg,var(--primary-blue),#1e3a8a);padding:1rem 2rem}.navbar-brand{font-size:1.5rem;font-weight:700;color:#fff!important}.nav-link{color:var(--white)!important}.hero-section{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));color:#fff;padding:80px 0}.hero-title{font-size:3rem;font-weight:700;color:#fff}.card{border:none;border-radius:15px;box-shadow:0 4px 20px rgba(0,0,0,0.1);margin-bottom:20px;background:#fff}.card-header{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));color:#fff;border-radius:15px 15px 0 0!important;padding:1.5rem}.stats-card{border-left:4px solid var(--gold)}.stats-number{font-size:2rem;font-weight:700;color:var(--primary-blue)}.btn-primary{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));border:none;padding:10px 25px;border-radius:25px;color:white}.btn-gold{background:linear-gradient(135deg,var(--gold),var(--light-gold));border:none;padding:10px 25px;border-radius:25px;color:white;font-weight:700}.btn-success{background:linear-gradient(135deg,#059669,#10b981);border:none;border-radius:25px;color:white}.btn-danger{background:linear-gradient(135deg,#dc2626,#ef4444);border:none;border-radius:25px;color:white}.form-control{border-radius:25px;padding:12px 20px;border:2px solid #e5e7eb}.table{background:#fff;border-radius:10px;overflow:hidden}.table thead{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));color:#fff}.sidebar{background:linear-gradient(180deg,var(--primary-blue),#1e3a8a);min-height:100vh;padding-top:20px}.sidebar .nav-link{color:#fff;padding:15px 20px;margin:5px 0;border-radius:10px}.sidebar .nav-link:hover,.sidebar .nav-link.active{background:rgba(255,255,255,0.15);color:#fff}.footer{background:var(--primary-blue);color:#fff;padding:30px 0;margin-top:50px}@media(max-width:768px){.hero-title{font-size:2rem}.sidebar{min-height:auto}}""")
print("✅ style.css created!")

print("\n🎉 DONE! Run: pip install reportlab && python app.py")
print("Admin: admin / admin123")