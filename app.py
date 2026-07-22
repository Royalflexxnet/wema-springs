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
