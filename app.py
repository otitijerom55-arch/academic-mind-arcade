import os
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, session, jsonify
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
    "subtitle": "Interactive Math & Physics Learning Engine",
    "owner_name": "Otiti Jerom",
    "owner_email": "otitijerom55@gmail.com",
    "copyright_year": "2026",
    "version": "v4.5 STEM Quantum Edition"
}

ADMIN_CREDENTIALS = {
    "email": "otitijerom55@gmail.com",
    "password": "Ultramaxjdistro-24-2009"
}

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(100), default="STEM Explorer")
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    quiz_scores = db.relationship('QuizAttempt', backref='user', lazy=True)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50), default="Physics", nullable=False) # Math, Physics, Integrated STEM
    level = db.Column(db.String(50), nullable=False)                      # Primary (PLE), O-Level, A-Level
    title = db.Column(db.String(150), nullable=False)
    doc_name = db.Column(db.String(150), nullable=False)
    video_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_badge = db.Column(db.String(50), default="Mechanics")

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_global_data():
    return dict(
        meta=PLATFORM_META, 
        is_admin=current_user.is_authenticated and current_user.is_admin, 
        user=current_user.email if current_user.is_authenticated else None,
        user_obj=current_user if current_user.is_authenticated else None
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
    featured_resources = Resource.query.limit(4).all()
    total_resources = Resource.query.count()
    return render_template('dashboard.html', featured_resources=featured_resources, total_resources=total_resources)

@app.route('/study-resources')
def study_resources():
    level_filter = request.args.get('level', 'all').lower()
    subject_filter = request.args.get('subject', 'all').lower()
    
    query = Resource.query
    if level_filter != 'all':
        query = query.filter(Resource.level.ilike(f"%{level_filter}%"))
    if subject_filter != 'all':
        query = query.filter(Resource.subject.ilike(f"%{subject_filter}%"))
        
    resources = query.all()
    return render_template(
        'study_resources.html', 
        resources=resources, 
        current_level=level_filter,
        current_subject=subject_filter
    )

@app.route('/simulations')
def simulations():
    sim_type = request.args.get('sim', 'projectile')
    return render_template('simulations.html', active_sim=sim_type)

@app.route('/formulas')
def formulas():
    return render_template('formulas.html')

@app.route('/calculators')
def calculators():
    return render_template('calculators.html')

@app.route('/quiz')
def quiz():
    attempts = []
    if current_user.is_authenticated:
        attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.created_at.desc()).limit(10).all()
    return render_template('quiz.html', attempts=attempts)

@app.route('/api/record-quiz', methods=['POST'])
def record_quiz():
    if not current_user.is_authenticated:
        return jsonify({"status": "guest", "message": "Result calculated (Sign in to record in student portfolio)"})
    
    data = request.get_json() or {}
    subject = data.get('subject', 'General STEM')
    score = int(data.get('score', 0))
    total = int(data.get('total', 5))
    percentage = round((score / total) * 100, 1) if total > 0 else 0
    
    attempt = QuizAttempt(
        user_id=current_user.id,
        subject=subject,
        score=score,
        total=total,
        percentage=percentage
    )
    db.session.add(attempt)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "score": score,
        "total": total,
        "percentage": percentage
    })

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
                    name="Otiti Jerom (Founder)",
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
            flash(f"Welcome back to Academic Mind Arcade, {user.name}!", "info")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid security credentials provided. Please re-enter your email and password.", "error")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        name = request.form.get('name', 'Student').strip()
        password = request.form.get('password', '').strip()
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Account with this email already exists. Please log in.", "error")
            return redirect(url_for('login'))
            
        is_admin = (email == ADMIN_CREDENTIALS['email'])
        new_user = User(
            email=email, 
            name=name or "STEM Student",
            password_hash=generate_password_hash(password), 
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        
        flash("Registration Verified! Welcome to Academic Mind Arcade Math & Physics Hub.", "success")
        return redirect(url_for('dashboard'))
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
        subject = request.form.get('subject', 'Physics')
        level = request.form.get('level')
        category_badge = request.form.get('category_badge', 'Mechanics')
        video_url = request.form.get('video_url')
        doc_name = request.form.get('doc_name')
        description = request.form.get('description')
        
        new_resource = Resource(
            subject=subject,
            level=level,
            title=title,
            category_badge=category_badge,
            doc_name=doc_name or "Official_Module_Resource.pdf",
            video_url=video_url,
            description=description
        )
        db.session.add(new_resource)
        db.session.commit()
        
        flash(f"Resource '{title}' deployed to live curriculum successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    resources = Resource.query.all()
    users_count = User.query.count()
    quizzes_count = QuizAttempt.query.count()
    return render_template(
        'admin.html', 
        resources=resources, 
        users_count=users_count, 
        quizzes_count=quizzes_count
    )

@app.route('/admin/delete-resource/<int:resource_id>', methods=['POST'])
@admin_required
def delete_resource(resource_id):
    res = Resource.query.get_or_404(resource_id)
    db.session.delete(res)
    db.session.commit()
    flash(f"Module '{res.title}' was removed.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/intellectual-property')
def intellectual_property():
    return render_template('intellectual_property.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Automatically Seed Initial Resources on First Launch
def seed_default_resources():
    # If table is empty or has old generic seeds, refresh with rich math & physics curriculum
    if Resource.query.count() <= 3:
        Resource.query.delete() # refresh cleanly
        defaults = [
            # Physics - O-Level
            Resource(
                subject="Physics",
                level="O-Level (Secondary)",
                category_badge="Classical Mechanics",
                title="Newtonian Mechanics, Kinematics & Momentum",
                doc_name="OLevel_Mechanics_and_Motion_Manual.pdf",
                video_url="https://www.youtube.com/embed/b1t41Q3xRM8",
                description="Comprehensive investigation of velocity, acceleration, Newton's three laws of motion, free body diagrams, and momentum conservation."
            ),
            # Physics - A-Level
            Resource(
                subject="Physics",
                level="A-Level (Upper Secondary)",
                category_badge="Electromagnetism",
                title="Electromagnetic Fields, Induction & Maxwell's Equations",
                doc_name="ALevel_Electrodynamics_and_Flux.pdf",
                video_url="https://www.youtube.com/embed/geTtl_4fP8M",
                description="Faraday's Law of induction, Lenz's Law, magnetic field flux density, Lorentz force equations, and oscillatory RLC alternating circuits."
            ),
            # Math - A-Level
            Resource(
                subject="Mathematics",
                level="A-Level (Upper Secondary)",
                category_badge="Calculus & Analysis",
                title="Differential & Integral Calculus with Applications",
                doc_name="ALevel_Pure_Calculus_Proofs.pdf",
                video_url="https://www.youtube.com/embed/WUvTyaaNkzM",
                description="Derivatives from first principles, chain rule, integration by parts, partial fractions, and differential equations in physical systems."
            ),
            # Math - O-Level
            Resource(
                subject="Mathematics",
                level="O-Level (Secondary)",
                category_badge="Algebra & Geometry",
                title="Quadratic Functions, Coordinate Geometry & Trigonometry",
                doc_name="OLevel_Algebra_Trig_Handbook.pdf",
                video_url="https://www.youtube.com/embed/m72bXvXz1Zc",
                description="Parabolas, vertex form, quadratic formulas, trigonometric identities (sine, cosine, tangent rules), and coordinate geometry proofs."
            ),
            # Physics - Waves & Optics (A-Level)
            Resource(
                subject="Physics",
                level="A-Level (Upper Secondary)",
                category_badge="Waves & Optics",
                title="Wave Interference, Diffraction & Quantum Duality",
                doc_name="ALevel_Wave_Optics_and_Photons.pdf",
                video_url="https://www.youtube.com/embed/Iuv6hY6zsd0",
                description="Young's double slit interference, diffraction gratings, standing waves, refractive indices, and introductory Planck-Einstein photon energy."
            ),
            # Primary Math & Logic
            Resource(
                subject="Mathematics",
                level="Primary (PLE)",
                category_badge="Foundational Math",
                title="Arithmetic Mastery, Fractions & Geometric Spatial Reasoning",
                doc_name="PLE_Foundational_Math_2026.pdf",
                video_url="https://www.youtube.com/embed/N-7K84_Z5fE",
                description="Primary curriculum mastery: prime factorizations, percentages, ratios, area and perimeter calculations, and foundational scientific logic."
            ),
            # Primary Elementary Science
            Resource(
                subject="Physics",
                level="Primary (PLE)",
                category_badge="Introductory Physics",
                title="Simple Machines, Forces & States of Matter",
                doc_name="PLE_Elementary_Physics_Guide.pdf",
                video_url="https://www.youtube.com/embed/fvOma4i-hDA",
                description="Exploration of levers, pulleys, inclined planes, gravity, friction, and heat expansion principles designed for emerging young scientists."
            ),
            # Math - Vectors & Matrices
            Resource(
                subject="Mathematics",
                level="A-Level (Upper Secondary)",
                category_badge="Linear Algebra",
                title="Vectors in 3D Space & Matrix Transformations",
                doc_name="ALevel_Vector_Spaces_and_Matrices.pdf",
                video_url="https://www.youtube.com/embed/k7RM-ot2NWY",
                description="Dot products, cross products, planes in 3D Euclidean space, determinant calculations, and eigenvalues in mechanical transformations."
            )
        ]
        db.session.bulk_save_objects(defaults)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_default_resources()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
