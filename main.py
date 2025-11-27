from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Text, Date, DateTime, ForeignKey
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
import json
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travelplanner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    joined_on: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="user")

class Trip(db.Model):
    __tablename__ = "trips"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    destination: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    budget: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user: Mapped["User"] = relationship("User", back_populates="trips")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/create_trip', methods=['GET', 'POST'])
@login_required
def create_trip():
    if request.method == 'POST':
        trip = Trip(
            user_id=current_user.id,
            destination=request.form.get('destination'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
            budget=request.form.get('budget'),
            notes=request.form.get('notes'),
            image=request.form.get('image')
        )
        db.session.add(trip)
        db.session.commit()
        return redirect(url_for('my_trips'))
    return render_template('create-trip.html')

@app.route('/my_trips')
@login_required
def my_trips():
    trips = db.session.execute(db.select(Trip).where(Trip.user_id == current_user.id)).scalars().all()
    return render_template('my-trips.html', trips=trips)

@app.route('/explore')
@login_required
def explore():
    try:
        prompt = """
        Return ONLY valid JSON. No explanation.
        Generate exactly 6 travel destinations.
        Format:
        [
          { "name": "", "desc": "", "image": "" }
        ]
        Use real Unsplash image URLs only.
        """

        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        raw = chat.choices[0].message.content.strip()
        destinations = json.loads(raw)

        return render_template("explore.html", destinations=destinations)

    except Exception as e:
        return f"Error generating destinations: {e}"

@app.route('/itinerary/<path:city>')
@login_required
def itinerary(city):
    try:
        prompt = f"""
        Create a detailed 2-day travel itinerary for {city}.
        Include:
        - Timings
        - Must-visit places
        - Food recommendations
        - Transport tips
        - Best photo spots
        Use clean bullet formatting.
        """

        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )


        itinerary_text = chat.choices[0].message.content

        return render_template("itinerary.html", city=city, itinerary=itinerary_text)

    except Exception as e:
        return f"Error generating itinerary: {e}"

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', current_user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/help')
@login_required
def help():
    return render_template('help.html')

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        existing_user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()

        if existing_user:
            flash("Account already exists.", "warning")
            return redirect(url_for("login"))

        if password == confirm_password:
            user = User(
                username=name,
                email=email,
                password_hash=generate_password_hash(password, 'pbkdf2:sha256', 8)
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Passwords do not match.", "danger")
        return redirect(url_for("register"))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)