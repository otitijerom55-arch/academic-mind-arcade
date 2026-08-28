import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

db_url = os.environ.get("DATABASE_URL", "sqlite:///academic_hub_v3.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "academic-hub-v3-secret")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# --- MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    student_class = db.Column(db.String(50), default="Senior One")
    security_question = db.Column(db.String(200), nullable=False)
    security_answer_hash = db.Column(db.String(200), nullable=False)
    has_configured_timetable = db.Column(db.Boolean, default=False)
    
    scores = db.relationship('Score', backref='owner', lazy=True, cascade="all, delete-orphan")
    profile = db.relationship('LearnerProfile', backref='owner', uselist=False, cascade="all, delete-orphan")

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)
    term = db.Column(db.String(50), nullable=False)
    score_obtained = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False, default=100.0)
    percentage = db.Column(db.Float, nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)

class LearnerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chronotype = db.Column(db.String(50), default="Morning Peak")
    focus_span = db.Column(db.Integer, default=45)
    weakest_subject = db.Column(db.String(100), default="Mathematics")
    morning_start = db.Column(db.String(10), default="06:00")
    evening_start = db.Column(db.String(10), default="17:30")
    weekend_start = db.Column(db.String(10), default="09:00")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

NLSC_SUBJECTS = [
    "Mathematics", "English Language", "Physics", "Chemistry", "Biology",
    "Geography", "History & Political Education", "Religious Education (CRE/IRE)",
    "Entrepreneurship", "Information & Communication Technology (ICT)",
    "Agriculture", "Performing Arts", "Art & Design", "Nutrition & Food Technology",
    "Physical Education", "Luganda / Local Language", "French", "Swahili"
]

CLASSES = ["Senior One", "Senior Two", "Senior Three", "Senior Four", "Senior Five", "Senior Six"]

def generate_moral_boost_and_advice(avg_score):
    if avg_score >= 80:
        return {"title": "🌟 Exceptional Mastery!", "message": "You are performing at an elite level across your subjects.", "advice": "Deepen your expertise by helping peers and attempting advanced Olympiad-style questions.", "badge_color": "bg-emerald-500 text-white"}
    elif avg_score >= 65:
        return {"title": "📈 Strong Performance!", "message": "Solid understanding demonstrated in both Exams & AOIs.", "advice": "Focus on high-yield subtopics in your target subject to breach the 80%+ threshold.", "badge_color": "bg-indigo-500 text-white"}
    elif avg_score >= 50:
        return {"title": "⚡ Steady Progress!", "message": "Consistency will turn your effort into high marks.", "advice": "Use active recall flashcards during your scheduled study blocks.", "badge_color": "bg-amber-500 text-white"}
    else:
        return {"title": "💪 High Growth Potential!", "message": "Setbacks are stepping stones to success.", "advice": "Review basic concepts in 15-minute daily intervals before moving to past paper problems.", "badge_color": "bg-rose-500 text-white"}

# --- ROUTES ---

@app.route("/")
@login_required
def index():
    scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.date_recorded.desc()).all()
    profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = LearnerProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    total_entries = len(scores)
    avg_percentage = round(sum(s.percentage for s in scores) / total_entries, 1) if total_entries > 0 else 0
    moral_booster = generate_moral_boost_and_advice(avg_percentage)
    
    return render_template(
        "dashboard.html",
        scores=scores,
        avg_percentage=avg_percentage,
        total_entries=total_entries,
        moral_booster=moral_booster,
        profile=profile,
        nlsc_subjects=NLSC_SUBJECTS,
        classes=CLASSES
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        student_class = request.form.get("student_class", "Senior One")
        sec_question = request.form.get("security_question", "").strip()
        sec_answer = request.form.get("security_answer", "").strip().lower()
        
        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash("Username or Email already exists.", "warning")
            return redirect(url_for("register"))
            
        hashed_pw = generate_password_hash(password, method="scrypt")
        hashed_ans = generate_password_hash(sec_answer, method="scrypt")
        
        new_user = User(
            username=username, email=email, password_hash=hashed_pw,
            student_class=student_class, security_question=sec_question,
            security_answer_hash=hashed_ans, has_configured_timetable=False
        )
        db.session.add(new_user)
        db.session.commit()
        
        db.session.add(LearnerProfile(user_id=new_user.id))
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for("index"))
    return render_template("register.html", classes=CLASSES)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    user = None
    if request.method == "POST":
        step = request.form.get("step")
        if step == "find_account":
            email = request.form.get("email", "").strip()
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("No account found with that email address.", "danger")
                return render_template("forgot_password.html", user=None)
            return render_template("forgot_password.html", user=user)
            
        elif step == "reset_password":
            user_id = request.form.get("user_id")
            user = User.query.get(user_id)
            sec_answer = request.form.get("security_answer", "").strip().lower()
            new_password = request.form.get("new_password", "")
            
            if user and check_password_hash(user.security_answer_hash, sec_answer):
                user.password_hash = generate_password_hash(new_password, method="scrypt")
                db.session.commit()
                flash("Password reset successfully! You can now log in.", "success")
                return redirect(url_for("login"))
            else:
                flash("Incorrect security answer.", "danger")
                return render_template("forgot_password.html", user=user)
                
    return render_template("forgot_password.html", user=user)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/save-timetable-settings", methods=["POST"])
@login_required
def save_timetable_settings():
    q1_energy = request.form.get("q1_energy", "Morning")
    q2_focus = int(request.form.get("q2_focus", "45"))
    weakest_sub = request.form.get("weakest_subject", "Mathematics").title()
    m_time = request.form.get("morning_start", "06:00")
    e_time = request.form.get("evening_start", "17:30")
    w_time = request.form.get("weekend_start", "09:00")
    
    profile = LearnerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = LearnerProfile(user_id=current_user.id)
        db.session.add(profile)
        
    profile.chronotype = "Morning Peak" if q1_energy == "Morning" else "Evening Peak"
    profile.focus_span = q2_focus
    profile.weakest_subject = weakest_sub
    profile.morning_start = m_time
    profile.evening_start = e_time
    profile.weekend_start = w_time
    
    current_user.has_configured_timetable = True
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/add-score", methods=["POST"])
@login_required
def add_score():
    subject_choice = request.form.get("subject_choice")
    custom_subject = request.form.get("custom_subject", "").strip().title()
    subject = custom_subject if subject_choice == "Custom" and custom_subject else subject_choice
    
    assessment_type = request.form.get("assessment_type", "Exam")
    term = request.form.get("term", "Term 1")
    score_obtained = float(request.form.get("score_obtained", 0))
    max_score = float(request.form.get("max_score", 100))
    
    percentage = round((score_obtained / max_score) * 100, 2) if max_score > 0 else 0
    
    new_entry = Score(
        user_id=current_user.id, subject=subject, assessment_type=assessment_type,
        term=term, score_obtained=score_obtained, max_score=max_score, percentage=percentage
    )
    db.session.add(new_entry)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/delete-score/<int:score_id>")
@login_required
def delete_score(score_id):
    score = Score.query.filter_by(id=score_id, user_id=current_user.id).first_or_404()
    db.session.delete(score)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/api/chart-data")
@login_required
def chart_data():
    scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.date_recorded.asc()).all()
    
    trend_labels = [f"{s.subject} ({s.assessment_type})" for s in scores]
    trend_percentages = [s.percentage for s in scores]
    
    aoi_scores = [s.percentage for s in scores if s.assessment_type == 'AOI']
    exam_scores = [s.percentage for s in scores if s.assessment_type == 'Exam']
    
    avg_aoi = round(sum(aoi_scores)/len(aoi_scores), 1) if aoi_scores else 0
    avg_exam = round(sum(exam_scores)/len(exam_scores), 1) if exam_scores else 0

    return jsonify({
        "trend_labels": trend_labels,
        "trend_percentages": trend_percentages,
        "comparison": {"AOI": avg_aoi, "Exam": avg_exam}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)