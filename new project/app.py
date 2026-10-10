from flask import Flask, render_template, request
import csv
import os
from datetime import datetime

app = Flask(__name__)

# CSV file will be created in your project folder
CSV_FILE = os.path.join(app.root_path, "appointments.csv")

# Create CSV file with column headings if it doesn't exist
def create_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Booking ID",
                "Booking Time",
                "Patient Name",
                "Email",
                "Phone",
                "Preferred Date",
                "Preferred Time",
                "Department",
                "Doctor",
                "Additional Message"
            ])


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/doctors")
def doctors():
    return render_template("doctors.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/appointment", methods=["GET", "POST"])
def appointment():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        date = request.form.get("date", "").strip()
        department = request.form.get("department", "").strip()
        doctor = request.form.get("doctor", "").strip()
        time = request.form.get("time", "").strip()
        message = request.form.get("message", "").strip()

        if not all([name, email, phone, date, department, doctor]):
            return render_template(
                "appointment.html",
                message="Please fill in all required fields.",
                success=False
            )

        try:
            create_csv()

            with open(
                CSV_FILE, mode="a", newline="", encoding="utf-8"
            ) as file:
                writer = csv.writer(file)
                writer.writerow([
                    datetime.now().strftime("%Y%m%d%H%M%S%f"),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    name,
                    email,
                    phone,
                    date,
                    department,
                    doctor,
                    message
                ])

            return render_template(
                "appointment.html",
                message="Appointment Successfully Booked!",
                success=True
            )

        except OSError:
            app.logger.exception("Could not save appointment to CSV")
            return render_template(
                "appointment.html",
                message="Unable to save your appointment. Please try again.",
                success=False
            )

    return render_template(
        "appointment.html",
        message=None,
        success=False
    )

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message_text = request.form.get("message", "").strip()

        if not name or not email or not message_text:
            return render_template(
                "contact.html",
                message="Please fill in all required fields.",
                success=False
            )

        try:
            csv_file = os.path.join(app.root_path, "contact_messages.csv")
            file_exists = os.path.exists(csv_file)

            with open(csv_file, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                if not file_exists or os.path.getsize(csv_file) == 0:
                    writer.writerow(["Submission Time", "Name", "Email", "Message"])

                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    name,
                    email,
                    message_text
                ])

            return render_template(
                "contact.html",
                message="Your message has been sent successfully!",
                success=True
            )

        except OSError:
            app.logger.exception("Contact CSV write failed")
            return render_template(
                "contact.html",
                message="Sorry, your message could not be saved. Please try again.",
                success=False
            )

    return render_template("contact.html", message=None, success=False)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
