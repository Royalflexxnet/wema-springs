import os
import tempfile
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import json
from functools import wraps
import secrets

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Database Configuration
# Use PostgreSQL in production, SQLite for local development
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render provides DATABASE_URL with 'postgres://' prefix, SQLAlchemy requires 'postgresql://'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to SQLite for local development
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ============================================
# DATABASE MODELS
# ============================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    account_number = db.Column(db.String(10), unique=True, nullable=False)
    account_balance = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    transactions_sent = db.relationship('Transaction', foreign_keys='Transaction.sender_id', backref='sender', lazy=True)
    transactions_received = db.relationship('Transaction', foreign_keys='Transaction.receiver_id', backref='receiver', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    transaction_type = db.Column(db.String(20), default='transfer')
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reference = db.Column(db.String(50), unique=True)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'

class SavingsPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    interest_rate = db.Column(db.Float, default=0.0)
    
    user = db.relationship('User', backref=db.backref('savings_plans', lazy=True))
    
    def __repr__(self):
        return f'<SavingsPlan {self.plan_name}>'

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    interest_rate = db.Column(db.Float, default=5.0)
    tenure_months = db.Column(db.Integer, default=12)
    approved_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('loan_applications', lazy=True))
    
    def __repr__(self):
        return f'<LoanApplication {self.id}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_type = db.Column(db.String(20), default='general')
    
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

# ============================================
# ADMIN REQUIRED DECORATOR
# ============================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# USER LOADER
# ============================================

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        
        # Validation
        if not all([username, email, password, full_name]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        # Check if user exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        # Generate account number
        account_number = str(secrets.randbelow(9000000000) + 1000000000)[:10]
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            account_number=account_number,
            account_balance=0.0
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Registration successful! Your account number is: {account_number}', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent transactions
    recent_transactions = Transaction.query.filter(
        (Transaction.sender_id == current_user.id) | 
        (Transaction.receiver_id == current_user.id)
    ).order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Get savings summary
    savings_total = db.session.query(db.func.sum(SavingsPlan.current_amount)).filter(
        SavingsPlan.user_id == current_user.id,
        SavingsPlan.status == 'active'
    ).scalar() or 0.0
    
    # Get loan summary
    loan_total = db.session.query(db.func.sum(LoanApplication.amount)).filter(
        LoanApplication.user_id == current_user.id,
        LoanApplication.status.in_(['pending', 'approved'])
    ).scalar() or 0.0
    
    # Get notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         recent_transactions=recent_transactions,
                         savings_total=savings_total,
                         loan_total=loan_total,
                         notifications=notifications)

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        recipient_account = request.form.get('recipient_account')
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description', '')
        
        # Validation
        if amount <= 0:
            flash('Amount must be greater than 0', 'danger')
            return render_template('transfer.html')
        
        if amount > current_user.account_balance:
            flash('Insufficient balance', 'danger')
            return render_template('transfer.html')
        
        # Find recipient
        recipient = User.query.filter_by(account_number=recipient_account).first()
        if not recipient:
            flash('Recipient account not found', 'danger')
            return render_template('transfer.html')
        
        if recipient.id == current_user.id:
            flash('Cannot transfer to your own account', 'danger')
            return render_template('transfer.html')
        
        # Perform transfer
        transaction_id = f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(10000):04d}"
        reference = f"REF{secrets.token_hex(8).upper()}"
        
        try:
            # Deduct from sender
            current_user.account_balance -= amount
            
            # Add to recipient
            recipient.account_balance += amount
            
            # Create transaction record
            transaction = Transaction(
                transaction_id=transaction_id,
                sender_id=current_user.id,
                receiver_id=recipient.id,
                amount=amount,
                description=description,
                transaction_type='transfer',
                reference=reference
            )
            
            db.session.add(transaction)
            
            # Create notifications
            sender_notification = Notification(
                user_id=current_user.id,
                title='Transfer Successful',
                message=f'You sent ₦{amount:,.2f} to {recipient.full_name} ({recipient.account_number})',
                notification_type='transaction'
            )
            
            receiver_notification = Notification(
                user_id=recipient.id,
                title='Funds Received',
                message=f'You received ₦{amount:,.2f} from {current_user.full_name} ({current_user.account_number})',
                notification_type='transaction'
            )
            
            db.session.add(sender_notification)
            db.session.add(receiver_notification)
            
            db.session.commit()
            
            flash(f'Transfer successful! ₦{amount:,.2f} sent to {recipient.full_name}', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Transfer failed. Please try again.', 'danger')
            print(f"Transfer error: {e}")
    
    return render_template('transfer.html')

@app.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    transactions = Transaction.query.filter(
        (Transaction.sender_id == current_user.id) | 
        (Transaction.receiver_id == current_user.id)
    ).order_by(Transaction.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('transactions.html', transactions=transactions)

@app.route('/savings', methods=['GET', 'POST'])
@login_required
def savings():
    if request.method == 'POST':
        plan_name = request.form.get('plan_name')
        target_amount = float(request.form.get('target_amount', 0))
        end_date_str = request.form.get('end_date')
        
        if not plan_name or target_amount <= 0:
            flash('Please provide valid plan details', 'danger')
            return redirect(url_for('savings'))
        
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        savings_plan = SavingsPlan(
            user_id=current_user.id,
            plan_name=plan_name,
            target_amount=target_amount,
            end_date=end_date,
            interest_rate=2.5
        )
        
        db.session.add(savings_plan)
        db.session.commit()
        
        flash(f'Savings plan "{plan_name}" created successfully!', 'success')
        return redirect(url_for('savings'))
    
    plans = SavingsPlan.query.filter_by(user_id=current_user.id).order_by(SavingsPlan.created_at.desc()).all()
    return render_template('savings.html', plans=plans)

@app.route('/savings/contribute/<int:plan_id>', methods=['POST'])
@login_required
def contribute_savings(plan_id):
    plan = SavingsPlan.query.get_or_404(plan_id)
    
    if plan.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('savings'))
    
    amount = float(request.form.get('amount', 0))
    
    if amount <= 0:
        flash('Amount must be greater than 0', 'danger')
        return redirect(url_for('savings'))
    
    if amount > current_user.account_balance:
        flash('Insufficient balance', 'danger')
        return redirect(url_for('savings'))
    
    try:
        # Deduct from account
        current_user.account_balance -= amount
        plan.current_amount += amount
        
        if plan.current_amount >= plan.target_amount:
            plan.status = 'completed'
        
        # Create transaction record
        transaction_id = f"SAV{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(10000):04d}"
        transaction = Transaction(
            transaction_id=transaction_id,
            sender_id=current_user.id,
            receiver_id=current_user.id,
            amount=amount,
            description=f'Savings contribution - {plan.plan_name}',
            transaction_type='savings'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Successfully contributed ₦{amount:,.2f} to {plan.plan_name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Contribution failed. Please try again.', 'danger')
        print(f"Savings contribution error: {e}")
    
    return redirect(url_for('savings'))

@app.route('/loan', methods=['GET', 'POST'])
@login_required
def loan():
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        purpose = request.form.get('purpose')
        tenure_months = int(request.form.get('tenure_months', 12))
        
        if amount <= 0 or not purpose:
            flash('Please provide valid loan details', 'danger')
            return redirect(url_for('loan'))
        
        # Check if user has pending loans
        pending_loan = LoanApplication.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()
        
        if pending_loan:
            flash('You have a pending loan application', 'warning')
            return redirect(url_for('loan'))
        
        loan_app = LoanApplication(
            user_id=current_user.id,
            amount=amount,
            purpose=purpose,
            tenure_months=tenure_months,
            interest_rate=5.0
        )
        
        db.session.add(loan_app)
        
        # Notification for admin (if we had admin, but we'll just log it)
        notification = Notification(
            user_id=current_user.id,
            title='Loan Application Submitted',
            message=f'Your loan application of ₦{amount:,.2f} has been submitted for review',
            notification_type='loan'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        flash('Loan application submitted successfully! You will be notified of the decision.', 'success')
        return redirect(url_for('dashboard'))
    
    loans = LoanApplication.query.filter_by(user_id=current_user.id).order_by(LoanApplication.created_at.desc()).all()
    return render_template('loan.html', loans=loans)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.phone_number = request.form.get('phone_number', current_user.phone_number)
        current_user.email = request.form.get('email', current_user.email)
        
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password:
            if new_password == confirm_password:
                current_user.set_password(new_password)
                flash('Password updated successfully!', 'success')
            else:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('profile'))
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/statement')
@login_required
def statement():
    """Generate statement of account as PDF"""
    from io import BytesIO
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date and not end_date:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.utcnow() - timedelta(days=30)
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.utcnow()
    
    transactions = Transaction.query.filter(
        ((Transaction.sender_id == current_user.id) | (Transaction.receiver_id == current_user.id)),
        Transaction.created_at.between(start_date, end_date)
    ).order_by(Transaction.created_at).all()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph('Wema Springs Bank', title_style))
    elements.append(Paragraph('Statement of Account', styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Account Information
    info_data = [
        ['Account Holder:', current_user.full_name],
        ['Account Number:', current_user.account_number],
        ['Period:', f'{start_date.strftime("%d-%m-%Y")} to {end_date.strftime("%d-%m-%Y")}'],
        ['Statement Date:', datetime.utcnow().strftime('%d-%m-%Y %H:%M')]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOLD', (0, 0), (0, -1), True),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # Transactions Table
    if transactions:
        table_data = [['Date', 'Description', 'Debit (₦)', 'Credit (₦)', 'Balance']]
        running_balance = 0
        
        # Get initial balance before the start date
        initial_transactions = Transaction.query.filter(
            ((Transaction.sender_id == current_user.id) | (Transaction.receiver_id == current_user.id)),
            Transaction.created_at < start_date
        ).all()
        
        for t in initial_transactions:
            if t.sender_id == current_user.id:
                running_balance -= t.amount
            else:
                running_balance += t.amount
        
        for t in transactions:
            if t.sender_id == current_user.id:
                debit = t.amount
                credit = 0
                running_balance -= t.amount
            else:
                debit = 0
                credit = t.amount
                running_balance += t.amount
            
            description = t.description or 'Transfer'
            if t.transaction_type == 'savings':
                description = f'Savings: {description}'
            
            table_data.append([
                t.created_at.strftime('%d-%m-%Y %H:%M'),
                description,
                f'{debit:,.2f}' if debit > 0 else '',
                f'{credit:,.2f}' if credit > 0 else '',
                f'{running_balance:,.2f}'
            ])
        
        # Add final balance
        table_data.append([
            '',
            'CLOSING BALANCE',
            '',
            '',
            f'{running_balance:,.2f}'
        ])
        
        transaction_table = Table(table_data, colWidths=[1.5*inch, 2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        transaction_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('BOLD', (0, -1), (-1, -1), True),
        ]))
        elements.append(transaction_table)
    else:
        elements.append(Paragraph('No transactions found for this period.', styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'statement_{current_user.account_number}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf',
        mimetype='application/pdf'
    )

@app.route('/api/balance')
@login_required
def api_balance():
    return jsonify({
        'balance': current_user.account_balance,
        'account_number': current_user.account_number,
        'full_name': current_user.full_name
    })

@app.route('/api/transactions')
@login_required
def api_transactions():
    limit = request.args.get('limit', 10, type=int)
    transactions = Transaction.query.filter(
        (Transaction.sender_id == current_user.id) | 
        (Transaction.receiver_id == current_user.id)
    ).order_by(Transaction.created_at.desc()).limit(limit).all()
    
    return jsonify([{
        'id': t.transaction_id,
        'amount': t.amount,
        'type': t.transaction_type,
        'description': t.description,
        'date': t.created_at.isoformat(),
        'status': t.status
    } for t in transactions])

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/loans')
@login_required
@admin_required
def admin_loans():
    loans = LoanApplication.query.order_by(LoanApplication.created_at.desc()).all()
    return render_template('admin/loans.html', loans=loans)

@app.route('/admin/loan/approve/<int:loan_id>', methods=['POST'])
@login_required
@admin_required
def admin_approve_loan(loan_id):
    loan = LoanApplication.query.get_or_404(loan_id)
    
    if loan.status != 'pending':
        flash('This loan has already been processed', 'warning')
        return redirect(url_for('admin_loans'))
    
    try:
        loan.status = 'approved'
        loan.approved_date = datetime.utcnow()
        
        # Credit the user's account
        user = User.query.get(loan.user_id)
        user.account_balance += loan.amount
        
        # Create notification
        notification = Notification(
            user_id=user.id,
            title='Loan Approved',
            message=f'Your loan application of ₦{loan.amount:,.2f} has been approved!',
            notification_type='loan'
        )
        db.session.add(notification)
        
        db.session.commit()
        flash(f'Loan approved! {user.full_name} has been credited with ₦{loan.amount:,.2f}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to approve loan. Please try again.', 'danger')
        print(f"Loan approval error: {e}")
    
    return redirect(url_for('admin_loans'))

@app.route('/admin/loan/reject/<int:loan_id>', methods=['POST'])
@login_required
@admin_required
def admin_reject_loan(loan_id):
    loan = LoanApplication.query.get_or_404(loan_id)
    
    if loan.status != 'pending':
        flash('This loan has already been processed', 'warning')
        return redirect(url_for('admin_loans'))
    
    try:
        loan.status = 'rejected'
        
        # Create notification
        notification = Notification(
            user_id=loan.user_id,
            title='Loan Application Rejected',
            message='We regret to inform you that your loan application has been rejected.',
            notification_type='loan'
        )
        db.session.add(notification)
        
        db.session.commit()
        flash('Loan application rejected', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to reject loan. Please try again.', 'danger')
        print(f"Loan rejection error: {e}")
    
    return redirect(url_for('admin_loans'))

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ============================================
# CONTEXT PROCESSORS
# ============================================

@app.context_processor
def utility_processor():
    def format_currency(amount):
        return f'₦{amount:,.2f}'
    
    def format_datetime(dt):
        return dt.strftime('%d-%m-%Y %H:%M') if dt else ''
    
    return dict(format_currency=format_currency, format_datetime=format_datetime)

# ============================================
# CREATE TABLES AND ADMIN USER
# ============================================

with app.app_context():
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@wemasprings.com',
            full_name='System Administrator',
            account_number='0000000001',
            account_balance=0.0,
            is_admin=True
        )
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        db.session.commit()
        print('Admin user created!')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
