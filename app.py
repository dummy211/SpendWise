import hmac
import os
import secrets
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlsplit

from flask import Flask, abort, redirect, render_template, request, session, url_for
from database.db import (
    DuplicateEmailError,
    authenticate_user,
    close_db,
    create_user,
    init_db,
    seed_db,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

app.teardown_appcontext(close_db)


def _csrf_token():
    token = session.get("_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": _csrf_token}


def _validate_secret_key():
    secret_key = app.config.get("SECRET_KEY")
    if not secret_key or secret_key == "dev-only-change-me":
        raise RuntimeError(
            "Set FLASK_SECRET_KEY to a unique random value before serving requests."
        )


@app.before_request
def protect_state_changes():
    _validate_secret_key()

    if request.method == "POST":
        expected_token = session.get("_csrf_token")
        submitted_token = request.form.get("csrf_token", "")
        if (
            not isinstance(expected_token, str)
            or not submitted_token
            or not hmac.compare_digest(expected_token, submitted_token)
        ):
            abort(400, description="Invalid or missing CSRF token.")


with app.app_context():
    init_db()
    seed_db()


@app.template_filter("inr")
def format_inr(value, show_paise=False):
    amount = Decimal(str(value or 0))
    if show_paise and amount != amount.to_integral_value():
        amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        amount = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    whole, _, fraction = format(abs(amount), "f").partition(".")
    trailing = whole[-3:]
    leading = whole[:-3]
    groups = []
    while leading:
        groups.insert(0, leading[-2:])
        leading = leading[:-2]
    formatted = ",".join(groups + [trailing])
    if fraction:
        formatted = f"{formatted}.{fraction}"

    sign = "-" if amount < 0 else ""
    return f"{sign}₹{formatted}"


DEMO_CURRENT_EXPENSES = (
    (780, "Food", "Groceries and fresh produce", 1),
    (420, "Food", "Lunch thali at a neighborhood restaurant", 3),
    (260, "Transport", "Metro card recharge", 4),
    (2450, "Bills", "Monthly electricity bill", 6),
    (525, "Health", "Pharmacy medicines", 8),
    (890, "Entertainment", "Cinema tickets and snacks", 10),
    (1750, "Shopping", "Household essentials from the local market", 12),
    (310, "Other", "Stationery and household items", 14),
)

DEMO_PREVIOUS_EXPENSES = (
    (1500, "Food", "Previous-month grocery run", 5),
    (1200, "Transport", "Previous-month transit pass", 11),
    (2000, "Bills", "Previous-month utility bill", 18),
    (900, "Shopping", "Previous-month household supplies", 24),
)


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=("GET", "POST"))
def register():
    if session.get("user_id") is not None:
        return redirect(url_for("dashboard"))

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
        return redirect(url_for("dashboard"))

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
        next_url = url_for("dashboard")

    return redirect(next_url)


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login", next=url_for("dashboard")))

    today = date.today()
    previous_month = today.month - 1 or 12
    previous_year = today.year - (1 if today.month == 1 else 0)
    current_month_start = date(today.year, today.month, 1)
    previous_month_start = date(previous_year, previous_month, 1)

    demo_expenses = []
    for index, (amount, category, description, days_ago) in enumerate(
        DEMO_CURRENT_EXPENSES,
        start=1,
    ):
        expense_date = max(
            current_month_start,
            today - timedelta(days=days_ago),
        )
        demo_expenses.append(
            {
                "id": index,
                "amount": amount,
                "category": category,
                "description": description,
                "date": expense_date,
            }
        )

    previous_month_days = monthrange(previous_year, previous_month)[1]
    for index, (amount, category, description, day) in enumerate(
        DEMO_PREVIOUS_EXPENSES,
        start=len(demo_expenses) + 1,
    ):
        expense_date = date(
            previous_year,
            previous_month,
            min(day, previous_month_days),
        )
        demo_expenses.append(
            {
                "id": index,
                "amount": amount,
                "category": category,
                "description": description,
                "date": expense_date,
            }
        )

    current_expenses = [
        expense
        for expense in demo_expenses
        if expense["date"] >= current_month_start
    ]
    previous_expenses = [
        expense
        for expense in demo_expenses
        if previous_month_start <= expense["date"] < current_month_start
    ]
    month_total = sum(expense["amount"] for expense in current_expenses)
    previous_total = sum(expense["amount"] for expense in previous_expenses)
    month_summary = {
        "total": month_total,
        "transaction_count": len(current_expenses),
    }

    spending_change = (
        round((month_total - previous_total) / previous_total * 100, 1)
        if previous_total
        else None
    )

    category_amounts = {}
    for expense in current_expenses:
        category_amounts[expense["category"]] = (
            category_amounts.get(expense["category"], 0) + expense["amount"]
        )
    category_totals = [
        {"category": category, "total": amount}
        for category, amount in category_amounts.items()
    ]
    category_totals.sort(
        key=lambda category: (-category["total"], category["category"]),
    )
    for category in category_totals:
        category["percentage"] = (
            round(category["total"] / month_total * 100, 1)
            if month_total
            else 0
        )

    recent_expenses = sorted(
        demo_expenses,
        key=lambda expense: (expense["date"], expense["id"]),
        reverse=True,
    )[:10]
    for expense in recent_expenses:
        expense["date"] = expense["date"].isoformat()

    return render_template(
        "dashboard.html",
        dashboard_error=False,
        month_name=today.strftime("%B %Y"),
        month_summary=month_summary,
        spending_change=spending_change,
        category_totals=category_totals,
        recent_expenses=recent_expenses,
        has_expenses=True,
    )


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@app.route("/terms-and-conditions")
def terms_and_conditions():
    return render_template("terms_and_conditions.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout", methods=("POST",))
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
    _validate_secret_key()
    app.run(port=5001)
