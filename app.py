import os
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, session
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, 
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ama-ultra-futuristic-key-2026-jerom')

# Database Configuration (Supports Render/Railway Postgres or local SQLite fallback)
db_url = os.environ.get('DATABASE_URL', 'sqlite:///arcade.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Global Ownership Metadata & Protected Admin Credentials
PLATFORM_META = {
    "brand_name": "Academic Mind Arcade™",
    "owner_name": "Otiti Jerom",
    "owner_email": "otitijerom55@gmail.com",
    "copyright_year": "2026",
    "version": "v4.0 Enterprise Infinite"
}

ADMIN_CREDENTIALS = {
    "email": "otitijerom55@gmail.com",
    "password": "Ultramaxjdistro-24-2009"
}

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    doc_name = db.Column(db.String(150), nullable=False)
    video_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_global_data():
    return dict(
        meta=PLATFORM_META, 
        is_admin=current_user.is_authenticated and current_user.is_admin, 
        user=current_user.email if current_user.is_authenticated else None
    )

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Security Restriction: Founder/Admin clearance required.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/study-resources')
def study_resources():
    level_filter = request.args.get('level', 'all').lower()
    if level_filter != 'all':
        resources = Resource.query.filter(Resource.level.ilike(f"%{level_filter}%")).all()
    else:
        resources = Resource.query.all()
    return render_template('study_resources.html', resources=resources, current_level=level_filter)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(email=email).first()

        # Hardcoded Admin Credentials Check & Automatic User Creation
        if email == ADMIN_CREDENTIALS['email'] and password == ADMIN_CREDENTIALS['password']:
            if not user:
                user = User(
                    email=email, 
                    password_hash=generate_password_hash(password), 
                    is_admin=True
                )
                db.session.add(user)
                db.session.commit()
            login_user(user)
            flash("Welcome back, Founder Otiti Jerom. Full System Control Active.", "success")
            return redirect(url_for('admin_dashboard'))
        
        elif user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Authentication Successful. Accessing Learning Arcade.", "info")
            return redirect(url_for('study_resources'))
        else:
            flash("Invalid security credentials provided.", "error")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Account with this email already exists.", "error")
            return redirect(url_for('login'))
            
        is_admin = (email == ADMIN_CREDENTIALS['email'])
        new_user = User(
            email=email, 
            password_hash=generate_password_hash(password), 
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        
        flash("Registration Verified. Arcades Unlocked.", "success")
        return redirect(url_for('study_resources'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Session successfully terminated.", "info")
    return redirect(url_for('dashboard'))

@app.route('/admin-control', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    if request.method == 'POST':
        title = request.form.get('title')
        level = request.form.get('level')
        video_url = request.form.get('video_url')
        doc_name = request.form.get('doc_name')
        description = request.form.get('description')
        
        new_resource = Resource(
            level=level,
            title=title,
            doc_name=doc_name or "Official_Module_Resource.pdf",
            video_url=video_url,
            description=description
        )
        db.session.add(new_resource)
        db.session.commit()
        
        flash(f"Resource '{title}' deployed to live arcade successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    resources = Resource.query.all()
    return render_template('admin.html', resources=resources)

@app.route('/intellectual-property')
def intellectual_property():
    return render_template('intellectual_property.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Automatically Seed Initial Resources on First Launch
def seed_default_resources():
    if Resource.query.count() == 0:
        defaults = [
            Resource(
                level="Primary (PLE)",
                title="Logic & Elemental Science Modules",
                doc_name="PLE_Foundational_Logic_2026.pdf",
                video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
                description="Primary-level core logic, fundamental problem solving, and introductory natural sciences."
            ),
            Resource(
                level="O-Level (Secondary)",
                title="Physics & Applied Mechanics Core",
                doc_name="OLevel_Physics_Lab_Manual.pdf",
                video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
                description="Lower secondary practical mechanics, velocity equations, and chemical interactions."
            ),
            Resource(
                level="A-Level (Upper Secondary)",
                title="Pure Mathematics & Vector Calculus",
                doc_name="ALevel_Advanced_Calculus.pdf",
                video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
                description="Upper secondary differential calculus, multi-dimensional vector systems, and proofs."
            )
        ]
        db.session.bulk_save_objects(defaults)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_default_resources()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)