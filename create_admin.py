from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    
    # Delete old admin if exists
    old = User.query.filter_by(username='admin').first()
    if old:
        db.session.delete(old)
        db.session.commit()
    
    # Create new admin with simple hash
    admin = User(
        username='admin',
        name='Administrator',
        role='admin',
        can_dashboard=True,
        can_edit_products=True,
        can_manage_inventory=True,
        can_record_sales=True,
        can_view_orders=True,
        can_manage_orders=True,
        can_manage_users=True,
        can_view_reports=True,
        can_view_customers=True,
        can_meter_readings=True
    )
    admin.password_hash = generate_password_hash('admin123', method='pbkdf2:sha256')
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin created successfully!")
    print("Username: admin")
    print("Password: admin123")
