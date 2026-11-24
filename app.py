import os
from urllib.parse import urlsplit

from flask import Flask, redirect, render_template, request, session, url_for
from database.db import (
    DuplicateEmailError,
    authenticate_user,
    close_db,
    create_user,
    init_db,
    seed_db,
)

app = Flask(__name__)
# Set FLASK_SECRET_KEY to a unique random value outside local development.
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY",
    "dev-only-change-me",
)

app.teardown_appcontext(close_db)

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=("GET", "POST"))
def register():
    if session.get("user_id") is not None:
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password.strip():
        return render_template(
            "register.html",
            error="Name, email, and password are required.",
            name=name,
            email=email,
        )

    if len(password) < 8:
        return render_template(
            "register.html",
            error="Password must be at least 8 characters.",
            name=name,
            email=email,
        )

    try:
        create_user(name, email, password)
    except DuplicateEmailError:
        return render_template(
            "register.html",
            error="An account with that email already exists.",
            name=name,
            email=email,
        )

    return redirect(url_for("login"))


@app.route("/login", methods=("GET", "POST"))
def login():
    if session.get("user_id") is not None:
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html", next_url=request.args.get("next", ""))

    submitted_email = request.form.get("email", "")
    email = submitted_email.strip().lower()
    password = request.form.get("password", "")
    next_url = request.form.get("next", "")

    if not email or not password.strip():
        return render_template(
            "login.html",
            error="Email and password are required.",
            email=submitted_email,
            next_url=next_url,
        )

    user = authenticate_user(email, password)
    if user is None:
        return render_template(
            "login.html",
            error="Invalid email or password.",
            email=submitted_email,
            next_url=next_url,
        )

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    target = urlsplit(next_url)
    if (
        not next_url.startswith("/")
        or next_url.startswith("//")
        or next_url.startswith("/\\")
        or target.scheme
        or target.netloc
    ):
        next_url = url_for("landing")

    return redirect(next_url)


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@app.route("/terms-and-conditions")
def terms_and_conditions():
    return render_template("terms_and_conditions.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
