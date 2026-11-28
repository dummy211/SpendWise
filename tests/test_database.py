import sqlite3

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from app import app
from database.db import get_db, init_db, seed_db


@pytest.fixture
def database(tmp_path):
    app.config.update(
        DATABASE=str(tmp_path / "database-test.db"),
        SECRET_KEY="database-test-secret",
        TESTING=True,
    )
    with app.app_context():
        init_db()
        yield get_db()


def test_database_initialization_and_seed_without_demo_password_are_safe(
    database, monkeypatch
):
    monkeypatch.delenv("SPENDWISE_DEMO_PASSWORD", raising=False)

    init_db()
    seed_db()
    seed_db()

    assert database.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_demo_seed_requires_configured_password_and_is_idempotent(
    database, monkeypatch
):
    monkeypatch.setenv("SPENDWISE_DEMO_PASSWORD", "configured-demo-password")

    seed_db()
    seed_db()

    user = database.execute(
        "SELECT id, password_hash FROM users WHERE email = ?",
        ("demo@spendly.com",),
    ).fetchone()
    assert check_password_hash(user["password_hash"], "configured-demo-password")
    assert database.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
    assert database.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 8


@pytest.mark.parametrize("demo_password", [None, "configured-demo-password"])
def test_seed_rotates_legacy_public_demo_password(
    database, monkeypatch, demo_password
):
    if demo_password is None:
        monkeypatch.delenv("SPENDWISE_DEMO_PASSWORD", raising=False)
    else:
        monkeypatch.setenv("SPENDWISE_DEMO_PASSWORD", demo_password)

    database.execute(
        """
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
        """,
        (
            "Demo User",
            "demo@spendly.com",
            generate_password_hash("demo123"),
        ),
    )
    database.commit()

    seed_db()

    password_hash = database.execute(
        "SELECT password_hash FROM users WHERE email = ?",
        ("demo@spendly.com",),
    ).fetchone()["password_hash"]
    assert not check_password_hash(password_hash, "demo123")
    if demo_password is not None:
        assert check_password_hash(password_hash, demo_password)


def test_seed_does_not_create_demo_account_when_another_user_exists(
    database, monkeypatch
):
    monkeypatch.setenv("SPENDWISE_DEMO_PASSWORD", "configured-demo-password")
    database.execute(
        """
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
        """,
        ("Existing User", "existing@example.com", generate_password_hash("password")),
    )
    database.commit()

    seed_db()

    assert database.execute(
        "SELECT COUNT(*) FROM users WHERE email = ?",
        ("demo@spendly.com",),
    ).fetchone()[0] == 0
    assert database.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 0


def test_repeated_initialization_preserves_existing_data(database):
    cursor = database.execute(
        """
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
        """,
        ("Existing User", "existing@example.com", generate_password_hash("password")),
    )
    user_id = cursor.lastrowid
    database.execute(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, 100, "Food", "2026-01-01", "Existing expense"),
    )
    database.commit()

    init_db()

    assert database.execute(
        "SELECT COUNT(*) FROM users WHERE email = ?",
        ("existing@example.com",),
    ).fetchone()[0] == 1
    assert database.execute(
        "SELECT description FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()["description"] == "Existing expense"


def test_database_rejects_expenses_for_unknown_users(database):
    with pytest.raises(sqlite3.IntegrityError):
        database.execute(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (99999, 100, "Food", "2026-01-01", "Invalid owner"),
        )
    database.rollback()
