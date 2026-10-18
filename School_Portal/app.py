
import os
import re
import sqlite3
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash


# Load configuration from the .env file
load_dotenv()

app = Flask(__name__)

secret_key = os.environ.get("SECRET_KEY")

if not secret_key or len(secret_key) < 32:
    raise RuntimeError(
        "Set a strong SECRET_KEY in your .env file before starting Flask."
    )

app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Enable this when deployed over HTTPS:
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=1 * 1024 * 1024,
)

# Protect POST requests against CSRF attacks
csrf = CSRFProtect(app)

DATABASE = os.path.join(app.root_path, "students.db")


# -----------------------------
# Database connection
# -----------------------------

def get_db_connection():
    connection = sqlite3.connect(DATABASE, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# -----------------------------
# Login protection
# -----------------------------

def login_required(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        if "student_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapper


# -----------------------------
# Home page
# -----------------------------

@app.route("/")
def home():
    if "student_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# -----------------------------
# Registration
# -----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if "student_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([full_name, email, password, confirm_password]):
            flash("Please fill in every field.", "error")
            return render_template("register.html")

        if len(full_name) < 2 or len(full_name) > 100:
            flash("Your name must be between 2 and 100 characters.", "error")
            return render_template("register.html")

        if len(email) > 254 or not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+", email
        ):
            flash("Please enter a valid email address.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Your password must contain at least 8 characters.", "error")
            return render_template("register.html")

        if len(password) > 128:
            flash("Your password is too long.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("The passwords do not match.", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        try:
            with get_db_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO students (full_name, email, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (full_name, email, password_hash),
                )

        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "error")
            return render_template("register.html")

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# Login
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if "student_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Enter your email and password.", "error")
            return render_template("login.html")

        with get_db_connection() as connection:
            student = connection.execute(
                """
                SELECT id, full_name, email, password_hash
                FROM students
                WHERE email = ?
                """,
                (email,),
            ).fetchone()

        if student and check_password_hash(
            student["password_hash"], password
        ):
            # Start a fresh session after successful authentication
            session.clear()
            session["student_id"] = student["id"]
            session["student_name"] = student["full_name"]
            session["student_email"] = student["email"]

            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# -----------------------------
# Student dashboard
# -----------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        student_name=session["student_name"],
        student_email=session["student_email"],
    )


# -----------------------------
# Logout
# -----------------------------

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have logged out successfully.", "success")
    return redirect(url_for("login"))


# -----------------------------
# Start the application
# -----------------------------

initialize_database()

if __name__ == "__main__":
    # Debug mode stays disabled
    app.run(debug=False)
