import re
import sqlite3

import pytest
from werkzeug.security import check_password_hash

from app import app
from database.db import init_db


def _post_with_csrf(client, path, data=None):
    page = client.get(path, follow_redirects=True)
    match = re.search(rb'name="csrf_token" value="([^"]+)"', page.data)
    assert match is not None
    form_data = dict(data or {})
    form_data["csrf_token"] = match.group(1).decode()
    return client.post(path, data=form_data)


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "test.db"
    app.config.update(
        DATABASE=str(database_path),
        SECRET_KEY="registration-test-secret",
        TESTING=True,
    )

    with app.app_context():
        init_db()

    with app.test_client() as test_client:
        yield test_client


def test_register_creates_hashed_user(client):
    response = _post_with_csrf(
        client,
        "/register",
        data={
            "name": "  Test User  ",
            "email": "  TEST@example.com ",
            "password": "secure123",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    with app.app_context():
        connection = sqlite3.connect(app.config["DATABASE"])
        row = connection.execute(
            "SELECT name, email, password_hash FROM users"
        ).fetchone()
        connection.close()

    assert row[0] == "Test User"
    assert row[1] == "test@example.com"
    assert row[2] != "secure123"
    assert check_password_hash(row[2], "secure123")


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (
            {"name": "Test User", "email": "test@example.com", "password": ""},
            "Name, email, and password are required.",
        ),
        (
            {"name": "Test User", "email": "test@example.com", "password": "        "},
            "Name, email, and password are required.",
        ),
        (
            {"name": "Test User", "email": "test@example.com", "password": "short"},
            "Password must be at least 8 characters.",
        ),
    ],
)
def test_register_rejects_invalid_input(client, data, message):
    response = _post_with_csrf(client, "/register", data=data)

    assert response.status_code == 200
    assert message.encode() in response.data


def test_register_rejects_duplicate_email_case_insensitively(client):
    valid_data = {
        "name": "First User",
        "email": "first@example.com",
        "password": "secure123",
    }
    _post_with_csrf(client, "/register", data=valid_data)

    response = _post_with_csrf(
        client,
        "/register",
        data={
            "name": "Second User",
            "email": " FIRST@EXAMPLE.COM ",
            "password": "secure456",
        },
    )

    assert response.status_code == 200
    assert b"An account with that email already exists." in response.data

    with app.app_context():
        connection = sqlite3.connect(app.config["DATABASE"])
        count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        connection.close()

    assert count == 1


@pytest.mark.parametrize("token", ["", "invalid-token"])
def test_registration_rejects_missing_or_invalid_csrf_token(client, token):
    client.get("/register")
    response = client.post(
        "/register",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "secure123",
            "csrf_token": token,
        },
    )

    assert response.status_code == 400
