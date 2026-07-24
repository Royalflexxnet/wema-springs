from flask import Flask, render_template, request, redirect, url_for, flash, make_response
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///wema_springs.db')
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
        if product.category == 'retail':
            return redirect(url_for('shop_retail', type=product.water_type))
        else:
            return redirect(url_for('shop_wholesale', type=product.water_type))
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

@app.route('/admin/inventory/delete/<int:record_id>')
@login_required
@permission_required('can_manage_inventory')
def delete_inventory(record_id):
    r = Inventory.query.get_or_404(record_id)
    p = Product.query.get(r.product_id)
    p.stock_quantity = p.stock_quantity - r.stock_in + r.stock_out
    db.session.delete(r)
    db.session.commit()
    flash('Record deleted.', 'success')
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

# ---- APP INIT (production safe) ----
with app.app_context():
    db.create_all()
    try:
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', name='Administrator', role='admin',
                         can_dashboard=True, can_edit_products=True, can_manage_inventory=True,
                         can_record_sales=True, can_view_orders=True, can_manage_orders=True,
                         can_manage_users=True, can_view_reports=True, can_view_customers=True,
                         can_meter_readings=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created (admin / admin123)")
        else:
            print("✅ Admin user already exists")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Could not create admin: {e}")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
