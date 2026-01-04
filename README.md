# 🌍 TravelPlanner

TravelPlanner is a Flask-based web application that helps users plan, manage, and organize trips with budget-aware itineraries, destination exploration, and AI-powered travel suggestions.

---

## ✨ Features

- 🔐 User Authentication (Register / Login / Logout)
- 🧳 Create, Edit & Delete Trips
- 📅 Trip Overlap Validation
- 🗺️ Explore Popular Destinations
- 🧠 AI-Generated Travel Itineraries (Groq LLM)
- 💰 Budget-Aware Planning with Currency Estimation
- 🖼️ Dynamic City Images
- 📩 Contact Form with Email Support
- 👤 User Profile Management
- 📊 Dashboard for Ongoing, Upcoming & Past Trips

---

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Database:** SQLite, SQLAlchemy ORM
- **Authentication:** Flask-Login
- **AI Integration:** Groq API
- **Frontend:** HTML, Jinja2, CSS
- **Email:** Gmail SMTP
- **Environment Management:** python-dotenv

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/bhavikakeswani/travelplanner.git
cd travelplanner
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:
```bash
SECRET_KEY=your_secret_key
GROQ_API_KEY=your_groq_api_key
EMAIL_KEY=your_gmail_address
PASSWORD_KEY=your_gmail_app_password
```

---

## ▶️ Running the Application
```bash
python main.py
```

Open your browser and visit:
```bash
http://127.0.0.1:5000
```

## 🧠 AI Itinerary Generation

TravelPlanner uses the **Groq LLM** to:
- Validate user-entered destinations
- Generate realistic, budget-constrained itineraries
- Suggest travel destinations in the Explore section

If the AI service is unavailable, the application gracefully falls back to predefined destinations.

---

## 🗃️ Database

- Uses **SQLite** (`travelplanner.db`)
- Tables are automatically created on first run using SQLAlchemy

---

## 📬 Contact Feature

- Messages submitted through the Contact page are emailed to the admin
- Logged-in users have their email auto-filled automatically

---

## 🔒 Security

- Passwords are securely hashed using **Werkzeug**
- User sessions are managed via **Flask-Login**
- Sensitive credentials are stored in environment variables

---

## 🚀 Future Improvements

- Real destination images (Unsplash / Pexels integration)
- Mobile-responsive UI
- Flight & hotel API integrations
- Interactive map-based trip visualization
- Live currency exchange rates

---

## 📸 Project Screenshots & Demo

This section showcases the user interface and key features of **TravelPlanner**.

### 🖼️ Screenshots
- Home Page
- User Dashboard
- Explore Destinations
- Trip Details & Itinerary
- Profile Page

<img width="1464" height="878" alt="Screenshot 2026-01-04 at 10 22 01 PM" src="https://github.com/user-attachments/assets/558755d3-9e5f-4e50-b336-d575507f7e65" />
<img width="1462" height="876" alt="Screenshot 2026-01-04 at 10 22 13 PM" src="https://github.com/user-attachments/assets/b6f25c94-03f5-44b4-9151-9300d9178655" />
<img width="1459" height="875" alt="Screenshot 2026-01-04 at 10 22 25 PM" src="https://github.com/user-attachments/assets/fa76062d-2108-4983-bc85-c091fa81fcf7" />
<img width="1459" height="878" alt="Screenshot 2026-01-04 at 10 22 53 PM" src="https://github.com/user-attachments/assets/f31e4bd8-7278-479e-b77e-8917af37ce76" />
<img width="1465" height="881" alt="Screenshot 2026-01-04 at 10 23 00 PM" src="https://github.com/user-attachments/assets/29a32ab7-59a5-420a-9bd1-9292132abcfd" />

## ⚙️ How It Works

1. Users register and log in securely
2. Trips are created with destination, dates, and budget
3. The system validates date overlaps and destinations
4. AI generates a realistic itinerary based on budget and duration
5. Trips are organized into ongoing, upcoming, and past categories
6. Users can edit, delete, and save itineraries for future reference
