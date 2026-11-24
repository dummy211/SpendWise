# Implementation Plan: Database Setup

## Current state

- `.github/specs/01-database-setup.md` is the source of truth.
- `database/db.py` is a placeholder with no implementation.
- `app.py` defines the Flask app and existing routes, but has no database setup.
- Existing placeholder routes must remain unchanged.
- No test directory was found during inspection.

## Confirmed decisions and remaining ambiguity

- Use `expense_tracker.db`; this matches the existing `.gitignore` rule.
- Use deterministic seed dates, formatted as `YYYY-MM-DD`, for repeatable tests.
- The seed section calls the field `password`, while the schema requires
  `password_hash`; the demo password must be hashed into `password_hash`.
- The spec does not explicitly define connection teardown, although Flask lifecycle
  cleanup is required by the project instructions; include it in implementation
  unless deliberately rejected.

## Ordered tasks and dependencies

1. **Confirm implementation decisions**
   - Use `expense_tracker.db` and deterministic `YYYY-MM-DD` seed dates.
   - Treat `password_hash` as the persisted field and hash `demo123`.
   - **Depends on:** none.
   - **Files:** plan/spec decision only.

2. **Implement `get_db()`**
   - Open the selected root-level SQLite file.
   - Set `row_factory = sqlite3.Row`.
   - Execute `PRAGMA foreign_keys = ON` on every connection.
   - Reuse the Flask application-context connection and close it at teardown.
   - **Depends on:** task 1.
   - **Files:** `database/db.py`.

3. **Implement `init_db()`**
   - Create `users` and `expenses` with `CREATE TABLE IF NOT EXISTS`.
   - Use the exact specified columns, primary keys, unique email constraint,
     foreign key, required fields, nullable description, and `datetime('now')`
     defaults.
   - Keep all SQL in `database/db.py` and use parameterized SQL for values.
   - **Depends on:** task 2.
   - **Files:** `database/db.py`.

4. **Implement `seed_db()`**
   - Return without writes when users already contain data.
   - Hash `demo123` with `werkzeug.security.generate_password_hash`.
   - Insert one demo user and eight linked expenses.
   - Use exactly the seven approved category values and valid `YYYY-MM-DD` dates.
   - Make the operation transactional and surface failures.
   - **Depends on:** task 3 and task 1’s seed-date decision.
   - **Files:** `database/db.py`.

5. **Wire startup initialization**
   - Import `init_db()` and `seed_db()` into `app.py`.
   - Run both inside `app.app_context()` before routes serve requests.
   - Do not add routes or modify existing placeholder behavior.
   - **Depends on:** tasks 2–4.
   - **Files:** `app.py`.

6. **Add focused database tests**
   - Add tests for database creation, row access, foreign-key enforcement,
     schema constraints, idempotent initialization, hashed demo password,
     eight seeded expenses, category coverage, repeat-safe seeding, and invalid
     foreign-key/duplicate-email errors.
   - Use temporary database paths so tests do not alter the development database.
   - **Depends on:** tasks 2–5.
   - **Files:** new `tests/test_database.py` or the repository’s chosen test module.

7. **Run verification**
   - Run focused tests and the full pytest suite if available.
   - Start/import the app to verify startup initialization succeeds.
   - Confirm existing routes and port 5001 remain unchanged.
   - Confirm no new packages are required and the selected database file remains
     ignored by Git.
   - **Depends on:** task 6.
   - **Files:** none expected.

## Testing criteria

- Startup creates the selected database file.
- `get_db()` returns `sqlite3.Row` rows and enables foreign keys.
- `users` and `expenses` match the specified schema.
- Duplicate user email raises an SQLite integrity error.
- Invalid expense `user_id` raises an SQLite foreign-key integrity error.
- Repeated `init_db()` calls are safe and preserve data.
- Startup or repeated `seed_db()` calls create exactly one demo user and eight
  expenses, with no duplicates.
- The stored demo password is a Werkzeug hash and validates against `demo123`.
- Seeded expenses use only the fixed categories and `YYYY-MM-DD` dates.
- Existing routes remain unchanged and the app continues using port 5001.

## Definition of Done

- `database/db.py` implements `get_db()`, `init_db()`, and `seed_db()`.
- `app.py` initializes and seeds the database inside an application context.
- Schema constraints and foreign-key enforcement work as specified.
- Seed data is hashed, linked, valid, deterministic, and repeat-safe.
- Focused database tests pass, with the full available suite passing.
- No dependencies or unrelated route behavior are changed.
