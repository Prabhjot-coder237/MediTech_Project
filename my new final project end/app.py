from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pathlib import Path
from datetime import datetime, date
import csv
import os

#app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)


app.secret_key = os.environ.get("SECRET_KEY", "change-this-key-before-deployment")

BASE_DIR = Path(__file__).resolve().parent
APPOINTMENTS_CSV = BASE_DIR / "appointments.csv"
CONTACTS_CSV = BASE_DIR / "contact_messages.csv"
USERS_CSV = BASE_DIR / "users.csv"

APPOINTMENT_FIELDS = [
    "Booking ID", "Booking Time", "Patient Name", "Email", "Phone",
    "Preferred Date", "Preferred Time", "Department", "Doctor", "Additional Message"
]
CONTACT_FIELDS = ["Submission Time", "Name", "Email", "Message"]
USER_FIELDS = ["name", "email", "password_hash"]


def ensure_csv(path, fields):
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=fields).writeheader()


def read_rows(path, fields):
    ensure_csv(path, fields)
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def append_row(path, fields, row):
    ensure_csv(path, fields)
    with path.open("a", newline="", encoding="utf-8") as file:
        csv.DictWriter(file, fieldnames=fields).writerow(row)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("patient_email"):
            flash("Please log in to access your dashboard.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_site_name():
    return {"site_name": "MediTeach", "now_date": date.today().isoformat()}

@app.route("/base")
def base():
    return render_template("base.html", title="Base Template")
@app.route("/")
def home():
    return render_template("home.html", title="Home")


@app.route("/about")
def about():
    return render_template("about.html", title="About Us")


@app.route("/doctors")
def doctors():
    return render_template("doctors.html", title="Our Doctors")


@app.route("/services")
def services():
    return render_template("services.html", title="Our Services")


@app.route("/appointment", methods=["GET", "POST"])
def appointment():
    if request.method == "POST":
        fields = {key: request.form.get(key, "").strip() for key in
                  ["name", "email", "phone", "date", "time", "department", "doctor", "message"]}
        if not all(fields[key] for key in
                   ["name", "email", "phone", "date", "time", "department", "doctor"]):
            flash("Please fill in all required appointment fields.", "error")
            return render_template("appointment.html", title="Book an Appointment", form_data=fields), 400
        try:
            append_row(APPOINTMENTS_CSV, APPOINTMENT_FIELDS, {
                "Booking ID": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "Booking Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Patient Name": fields["name"], "Email": fields["email"], "Phone": fields["phone"],
                "Preferred Date": fields["date"], "Preferred Time": fields["time"],
                "Department": fields["department"], "Doctor": fields["doctor"],
                "Additional Message": fields["message"]
            })
        except OSError:
            app.logger.exception("Unable to save appointment")
            flash("Your appointment could not be saved. Please try again.", "error")
            return render_template("appointment.html", title="Book an Appointment", form_data=fields), 500
        flash(f"Appointment successfully booked for {fields['name']}!", "success")
        return redirect(url_for("appointment"))
    return render_template("appointment.html", title="Book an Appointment", form_data={})


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        message = request.form.get("message", "").strip()
        data = {"name": name, "email": email, "message": message}
        if not all([name, email, message]):
            flash("Please complete all required fields.", "error")
            return render_template("contact.html", title="Contact Us", form_data=data), 400
        try:
            append_row(CONTACTS_CSV, CONTACT_FIELDS, {
                "Submission Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Name": name, "Email": email, "Message": message
            })
        except OSError:
            app.logger.exception("Unable to save contact message")
            flash("Your message could not be saved. Please try again.", "error")
            return render_template("contact.html", title="Contact Us", form_data=data), 500
        flash(f"Thank you, {name}. Your message has been sent successfully!", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html", title="Contact Us", form_data={})


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("patient_email"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please complete all required fields.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif any(user.get("email", "").lower() == email for user in read_rows(USERS_CSV, USER_FIELDS)):
            flash("An account with this email already exists. Please log in.", "error")
        else:
            append_row(USERS_CSV, USER_FIELDS, {
                "name": name,
                "email": email,
                "password_hash": generate_password_hash(password)
            })
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", title="Sign Up")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    return register()


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("patient_email"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = next((u for u in read_rows(USERS_CSV, USER_FIELDS)
                     if u.get("email", "").lower() == email), None)
        if user and check_password_hash(user.get("password_hash", ""), password):
            session.clear()
            session["patient_email"] = user["email"]
            session["patient_name"] = user["name"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html", title="Login")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title="Patient Dashboard")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
