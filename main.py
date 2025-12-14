from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Text, Date, DateTime, ForeignKey
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime,date
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

CITY_TO_COUNTRY = {
    "paris": "france",
    "london": "uk",
    "dubai": "uae",
    "rome": "italy",
    "tokyo": "japan",
    "new york": "usa",
    "goa": "india",
    "delhi": "india",
    "mumbai": "india",
    "bali": "indonesia"
}

COUNTRY_CURRENCY = {
    "india": {"symbol": "₹", "inr_per_unit": 1.0},
    "france": {"symbol": "€", "inr_per_unit": 90.0},
    "uk": {"symbol": "£", "inr_per_unit": 105.0},
    "usa": {"symbol": "$", "inr_per_unit": 83.0},
    "uae": {"symbol": "AED", "inr_per_unit": 23.0},
    "japan": {"symbol": "¥", "inr_per_unit": 0.58},
    "italy": {"symbol": "€", "inr_per_unit": 90.0},
    "indonesia": {"symbol": "Rp", "inr_per_unit": 0.0055}
}

COUNTRY_COST_BASIS = {
    "india": {"hotel": 2500, "meal": 700, "transport": 300, "activity": 500},
    "france": {"hotel": 100, "meal": 18, "transport": 12, "activity": 18},
    "uk": {"hotel": 110, "meal": 20, "transport": 10, "activity": 22},
    "usa": {"hotel": 130, "meal": 22, "transport": 15, "activity": 25},
    "uae": {"hotel": 120, "meal": 25, "transport": 14, "activity": 24},
    "japan": {"hotel": 14000, "meal": 2000, "transport": 800, "activity": 2500},
    "italy": {"hotel": 110, "meal": 20, "transport": 12, "activity": 20},
    "indonesia": {"hotel": 450000, "meal": 90000, "transport": 25000, "activity": 80000}
}

def fmt_date(d: date) -> str:
    return d.strftime("%d %b %Y")

def normalize_city(city: str) -> str:
    return (city or "").strip().lower()

def get_country_info(city: str):
    city_key = normalize_city(city)
    country = CITY_TO_COUNTRY.get(city_key, "india")
    currency = COUNTRY_CURRENCY.get(country, COUNTRY_CURRENCY["india"])
    costs = COUNTRY_COST_BASIS.get(country, COUNTRY_COST_BASIS["india"])
    return country, currency, costs

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
        start = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()

        existing_trips = db.session.execute(
            db.select(Trip).where(Trip.user_id == current_user.id)
        ).scalars().all()

        for t in existing_trips:
            if not (end < t.start_date or start > t.end_date):
                flash( f"Trip overlaps with an existing trip from "
                    f"{fmt_date(t.start_date)} to {fmt_date(t.end_date)}.",
                    "danger")

                return redirect(url_for('create_trip'))

        trip = Trip(
            user_id=current_user.id,
            destination=request.form.get('destination'),
            start_date=start,
            end_date=end,
            budget=float(request.form.get('budget') or 0),
            notes=request.form.get('notes'),
            image=f"https://picsum.photos/seed/{request.form.get('destination')}/600/400"
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

@app.route('/trip/<int:id>')
@login_required
def trip_details(id):
    trip = db.session.get(Trip, id)
    if trip is None or trip.user_id != current_user.id:
        flash("Trip not found or access denied.", "danger")
        return redirect(url_for('my_trips'))
    return render_template('trip-details.html', trip=trip)

@app.route('/explore')
@login_required
def explore():
    try:
        prompt = """
        Return ONLY valid JSON array. No explanation.
        Generate exactly 6 travel destinations.
        Format:
        [
          { "name": "City Name", "desc": "Short description" }
        ]
        """
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = chat.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        destinations = json.loads(raw)
        for d in destinations:
            d["image"] = f"https://picsum.photos/seed/{d['name']}/600/400"
        return render_template("explore.html", destinations=destinations)
    except Exception:
        destinations = [
            {"name": "Paris", "desc": "City of lights", "image": "https://picsum.photos/seed/paris/600/400"},
            {"name": "Tokyo", "desc": "Culture and tech", "image": "https://picsum.photos/seed/tokyo/600/400"},
            {"name": "Goa", "desc": "Beaches & nightlife", "image": "https://picsum.photos/seed/goa/600/400"},
            {"name": "Dubai", "desc": "Luxury & skyline", "image": "https://picsum.photos/seed/dubai/600/400"},
            {"name": "Rome", "desc": "History & food", "image": "https://picsum.photos/seed/rome/600/400"},
            {"name": "Bali", "desc": "Nature & temples", "image": "https://picsum.photos/seed/bali/600/400"},
        ]
        return render_template("explore.html", destinations=destinations)

@app.route('/itinerary/<path:city>', methods=['GET', 'POST'])
@login_required
def itinerary(city):
    image = request.args.get('image')

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        budget = float(request.form.get('budget') or 0)

        if not start_date or not end_date:
            flash("Please select valid dates.", "warning")
            return redirect(request.url)

        country, currency, costs = get_country_info(city)
        budget_in_inr = budget
        local_budget = budget_in_inr / currency["inr_per_unit"]

        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        nights = max((end - start).days, 1)

        min_hotel = costs["hotel"] * nights
        min_food = costs["meal"] * 2 * nights
        min_transport = costs["transport"] * nights
        min_activities = costs["activity"] * 4

        min_total_local = min_hotel + min_food + min_transport + min_activities
        min_total_inr = min_total_local * currency["inr_per_unit"]

        if local_budget < min_total_local:
            itinerary_text = f"Budget is not sufficient for a proper trip to {city}. Minimum recommended budget is {currency['symbol']}{min_total_local:,.0f} (≈ ₹{min_total_inr:,.0f})."
            return render_template(
                "itinerary.html",
                city=city,
                image=image,
                itinerary=itinerary_text,
                start_date=start_date,
                end_date=end_date,
                budget=budget_in_inr
            )

        prompt = f"""
Create a detailed travel itinerary for {city} (country: {country}) that is strictly budget-accurate.
Dates: {start_date} to {end_date} (nights: {nights})
Budget Local: {currency['symbol']}{local_budget:,.0f}
Use realistic pricing and do not exceed the budget.
"""
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        itinerary_text = chat.choices[0].message.content.strip()

        return render_template(
            "itinerary.html",
            city=city,
            image=image,
            itinerary=itinerary_text,
            start_date=start_date,
            end_date=end_date,
            budget=budget_in_inr
        )

    return render_template(
        "itinerary.html",
        city=city,
        image=image,
        itinerary=None,
        start_date=None,
        end_date=None,
        budget=None
    )

@app.route('/save_itinerary', methods=['POST'])
@login_required
def save_itinerary():
    destination = request.form.get('destination')
    notes = request.form.get('notes')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    budget = request.form.get('budget')

    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except Exception:
        flash("Invalid dates provided.", "danger")
        return redirect(request.referrer)

    if start > end:
        flash("Start date cannot be after end date.", "danger")
        return redirect(request.referrer)

    existing_trips = db.session.execute(
        db.select(Trip).where(Trip.user_id == current_user.id)
    ).scalars().all()

    for t in existing_trips:
        if not (end < t.start_date or start > t.end_date):
            flash(
                f"Trip overlaps with an existing trip from "
                f"{fmt_date(t.start_date)} to {fmt_date(t.end_date)}.",
                "danger")
            
            return redirect(request.referrer)

    trip = Trip(
        user_id=current_user.id,
        destination=destination,
        start_date=start,
        end_date=end,
        budget=float(budget or 0),
        notes=notes,
        image=f"https://picsum.photos/seed/{destination}/600/400"
    )

    db.session.add(trip)
    db.session.commit()

    flash("Trip added!", "success")
    return redirect(url_for('my_trips'))

@app.route('/edit_trip/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_trip(id):
    trip = db.session.get(Trip, id)
    if trip is None or trip.user_id != current_user.id:
        flash("Trip not found.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        start = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()

        if start > end:
            flash("Start date cannot be after end date.", "danger")
            return redirect(url_for('edit_trip', id=id))

        existing_trips = db.session.execute(
            db.select(Trip).where(Trip.user_id == current_user.id, Trip.id != id)
        ).scalars().all()

        for t in existing_trips:
            if not (end < t.start_date or start > t.end_date):
                flash(f"Edited dates overlap with an existing trip from {t.start_date} to {t.end_date}.", "danger")
                return redirect(url_for('edit_trip', id=id))

        trip.destination = request.form.get('destination')
        trip.start_date = start
        trip.end_date = end
        trip.budget = float(request.form.get('budget') or 0)
        trip.notes = request.form.get('notes')
        db.session.commit()

        flash("Trip updated!", "success")
        return redirect(url_for('dashboard'))

    return render_template('edit-trip.html', trip=trip)

@app.route('/delete_trip/<int:id>')
@login_required
def delete_trip(id):
    trip = db.session.get(Trip, id)
    if trip is None or trip.user_id != current_user.id:
        flash("Trip not found.", "danger")
        return redirect(url_for('dashboard'))

    db.session.delete(trip)
    db.session.commit()
    flash("Trip deleted!", "success")
    return redirect(url_for('dashboard'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', current_user=current_user)

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.phone = request.form['phone']
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for('profile'))
    return render_template('edit-profile.html')

@app.route('/dashboard')
@login_required
def dashboard():
    trips = db.session.execute(
        db.select(Trip).where(Trip.user_id == current_user.id)
    ).scalars().all()

    today = date.today()

    ongoing = [t for t in trips if t.start_date <= today <= t.end_date]
    upcoming = [t for t in trips if t.start_date > today]
    past = [t for t in trips if t.end_date < today]

    return render_template(
        'dashboard.html',
        user_trips=trips,
        ongoing=ongoing,
        upcoming=upcoming,
        past=past
    )


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

        existing = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()

        if existing:
            flash("Account already exists.", "warning")
            return redirect(url_for("login"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        user = User(
            username=name,
            email=email,
            password_hash=generate_password_hash(password, 'pbkdf2:sha256', 8)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid credentials.", "danger")
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