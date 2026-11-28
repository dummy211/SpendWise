import calendar
import os
import secrets
import sqlite3
from datetime import date

from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash


DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "expense_tracker.db",
)


class DuplicateEmailError(Exception):
    """Raised when a user attempts to register an existing email address."""


def get_db():
    if "db" not in g:
        database_path = current_app.config.get("DATABASE", DATABASE)

        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection

    return g.db


def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    db.commit()


def create_user(name, email, password):
    db = get_db()

    try:
        cursor = db.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (name, email, generate_password_hash(password)),
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as error:
        db.rollback()
        if "users.email" in str(error):
            raise DuplicateEmailError from error
        raise


def authenticate_user(email, password):
    user = get_db().execute(
        """
        SELECT id, name, password_hash
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return None

    return {"id": user["id"], "name": user["name"]}


def seed_db():
    db = get_db()

    demo_email = "demo@spendly.com"
    demo_user = db.execute(
        "SELECT id, password_hash FROM users WHERE email = ?",
        (demo_email,),
    ).fetchone()
    if demo_user is not None:
        if check_password_hash(demo_user["password_hash"], "demo123"):
            demo_password = os.environ.get("SPENDWISE_DEMO_PASSWORD")
            if not demo_password:
                demo_password = secrets.token_urlsafe(32)
            db.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(demo_password), demo_user["id"]),
            )
            db.commit()
        return

    existing_user = db.execute(
        "SELECT id FROM users LIMIT 1"
    ).fetchone()
    demo_password = os.environ.get("SPENDWISE_DEMO_PASSWORD")
    if existing_user is not None or not demo_password:
        return

    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    expense_days = (1, 4, 7, 10, 13, 16, 19, 22)

    expenses = [
        (250.0, "Food", "Lunch"),
        (180.0, "Transport", "Local commute"),
        (2200.0, "Bills", "Monthly utility bill"),
        (600.0, "Health", "Pharmacy purchase"),
        (950.0, "Entertainment", "Movie and refreshments"),
        (1600.0, "Shopping", "Household shopping"),
        (350.0, "Other", "Miscellaneous expense"),
        (420.0, "Food", "Groceries"),
    ]

    try:
        cursor = db.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (
                "Demo User",
                demo_email,
                generate_password_hash(demo_password),
            ),
        )
        user_id = cursor.lastrowid

        for index, (amount, category, description) in enumerate(expenses):
            expense_date = today.replace(day=min(expense_days[index], last_day))
            db.execute(
                """
                INSERT INTO expenses
                    (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    amount,
                    category,
                    expense_date.isoformat(),
                    description,
                ),
            )

        db.commit()
    except sqlite3.Error:
        db.rollback()
        raise
