import sqlite3

import pytest
from werkzeug.security import check_password_hash

from app import app
from database.db import init_db


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "test.db"
    app.config.update(
        DATABASE=str(database_path),
        TESTING=True,
    )

    with app.app_context():
        init_db()

    with app.test_client() as test_client:
        yield test_client


def test_register_creates_hashed_user(client):
    response = client.post(
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
    response = client.post("/register", data=data)

    assert response.status_code == 200
    assert message.encode() in response.data


def test_register_rejects_duplicate_email_case_insensitively(client):
    valid_data = {
        "name": "First User",
        "email": "first@example.com",
        "password": "secure123",
    }
    client.post("/register", data=valid_data)

    response = client.post(
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
