import calendar
import os
import sqlite3
from datetime import date

from flask import current_app, g
from werkzeug.security import generate_password_hash


DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "expense_tracker.db",
)


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


def seed_db():
    db = get_db()

    existing_user = db.execute(
        "SELECT id FROM users LIMIT 1"
    ).fetchone()
    if existing_user is not None:
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
                "demo@spendly.com",
                generate_password_hash("demo123"),
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
