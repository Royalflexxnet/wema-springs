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

# ============================================
# requirements.txt
# ============================================
with open("requirements.txt", "w") as f:
    f.write("""Flask==2.3.2
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
Werkzeug==2.3.6
reportlab==4.0.0
""")
print("✅ requirements.txt")

# ============================================
# database.py
# ============================================
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
""")
print("✅ database.py")

# ============================================
# app.py
# ============================================
with open("app.py", "w", encoding="utf-8") as f:
    f.write("""from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_user, login_required, logout_user, current_user
from database import db, login_manager, User, Product, Order, OrderItem, Inventory, MeterReading, PriceHistory, WalkInSale
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

def generate_pdf(elements, filename):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/')
def index():
    retail_products = Product.query.filter_by(category='retail').limit(4).all()
    wholesale_products = Product.query.filter_by(category='wholesale').limit(4).all()
    return render_template('index.html', retail_products=retail_products, wholesale_products=wholesale_products)

@app.route('/shop/retail')
def shop_retail():
    products = Product.query.filter_by(category='retail').all()
    return render_template('shop_retail.html', products=products)

@app.route('/shop/wholesale')
def shop_wholesale():
    products = Product.query.filter_by(category='wholesale').all()
    return render_template('shop_wholesale.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone_number', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        email = request.form.get('email', '')
        area = request.form.get('area_of_residence', '')
        if not phone or not password or not name:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(phone_number=phone).first():
            flash('Phone already registered!', 'danger')
            return redirect(url_for('login'))
        user = User(phone_number=phone, name=name, email=email, area_of_residence=area, role='client')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registered! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')
        if not login_id or not password:
            flash('Enter login details.', 'danger')
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
        return redirect(url_for('shop_retail'))
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

@app.route('/dashboard/admin')
@login_required
@staff_required
def admin_dashboard():
    if current_user.is_field_marshal:
        total_orders = Order.query.filter_by(field_marshal_id=current_user.id).count()
    else:
        total_orders = Order.query.count()
    total_walkins = db.session.query(func.sum(WalkInSale.total_amount)).scalar() or 0
    online_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.payment_status == 'paid').scalar() or 0
    total_revenue = online_sales + total_walkins
    total_customers = User.query.filter_by(role='client').count()
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.stock_quantity < 10).all()
    return render_template('dashboard/admin_dashboard.html',
                         total_orders=total_orders, total_revenue=total_revenue,
                         total_customers=total_customers, total_products=total_products, low_stock=low_stock)

@app.route('/admin/field-order')
@login_required
@staff_required
def field_order():
    if not current_user.is_field_marshal and current_user.role != 'admin':
        flash('Field Marshals only.', 'danger')
        return redirect(url_for('admin_dashboard'))
    products = Product.query.filter(Product.stock_quantity > 0).all()
    clients = User.query.filter_by(role='client').order_by(User.name).all()
    my_orders = Order.query.filter_by(field_marshal_id=current_user.id).order_by(Order.order_date.desc()).limit(20).all()
    return render_template('dashboard/field_order.html', products=products, clients=clients, my_orders=my_orders)

@app.route('/admin/field-order/place', methods=['POST'])
@login_required
@staff_required
def place_field_order():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    client_id = request.form.get('client_id')
    mpesa_code = request.form.get('mpesa_code', '')
    delivery_address = request.form.get('delivery_address', '')
    payment_method = request.form.get('payment_method', 'cash')
    product = Product.query.get_or_404(product_id)
    if product.stock_quantity < quantity:
        flash('Insufficient stock!', 'danger')
        return redirect(url_for('field_order'))
    total = product.price * quantity
    order = Order(user_id=client_id, field_marshal_id=current_user.id, total_amount=total,
                  mpesa_code=mpesa_code, payment_status='paid' if (mpesa_code or payment_method == 'mpesa') else 'pending',
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
                   mpesa_code=mpesa_code if payment_method == 'mpesa' else None,
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
    customers = User.query.filter_by(role='client').order_by(User.name).all()
    return render_template('dashboard/customers.html', customers=customers)

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
    all_staff = User.query.filter(User.role != 'client').order_by(User.created_at.desc()).all()
    all_clients = User.query.filter_by(role='client').order_by(User.name).all()
    return render_template('dashboard/users.html', staff=all_staff, clients=all_clients)

@app.route('/admin/users/add', methods=['POST'])
@login_required
@permission_required('can_manage_users')
def add_user():
    role = request.form.get('role', 'client')
    is_staff = (role != 'client')
    user = User(
        username=request.form.get('username') if is_staff else None,
        phone_number=request.form.get('phone_number') or None,
        name=request.form.get('name'),
        role=role,
        email=request.form.get('email', ''),
        area_of_residence=request.form.get('area_of_residence', ''),
        is_field_marshal=(role == 'field_marshal'),
        can_dashboard=is_staff,
        can_edit_products=bool(request.form.get('can_edit_products')) if is_staff else False,
        can_manage_inventory=bool(request.form.get('can_manage_inventory')) if is_staff else False,
        can_record_sales=bool(request.form.get('can_record_sales')) if is_staff else False,
        can_view_orders=bool(request.form.get('can_view_orders')) if is_staff else False,
        can_manage_orders=bool(request.form.get('can_manage_orders')) if is_staff else False,
        can_manage_users=bool(request.form.get('can_manage_users')) if is_staff else False,
        can_view_reports=bool(request.form.get('can_view_reports')) if is_staff else False,
        can_view_customers=bool(request.form.get('can_view_customers')) if is_staff else False,
        can_meter_readings=bool(request.form.get('can_meter_readings')) if is_staff else False
    )
    user.set_password(request.form.get('password'))
    db.session.add(user)
    db.session.commit()
    flash(f'User {user.name} created as {role}!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
@login_required
@permission_required('can_manage_users')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    user.name = request.form.get('name', user.name)
    user.role = request.form.get('role', user.role)
    user.email = request.form.get('email', user.email)
    user.phone_number = request.form.get('phone_number') or user.phone_number
    user.username = request.form.get('username') or user.username
    user.area_of_residence = request.form.get('area_of_residence', user.area_of_residence)
    is_staff = (user.role != 'client')
    user.is_field_marshal = (user.role == 'field_marshal')
    if is_staff:
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
    flash('User updated!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/users/delete/<int:user_id>')
@login_required
@permission_required('can_manage_users')
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Cannot delete yourself!', 'danger')
        return redirect(url_for('manage_users'))
    db.session.delete(User.query.get_or_404(user_id))
    db.session.commit()
    flash('User deleted!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/prices')
@login_required
@permission_required('can_edit_products')
def manage_prices():
    retail_products = Product.query.filter_by(category='retail').all()
    wholesale_products = Product.query.filter_by(category='wholesale').all()
    return render_template('dashboard/prices.html', retail_products=retail_products, wholesale_products=wholesale_products)

@app.route('/admin/products/add', methods=['POST'])
@login_required
@permission_required('can_edit_products')
def add_product():
    category = request.form.get('category')
    product = Product(name=request.form.get('name'), category=category,
                      price=float(request.form.get('price', 0)),
                      wholesale_min_qty=int(request.form.get('wholesale_min_qty', 0)) if category == 'wholesale' else 0)
    db.session.add(product)
    db.session.flush()
    if 'image' in request.files and request.files['image'].filename:
        img = request.files['image']
        fname = f"product_{product.id}_{img.filename}"
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        product.image = fname
    db.session.commit()
    flash('Product added!', 'success')
    return redirect(url_for('manage_prices'))

@app.route('/admin/prices/update', methods=['POST'])
@login_required
@permission_required('can_edit_products')
def update_price():
    product = Product.query.get_or_404(request.form.get('product_id'))
    new_price = float(request.form.get('price', 0))
    if product.price != new_price:
        db.session.add(PriceHistory(product_id=product.id, old_price=product.price or 0, new_price=new_price, changed_by=current_user.id))
    product.name = request.form.get('name', product.name)
    product.category = request.form.get('category', product.category)
    product.price = new_price if new_price > 0 else product.price
    if product.category == 'wholesale':
        product.wholesale_min_qty = int(request.form.get('wholesale_min_qty', product.wholesale_min_qty))
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

@app.route('/admin/meter-readings')
@login_required
@permission_required('can_meter_readings')
def meter_readings():
    readings = MeterReading.query.order_by(MeterReading.reading_date.desc()).all()
    return render_template('dashboard/meter_reading.html', readings=readings)

@app.route('/admin/meter-readings/add', methods=['POST'])
@login_required
@permission_required('can_meter_readings')
def add_meter_reading():
    db.session.add(MeterReading(
        meter_number=request.form.get('meter_number'),
        reading_value=float(request.form.get('reading_value')),
        liters_produced=float(request.form.get('liters_produced')),
        recorded_by=current_user.id,
        notes=request.form.get('notes', '')
    ))
    db.session.commit()
    flash('Meter reading recorded successfully!', 'success')
    return redirect(url_for('meter_readings'))

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

@app.route('/admin/reports')
@login_required
@permission_required('can_view_reports')
def reports():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    online_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.order_date.between(start_dt, end_dt)).filter(Order.payment_status == 'paid').scalar() or 0
    total_walkins = db.session.query(func.sum(WalkInSale.total_amount)).filter(WalkInSale.sale_date.between(start_dt, end_dt)).scalar() or 0
    total_orders = Order.query.filter(Order.order_date.between(start_dt, end_dt)).count()
    total_produced = db.session.query(func.sum(MeterReading.liters_produced)).filter(MeterReading.reading_date.between(start_dt, end_dt)).scalar() or 0
    return render_template('dashboard/reports.html', start_date=start_date, end_date=end_date,
                         online_sales=online_sales, total_walkins=total_walkins,
                         total_revenue=online_sales + total_walkins,
                         total_orders=total_orders, total_produced=total_produced)

@app.route('/admin/reports/sales-pdf')
@login_required
@permission_required('can_view_reports')
def sales_report_pdf():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    styles = getSampleStyleSheet()
    elements = [Paragraph("WEMA SPRINGS - SALES REPORT", styles['Title']), Paragraph(f"{start_date} to {end_date}", styles['Normal']), Spacer(1, 15)]
    online_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.order_date.between(start_dt, end_dt)).filter(Order.payment_status == 'paid').scalar() or 0
    walkin_sales = db.session.query(func.sum(WalkInSale.total_amount)).filter(WalkInSale.sale_date.between(start_dt, end_dt)).scalar() or 0
    sd = [['SALES SUMMARY', ''], ['Online Sales', f'KES {online_sales:,.2f}'], ['Walk-in Sales', f'KES {walkin_sales:,.2f}'], ['TOTAL', f'KES {online_sales+walkin_sales:,.2f}']]
    st = Table(sd, colWidths=[250, 250])
    st.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('SPAN', (0, 0), (-1, 0)), ('GRID', (0, 0), (-1, -1), 1, colors.black), ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#f59e0b'))]))
    elements.append(st)
    return generate_pdf(elements, f'Sales_Report_{start_date}_{end_date}.pdf')

@app.route('/admin/reports/inventory-pdf')
@login_required
@permission_required('can_view_reports')
def inventory_report_pdf():
    styles = getSampleStyleSheet()
    elements = [Paragraph("WEMA SPRINGS - INVENTORY REPORT", styles['Title']), Spacer(1, 15)]
    products = Product.query.all()
    idata = [['Product', 'Category', 'Price', 'Stock', 'Status']]
    for p in products:
        status = 'Good' if p.stock_quantity > 20 else 'Low' if p.stock_quantity > 5 else 'Critical'
        idata.append([p.name, p.category, f'{p.price:,.2f}', str(p.stock_quantity), status])
    it = Table(idata, colWidths=[150, 80, 80, 60, 80])
    it.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    elements.append(it)
    return generate_pdf(elements, f'Inventory_Report_{datetime.now().strftime("%Y%m%d")}.pdf')

@app.route('/admin/reports/meter-pdf')
@login_required
@permission_required('can_view_reports')
def meter_report_pdf():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    styles = getSampleStyleSheet()
    elements = [Paragraph("WEMA SPRINGS - METER REPORT", styles['Title']), Paragraph(f"{start_date} to {end_date}", styles['Normal']), Spacer(1, 15)]
    readings = MeterReading.query.filter(MeterReading.reading_date.between(start_dt, end_dt)).order_by(MeterReading.reading_date.desc()).all()
    total_liters = sum(r.liters_produced for r in readings)
    elements.append(Paragraph(f"Total Water Produced: {total_liters:,.0f} Liters", styles['Heading3']))
    elements.append(Spacer(1, 10))
    mdata = [['Date', 'Meter #', 'Reading', 'Liters', 'Notes']]
    for r in readings: mdata.append([r.reading_date.strftime('%Y-%m-%d %H:%M'), r.meter_number, str(r.reading_value), f'{r.liters_produced:,.0f}', r.notes or ''])
    mt = Table(mdata, colWidths=[100, 80, 80, 80, 150])
    mt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), 1, colors.black), ('FONTSIZE', (0, 0), (-1, -1), 8)]))
    elements.append(mt)
    return generate_pdf(elements, f'Meter_Report_{start_date}_{end_date}.pdf')

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

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
""")
print("✅ app.py")

# ============================================
# TEMPLATES - Only meter_reading.html is critical, others same as before
# ============================================
templates = {}

templates['base.html'] = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>{% block title %}Wema Springs{% endblock %}</title>\n<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">\n<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">\n<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/style.css\') }}">\n</head>\n<body>\n<nav class="navbar navbar-expand-lg navbar-dark"><div class="container-fluid px-3">\n<a class="navbar-brand" href="{{ url_for(\'index\') }}"><i class="bi bi-droplet-fill"></i> WEMA SPRINGS</a>\n<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button>\n<div class="collapse navbar-collapse" id="navbarNav"><ul class="navbar-nav ms-auto">\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'index\') }}">Home</a></li>\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'shop_retail\') }}">Retail</a></li>\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'shop_wholesale\') }}">Wholesale</a></li>\n{% if current_user.is_authenticated %}\n{% if current_user.role == \'client\' %}\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'client_dashboard\') }}">Dashboard</a></li>\n{% else %}\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a></li>\n{% endif %}\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'logout\') }}">Logout</a></li>\n{% else %}\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'login\') }}">Login</a></li>\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'register\') }}">Register</a></li>\n{% endif %}\n</ul></div></div></nav>\n{% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}<div class="container mt-2">{% for c,m in messages %}<div class="alert alert-{{ c }} alert-dismissible fade show py-2">{{ m }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>{% endfor %}</div>{% endif %}{% endwith %}\n<main>{% block content %}{% endblock %}</main>\n<footer class="footer"><div class="container"><div class="row"><div class="col-6"><h6>Wema Springs</h6></div><div class="col-6 text-end"><small>&copy; 2024</small></div></div></div></footer>\n<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>\n</body>\n</html>'

templates['index.html'] = '{% extends "base.html" %}\n{% block title %}Wema Springs - Home{% endblock %}\n{% block content %}\n<section class="hero-section"><div class="container"><div class="row align-items-center"><div class="col-lg-6"><h1 class="hero-title">Pure Water, Pure Life</h1><p class="lead text-white mb-4">Fresh spring water delivered.</p><div class="d-flex gap-2 flex-wrap"><a href="{{ url_for(\'shop_retail\') }}" class="btn btn-gold">Retail Shop</a><a href="{{ url_for(\'shop_wholesale\') }}" class="btn btn-outline-light">Wholesale</a></div></div><div class="col-lg-6 text-center d-none d-lg-block"><i class="bi bi-droplet-fill" style="font-size:12rem;color:rgba(255,255,255,0.3);"></i></div></div></div></section>\n<section class="py-4"><div class="container"><h3 class="text-center mb-4">Retail Products</h3><div class="row">{% for p in retail_products %}<div class="col-6 col-md-3 mb-3"><div class="card"><div class="card-body text-center p-3"><h6>{{ p.name }}</h6><h5 class="text-primary">KES {{ "%.2f"|format(p.price) }}</h5></div></div></div>{% endfor %}</div></div></section>\n{% endblock %}'

templates['login.html'] = '{% extends "base.html" %}\n{% block title %}Login{% endblock %}\n{% block content %}\n<div class="container py-4"><div class="row justify-content-center"><div class="col-11 col-md-5"><div class="card"><div class="card-header text-center"><h4>Login</h4></div><div class="card-body p-3"><form method="POST"><div class="mb-3"><label class="form-label">Phone or Username</label><input type="text" name="login_id" class="form-control" required></div><div class="mb-3"><label class="form-label">Password</label><input type="password" name="password" class="form-control" required></div><button type="submit" class="btn btn-primary w-100">Login</button></form><div class="text-center mt-2"><small>No account? <a href="{{ url_for(\'register\') }}">Register</a></small></div></div></div></div></div></div>\n{% endblock %}'

templates['register.html'] = '{% extends "base.html" %}\n{% block title %}Register{% endblock %}\n{% block content %}\n<div class="container py-4"><div class="row justify-content-center"><div class="col-11 col-md-6"><div class="card"><div class="card-header text-center"><h4>Create Account</h4></div><div class="card-body p-3"><form method="POST"><div class="mb-2"><label class="form-label">Full Name *</label><input type="text" name="name" class="form-control" required></div><div class="mb-2"><label class="form-label">Phone *</label><input type="text" name="phone_number" class="form-control" required></div><div class="mb-2"><label class="form-label">Email</label><input type="email" name="email" class="form-control"></div><div class="mb-2"><label class="form-label">Area</label><input type="text" name="area_of_residence" class="form-control"></div><div class="mb-2"><label class="form-label">Password *</label><input type="password" name="password" class="form-control" required></div><div class="mb-2"><label class="form-label">Confirm *</label><input type="password" name="confirm_password" class="form-control" required></div><button type="submit" class="btn btn-primary w-100 mt-2">Register</button></form></div></div></div></div></div>\n{% endblock %}'

templates['shop_retail.html'] = '{% extends "base.html" %}\n{% block title %}Retail Shop{% endblock %}\n{% block content %}\n<div class="container py-3"><h3 class="text-center mb-3">Retail Shop</h3><div class="row">{% for p in products %}<div class="col-6 col-md-4 col-lg-3 mb-3"><div class="card h-100"><div class="card-body text-center p-3"><i class="bi bi-droplet-fill" style="font-size:2.5rem;color:var(--secondary-blue);"></i><h6>{{ p.name }}</h6><h5>KES {{ "%.2f"|format(p.price) }}</h5><small class="text-muted">Stock: {{ p.stock_quantity }}</small>{% if current_user.is_authenticated and current_user.role==\'client\' and p.stock_quantity>0 %}<button class="btn btn-gold btn-sm w-100 mt-2" data-bs-toggle="modal" data-bs-target="#om{{ p.id }}">Order</button>{% elif not current_user.is_authenticated %}<a href="{{ url_for(\'login\') }}" class="btn btn-primary btn-sm w-100 mt-2">Login</a>{% endif %}</div></div></div>{% endfor %}</div></div>\n{% endblock %}'

templates['shop_wholesale.html'] = '{% extends "base.html" %}\n{% block title %}Wholesale Shop{% endblock %}\n{% block content %}\n<div class="container py-3"><h3 class="text-center mb-3">Wholesale Shop</h3><div class="row">{% for p in products %}<div class="col-6 col-md-4 col-lg-3 mb-3"><div class="card h-100"><div class="card-body text-center p-3"><i class="bi bi-box-seam" style="font-size:2.5rem;color:var(--gold);"></i><h6>{{ p.name }}</h6><h5>KES {{ "%.2f"|format(p.price) }}</h5><small>Min: {{ p.wholesale_min_qty }} | Stock: {{ p.stock_quantity }}</small>{% if current_user.is_authenticated and current_user.role==\'client\' and p.stock_quantity>=p.wholesale_min_qty %}<button class="btn btn-gold btn-sm w-100 mt-2" data-bs-toggle="modal" data-bs-target="#om{{ p.id }}">Order</button>{% elif not current_user.is_authenticated %}<a href="{{ url_for(\'login\') }}" class="btn btn-primary btn-sm w-100 mt-2">Login</a>{% endif %}</div></div></div>{% endfor %}</div></div>\n{% endblock %}'

templates['dashboard/client_dashboard.html'] = '{% extends "base.html" %}\n{% block title %}My Dashboard{% endblock %}\n{% block content %}\n<div class="container py-3"><h4>Welcome, {{ current_user.name }}!</h4><div class="card mt-3"><div class="card-header"><h5>My Orders</h5></div><div class="card-body p-2">{% if orders %}<div class="table-responsive"><table class="table table-sm"><thead><tr><th>ID</th><th>Date</th><th>Total</th><th>Status</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.order_date.strftime(\'%Y-%m-%d\') }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td><span class="badge bg-{{ \'warning\' if o.status==\'pending\' else \'success\' }}">{{ o.status }}</span></td></tr>{% endfor %}</tbody></table></div>{% else %}<p class="p-3">No orders. <a href="{{ url_for(\'shop_retail\') }}">Shop</a></p>{% endif %}</div></div></div>\n{% endblock %}'

templates['dashboard/admin_dashboard.html'] = '{% extends "base.html" %}\n{% block title %}Dashboard{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3">\n<a class="nav-link active" href="{{ url_for(\'admin_dashboard\') }}"><i class="bi bi-speedometer2"></i> Dashboard</a>\n{% if current_user.role==\'admin\' or current_user.can_record_sales %}<a class="nav-link" href="{{ url_for(\'walkin_sale\') }}"><i class="bi bi-cart-plus"></i> Walk-in Sale</a>{% endif %}\n{% if current_user.is_field_marshal or current_user.role==\'admin\' %}<a class="nav-link" href="{{ url_for(\'field_order\') }}"><i class="bi bi-person-lines-fill"></i> Field Orders</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_orders %}<a class="nav-link" href="{{ url_for(\'manage_orders\') }}"><i class="bi bi-cart-check"></i> Orders</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_customers %}<a class="nav-link" href="{{ url_for(\'manage_customers\') }}"><i class="bi bi-people"></i> Customers</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_manage_inventory %}<a class="nav-link" href="{{ url_for(\'inventory\') }}"><i class="bi bi-box-seam"></i> Inventory</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_edit_products %}<a class="nav-link" href="{{ url_for(\'manage_prices\') }}"><i class="bi bi-tag"></i> Products</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_manage_users %}<a class="nav-link" href="{{ url_for(\'manage_users\') }}"><i class="bi bi-person-gear"></i> Users</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_meter_readings %}<a class="nav-link" href="{{ url_for(\'meter_readings\') }}"><i class="bi bi-speedometer"></i> Meter</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_reports %}<a class="nav-link" href="{{ url_for(\'reports\') }}"><i class="bi bi-graph-up"></i> Reports</a>{% endif %}</nav></div>\n<div class="col-md-10 col-12 py-3"><h4>Dashboard</h4>\n<div class="row g-2 mb-3"><div class="col-6 col-md-3"><div class="card stats-card"><div class="card-body p-3"><small>Orders</small><div class="stats-number">{{ total_orders }}</div></div></div></div><div class="col-6 col-md-3"><div class="card stats-card"><div class="card-body p-3"><small>Revenue</small><div class="stats-number">KES {{ "%.0f"|format(total_revenue) }}</div></div></div></div><div class="col-6 col-md-3"><div class="card stats-card"><div class="card-body p-3"><small>Customers</small><div class="stats-number">{{ total_customers }}</div></div></div></div><div class="col-6 col-md-3"><div class="card stats-card"><div class="card-body p-3"><small>Products</small><div class="stats-number">{{ total_products }}</div></div></div></div></div>\n</div></div></div>\n{% endblock %}'

templates['dashboard/field_order.html'] = '{% extends "base.html" %}\n{% block title %}Field Orders{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'field_order\') }}">Field Orders</a></nav></div>\n<div class="col-md-10 col-12 py-3"><div class="row"><div class="col-12 col-md-5 mb-3"><div class="card"><div class="card-header" style="background:#8b5cf6;"><h5>Place Order</h5></div><div class="card-body p-3"><form action="{{ url_for(\'place_field_order\') }}" method="POST">\n<div class="mb-2"><label class="form-label">Client</label><select name="client_id" class="form-control" required><option value="">-- Select --</option>{% for c in clients %}<option value="{{ c.id }}">{{ c.name }} - {{ c.phone_number }}</option>{% endfor %}</select></div>\n<div class="mb-2"><label class="form-label">Product</label><select name="product_id" class="form-control" required>{% for p in products %}<option value="{{ p.id }}">{{ p.name }} - KES {{ "%.2f"|format(p.price) }}</option>{% endfor %}</select></div>\n<div class="mb-2"><label class="form-label">Qty</label><input type="number" name="quantity" class="form-control" value="1" required></div>\n<div class="mb-2"><label class="form-label">Address</label><input type="text" name="delivery_address" class="form-control"></div>\n<div class="mb-2"><label class="form-label">Payment</label><select name="payment_method" class="form-control"><option value="cash">Cash</option><option value="mpesa">M-Pesa</option></select></div>\n<div class="mb-2"><label class="form-label">M-Pesa Code</label><input type="text" name="mpesa_code" class="form-control"></div>\n<button type="submit" class="btn w-100 text-white" style="background:#8b5cf6;">Place Order</button></form></div></div></div>\n<div class="col-12 col-md-7"><div class="card"><div class="card-header"><h5>My Recent Orders</h5></div><div class="card-body p-2"><table class="table table-sm"><thead><tr><th>ID</th><th>Client</th><th>Total</th></tr></thead><tbody>{% for o in my_orders %}<tr><td>#{{ o.id }}</td><td>{{ o.customer.name }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td></tr>{% endfor %}</tbody></table></div></div></div></div></div></div></div>\n{% endblock %}'

templates['dashboard/walkin_sale.html'] = '{% extends "base.html" %}\n{% block title %}Walk-in Sale{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'walkin_sale\') }}">Walk-in Sale</a></nav></div>\n<div class="col-md-10 col-12 py-3"><div class="row"><div class="col-12 col-md-5 mb-3"><div class="card"><div class="card-header" style="background:#059669;"><h5>Record Sale</h5></div><div class="card-body p-3"><form action="{{ url_for(\'record_walkin_sale\') }}" method="POST">\n<div class="mb-2"><label class="form-label">Product</label><select name="product_id" class="form-control" required>{% for p in products %}<option value="{{ p.id }}">{{ p.name }} - KES {{ "%.2f"|format(p.price) }}</option>{% endfor %}</select></div>\n<div class="mb-2"><label class="form-label">Qty</label><input type="number" name="quantity" class="form-control" value="1" required></div>\n<div class="mb-2"><label class="form-label">Payment</label><select name="payment_method" class="form-control"><option value="cash">Cash</option><option value="mpesa">M-Pesa</option></select></div>\n<div class="mb-2"><label class="form-label">M-Pesa Code</label><input type="text" name="mpesa_code" class="form-control"></div>\n<div class="mb-2"><label class="form-label">Customer</label><input type="text" name="customer_name" class="form-control" value="Walk-in"></div>\n<button type="submit" class="btn btn-success w-100">Record Sale</button></form></div></div></div>\n<div class="col-12 col-md-7"><div class="card"><div class="card-header"><h5>Today</h5></div><div class="card-body p-2"><table class="table table-sm"><thead><tr><th>Time</th><th>Product</th><th>Total</th></tr></thead><tbody>{% for s in today_sales %}<tr><td>{{ s.sale_date.strftime(\'%H:%M\') }}</td><td>{{ s.product.name }}</td><td>KES {{ "%.2f"|format(s.total_amount) }}</td></tr>{% endfor %}</tbody></table></div></div></div></div></div></div></div>\n{% endblock %}'

templates['dashboard/customers.html'] = '{% extends "base.html" %}\n{% block title %}Customers{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_customers\') }}">Customers</a></nav></div>\n<div class="col-md-10 col-12 py-3"><h4>Customers</h4><div class="table-responsive"><table class="table table-sm"><thead><tr><th>Name</th><th>Phone</th><th>Area</th></tr></thead><tbody>{% for c in customers %}<tr><td>{{ c.name }}</td><td>{{ c.phone_number }}</td><td>{{ c.area_of_residence or \'-\' }}</td></tr>{% endfor %}</tbody></table></div></div></div></div>\n{% endblock %}'

templates['dashboard/customer_detail.html'] = '{% extends "base.html" %}\n{% block title %}Customer{% endblock %}\n{% block content %}\n<div class="container py-3"><h4>{{ customer.name }}</h4><p>Phone: {{ customer.phone_number }} | Area: {{ customer.area_of_residence or \'-\' }}</p><table class="table table-sm"><thead><tr><th>ID</th><th>Date</th><th>Total</th><th>Status</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.order_date.strftime(\'%Y-%m-%d\') }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td>{{ o.status }}</td></tr>{% endfor %}</tbody></table></div>\n{% endblock %}'

templates['dashboard/orders.html'] = '{% extends "base.html" %}\n{% block title %}Orders{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_orders\') }}">Orders</a></nav></div>\n<div class="col-md-10 col-12 py-3"><h4>Orders</h4><div class="table-responsive"><table class="table table-sm"><thead><tr><th>ID</th><th>Customer</th><th>Phone</th><th>Total</th><th>Status</th><th>Action</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.customer.name }}</td><td>{{ o.customer.phone_number }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td><span class="badge bg-{{ \'warning\' if o.status==\'pending\' else \'success\' }}">{{ o.status }}</span></td><td>{% if current_user.role==\'admin\' or current_user.can_manage_orders %}<button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#upd{{ o.id }}">Update</button>{% endif %}</td></tr>{% endfor %}</tbody></table></div></div></div></div>\n{% for o in orders %}<div class="modal fade" id="upd{{ o.id }}"><div class="modal-dialog modal-sm"><div class="modal-content"><div class="modal-header"><h6>Update #{{ o.id }}</h6></div><form action="{{ url_for(\'update_order\', order_id=o.id) }}" method="POST"><div class="modal-body"><select name="status" class="form-control"><option value="pending">Pending</option><option value="confirmed">Confirmed</option><option value="delivered">Delivered</option><option value="cancelled">Cancelled</option></select></div><div class="modal-footer"><button type="submit" class="btn btn-gold btn-sm">Update</button></div></form></div></div></div>{% endfor %}\n{% endblock %}'

templates['dashboard/users.html'] = '{% extends "base.html" %}\n{% block title %}Users{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_users\') }}">Users</a></nav></div>\n<div class="col-md-10 col-12 py-3"><div class="d-flex justify-content-between mb-3"><h4>User Management</h4><button class="btn btn-gold btn-sm" data-bs-toggle="modal" data-bs-target="#addUserModal">+ Add User</button></div>\n<div class="card mb-3"><div class="card-header py-2"><h6>Staff</h6></div><div class="card-body p-2"><table class="table table-sm"><thead><tr><th>Name</th><th>Username</th><th>Role</th><th>Actions</th></tr></thead><tbody>{% for u in staff %}<tr><td>{{ u.name }}</td><td>{{ u.username }}</td><td>{{ u.role }}</td><td>{% if u.id != current_user.id %}<button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#editUser{{ u.id }}">Edit</button><a href="{{ url_for(\'delete_user\', user_id=u.id) }}" class="btn btn-sm btn-outline-danger" onclick="return confirm(\'Delete?\')">Del</a>{% endif %}</td></tr>{% endfor %}</tbody></table></div></div>\n<div class="card"><div class="card-header py-2"><h6>Clients</h6></div><div class="card-body p-2"><table class="table table-sm"><thead><tr><th>Name</th><th>Phone</th><th>Area</th><th>Actions</th></tr></thead><tbody>{% for c in clients %}<tr><td>{{ c.name }}</td><td>{{ c.phone_number }}</td><td>{{ c.area_of_residence or \'-\' }}</td><td><button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#editUser{{ c.id }}">Edit</button><a href="{{ url_for(\'delete_user\', user_id=c.id) }}" class="btn btn-sm btn-outline-danger" onclick="return confirm(\'Delete?\')">Del</a></td></tr>{% endfor %}</tbody></table></div></div></div></div></div>\n\n<div class="modal fade" id="addUserModal"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5>Add User</h5><button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button></div><form action="{{ url_for(\'add_user\') }}" method="POST"><div class="modal-body"><div class="row"><div class="col-md-6">\n<div class="mb-2"><label>Full Name *</label><input type="text" name="name" class="form-control" required></div>\n<div class="mb-2"><label>Role *</label><select name="role" id="addRole" class="form-control" required onchange="var s=this.value!=\'client\';document.getElementById(\'sf\').style.display=s?\'block\':\'none\';document.getElementById(\'cf\').style.display=s?\'none\':\'block\';"><option value="client">Client</option><option value="cashier">Cashier</option><option value="accountant">Accountant</option><option value="field_marshal">Field Marshal</option><option value="admin">Admin</option></select></div>\n<div class="mb-2"><label>Password *</label><input type="password" name="password" class="form-control" required></div></div><div class="col-md-6">\n<div id="sf"><div class="mb-2"><label>Username *</label><input type="text" name="username" class="form-control"></div></div>\n<div id="cf" style="display:none;"><div class="mb-2"><label>Phone *</label><input type="text" name="phone_number" class="form-control"></div><div class="mb-2"><label>Area</label><input type="text" name="area_of_residence" class="form-control"></div></div>\n<div class="mb-2"><label>Email</label><input type="email" name="email" class="form-control"></div></div></div></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Add User</button></div></form></div></div></div>\n\n{% for u in staff + clients %}{% if u.id != current_user.id %}<div class="modal fade" id="editUser{{ u.id }}"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h5>Edit {{ u.name }}</h5></div><form action="{{ url_for(\'edit_user\', user_id=u.id) }}" method="POST"><div class="modal-body"><div class="mb-2"><label>Name</label><input type="text" name="name" class="form-control" value="{{ u.name }}"></div><div class="mb-2"><label>Role</label><select name="role" class="form-control"><option value="client" {{ \'selected\' if u.role==\'client\' }}>Client</option><option value="cashier" {{ \'selected\' if u.role==\'cashier\' }}>Cashier</option><option value="accountant" {{ \'selected\' if u.role==\'accountant\' }}>Accountant</option><option value="field_marshal" {{ \'selected\' if u.role==\'field_marshal\' }}>Field Marshal</option><option value="admin" {{ \'selected\' if u.role==\'admin\' }}>Admin</option></select></div><div class="mb-2"><label>Phone</label><input type="text" name="phone_number" class="form-control" value="{{ u.phone_number or \'\' }}"></div><div class="mb-2"><label>Username</label><input type="text" name="username" class="form-control" value="{{ u.username or \'\' }}"></div><div class="mb-2"><label>Area</label><input type="text" name="area_of_residence" class="form-control" value="{{ u.area_of_residence or \'\' }}"></div></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Update</button></div></form></div></div></div>{% endif %}{% endfor %}\n{% endblock %}'

templates['dashboard/prices.html'] = '{% extends "base.html" %}\n{% block title %}Products{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_prices\') }}">Products</a></nav></div>\n<div class="col-md-10 col-12 py-3"><div class="d-flex justify-content-between mb-3"><h4>Products</h4><button class="btn btn-gold btn-sm" data-bs-toggle="modal" data-bs-target="#addProductModal">+ Add</button></div>\n<div class="card mb-3"><div class="card-header py-2"><h6>Retail</h6></div><div class="card-body p-2"><table class="table table-sm"><thead><tr><th>Name</th><th>Price</th><th>Stock</th></tr></thead><tbody>{% for p in retail_products %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.stock_quantity }}</td></tr>{% endfor %}</tbody></table></div></div>\n<div class="card"><div class="card-header py-2"><h6>Wholesale</h6></div><div class="card-body p-2"><table class="table table-sm"><thead><tr><th>Name</th><th>Price</th><th>Min Qty</th><th>Stock</th></tr></thead><tbody>{% for p in wholesale_products %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.wholesale_min_qty }}</td><td>{{ p.stock_quantity }}</td></tr>{% endfor %}</tbody></table></div></div></div></div></div>\n\n<div class="modal fade" id="addProductModal"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5>Add Product</h5></div><form action="{{ url_for(\'add_product\') }}" method="POST"><div class="modal-body"><div class="mb-2"><label>Name</label><input type="text" name="name" class="form-control" required></div><div class="mb-2"><label>Category</label><select name="category" class="form-control" onchange="document.getElementById(\'wq\').style.display=this.value==\'wholesale\'?\'block\':\'none\'"><option value="retail">Retail</option><option value="wholesale">Wholesale</option></select></div><div class="mb-2"><label>Price (KES)</label><input type="number" step="0.01" name="price" class="form-control" required></div><div class="mb-2" id="wq" style="display:none;"><label>Min Wholesale Qty</label><input type="number" name="wholesale_min_qty" class="form-control" value="5"></div></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Add</button></div></form></div></div></div>\n{% endblock %}'

templates['dashboard/inventory.html'] = '{% extends "base.html" %}\n{% block title %}Inventory{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'inventory\') }}">Inventory</a></nav></div>\n<div class="col-md-10 col-12 py-3"><div class="d-flex justify-content-between mb-3"><h4>Inventory</h4><button class="btn btn-gold btn-sm" data-bs-toggle="modal" data-bs-target="#addStockModal">+ Add Stock</button></div>\n<table class="table table-sm"><thead><tr><th>Product</th><th>Price</th><th>Stock</th><th>Status</th></tr></thead><tbody>{% for p in products %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td><strong>{{ p.stock_quantity }}</strong></td><td><span class="badge bg-{{ \'success\' if p.stock_quantity>20 else \'warning\' if p.stock_quantity>5 else \'danger\' }}">{{ \'Good\' if p.stock_quantity>20 else \'Low\' if p.stock_quantity>5 else \'Critical\' }}</span></td></tr>{% endfor %}</tbody></table></div></div></div>\n\n<div class="modal fade" id="addStockModal"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5>Add Stock</h5></div><form action="{{ url_for(\'add_stock\') }}" method="POST"><div class="modal-body"><div class="mb-2"><label>Product</label><select name="product_id" class="form-control">{% for p in products %}<option value="{{ p.id }}">{{ p.name }}</option>{% endfor %}</select></div><div class="mb-2"><label>Quantity</label><input type="number" name="quantity" class="form-control" min="1" required></div><div class="mb-2"><label>Notes</label><input type="text" name="notes" class="form-control"></div></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Add Stock</button></div></form></div></div></div>\n{% endblock %}'

# ============ FIXED METER READING TEMPLATE WITH MODAL ============
templates['dashboard/meter_reading.html'] = '''{% extends "base.html" %}
{% block title %}Meter Readings{% endblock %}
{% block content %}
<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3"><a class="nav-link" href="{{ url_for('admin_dashboard') }}">Dashboard</a><a class="nav-link active" href="{{ url_for('meter_readings') }}">Meter</a></nav></div>
<div class="col-md-10 col-12 py-3"><div class="d-flex justify-content-between mb-3"><h4>Meter Readings</h4><button class="btn btn-gold btn-sm" data-bs-toggle="modal" data-bs-target="#addReadingModal">+ Add Reading</button></div>
<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Date</th><th>Meter #</th><th>Reading</th><th>Liters Produced</th><th>Notes</th></tr></thead><tbody>{% for r in readings %}<tr><td>{{ r.reading_date.strftime('%Y-%m-%d %H:%M') }}</td><td>{{ r.meter_number }}</td><td>{{ r.reading_value }}</td><td><strong>{{ r.liters_produced }} L</strong></td><td>{{ r.notes or '-' }}</td></tr>{% endfor %}</tbody></table></div></div></div></div>

<!-- Add Meter Reading Modal -->
<div class="modal fade" id="addReadingModal" tabindex="-1" aria-labelledby="addReadingModalLabel" aria-hidden="true">
<div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:linear-gradient(135deg,#1e40af,#3b82f6);color:white;"><h5 class="modal-title" id="addReadingModalLabel"><i class="bi bi-speedometer"></i> Record Meter Reading</h5><button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button></div>
<form action="{{ url_for('add_meter_reading') }}" method="POST"><div class="modal-body">
<div class="mb-3"><label class="form-label"><i class="bi bi-upc-scan"></i> Meter Number *</label><input type="text" name="meter_number" class="form-control" placeholder="e.g., MTR-001" required></div>
<div class="mb-3"><label class="form-label"><i class="bi bi-gauge"></i> Reading Value *</label><input type="number" step="0.01" name="reading_value" class="form-control" placeholder="Current meter reading" required></div>
<div class="mb-3"><label class="form-label"><i class="bi bi-droplet"></i> Liters Produced *</label><input type="number" step="0.01" name="liters_produced" class="form-control" placeholder="Liters produced this period" required></div>
<div class="mb-3"><label class="form-label"><i class="bi bi-journal-text"></i> Notes</label><textarea name="notes" class="form-control" rows="2" placeholder="Any additional notes..."></textarea></div></div>
<div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn btn-gold"><i class="bi bi-check-circle"></i> Save Reading</button></div></form></div></div></div>
{% endblock %}'''

templates['dashboard/reports.html'] = '{% extends "base.html" %}\n{% block title %}Reports{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block p-0"><nav class="nav flex-column p-3"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'reports\') }}">Reports</a></nav></div>\n<div class="col-md-10 col-12 py-3"><h4>Reports</h4>\n<div class="card mb-3"><div class="card-body p-3"><form method="GET" class="row g-2"><div class="col-5 col-md-4"><input type="date" name="start_date" class="form-control" value="{{ start_date }}"></div><div class="col-5 col-md-4"><input type="date" name="end_date" class="form-control" value="{{ end_date }}"></div><div class="col-2 col-md-4"><button type="submit" class="btn btn-primary w-100">Go</button></div></form></div></div>\n<div class="row g-2 mb-3"><div class="col-6 col-md-3"><div class="card stats-card"><div class="card-body p-3"><small>Online</small><div class="stats-number">KES {{ "%.0f"|format(online_sales) }}</div></div></div></div><div class="col-6 col-md-3"><div class="card stats-card"><div class="card-body p-3"><small>Walk-in</small><div class="stats-number">KES {{ "%.0f"|format(total_walkins) }}</div></div></div></div><div class="col-6 col-md-3"><div class="card stats-card"><div class="card-body p-3"><small>Total</small><div class="stats-number">KES {{ "%.0f"|format(total_revenue) }}</div></div></div></div><div class="col-6 col-md-3"><div class="card stats-card"><div class="card-body p-3"><small>Orders</small><div class="stats-number">{{ total_orders }}</div></div></div></div></div>\n<div class="d-flex flex-wrap gap-2"><a href="{{ url_for(\'sales_report_pdf\', start_date=start_date, end_date=end_date) }}" class="btn btn-danger btn-sm"><i class="bi bi-file-pdf"></i> Sales PDF</a><a href="{{ url_for(\'inventory_report_pdf\') }}" class="btn btn-warning btn-sm"><i class="bi bi-file-pdf"></i> Inventory PDF</a><a href="{{ url_for(\'meter_report_pdf\', start_date=start_date, end_date=end_date) }}" class="btn btn-info btn-sm"><i class="bi bi-file-pdf"></i> Meter PDF</a></div></div></div></div>\n{% endblock %}'

for filename, content in templates.items():
    filepath = os.path.join("templates", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ All templates created!")

with open("static/css/style.css", "w") as f:
    f.write(""":root{--primary-blue:#1e40af;--secondary-blue:#3b82f6;--gold:#f59e0b;--light-gold:#fbbf24;--white:#fff}*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#f0f9ff,#e0f2fe);min-height:100vh}.navbar{background:linear-gradient(135deg,var(--primary-blue),#1e3a8a);padding:0.5rem 1rem}.navbar-brand{font-size:1.3rem;font-weight:700;color:#fff!important}.nav-link{color:#fff!important;font-size:0.9rem}.hero-section{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));color:#fff;padding:40px 0}.hero-title{font-size:2rem;font-weight:700;color:#fff}@media(min-width:768px){.hero-title{font-size:3rem}.navbar-brand{font-size:1.5rem}.hero-section{padding:80px 0}}.card{border:none;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.08);margin-bottom:15px;background:#fff}.card-header{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));color:#fff;border-radius:12px 12px 0 0!important;padding:0.75rem 1rem}.stats-card{border-left:4px solid var(--gold)}.stats-number{font-size:1.5rem;font-weight:700;color:var(--primary-blue)}@media(min-width:768px){.stats-number{font-size:2rem}}.btn-primary{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));border:none;padding:8px 20px;border-radius:25px;color:white}.btn-gold{background:linear-gradient(135deg,var(--gold),var(--light-gold));border:none;padding:8px 20px;border-radius:25px;color:white;font-weight:700}.btn-success{background:linear-gradient(135deg,#059669,#10b981);border:none;border-radius:25px;color:white}.btn-danger{background:linear-gradient(135deg,#dc2626,#ef4444);border:none;border-radius:25px;color:white}.form-control{border-radius:20px;padding:8px 15px;border:2px solid #e5e7eb;font-size:0.9rem}.table{background:#fff;border-radius:10px;overflow:hidden;font-size:0.85rem}.table thead{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));color:#fff}.sidebar{background:linear-gradient(180deg,var(--primary-blue),#1e3a8a);min-height:100vh;padding-top:10px}.sidebar .nav-link{color:#fff;padding:10px 15px;margin:2px 0;border-radius:8px;font-size:0.9rem}.sidebar .nav-link:hover,.sidebar .nav-link.active{background:rgba(255,255,255,0.15);color:#fff}.footer{background:var(--primary-blue);color:#fff;padding:15px 0;margin-top:30px;font-size:0.85rem}.badge{padding:5px 10px;border-radius:15px;font-size:0.75rem}@media(max-width:767px){.sidebar{min-height:auto;padding:10px}.sidebar .nav-link{display:inline-block;padding:8px 12px;font-size:0.8rem}.table{font-size:0.75rem}.btn{font-size:0.8rem;padding:6px 15px}}""")
print("✅ style.css created!")

print("\n" + "="*50)
print("🎉 COMPLETE!")
print("Run: pip install reportlab && python app.py")
print("Admin: admin / admin123")
print("="*50)