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
    registered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
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
            if not current_user.is_authenticated: return redirect(url_for('login'))
            if current_user.role == 'admin': return f(*args, **kwargs)
            if not getattr(current_user, permission, False):
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

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        cp = request.form.get('current_password', '')
        np = request.form.get('new_password', '')
        cnp = request.form.get('confirm_password', '')
        if not current_user.check_password(cp): flash('Wrong password.', 'danger'); return redirect(url_for('change_password'))
        if len(np) < 4: flash('Too short.', 'danger'); return redirect(url_for('change_password'))
        if np != cnp: flash('Mismatch.', 'danger'); return redirect(url_for('change_password'))
        current_user.set_password(np); db.session.commit()
        flash('Password changed!', 'success')
        return redirect(url_for('admin_dashboard') if current_user.role != 'client' else url_for('client_dashboard'))
    return render_template('change_password.html')

@app.route('/')
def index():
    retail = Product.query.filter_by(category='retail').limit(4).all()
    wholesale = Product.query.filter_by(category='wholesale').limit(4).all()
    salty = Product.query.filter_by(category='salty').limit(4).all()
    return render_template('index.html', retail_products=retail, wholesale_products=wholesale, salty_products=salty)

@app.route('/shop/retail')
def shop_retail():
    return render_template('shop_retail.html', products=Product.query.filter_by(category='retail').all())

@app.route('/shop/wholesale')
def shop_wholesale():
    return render_template('shop_wholesale.html', products=Product.query.filter_by(category='wholesale').all())

@app.route('/shop/salty')
def shop_salty():
    return render_template('shop_salty.html', products=Product.query.filter_by(category='salty').all())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone_number', '').strip()
        pw = request.form.get('password'); cpw = request.form.get('confirm_password')
        name = request.form.get('name'); email = request.form.get('email'); area = request.form.get('area_of_residence')
        if not phone or not pw or not name: flash('Fill all fields.', 'danger'); return redirect(url_for('register'))
        if pw != cpw: flash('Passwords mismatch.', 'danger'); return redirect(url_for('register'))
        if User.query.filter_by(phone_number=phone).first(): flash('Phone exists.', 'danger'); return redirect(url_for('login'))
        u = User(phone_number=phone, name=name, email=email, area_of_residence=area, role='client')
        u.set_password(pw); db.session.add(u); db.session.commit()
        flash('Registered! Login.', 'success'); return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        lid = request.form.get('login_id', '').strip(); pw = request.form.get('password', '')
        if not lid or not pw: flash('Enter details.', 'danger'); return render_template('login.html')
        u = User.query.filter(or_(User.username == lid, User.phone_number == lid)).first()
        if u and u.check_password(pw):
            login_user(u); flash(f'Welcome, {u.name}!', 'success')
            return redirect(url_for('admin_dashboard') if u.role != 'client' else url_for('client_dashboard'))
        flash('Invalid.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user(); return redirect(url_for('index'))

@app.route('/dashboard/client')
@login_required
def client_dashboard():
    if current_user.role != 'client': return redirect(url_for('admin_dashboard'))
    return render_template('dashboard/client_dashboard.html', orders=Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all())

@app.route('/place-order', methods=['POST'])
@login_required
def place_order():
    pid = request.form.get('product_id'); qty = int(request.form.get('quantity', 1))
    mpesa = request.form.get('mpesa_code'); addr = request.form.get('delivery_address', current_user.area_of_residence)
    p = Product.query.get_or_404(pid)
    if p.stock_quantity < qty: flash('No stock!', 'danger'); return redirect(url_for('shop_retail'))
    total = p.price * qty
    o = Order(user_id=current_user.id, total_amount=total, mpesa_code=mpesa, payment_status='paid' if mpesa else 'pending', delivery_address=addr, order_type=p.category, source='online')
    db.session.add(o); db.session.flush()
    db.session.add(OrderItem(order_id=o.id, product_id=p.id, quantity=qty, unit_price=p.price))
    p.stock_quantity -= qty
    db.session.add(Inventory(product_id=p.id, stock_out=qty, current_stock=p.stock_quantity, recorded_by=current_user.id, notes=f'Order #{o.id}'))
    db.session.commit()
    flash(f'Order placed! KES {total:.2f}', 'success'); return redirect(url_for('client_dashboard'))

@app.route('/dashboard/admin')
@login_required
@staff_required
def admin_dashboard():
    total_orders = Order.query.count()
    tw = db.session.query(func.sum(WalkInSale.total_amount)).scalar() or 0
    os_ = db.session.query(func.sum(Order.total_amount)).filter(Order.payment_status == 'paid').scalar() or 0
    return render_template('dashboard/admin_dashboard.html', total_orders=total_orders, total_revenue=os_+tw, total_customers=User.query.filter_by(role='client').count(), total_products=Product.query.count())

# FIELD MARSHAL
@app.route('/admin/field-order')
@login_required
@staff_required
def field_order():
    if not current_user.is_field_marshal and current_user.role != 'admin': flash('Only Field Marshals.', 'danger'); return redirect(url_for('admin_dashboard'))
    return render_template('dashboard/field_order.html', products=Product.query.filter(Product.stock_quantity>0).all(), clients=User.query.filter_by(role='client').order_by(User.name).all(), my_orders=Order.query.filter_by(field_marshal_id=current_user.id).order_by(Order.order_date.desc()).limit(20).all())

@app.route('/admin/field-order/register-client', methods=['POST'])
@login_required
@staff_required
def field_register_client():
    phone = request.form.get('phone_number','').strip(); name = request.form.get('name','').strip(); area = request.form.get('area_of_residence','').strip()
    if not phone or not name: flash('Name & phone required.', 'danger'); return redirect(url_for('field_order'))
    if User.query.filter_by(phone_number=phone).first(): flash('Exists!', 'warning'); return redirect(url_for('field_order'))
    c = User(phone_number=phone, name=name, area_of_residence=area, role='client', registered_by=current_user.id); c.set_password('123456')
    db.session.add(c); db.session.commit()
    flash(f'Client {name} registered!', 'success'); return redirect(url_for('field_order'))

@app.route('/admin/field-order/place', methods=['POST'])
@login_required
@staff_required
def place_field_order():
    pid = request.form.get('product_id'); qty = int(request.form.get('quantity',1)); cid = request.form.get('client_id')
    mpesa = request.form.get('mpesa_code',''); addr = request.form.get('delivery_address',''); pm = request.form.get('payment_method','cash')
    p = Product.query.get_or_404(pid)
    if p.stock_quantity < qty: flash('No stock!', 'danger'); return redirect(url_for('field_order'))
    total = p.price * qty
    o = Order(user_id=cid, field_marshal_id=current_user.id, total_amount=total, mpesa_code=mpesa, payment_status='paid' if (mpesa or pm=='mpesa') else 'pending', delivery_address=addr, order_type=p.category, source='field_marshal')
    db.session.add(o); db.session.flush()
    db.session.add(OrderItem(order_id=o.id, product_id=p.id, quantity=qty, unit_price=p.price))
    p.stock_quantity -= qty
    db.session.add(Inventory(product_id=p.id, stock_out=qty, current_stock=p.stock_quantity, recorded_by=current_user.id, notes=f'Field order #{o.id}'))
    db.session.commit()
    flash(f'Order placed! KES {total:.2f}', 'success'); return redirect(url_for('field_order'))

@app.route('/admin/field-order/my-clients')
@login_required
@staff_required
def field_my_clients():
    return render_template('dashboard/field_clients.html', clients=User.query.filter_by(role='client', registered_by=current_user.id).all())

@app.route('/admin/field-order/client-orders/<int:client_id>')
@login_required
@staff_required
def field_client_orders(client_id):
    c = User.query.get_or_404(client_id)
    return render_template('dashboard/field_client_orders.html', client=c, orders=Order.query.filter_by(user_id=client_id, field_marshal_id=current_user.id).order_by(Order.order_date.desc()).all())

# WALK-IN SALE
@app.route('/admin/walkin-sale')
@login_required
@permission_required('can_record_sales')
def walkin_sale():
    return render_template('dashboard/walkin_sale.html', products=Product.query.all(), today_sales=WalkInSale.query.filter(func.date(WalkInSale.sale_date)==datetime.now().date()).order_by(WalkInSale.sale_date.desc()).all())

@app.route('/admin/walkin-sale/record', methods=['POST'])
@login_required
@permission_required('can_record_sales')
def record_walkin_sale():
    pid = request.form.get('product_id'); qty = int(request.form.get('quantity',1)); pm = request.form.get('payment_method','cash')
    mpesa = request.form.get('mpesa_code',''); cn = request.form.get('customer_name','Walk-in')
    p = Product.query.get_or_404(pid)
    if p.stock_quantity < qty: flash('No stock!', 'danger'); return redirect(url_for('walkin_sale'))
    total = p.price * qty
    db.session.add(WalkInSale(product_id=p.id, quantity=qty, unit_price=p.price, total_amount=total, payment_method=pm, mpesa_code=mpesa if pm=='mpesa' else None, customer_name=cn, recorded_by=current_user.id))
    p.stock_quantity -= qty
    db.session.add(Inventory(product_id=p.id, stock_out=qty, current_stock=p.stock_quantity, recorded_by=current_user.id, notes='Walk-in'))
    db.session.commit()
    flash(f'Sale! KES {total:.2f}', 'success'); return redirect(url_for('walkin_sale'))

# CUSTOMERS
@app.route('/admin/customers')
@login_required
@permission_required('can_view_customers')
def manage_customers():
    if current_user.is_field_marshal and current_user.role != 'admin':
        cust = User.query.filter_by(role='client', registered_by=current_user.id).order_by(User.created_at.desc()).all()
    else:
        cust = User.query.filter_by(role='client').order_by(User.created_at.desc()).all()
    return render_template('dashboard/customers.html', customers=cust)

@app.route('/admin/customers/view/<int:user_id>')
@login_required
def view_customer(user_id):
    return render_template('dashboard/customer_detail.html', customer=User.query.get_or_404(user_id), orders=Order.query.filter_by(user_id=user_id).order_by(Order.order_date.desc()).all())

# STAFF
@app.route('/admin/users')
@login_required
@permission_required('can_manage_users')
def manage_users():
    return render_template('dashboard/users.html', staff=User.query.filter(User.role!='client').order_by(User.created_at.desc()).all())

@app.route('/admin/users/add', methods=['POST'])
@login_required
@permission_required('can_manage_users')
def add_user():
    r = request.form.get('role','cashier')
    u = User(username=request.form.get('username'), name=request.form.get('name'), role=r, email=request.form.get('email'), is_field_marshal=(r=='field_marshal'), can_dashboard=True, can_edit_products=bool(request.form.get('can_edit_products')), can_manage_inventory=bool(request.form.get('can_manage_inventory')), can_record_sales=bool(request.form.get('can_record_sales')), can_view_orders=bool(request.form.get('can_view_orders')), can_manage_orders=bool(request.form.get('can_manage_orders')), can_manage_users=bool(request.form.get('can_manage_users')), can_view_reports=bool(request.form.get('can_view_reports')), can_view_customers=bool(request.form.get('can_view_customers')), can_meter_readings=bool(request.form.get('can_meter_readings')))
    u.set_password(request.form.get('password')); db.session.add(u); db.session.commit()
    flash(f'Staff {u.name} created!', 'success'); return redirect(url_for('manage_users'))

@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
@login_required
@permission_required('can_manage_users')
def edit_user(user_id):
    u = User.query.get_or_404(user_id)
    u.name = request.form.get('name', u.name); r = request.form.get('role', u.role); u.role = r
    u.email = request.form.get('email', u.email); u.username = request.form.get('username') or u.username
    u.is_field_marshal = (r == 'field_marshal')
    u.can_edit_products = bool(request.form.get('can_edit_products')); u.can_manage_inventory = bool(request.form.get('can_manage_inventory'))
    u.can_record_sales = bool(request.form.get('can_record_sales')); u.can_view_orders = bool(request.form.get('can_view_orders'))
    u.can_manage_orders = bool(request.form.get('can_manage_orders')); u.can_manage_users = bool(request.form.get('can_manage_users'))
    u.can_view_reports = bool(request.form.get('can_view_reports')); u.can_view_customers = bool(request.form.get('can_view_customers'))
    u.can_meter_readings = bool(request.form.get('can_meter_readings'))
    db.session.commit(); flash('Updated!', 'success'); return redirect(url_for('manage_users'))

@app.route('/admin/users/delete/<int:user_id>')
@login_required
@permission_required('can_manage_users')
def delete_user(user_id):
    if user_id == current_user.id: flash('Cannot delete self.', 'danger'); return redirect(url_for('manage_users'))
    db.session.delete(User.query.get_or_404(user_id)); db.session.commit()
    flash('Deleted!', 'success'); return redirect(url_for('manage_users'))

# PRODUCTS
@app.route('/admin/prices')
@login_required
@permission_required('can_edit_products')
def manage_prices():
    return render_template('dashboard/prices.html', retail_products=Product.query.filter_by(category='retail').all(), wholesale_products=Product.query.filter_by(category='wholesale').all(), salty_products=Product.query.filter_by(category='salty').all())

@app.route('/admin/products/add', methods=['POST'])
@login_required
@permission_required('can_edit_products')
def add_product():
    cat = request.form.get('category'); price = float(request.form.get('price',0))
    wmq = int(request.form.get('wholesale_min_qty',0)) if cat in ['wholesale','salty'] else 0
    p = Product(name=request.form.get('name'), category=cat, price=price, wholesale_min_qty=wmq)
    db.session.add(p); db.session.flush()
    if 'image' in request.files and request.files['image'].filename:
        img = request.files['image']; img.save(os.path.join(app.config['UPLOAD_FOLDER'], f"p{p.id}_{img.filename}")); p.image = f"p{p.id}_{img.filename}"
    db.session.commit(); flash(f'{cat.title()} product added!', 'success'); return redirect(url_for('manage_prices'))

@app.route('/admin/prices/update', methods=['POST'])
@login_required
@permission_required('can_edit_products')
def update_price():
    p = Product.query.get_or_404(request.form.get('product_id')); np = float(request.form.get('price',0))
    if p.price != np: db.session.add(PriceHistory(product_id=p.id, old_price=p.price or 0, new_price=np, changed_by=current_user.id))
    p.name = request.form.get('name', p.name); p.category = request.form.get('category', p.category); p.price = np if np > 0 else p.price
    if p.category in ['wholesale','salty']: p.wholesale_min_qty = int(request.form.get('wholesale_min_qty', p.wholesale_min_qty))
    if 'image' in request.files and request.files['image'].filename:
        img = request.files['image']; img.save(os.path.join(app.config['UPLOAD_FOLDER'], f"p{p.id}_{img.filename}")); p.image = f"p{p.id}_{img.filename}"
    db.session.commit(); flash('Updated!', 'success'); return redirect(url_for('manage_prices'))

# INVENTORY
@app.route('/admin/inventory')
@login_required
@permission_required('can_manage_inventory')
def inventory():
    return render_template('dashboard/inventory.html', products=Product.query.all())

@app.route('/admin/inventory/add-stock', methods=['POST'])
@login_required
@permission_required('can_manage_inventory')
def add_stock():
    p = Product.query.get_or_404(request.form.get('product_id')); qty = int(request.form.get('quantity'))
    p.stock_quantity += qty
    db.session.add(Inventory(product_id=p.id, stock_in=qty, current_stock=p.stock_quantity, recorded_by=current_user.id, notes=request.form.get('notes','')))
    db.session.commit(); flash(f'Added {qty}!', 'success'); return redirect(url_for('inventory'))

# METER
@app.route('/admin/meter-readings')
@login_required
@permission_required('can_meter_readings')
def meter_readings():
    return render_template('dashboard/meter_reading.html', readings=MeterReading.query.order_by(MeterReading.reading_date.desc()).all())

@app.route('/admin/meter-readings/add', methods=['POST'])
@login_required
@permission_required('can_meter_readings')
def add_meter_reading():
    db.session.add(MeterReading(meter_number=request.form.get('meter_number'), reading_value=float(request.form.get('reading_value')), liters_produced=float(request.form.get('liters_produced')), recorded_by=current_user.id, notes=request.form.get('notes','')))
    db.session.commit(); flash('Recorded!', 'success'); return redirect(url_for('meter_readings'))

# ORDERS
@app.route('/admin/orders')
@login_required
@permission_required('can_view_orders')
def manage_orders():
    if current_user.is_field_marshal and current_user.role != 'admin':
        orders = Order.query.filter_by(field_marshal_id=current_user.id).order_by(Order.order_date.desc()).all()
    else:
        orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('dashboard/orders.html', orders=orders)

@app.route('/admin/orders/update/<int:order_id>', methods=['POST'])
@login_required
@permission_required('can_manage_orders')
def update_order(order_id):
    o = Order.query.get_or_404(order_id); o.status = request.form.get('status')
    if o.status == 'delivered': o.payment_status = 'paid'
    db.session.commit(); flash('Updated!', 'success'); return redirect(url_for('manage_orders'))

# REPORTS
@app.route('/admin/reports')
@login_required
@permission_required('can_view_reports')
def reports():
    sd = request.args.get('start_date', (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d'))
    ed = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    sdt = datetime.strptime(sd, '%Y-%m-%d'); edt = datetime.strptime(ed, '%Y-%m-%d') + timedelta(days=1)
    os_ = db.session.query(func.sum(Order.total_amount)).filter(Order.order_date.between(sdt,edt)).filter(Order.payment_status=='paid').scalar() or 0
    tw = db.session.query(func.sum(WalkInSale.total_amount)).filter(WalkInSale.sale_date.between(sdt,edt)).scalar() or 0
    return render_template('dashboard/reports.html', start_date=sd, end_date=ed, online_sales=os_, total_walkins=tw, total_revenue=os_+tw, total_orders=Order.query.filter(Order.order_date.between(sdt,edt)).count())

@app.route('/admin/reports/pdf')
@login_required
@permission_required('can_view_reports')
def reports_pdf():
    buffer = BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=A4); styles = getSampleStyleSheet()
    doc.build([Paragraph("WEMA SPRINGS - REPORT", styles['Title'])])
    buffer.seek(0); response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'; response.headers['Content-Disposition'] = 'attachment; filename=report.pdf'
    return response

with app.app_context():
    db.drop_all(); db.create_all()
    admin = User(username='admin', name='Administrator', role='admin', can_dashboard=True, can_edit_products=True, can_manage_inventory=True, can_record_sales=True, can_view_orders=True, can_manage_orders=True, can_manage_users=True, can_view_reports=True, can_view_customers=True, can_meter_readings=True)
    admin.set_password('admin123'); db.session.add(admin); db.session.commit()
    print("✅ Admin: admin / admin123")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
""")
print("✅ app.py")

# ============================================
# TEMPLATES
# ============================================
templates = {}

templates['base.html'] = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>{% block title %}Wema Springs{% endblock %}</title>\n<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">\n<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">\n<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/style.css\') }}">\n</head>\n<body>\n<nav class="navbar navbar-expand-lg navbar-dark"><div class="container">\n<a class="navbar-brand" href="{{ url_for(\'index\') }}" style="color:#fff!important;"><i class="bi bi-droplet-fill"></i> WEMA SPRINGS</a>\n<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button>\n<div class="collapse navbar-collapse" id="navbarNav"><ul class="navbar-nav ms-auto">\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'index\') }}">Home</a></li>\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'shop_retail\') }}">Retail</a></li>\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'shop_wholesale\') }}">Wholesale</a></li>\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'shop_salty\') }}">Salty Water</a></li>\n{% if current_user.is_authenticated %}\n{% if current_user.role == \'client\' %}<li class="nav-item"><a class="nav-link" href="{{ url_for(\'client_dashboard\') }}">Dashboard</a></li>{% else %}<li class="nav-item"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a></li>{% endif %}\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'change_password\') }}"><i class="bi bi-key"></i> Password</a></li>\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'logout\') }}">Logout</a></li>\n{% else %}\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'login\') }}">Login</a></li>\n<li class="nav-item"><a class="nav-link" href="{{ url_for(\'register\') }}">Register</a></li>\n{% endif %}\n</ul></div></div></nav>\n{% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}<div class="container mt-3">{% for c,m in messages %}<div class="alert alert-{{ c }} alert-dismissible fade show">{{ m }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>{% endfor %}</div>{% endif %}{% endwith %}\n<main>{% block content %}{% endblock %}</main>\n<footer class="footer"><div class="container"><div class="row"><div class="col-md-6"><h5>Wema Springs</h5><p>Pure & Salty Water Solutions</p></div><div class="col-md-6 text-md-end"><p>&copy; 2024 Wema Springs</p></div></div></div></footer>\n<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>\n</body>\n</html>'

templates['change_password.html'] = '{% extends "base.html" %}\n{% block title %}Change Password{% endblock %}\n{% block content %}\n<div class="container py-5"><div class="row justify-content-center"><div class="col-md-5"><div class="card"><div class="card-header text-center"><h3><i class="bi bi-key"></i> Change Password</h3></div><div class="card-body p-4"><form method="POST">\n<div class="mb-3"><label>Current Password</label><input type="password" name="current_password" class="form-control" required></div>\n<div class="mb-3"><label>New Password</label><input type="password" name="new_password" class="form-control" required></div>\n<div class="mb-3"><label>Confirm New Password</label><input type="password" name="confirm_password" class="form-control" required></div>\n<button type="submit" class="btn btn-primary w-100">Change Password</button></form></div></div></div></div></div>\n{% endblock %}'

templates['index.html'] = '{% extends "base.html" %}\n{% block title %}Wema Springs - Home{% endblock %}\n{% block content %}\n<section class="hero-section"><div class="container"><div class="row"><div class="col-lg-6"><h1 class="hero-title">Pure & Salty Water</h1><p class="lead text-white mb-4">Fresh spring water & bulk salty water delivery.</p><div class="d-flex gap-3 flex-wrap"><a href="{{ url_for(\'shop_retail\') }}" class="btn btn-gold btn-lg">Retail</a><a href="{{ url_for(\'shop_wholesale\') }}" class="btn btn-outline-light btn-lg">Wholesale</a><a href="{{ url_for(\'shop_salty\') }}" class="btn btn-outline-light btn-lg">Salty Water</a></div></div><div class="col-lg-6 text-center"><i class="bi bi-droplet-fill" style="font-size:15rem;color:rgba(255,255,255,0.3);"></i></div></div></div></section>\n{% if retail_products %}<section class="py-5"><div class="container"><h3>Retail Water</h3><div class="row">{% for p in retail_products %}<div class="col-md-3"><div class="card"><div class="card-body text-center"><h5>{{ p.name }}</h5><h4>KES {{ "%.2f"|format(p.price) }}</h4></div></div></div>{% endfor %}</div></div></section>{% endif %}\n{% if salty_products %}<section class="py-5" style="background:#fef3c7;"><div class="container"><h3 style="color:#92400e;">Salty/Borehole Water</h3><div class="row">{% for p in salty_products %}<div class="col-md-3"><div class="card"><div class="card-body text-center"><i class="bi bi-truck"></i><h5>{{ p.name }}</h5><h4>KES {{ "%.2f"|format(p.price) }}</h4></div></div></div>{% endfor %}</div></div></section>{% endif %}\n{% endblock %}'

templates['login.html'] = '{% extends "base.html" %}\n{% block title %}Login{% endblock %}\n{% block content %}\n<div class="container py-5"><div class="row justify-content-center"><div class="col-md-5"><div class="card"><div class="card-header text-center"><h3>Login</h3></div><div class="card-body p-4"><form method="POST"><div class="mb-3"><label>Phone or Username</label><input type="text" name="login_id" class="form-control" required></div><div class="mb-3"><label>Password</label><input type="password" name="password" class="form-control" required></div><button type="submit" class="btn btn-primary w-100">Login</button></form></div></div></div></div></div>\n{% endblock %}'

templates['register.html'] = '{% extends "base.html" %}\n{% block title %}Register{% endblock %}\n{% block content %}\n<div class="container py-5"><div class="row justify-content-center"><div class="col-md-6"><div class="card"><div class="card-header text-center"><h3>Create Account</h3></div><div class="card-body p-4"><form method="POST"><div class="mb-3"><label>Full Name *</label><input type="text" name="name" class="form-control" required></div><div class="mb-3"><label>Phone *</label><input type="text" name="phone_number" class="form-control" required></div><div class="mb-3"><label>Email</label><input type="email" name="email" class="form-control"></div><div class="mb-3"><label>Area *</label><input type="text" name="area_of_residence" class="form-control" required></div><div class="mb-3"><label>Password *</label><input type="password" name="password" class="form-control" required></div><div class="mb-3"><label>Confirm *</label><input type="password" name="confirm_password" class="form-control" required></div><button type="submit" class="btn btn-primary w-100">Register</button></form></div></div></div></div></div>\n{% endblock %}'

# SHOP TEMPLATES
templates['shop_retail.html'] = '{% extends "base.html" %}\n{% block title %}Retail Shop{% endblock %}\n{% block content %}\n<div class="container py-5"><h2 class="text-center mb-4" style="color:var(--primary-blue);"><i class="bi bi-shop"></i> Retail Shop</h2>\n<div class="row">{% for p in products %}<div class="col-md-4 mb-4"><div class="card h-100"><div class="card-body text-center"><i class="bi bi-droplet-fill" style="font-size:4rem;color:var(--secondary-blue);"></i><h4>{{ p.name }}</h4><h3>KES {{ "%.2f"|format(p.price) }}</h3><p><span class="badge bg-{{ \'success\' if p.stock_quantity>0 else \'danger\' }}">{{ \'In Stock\' if p.stock_quantity>0 else \'Out\' }}</span></p>{% if current_user.is_authenticated and current_user.role==\'client\' and p.stock_quantity>0 %}<button class="btn btn-gold w-100" onclick="openModal(\'{{ p.id }}\',\'{{ p.name }}\',{{ p.price }},{{ p.stock_quantity }},\'retail\')">Order Now</button>{% elif not current_user.is_authenticated %}<a href="{{ url_for(\'login\') }}" class="btn btn-primary w-100">Login to Order</a>{% endif %}</div></div></div>{% endfor %}</div></div>\n<div class="modal fade" id="orderModal"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5 id="omTitle">Order</h5></div><form action="{{ url_for(\'place_order\') }}" method="POST"><div class="modal-body"><input type="hidden" name="product_id" id="omPid"><input type="hidden" name="order_type" id="omType"><div class="mb-3"><label>Qty</label><input type="number" name="quantity" id="omQty" class="form-control" value="1" min="1" required oninput="updateTotal()"></div><div class="mb-3"><label>Delivery</label><input type="text" name="delivery_address" class="form-control" value="{{ current_user.area_of_residence if current_user.is_authenticated else \'\' }}"></div><div class="mb-3"><label>M-Pesa Code</label><input type="text" name="mpesa_code" class="form-control"></div><div class="alert alert-info text-center"><strong>Total: <span id="omTotal" style="font-size:1.3rem;"></span></strong></div></div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn btn-gold">Confirm</button></div></form></div></div></div>\n<script>var cp=0,cs=0;function openModal(i,n,p,s,t){document.getElementById(\'omPid\').value=i;document.getElementById(\'omType\').value=t;document.getElementById(\'omTitle\').innerText=\'Order: \'+n;document.getElementById(\'omQty\').value=1;document.getElementById(\'omQty\').max=s;cp=p;cs=s;updateTotal();new bootstrap.Modal(document.getElementById(\'orderModal\')).show()}function updateTotal(){var q=parseInt(document.getElementById(\'omQty\').value)||1;if(q>cs)q=cs;if(q<1)q=1;document.getElementById(\'omTotal\').innerText=\'KES \'+(q*cp).toFixed(2)}</script>\n{% endblock %}'

templates['shop_wholesale.html'] = '{% extends "base.html" %}\n{% block title %}Wholesale Shop{% endblock %}\n{% block content %}\n<div class="container py-5"><h2 class="text-center mb-4"><i class="bi bi-boxes"></i> Wholesale Shop</h2>\n<div class="row">{% for p in products %}<div class="col-md-4 mb-4"><div class="card h-100"><div class="card-body text-center"><i class="bi bi-box-seam" style="font-size:4rem;color:var(--gold);"></i><h4>{{ p.name }}</h4><h3>KES {{ "%.2f"|format(p.price) }}</h3><p><strong>Min: {{ p.wholesale_min_qty }}</strong></p>{% if current_user.is_authenticated and current_user.role==\'client\' and p.stock_quantity>=p.wholesale_min_qty %}<button class="btn btn-gold w-100" onclick="openWs(\'{{ p.id }}\',\'{{ p.name }}\',{{ p.price }},{{ p.stock_quantity }},{{ p.wholesale_min_qty }})">Order Now</button>{% elif not current_user.is_authenticated %}<a href="{{ url_for(\'login\') }}" class="btn btn-primary w-100">Login to Order</a>{% endif %}</div></div></div>{% endfor %}</div></div>\n<div class="modal fade" id="wsModal"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#f59e0b;color:white;"><h5 id="wsTitle">Wholesale</h5></div><form action="{{ url_for(\'place_order\') }}" method="POST"><div class="modal-body"><input type="hidden" name="product_id" id="wsPid"><input type="hidden" name="order_type" value="wholesale"><div class="mb-3"><label>Qty (Min: <span id="wsMin"></span>)</label><input type="number" name="quantity" id="wsQty" class="form-control" required oninput="updateWs()"></div><div class="mb-3"><label>Delivery</label><input type="text" name="delivery_address" class="form-control" value="{{ current_user.area_of_residence if current_user.is_authenticated else \'\' }}"></div><div class="mb-3"><label>M-Pesa Code</label><input type="text" name="mpesa_code" class="form-control"></div><div class="alert alert-warning text-center"><strong>Total: <span id="wsTotal" style="font-size:1.3rem;"></span></strong></div></div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn btn-gold">Confirm</button></div></form></div></div></div>\n<script>var wp=0,ws=0,wm=0;function openWs(i,n,p,s,m){document.getElementById(\'wsPid\').value=i;document.getElementById(\'wsTitle\').innerText=\'Wholesale: \'+n;document.getElementById(\'wsQty\').value=m;document.getElementById(\'wsQty\').min=m;document.getElementById(\'wsQty\').max=s;document.getElementById(\'wsMin\').innerText=m;wp=p;ws=s;wm=m;updateWs();new bootstrap.Modal(document.getElementById(\'wsModal\')).show()}function updateWs(){var q=parseInt(document.getElementById(\'wsQty\').value)||wm;if(q>ws)q=ws;if(q<wm)q=wm;document.getElementById(\'wsTotal\').innerText=\'KES \'+(q*wp).toFixed(2)}</script>\n{% endblock %}'

templates['shop_salty.html'] = '{% extends "base.html" %}\n{% block title %}Salty Water{% endblock %}\n{% block content %}\n<div class="container py-5"><h2 class="text-center mb-4" style="color:#92400e;"><i class="bi bi-truck"></i> Salty / Borehole Water</h2><p class="text-center text-muted">Bulk salty water for construction, farms, and homes. Delivered by truck/tanker.</p>\n<div class="row">{% for p in products %}<div class="col-md-4 mb-4"><div class="card h-100" style="border:2px solid #d97706;"><div class="card-body text-center"><i class="bi bi-truck" style="font-size:4rem;color:#d97706;"></i><h4>{{ p.name }}</h4><h3 style="color:#92400e;">KES {{ "%.2f"|format(p.price) }}</h3><p><strong>Min Order: {{ p.wholesale_min_qty }} units</strong></p><p><span class="badge bg-{{ \'success\' if p.stock_quantity>=p.wholesale_min_qty else \'danger\' }}">{{ \'Available\' if p.stock_quantity>=p.wholesale_min_qty else \'Low\' }}</span></p>{% if current_user.is_authenticated and current_user.role==\'client\' and p.stock_quantity>=p.wholesale_min_qty %}<button class="btn w-100 text-white" style="background:#d97706;" onclick="openSalty(\'{{ p.id }}\',\'{{ p.name }}\',{{ p.price }},{{ p.stock_quantity }},{{ p.wholesale_min_qty }})">Order Now</button>{% elif not current_user.is_authenticated %}<a href="{{ url_for(\'login\') }}" class="btn btn-primary w-100">Login to Order</a>{% endif %}</div></div></div>{% endfor %}</div></div>\n<div class="modal fade" id="saltyModal"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#d97706;color:white;"><h5 id="saltyTitle">Salty Water</h5></div><form action="{{ url_for(\'place_order\') }}" method="POST"><div class="modal-body"><input type="hidden" name="product_id" id="saltyPid"><input type="hidden" name="order_type" value="salty"><div class="mb-3"><label>Qty (Min: <span id="saltyMin"></span>)</label><input type="number" name="quantity" id="saltyQty" class="form-control" required oninput="updateSalty()"></div><div class="mb-3"><label>Delivery Address</label><input type="text" name="delivery_address" class="form-control" value="{{ current_user.area_of_residence if current_user.is_authenticated else \'\' }}"></div><div class="mb-3"><label>M-Pesa Code</label><input type="text" name="mpesa_code" class="form-control"></div><div class="alert text-center" style="background:#fef3c7;"><strong>Total: <span id="saltyTotal" style="font-size:1.3rem;"></span></strong></div></div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn text-white" style="background:#d97706;">Confirm Order</button></div></form></div></div></div>\n<script>var sp=0,ss=0,sm=0;function openSalty(i,n,p,s,m){document.getElementById(\'saltyPid\').value=i;document.getElementById(\'saltyTitle\').innerText=\'Salty: \'+n;document.getElementById(\'saltyQty\').value=m;document.getElementById(\'saltyQty\').min=m;document.getElementById(\'saltyQty\').max=s;document.getElementById(\'saltyMin\').innerText=m;sp=p;ss=s;sm=m;updateSalty();new bootstrap.Modal(document.getElementById(\'saltyModal\')).show()}function updateSalty(){var q=parseInt(document.getElementById(\'saltyQty\').value)||sm;if(q>ss)q=ss;if(q<sm)q=sm;document.getElementById(\'saltyTotal\').innerText=\'KES \'+(q*sp).toFixed(2)}</script>\n{% endblock %}'

# DASHBOARD TEMPLATES
templates['dashboard/client_dashboard.html'] = '{% extends "base.html" %}\n{% block title %}My Dashboard{% endblock %}\n{% block content %}\n<div class="container py-4"><h2>Welcome, {{ current_user.name }}!</h2><div class="card mt-4"><div class="card-header"><h5>My Orders</h5></div><div class="card-body">{% if orders %}<table class="table"><thead><tr><th>ID</th><th>Date</th><th>Total</th><th>Status</th><th>Payment</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.order_date.strftime(\'%Y-%m-%d\') }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td>{{ o.status }}</td><td>{{ o.payment_status }}</td></tr>{% endfor %}</tbody></table>{% else %}<p>No orders. <a href="{{ url_for(\'shop_retail\') }}">Shop</a></p>{% endif %}</div></div></div>\n{% endblock %}'

templates['dashboard/admin_dashboard.html'] = '{% extends "base.html" %}\n{% block title %}Dashboard{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column">\n<a class="nav-link active" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a>\n{% if current_user.role==\'admin\' or current_user.can_record_sales %}<a class="nav-link" href="{{ url_for(\'walkin_sale\') }}">Walk-in Sale</a>{% endif %}\n{% if current_user.is_field_marshal or current_user.role==\'admin\' %}<a class="nav-link" href="{{ url_for(\'field_order\') }}">Field Orders</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_orders %}<a class="nav-link" href="{{ url_for(\'manage_orders\') }}">Orders</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_customers %}<a class="nav-link" href="{{ url_for(\'manage_customers\') }}">Customers</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_manage_inventory %}<a class="nav-link" href="{{ url_for(\'inventory\') }}">Inventory</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_edit_products %}<a class="nav-link" href="{{ url_for(\'manage_prices\') }}">Products</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_manage_users %}<a class="nav-link" href="{{ url_for(\'manage_users\') }}">Staff</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_meter_readings %}<a class="nav-link" href="{{ url_for(\'meter_readings\') }}">Meter</a>{% endif %}\n{% if current_user.role==\'admin\' or current_user.can_view_reports %}<a class="nav-link" href="{{ url_for(\'reports\') }}">Reports</a>{% endif %}\n</nav></div><div class="col-md-10 py-4"><h2>Dashboard</h2><div class="row"><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Orders</h6><div class="stats-number">{{ total_orders }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Revenue</h6><div class="stats-number">KES {{ "%.0f"|format(total_revenue) }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Customers</h6><div class="stats-number">{{ total_customers }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Products</h6><div class="stats-number">{{ total_products }}</div></div></div></div></div></div></div></div>\n{% endblock %}'

templates['dashboard/prices.html'] = '{% extends "base.html" %}\n{% block title %}Products & Prices{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_prices\') }}">Products</a></nav></div>\n<div class="col-md-10 py-4"><h2>Products & Prices</h2>\n\n<!-- RETAIL -->\n<div class="card mb-4"><div class="card-header d-flex justify-content-between" style="background:var(--secondary-blue);"><h5 class="mb-0">Retail Products</h5><button class="btn btn-light btn-sm" data-bs-toggle="modal" data-bs-target="#addRetail">+ Add Retail</button></div>\n<div class="card-body"><table class="table"><thead><tr><th>Name</th><th>Price</th><th>Stock</th><th>Edit</th></tr></thead><tbody>{% for p in retail_products %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.stock_quantity }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#edit{{ p.id }}">Edit</button></td></tr>{% endfor %}</tbody></table></div></div>\n\n<!-- WHOLESALE -->\n<div class="card mb-4"><div class="card-header d-flex justify-content-between" style="background:var(--gold);"><h5 class="mb-0">Wholesale Products</h5><button class="btn btn-light btn-sm" data-bs-toggle="modal" data-bs-target="#addWholesale">+ Add Wholesale</button></div>\n<div class="card-body"><table class="table"><thead><tr><th>Name</th><th>Price</th><th>Min Qty</th><th>Stock</th><th>Edit</th></tr></thead><tbody>{% for p in wholesale_products %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.wholesale_min_qty }}</td><td>{{ p.stock_quantity }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#edit{{ p.id }}">Edit</button></td></tr>{% endfor %}</tbody></table></div></div>\n\n<!-- SALTY WATER -->\n<div class="card mb-4"><div class="card-header d-flex justify-content-between" style="background:#d97706;"><h5 class="mb-0">Salty/Borehole Water</h5><button class="btn btn-light btn-sm" data-bs-toggle="modal" data-bs-target="#addSalty">+ Add Salty Water</button></div>\n<div class="card-body"><table class="table"><thead><tr><th>Name</th><th>Price</th><th>Min Qty</th><th>Stock</th><th>Edit</th></tr></thead><tbody>{% for p in salty_products %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.wholesale_min_qty }}</td><td>{{ p.stock_quantity }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#edit{{ p.id }}">Edit</button></td></tr>{% endfor %}</tbody></table></div></div>\n\n</div></div></div>\n\n<!-- ADD MODALS -->\n<div class="modal fade" id="addRetail"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:var(--secondary-blue);color:white;"><h5>Add Retail Product</h5></div><form action="{{ url_for(\'add_product\') }}" method="POST"><div class="modal-body"><input type="hidden" name="category" value="retail"><div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" required></div><div class="mb-3"><label>Price (KES)</label><input type="number" step="0.01" name="price" class="form-control" required></div></div><div class="modal-footer"><button type="submit" class="btn btn-primary">Add</button></div></form></div></div></div>\n\n<div class="modal fade" id="addWholesale"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:var(--gold);color:white;"><h5>Add Wholesale Product</h5></div><form action="{{ url_for(\'add_product\') }}" method="POST"><div class="modal-body"><input type="hidden" name="category" value="wholesale"><div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" required></div><div class="mb-3"><label>Price (KES)</label><input type="number" step="0.01" name="price" class="form-control" required></div><div class="mb-3"><label>Min Qty</label><input type="number" name="wholesale_min_qty" class="form-control" value="5"></div></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Add</button></div></form></div></div></div>\n\n<div class="modal fade" id="addSalty"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#d97706;color:white;"><h5>Add Salty Water Product</h5></div><form action="{{ url_for(\'add_product\') }}" method="POST"><div class="modal-body"><input type="hidden" name="category" value="salty"><div class="mb-3"><label>Name (e.g., Tanker 10,000L)</label><input type="text" name="name" class="form-control" required></div><div class="mb-3"><label>Price (KES)</label><input type="number" step="0.01" name="price" class="form-control" required></div><div class="mb-3"><label>Min Qty</label><input type="number" name="wholesale_min_qty" class="form-control" value="1"></div></div><div class="modal-footer"><button type="submit" class="btn text-white" style="background:#d97706;">Add</button></div></form></div></div></div>\n\n{% for p in retail_products + wholesale_products + salty_products %}\n<div class="modal fade" id="edit{{ p.id }}"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5>Edit {{ p.name }}</h5></div><form action="{{ url_for(\'update_price\') }}" method="POST"><div class="modal-body"><input type="hidden" name="product_id" value="{{ p.id }}"><input type="hidden" name="category" value="{{ p.category }}"><div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" value="{{ p.name }}"></div><div class="mb-3"><label>Price</label><input type="number" step="0.01" name="price" class="form-control" value="{{ "%.2f"|format(p.price) }}"></div>{% if p.category in [\'wholesale\',\'salty\'] %}<div class="mb-3"><label>Min Qty</label><input type="number" name="wholesale_min_qty" class="form-control" value="{{ p.wholesale_min_qty }}"></div>{% endif %}</div><div class="modal-footer"><button type="submit" class="btn btn-gold">Update</button></div></form></div></div></div>\n{% endfor %}\n{% endblock %}'

templates['dashboard/inventory.html'] = '{% extends "base.html" %}\n{% block title %}Inventory{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'inventory\') }}">Inventory</a></nav></div>\n<div class="col-md-10 py-4"><h2>Inventory</h2>\n<!-- RETAIL STOCK -->\n<div class="card mb-4"><div class="card-header d-flex justify-content-between" style="background:var(--secondary-blue);"><h5 class="mb-0">Retail Stock</h5><button class="btn btn-light btn-sm" data-bs-toggle="modal" data-bs-target="#addRetailStock">+ Add Retail Stock</button></div>\n<div class="card-body"><table class="table"><thead><tr><th>Name</th><th>Price</th><th>Stock</th><th>Status</th></tr></thead><tbody>{% for p in products %}{% if p.category==\'retail\' %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td><strong>{{ p.stock_quantity }}</strong></td><td><span class="badge bg-{{ \'success\' if p.stock_quantity>20 else \'warning\' if p.stock_quantity>5 else \'danger\' }}">{{ \'Good\' if p.stock_quantity>20 else \'Low\' if p.stock_quantity>5 else \'Critical\' }}</span></td></tr>{% endif %}{% endfor %}</tbody></table></div></div>\n<!-- WHOLESALE STOCK -->\n<div class="card mb-4"><div class="card-header d-flex justify-content-between" style="background:var(--gold);"><h5 class="mb-0">Wholesale Stock</h5><button class="btn btn-light btn-sm" data-bs-toggle="modal" data-bs-target="#addWsStock">+ Add Wholesale Stock</button></div>\n<div class="card-body"><table class="table"><thead><tr><th>Name</th><th>Price</th><th>Min Qty</th><th>Stock</th><th>Status</th></tr></thead><tbody>{% for p in products %}{% if p.category==\'wholesale\' %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.wholesale_min_qty }}</td><td><strong>{{ p.stock_quantity }}</strong></td><td><span class="badge bg-{{ \'success\' if p.stock_quantity>20 else \'warning\' if p.stock_quantity>5 else \'danger\' }}">{{ \'Good\' if p.stock_quantity>20 else \'Low\' if p.stock_quantity>5 else \'Critical\' }}</span></td></tr>{% endif %}{% endfor %}</tbody></table></div></div>\n<!-- SALTY STOCK -->\n<div class="card mb-4"><div class="card-header d-flex justify-content-between" style="background:#d97706;"><h5 class="mb-0">Salty Water Stock</h5><button class="btn btn-light btn-sm" data-bs-toggle="modal" data-bs-target="#addSaltyStock">+ Add Salty Water Stock</button></div>\n<div class="card-body"><table class="table"><thead><tr><th>Name</th><th>Price</th><th>Min Qty</th><th>Stock</th><th>Status</th></tr></thead><tbody>{% for p in products %}{% if p.category==\'salty\' %}<tr><td>{{ p.name }}</td><td>KES {{ "%.2f"|format(p.price) }}</td><td>{{ p.wholesale_min_qty }}</td><td><strong>{{ p.stock_quantity }}</strong></td><td><span class="badge bg-{{ \'success\' if p.stock_quantity>20 else \'warning\' if p.stock_quantity>5 else \'danger\' }}">{{ \'Good\' if p.stock_quantity>20 else \'Low\' if p.stock_quantity>5 else \'Critical\' }}</span></td></tr>{% endif %}{% endfor %}</tbody></table></div></div>\n</div></div></div>\n\n<!-- STOCK MODALS -->\n{% set categories = [{\'id\':\'addRetailStock\',\'cat\':\'retail\',\'bg\':\'var(--secondary-blue)\',\'title\':\'Retail\'}, {\'id\':\'addWsStock\',\'cat\':\'wholesale\',\'bg\':\'var(--gold)\',\'title\':\'Wholesale\'}, {\'id\':\'addSaltyStock\',\'cat\':\'salty\',\'bg\':\'#d97706\',\'title\':\'Salty Water\'}] %}\n{% for c in categories %}\n<div class="modal fade" id="{{ c.id }}"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:{{ c.bg }};color:white;"><h5>Add {{ c.title }} Stock</h5></div><form action="{{ url_for(\'add_stock\') }}" method="POST"><div class="modal-body"><div class="mb-3"><label>Product</label><select name="product_id" class="form-control" required>{% for p in products %}{% if p.category==c.cat %}<option value="{{ p.id }}">{{ p.name }} ({{ p.stock_quantity }})</option>{% endif %}{% endfor %}</select></div><div class="mb-3"><label>Quantity</label><input type="number" name="quantity" class="form-control" required></div><div class="mb-3"><label>Notes</label><textarea name="notes" class="form-control"></textarea></div></div><div class="modal-footer"><button type="submit" class="btn" style="background:{{ c.bg }};color:white;">Add Stock</button></div></form></div></div></div>\n{% endfor %}\n{% endblock %}'

templates['dashboard/walkin_sale.html'] = '{% extends "base.html" %}\n{% block title %}Walk-in Sale{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'walkin_sale\') }}">Walk-in</a></nav></div>\n<div class="col-md-10 py-4"><div class="row"><div class="col-md-5"><div class="card"><div class="card-header" style="background:#059669;"><h5>Record Sale</h5></div><div class="card-body"><form action="{{ url_for(\'record_walkin_sale\') }}" method="POST">\n<div class="mb-3"><label>Product</label><select name="product_id" class="form-control" required>{% for p in products %}<option value="{{ p.id }}">[{{ p.category.upper() }}] {{ p.name }} - KES {{ "%.2f"|format(p.price) }}</option>{% endfor %}</select></div>\n<div class="mb-3"><label>Qty</label><input type="number" name="quantity" class="form-control" value="1" required></div>\n<div class="mb-3"><label>Payment</label><select name="payment_method" class="form-control"><option value="cash">Cash</option><option value="mpesa">M-Pesa</option></select></div>\n<div class="mb-3"><label>M-Pesa Code</label><input type="text" name="mpesa_code" class="form-control"></div>\n<div class="mb-3"><label>Customer</label><input type="text" name="customer_name" class="form-control" value="Walk-in"></div>\n<button type="submit" class="btn btn-success w-100">Record Sale</button></form></div></div></div>\n<div class="col-md-7"><div class="card"><div class="card-header"><h5>Today</h5></div><div class="card-body"><table class="table table-sm">{% for s in today_sales %}<tr><td>{{ s.sale_date.strftime(\'%H:%M\') }}</td><td>{{ s.product.name }}</td><td>KES {{ "%.2f"|format(s.total_amount) }}</td></tr>{% endfor %}</table></div></div></div></div></div></div></div>\n{% endblock %}'

templates['dashboard/field_order.html'] = '{% extends "base.html" %}\n{% block title %}Field Orders{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'field_order\') }}">Field</a></nav></div>\n<div class="col-md-10 py-4"><div class="row"><div class="col-md-6"><div class="card mb-4"><div class="card-header" style="background:#8b5cf6;"><h5>Register Client</h5></div><div class="card-body"><form action="{{ url_for(\'field_register_client\') }}" method="POST"><div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" required></div><div class="mb-3"><label>Phone</label><input type="text" name="phone_number" class="form-control" required></div><div class="mb-3"><label>Area</label><input type="text" name="area_of_residence" class="form-control"></div><button type="submit" class="btn w-100 text-white" style="background:#8b5cf6;">Register</button></form></div></div>\n<div class="card"><div class="card-header" style="background:#8b5cf6;"><h5>Place Order</h5></div><div class="card-body"><form action="{{ url_for(\'place_field_order\') }}" method="POST">\n<select name="client_id" class="form-control mb-2" required>{% for c in clients %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}</select>\n<select name="product_id" class="form-control mb-2" required>{% for p in products %}<option value="{{ p.id }}">[{{ p.category.upper() }}] {{ p.name }} - KES {{ "%.2f"|format(p.price) }}</option>{% endfor %}</select>\n<input type="number" name="quantity" class="form-control mb-2" value="1" required>\n<input type="text" name="delivery_address" class="form-control mb-2" placeholder="Delivery address">\n<select name="payment_method" class="form-control mb-2"><option value="cash">Cash</option><option value="mpesa">M-Pesa</option></select>\n<input type="text" name="mpesa_code" class="form-control mb-2" placeholder="M-Pesa Code">\n<button type="submit" class="btn w-100 text-white" style="background:#8b5cf6;">Place Order</button></form></div></div></div>\n<div class="col-md-6"><div class="card"><div class="card-header"><h5>Recent</h5></div><div class="card-body"><table class="table table-sm">{% for o in my_orders %}<tr><td>#{{ o.id }}</td><td>{{ o.customer.name }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td>{{ o.status }}</td></tr>{% endfor %}</table></div></div></div></div></div></div></div>\n{% endblock %}'

templates['dashboard/customers.html'] = '{% extends "base.html" %}\n{% block title %}Customers{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_customers\') }}">Customers</a></nav></div>\n<div class="col-md-10 py-4"><h2>Customers</h2><table class="table"><thead><tr><th>Name</th><th>Phone</th><th>Area</th><th>Action</th></tr></thead><tbody>{% for c in customers %}<tr><td>{{ c.name }}</td><td>{{ c.phone_number }}</td><td>{{ c.area_of_residence or \'-\' }}</td><td><a href="{{ url_for(\'view_customer\', user_id=c.id) }}" class="btn btn-sm btn-primary">View</a></td></tr>{% endfor %}</tbody></table></div></div></div>\n{% endblock %}'

templates['dashboard/customer_detail.html'] = '{% extends "base.html" %}\n{% block title %}Customer{% endblock %}\n{% block content %}\n<div class="container py-4"><h2>{{ customer.name }}</h2><p>{{ customer.phone_number }} | {{ customer.area_of_residence or \'-\' }}</p><table class="table"><thead><tr><th>ID</th><th>Date</th><th>Total</th><th>Payment</th><th>Status</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.order_date.strftime(\'%Y-%m-%d\') }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td>{{ o.payment_status }}</td><td>{{ o.status }}</td></tr>{% endfor %}</tbody></table></div>\n{% endblock %}'

templates['dashboard/orders.html'] = '{% extends "base.html" %}\n{% block title %}Orders{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_orders\') }}">Orders</a></nav></div>\n<div class="col-md-10 py-4"><h2>Orders</h2><table class="table"><thead><tr><th>ID</th><th>Customer</th><th>Phone</th><th>Total</th><th>Status</th><th>Payment</th><th>Source</th><th>Action</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.customer.name }}</td><td>{{ o.customer.phone_number }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td>{{ o.status }}</td><td>{{ o.payment_status }}</td><td>{{ o.source }}</td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#upd{{ o.id }}">Update</button></td></tr>{% endfor %}</tbody></table></div></div></div>\n{% for o in orders %}<div class="modal fade" id="upd{{ o.id }}"><div class="modal-dialog"><div class="modal-content"><div class="modal-header" style="background:#1e40af;color:white;"><h5>#{{ o.id }}</h5></div><form action="{{ url_for(\'update_order\', order_id=o.id) }}" method="POST"><div class="modal-body"><select name="status" class="form-control"><option value="pending">Pending</option><option value="confirmed">Confirmed</option><option value="delivered">Delivered</option><option value="cancelled">Cancelled</option></select></div><div class="modal-footer"><button type="submit" class="btn btn-gold">Update</button></div></form></div></div></div>{% endfor %}\n{% endblock %}'

templates['dashboard/users.html'] = '{% extends "base.html" %}\n{% block title %}Staff{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'manage_users\') }}">Staff</a></nav></div>\n<div class="col-md-10 py-4"><div class="d-flex justify-content-between mb-4"><h2>Staff</h2><button class="btn btn-gold" data-bs-toggle="modal" data-bs-target="#addUser">+ Add</button></div>\n<table class="table"><thead><tr><th>Name</th><th>Username</th><th>Role</th><th>Actions</th></tr></thead><tbody>{% for u in staff %}<tr><td>{{ u.name }}</td><td>{{ u.username }}</td><td>{{ u.role }}</td><td>{% if u.id!=current_user.id %}<button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#editUser{{ u.id }}">Edit</button><a href="{{ url_for(\'delete_user\', user_id=u.id) }}" class="btn btn-sm btn-danger" onclick="return confirm(\'Delete?\')">Del</a>{% endif %}</td></tr>{% endfor %}</tbody></table></div></div></div>\n{% endblock %}'

templates['dashboard/meter_reading.html'] = '{% extends "base.html" %}\n{% block title %}Meter{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'meter_readings\') }}">Meter</a></nav></div>\n<div class="col-md-10 py-4"><h2>Meter</h2><button class="btn btn-gold mb-4" data-bs-toggle="modal" data-bs-target="#addReading">+ Add</button>\n<table class="table"><thead><tr><th>Date</th><th>Meter #</th><th>Reading</th><th>Liters</th></tr></thead><tbody>{% for r in readings %}<tr><td>{{ r.reading_date.strftime(\'%Y-%m-%d\') }}</td><td>{{ r.meter_number }}</td><td>{{ r.reading_value }}</td><td>{{ r.liters_produced }} L</td></tr>{% endfor %}</tbody></table></div></div></div>\n{% endblock %}'

templates['dashboard/reports.html'] = '{% extends "base.html" %}\n{% block title %}Reports{% endblock %}\n{% block content %}\n<div class="container-fluid"><div class="row"><div class="col-md-2 sidebar d-none d-md-block"><nav class="nav flex-column"><a class="nav-link" href="{{ url_for(\'admin_dashboard\') }}">Dashboard</a><a class="nav-link active" href="{{ url_for(\'reports\') }}">Reports</a></nav></div>\n<div class="col-md-10 py-4"><h2>Reports</h2>\n<div class="card mb-4"><div class="card-body"><form method="GET" class="row"><div class="col-md-4"><label>Start</label><input type="date" name="start_date" class="form-control" value="{{ start_date }}"></div><div class="col-md-4"><label>End</label><input type="date" name="end_date" class="form-control" value="{{ end_date }}"></div><div class="col-md-4"><label>&nbsp;</label><button type="submit" class="btn btn-primary w-100">Generate</button></div></form></div></div>\n<div class="row mb-4"><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Online</h6><div class="stats-number">KES {{ "%.0f"|format(online_sales) }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Walk-in</h6><div class="stats-number">KES {{ "%.0f"|format(total_walkins) }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Total</h6><div class="stats-number">KES {{ "%.0f"|format(total_revenue) }}</div></div></div></div><div class="col-md-3"><div class="card stats-card"><div class="card-body"><h6>Orders</h6><div class="stats-number">{{ total_orders }}</div></div></div></div></div>\n<a href="{{ url_for(\'reports_pdf\') }}" class="btn btn-danger"><i class="bi bi-file-pdf"></i> PDF</a></div></div></div>\n{% endblock %}'

templates['dashboard/field_clients.html'] = '{% extends "base.html" %}\n{% block title %}My Clients{% endblock %}\n{% block content %}\n<div class="container py-4"><h2>My Clients</h2><table class="table"><thead><tr><th>Name</th><th>Phone</th><th>Area</th></tr></thead><tbody>{% for c in clients %}<tr><td>{{ c.name }}</td><td>{{ c.phone_number }}</td><td>{{ c.area_of_residence or \'-\' }}</td></tr>{% endfor %}</tbody></table></div>\n{% endblock %}'

templates['dashboard/field_client_orders.html'] = '{% extends "base.html" %}\n{% block title %}Client Orders{% endblock %}\n{% block content %}\n<div class="container py-4"><h2>{{ client.name }}</h2><table class="table"><thead><tr><th>ID</th><th>Date</th><th>Total</th><th>Payment</th><th>Status</th></tr></thead><tbody>{% for o in orders %}<tr><td>#{{ o.id }}</td><td>{{ o.order_date.strftime(\'%Y-%m-%d\') }}</td><td>KES {{ "%.2f"|format(o.total_amount) }}</td><td>{{ o.payment_status }}</td><td>{{ o.status }}</td></tr>{% endfor %}</tbody></table></div>\n{% endblock %}'

for filename, content in templates.items():
    filepath = os.path.join("templates", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ All templates created!")

with open("static/css/style.css", "w") as f:
    f.write(""":root{--primary-blue:#1e40af;--secondary-blue:#3b82f6;--gold:#f59e0b;--light-gold:#fbbf24;--white:#ffffff}*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#f0f9ff,#e0f2fe);min-height:100vh}.navbar{background:linear-gradient(135deg,var(--primary-blue),#1e3a8a);padding:1rem 2rem}.navbar-brand{font-size:1.5rem;font-weight:700;color:#fff!important}.nav-link{color:var(--white)!important}.hero-section{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));color:#fff;padding:80px 0}.hero-title{font-size:3rem;font-weight:700;color:#fff}.card{border:none;border-radius:15px;box-shadow:0 4px 20px rgba(0,0,0,0.1);margin-bottom:20px;background:#fff}.card-header{color:#fff;border-radius:15px 15px 0 0!important;padding:1.5rem}.stats-card{border-left:4px solid var(--gold)}.stats-number{font-size:2rem;font-weight:700;color:var(--primary-blue)}.btn-primary{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));border:none;padding:10px 25px;border-radius:25px;color:white}.btn-gold{background:linear-gradient(135deg,var(--gold),var(--light-gold));border:none;padding:10px 25px;border-radius:25px;color:white;font-weight:700}.btn-success{background:linear-gradient(135deg,#059669,#10b981);border:none;border-radius:25px;color:white}.btn-danger{background:linear-gradient(135deg,#dc2626,#ef4444);border:none;border-radius:25px;color:white}.form-control{border-radius:25px;padding:12px 20px;border:2px solid #e5e7eb}.table{background:#fff;border-radius:10px;overflow:hidden}.table thead{background:linear-gradient(135deg,var(--primary-blue),var(--secondary-blue));color:#fff}.sidebar{background:linear-gradient(180deg,var(--primary-blue),#1e3a8a);min-height:100vh;padding-top:20px}.sidebar .nav-link{color:#fff;padding:15px 20px;margin:5px 0;border-radius:10px}.sidebar .nav-link:hover,.sidebar .nav-link.active{background:rgba(255,255,255,0.15);color:#fff}.footer{background:var(--primary-blue);color:#fff;padding:30px 0;margin-top:50px}@media(max-width:768px){.hero-title{font-size:2rem}.sidebar{min-height:auto}}""")
print("✅ style.css created!")

print("\n" + "="*50)
print("🎉 DONE! Run: pip install reportlab && python app.py")
print("Admin: admin / admin123")
print("="*50)
print("NEW: Salty/Borehole Water section added!")
print("  - shop/salty - for trucks, construction, farms, homes")
print("  - Separate product category with its own pricing")
print("  - Appears on homepage with dedicated section")
print("="*50)