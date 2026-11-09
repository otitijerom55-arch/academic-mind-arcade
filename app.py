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
app.secret_key = os.environ.get('SECRET_KEY', 'ama-ultra-futuristic-key-2026-jerom-ultrajcentral')

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
    "trademark": "ULTRAJCENTRAL™",
    "brand_name": "ULTRAJCENTRAL™ Academic Mind Arcade",
    "short_brand": "ULTRAJCENTRAL™",
    "subtitle": "ULTRAJCENTRAL™ Interactive Mathematics & Physics Education System",
    "owner_name": "Otiti Jerom",
    "owner_email": "otitijerom55@gmail.com",
    "copyright_year": "2026",
    "version": "v5.0 ULTRAJCENTRAL™ Quantum Edition"
}

ADMIN_CREDENTIALS = {
    "email": "otitijerom55@gmail.com",
    "password": "Ultramaxjdistro-24-2009"
}

# Bilingual UI Translation Dictionaries (English & Kiswahili)
TRANSLATIONS = {
    "en": {
        "portal_title": "STUDENT PORTAL",
        "portal_subtitle": "ULTRAJCENTRAL™ Academic Mind Arcade Gateway",
        "email_label": "User / Admin Email",
        "email_placeholder": "student@example.com",
        "password_label": "Password Access Key",
        "password_placeholder": "••••••••••••••••",
        "login_button": "Authorize Session ➔",
        "create_account": "Create Student Account",
        "about_system": "About System & ULTRAJCENTRAL™",
        "switch_lang": "Badili lugha kuwa Kiswahili",
        "lang_name": "English",
        "invalid_credentials": "Invalid security credentials provided. Please re-enter your email and password.",
        "admin_welcome": "Welcome back, Founder Otiti Jerom. ULTRAJCENTRAL™ Full System Control Active.",
        "user_welcome": "Welcome back to ULTRAJCENTRAL™, {name}!",
        "reg_title": "STUDENT REGISTRATION",
        "reg_subtitle": "Join ULTRAJCENTRAL™ Math & Physics Learning Hub",
        "name_label": "Full Name",
        "name_placeholder": "Isaac Newton",
        "reg_button": "Unlock Learning Arcades ➔",
        "already_registered": "Already registered? Sign In",
        "session_ended": "Session successfully terminated.",
        "account_exists": "Account with this email already exists. Please log in.",
        "reg_success": "Registration Verified! Welcome to ULTRAJCENTRAL™ Math & Physics Hub."
    },
    "sw": {
        "portal_title": "TOVUTI YA WANAFUNZI",
        "portal_subtitle": "Lango la Masomo ya Hisabati na Fizikia la ULTRAJCENTRAL™",
        "email_label": "Barua Pepe ya Mtumiaji / Msimamizi",
        "email_placeholder": "mwanafunzi@example.com",
        "password_label": "Nenosiri la Kuingilia",
        "password_placeholder": "••••••••••••••••",
        "login_button": "Thibitisha na Ingia ➔",
        "create_account": "Fungua Akaunti ya Mwanafunzi",
        "about_system": "Kuhusu Mfumo na ULTRAJCENTRAL™",
        "switch_lang": "Switch language to English",
        "lang_name": "Kiswahili",
        "invalid_credentials": "Kitambulisho si sahihi. Tafadhali thibitisha barua pepe na nenosiri lako.",
        "admin_welcome": "Karibu tena, Mwanzilishi Otiti Jerom. Udhibiti Kamili wa Mfumo wa ULTRAJCENTRAL™ Umewashwa.",
        "user_welcome": "Karibu tena kwenye ULTRAJCENTRAL™, {name}!",
        "reg_title": "USAJILI WA MWANAFUNZI",
        "reg_subtitle": "Jiunge na Lango la Sayansi ya Hisabati na Fizikia la ULTRAJCENTRAL™",
        "name_label": "Jina Kamili",
        "name_placeholder": "Isaac Newton",
        "reg_button": "Fungua Milango ya Masomo ➔",
        "already_registered": "Je, una akaunti tayari? Ingia hapa",
        "session_ended": "Kipindi kimefungwa kwa ufanisi.",
        "account_exists": "Akaunti yenye barua pepe hii tayari ipo. Tafadhali ingia.",
        "reg_success": "Usajili Umethibitishwa! Karibu kwenye Jukwaa la ULTRAJCENTRAL™."
    }
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
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_global_data():
    current_lang = session.get('lang', 'en')
    if current_lang not in ('en', 'sw'):
        current_lang = 'en'
    t = TRANSLATIONS[current_lang]
    return dict(
        meta=PLATFORM_META, 
        is_admin=current_user.is_authenticated and current_user.is_admin, 
        user=current_user.email if current_user.is_authenticated else None,
        user_obj=current_user if current_user.is_authenticated else None,
        current_lang=current_lang,
        t=t
    )

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Security Restriction: ULTRAJCENTRAL™ Founder/Admin clearance required.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Language Switcher Route
@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in ('en', 'sw'):
        session['lang'] = lang
    next_url = request.args.get('next') or request.referrer or url_for('login')
    return redirect(next_url)

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
    lang_param = request.args.get('lang')
    if lang_param in ('en', 'sw'):
        session['lang'] = lang_param

    current_lang = session.get('lang', 'en')
    t = TRANSLATIONS.get(current_lang, TRANSLATIONS['en'])

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(email=email).first()

        # Hardcoded Admin Credentials Check & Automatic User Creation
        if email == ADMIN_CREDENTIALS['email'] and password == ADMIN_CREDENTIALS['password']:
            if not user:
                user = User(
                    email=email, 
                    name="Otiti Jerom (ULTRAJCENTRAL Founder)",
                    password_hash=generate_password_hash(password), 
                    is_admin=True
                )
                db.session.add(user)
                db.session.commit()
            login_user(user)
            flash(t['admin_welcome'], "success")
            return redirect(url_for('admin_dashboard'))
        
        elif user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(t['user_welcome'].format(name=user.name), "info")
            return redirect(url_for('dashboard'))
        else:
            flash(t['invalid_credentials'], "error")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    lang_param = request.args.get('lang')
    if lang_param in ('en', 'sw'):
        session['lang'] = lang_param

    current_lang = session.get('lang', 'en')
    t = TRANSLATIONS.get(current_lang, TRANSLATIONS['en'])

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        name = request.form.get('name', 'Student').strip()
        password = request.form.get('password', '').strip()
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash(t['account_exists'], "error")
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
        
        flash(t['reg_success'], "success")
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    current_lang = session.get('lang', 'en')
    t = TRANSLATIONS.get(current_lang, TRANSLATIONS['en'])
    logout_user()
    flash(t['session_ended'], "info")
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
            doc_name=doc_name or "ULTRAJCENTRAL_Module_Resource.pdf",
            video_url=video_url,
            description=description
        )
        db.session.add(new_resource)
        db.session.commit()
        
        flash(f"ULTRAJCENTRAL™ Module '{title}' deployed to live curriculum successfully.", "success")
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
    res = db.session.get(Resource, resource_id)
    if not res:
        flash("Resource not found.", "error")
        return redirect(url_for('admin_dashboard'))
    db.session.delete(res)
    db.session.commit()
    flash(f"ULTRAJCENTRAL™ Module '{res.title}' was removed.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/intellectual-property')
def intellectual_property():
    return render_template('intellectual_property.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Automatically Seed Initial Resources on First Launch
def seed_default_resources():
    if Resource.query.count() <= 3:
        Resource.query.delete()
        defaults = [
            # Physics - O-Level
            Resource(
                subject="Physics",
                level="O-Level (Secondary)",
                category_badge="Classical Mechanics",
                title="Newtonian Mechanics, Kinematics & Momentum",
                doc_name="ULTRAJCENTRAL_OLevel_Mechanics_and_Motion_Manual.pdf",
                video_url="https://www.youtube.com/embed/b1t41Q3xRM8",
                description="Comprehensive investigation of velocity, acceleration, Newton's three laws of motion, free body diagrams, and momentum conservation."
            ),
            # Physics - A-Level
            Resource(
                subject="Physics",
                level="A-Level (Upper Secondary)",
                category_badge="Electromagnetism",
                title="Electromagnetic Fields, Induction & Maxwell's Equations",
                doc_name="ULTRAJCENTRAL_ALevel_Electrodynamics_and_Flux.pdf",
                video_url="https://www.youtube.com/embed/geTtl_4fP8M",
                description="Faraday's Law of induction, Lenz's Law, magnetic field flux density, Lorentz force equations, and oscillatory RLC alternating circuits."
            ),
            # Math - A-Level
            Resource(
                subject="Mathematics",
                level="A-Level (Upper Secondary)",
                category_badge="Calculus & Analysis",
                title="Differential & Integral Calculus with Applications",
                doc_name="ULTRAJCENTRAL_ALevel_Pure_Calculus_Proofs.pdf",
                video_url="https://www.youtube.com/embed/WUvTyaaNkzM",
                description="Derivatives from first principles, chain rule, integration by parts, partial fractions, and differential equations in physical systems."
            ),
            # Math - O-Level
            Resource(
                subject="Mathematics",
                level="O-Level (Secondary)",
                category_badge="Algebra & Geometry",
                title="Quadratic Functions, Coordinate Geometry & Trigonometry",
                doc_name="ULTRAJCENTRAL_OLevel_Algebra_Trig_Handbook.pdf",
                video_url="https://www.youtube.com/embed/m72bXvXz1Zc",
                description="Parabolas, vertex form, quadratic formulas, trigonometric identities (sine, cosine, tangent rules), and coordinate geometry proofs."
            ),
            # Physics - Waves & Optics (A-Level)
            Resource(
                subject="Physics",
                level="A-Level (Upper Secondary)",
                category_badge="Waves & Optics",
                title="Wave Interference, Diffraction & Quantum Duality",
                doc_name="ULTRAJCENTRAL_ALevel_Wave_Optics_and_Photons.pdf",
                video_url="https://www.youtube.com/embed/Iuv6hY6zsd0",
                description="Young's double slit interference, diffraction gratings, standing waves, refractive indices, and introductory Planck-Einstein photon energy."
            ),
            # Primary Math & Logic
            Resource(
                subject="Mathematics",
                level="Primary (PLE)",
                category_badge="Foundational Math",
                title="Arithmetic Mastery, Fractions & Geometric Spatial Reasoning",
                doc_name="ULTRAJCENTRAL_PLE_Foundational_Math_2026.pdf",
                video_url="https://www.youtube.com/embed/N-7K84_Z5fE",
                description="Primary curriculum mastery: prime factorizations, percentages, ratios, area and perimeter calculations, and foundational scientific logic."
            ),
            # Primary Elementary Science
            Resource(
                subject="Physics",
                level="Primary (PLE)",
                category_badge="Introductory Physics",
                title="Simple Machines, Forces & States of Matter",
                doc_name="ULTRAJCENTRAL_PLE_Elementary_Physics_Guide.pdf",
                video_url="https://www.youtube.com/embed/fvOma4i-hDA",
                description="Exploration of levers, pulleys, inclined planes, gravity, friction, and heat expansion principles designed for emerging young scientists."
            ),
            # Math - Vectors & Matrices
            Resource(
                subject="Mathematics",
                level="A-Level (Upper Secondary)",
                category_badge="Linear Algebra",
                title="Vectors in 3D Space & Matrix Transformations",
                doc_name="ULTRAJCENTRAL_ALevel_Vector_Spaces_and_Matrices.pdf",
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
