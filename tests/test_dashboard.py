from datetime import date
from urllib.parse import parse_qs, urlsplit

import pytest

from app import app
from database.db import create_user, get_db, init_db


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "dashboard-test.db"
    app.config.update(
        DATABASE=str(database_path),
        SECRET_KEY="dashboard-test-secret",
        TESTING=True,
    )

    with app.app_context():
        init_db()
        create_user("Dashboard User", "dashboard@example.com", "secure123")

    with app.test_client() as test_client:
        yield test_client


def _insert_expense(user_id, amount, category, expense_date, description):
    with app.app_context():
        get_db().execute(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, amount, category, expense_date.isoformat(), description),
        )
        get_db().commit()


def _login(client, email="dashboard@example.com"):
    return client.post(
        "/login",
        data={"email": email, "password": "secure123"},
    )


def test_logged_out_dashboard_redirects_to_login_with_next(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    location = urlsplit(response.headers["Location"])
    assert location.path == "/login"
    assert parse_qs(location.query)["next"] == ["/dashboard"]


def test_successful_login_defaults_to_dashboard(client):
    response = _login(client)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_dashboard_shows_labeled_demo_summary_and_categories(client):
    _login(client)
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Sample data:" in response.data
    assert b"hardcoded example expenses" in response.data
    assert b"Spent this month" in response.data
    assert "₹7,385".encode("utf-8") in response.data
    assert b"8" in response.data
    assert b"Top category" in response.data
    assert b"Bills" in response.data
    assert b"31.9%" in response.data
    assert b"Groceries and fresh produce" in response.data


def test_dashboard_uses_demo_values_instead_of_saved_user_expenses(client):
    with app.app_context():
        other_user_id = create_user(
            "Other User",
            "other@example.com",
            "secure123",
        )
        user_id = get_db().execute(
            "SELECT id FROM users WHERE email = ?",
            ("dashboard@example.com",),
        ).fetchone()["id"]

    _insert_expense(user_id, 1200, "Food", date.today(), "Saved private groceries")
    _insert_expense(
        other_user_id,
        99000,
        "Shopping",
        date.today(),
        "Saved other-user expense",
    )
    _login(client)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Groceries and fresh produce" in response.data
    assert b"Saved private groceries" not in response.data
    assert b"Saved other-user expense" not in response.data
    assert "₹99,000".encode("utf-8") not in response.data


def test_dashboard_shows_demo_data_even_when_user_has_no_saved_expenses(client):
    _login(client)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Sample data:" in response.data
    assert b"Your spending story starts here" not in response.data
    assert b"Spent this month" in response.data


def test_dashboard_limits_recent_demo_expenses_to_ten(client):
    _login(client)

    response = client.get("/dashboard")
    page = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "Previous-month utility bill" in page
    assert "Previous-month household supplies" in page
    assert "Previous-month grocery run" not in page
    assert "Previous-month transit pass" not in page


def test_inr_filter_uses_indian_grouping_and_optional_paise():
    inr = app.jinja_env.filters["inr"]

    assert inr(1234567) == "₹12,34,567"
    assert inr(1234.5, True) == "₹1,234.50"
    assert inr(1200.0, True) == "₹1,200"
