from flask import Flask, render_template, request, redirect, url_for, flash, make_response
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
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
