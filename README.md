# Academic Mind Arcade™ - Math & Physics Educational Platform

Academic Mind Arcade is a next-generation interactive web platform dedicated to **Mathematics** and **Physics** education. It features interactive lab simulations, formula cheat sheets, calculators, interactive practice quizzes with instant grading, curriculum resources, and student progress tracking across Primary, Secondary (O-Level), and Advanced (A-Level) tiers.

---

## 🌟 Key Features

1. **Interactive Physics & Math Simulations (Virtual Labs)**
   - **Projectile Motion Lab**: Real-time canvas physics with customizable velocity, launch angle, and gravitational acceleration (Earth, Moon, Mars, Jupiter). Shows trajectory paths, flight time, max height, and horizontal range.
   - **Simple Harmonic Motion & Pendulum**: Real-time harmonic oscillation simulation with adjustable string length, gravity, damping, and energy diagrams (Kinetic vs Potential).
   - **Wave Optics & Optics Lab**: Wave interference, refraction index (Snell's Law) visualizer with ray bending simulation.
   - **Function Plotter & Calculus Explorer**: Dynamic function graphing ($f(x) = \sin(x), x^2, e^x, \cos(x)$ etc.) with visual tangent lines and instantaneous derivative slope calculator.

2. **Interactive Math & Physics Solvers / Calculators**
   - **Kinematics Solver**: Instant computation of SUVAT kinematics variables ($v = u + at$, $s = ut + \frac{1}{2}at^2$, etc.).
   - **Quadratic & Polynomial Solver**: Step-by-step roots derivation with discriminant analysis.
   - **Newton's Laws & Force / Energy Calculator**: Work, kinetic energy, momentum, and gravitational force.
   - **Ohm's Law & Circuit Analyzer**: Voltage, current, resistance, and electrical power calculation.

3. **Formula Codex & Interactive Cheat Sheets**
   - Beautifully formatted LaTeX mathematical and physical formulas using **KaTeX**.
   - Categorized across Classical Mechanics, Electromagnetism, Thermodynamics, Waves & Optics, Calculus & Algebra, and Trigonometry & Vectors.
   - Includes real-time search and filter tags for rapid study and exam revision.

4. **Self-Paced Diagnostic Quizzes & Interactive Practice**
   - Curated problem sets across Math & Physics categories (Mechanics, Calculus, Electromagnetism, Algebra).
   - Real-time instant answer checking, detailed step-by-step mathematical explanations, score calculation, and performance stats.

5. **Curriculum Resources & Multi-Tier Study Tracks**
   - Categorized by **Primary (PLE)**, **O-Level (Secondary)**, and **A-Level (Upper Secondary)**.
   - Video lessons with embedded educational stream players and downloadable study guides.
   - Filter by subject: **Mathematics**, **Physics**, or **Integrated STEM**.

6. **User Authentication & Personalized Student Dashboard**
   - Student accounts, profile management, completed simulation logs, and quiz score tracking.
   - Admin management hub to publish and manage curriculum modules.

---

## 🚀 Technology Stack

- **Backend**: Python 3.11, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug, Gunicorn
- **Database**: SQLite (default local) / PostgreSQL compatible
- **Frontend**: Tailwind CSS, HTML5 Canvas, KaTeX (LaTeX math rendering), Space Grotesk & Plus Jakarta Sans typography
- **Interactive Simulations**: Pure HTML5 Canvas & vanilla JavaScript physics engines

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+
- `pip`

### Installation

```bash
# Clone the repository
git clone https://github.com/otitijerom55-arch/academic-mind-arcade.git
cd academic-mind-arcade

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
python3 app.py
```

The application will start at `http://localhost:5000`.

---

## 📂 Project Structure

```text
├── app.py                      # Flask routes, database models, seed logic
├── requirements.txt            # Python dependencies
├── Procfile                    # Deployment entry point for web dynos
├── templates/
│   ├── layout.html             # Base cyber-aesthetic layout with KaTeX & nav
│   ├── dashboard.html          # Main landing hub with Math & Physics highlights
│   ├── simulations.html        # Interactive Physics & Math virtual labs
│   ├── formulas.html           # Comprehensive Math & Physics formula reference
│   ├── calculators.html        # Interactive STEM computational tools
│   ├── quiz.html               # Practice quizzes with automated grading
│   ├── study_resources.html    # Categorized learning modules & video streams
│   ├── login.html              # Student/Admin sign-in portal
│   ├── register.html           # Student registration
│   ├── admin.html              # Management and curriculum publishing hub
│   ├── about.html              # Educational platform mission & credits
│   └── intellectual_property.html # Legal and copyright notices
└── README.md                   # Platform documentation
```

---

## 📜 License & Copyright

&copy; 2026 Academic Mind Arcade™. Proprietary educational platform. Designed for curious minds exploring the wonders of Mathematics and the physical universe.
