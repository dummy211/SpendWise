# Spec: Registration

## Overview

This feature converts the existing `/register` page into a working account-creation flow. It is the second SpendWise roadmap step and lets a public visitor validate an account form, create a unique user in SQLite, and receive a clear success or error result.

## Depends on

- Step 01 — Database Setup must provide the `users` table and database connection helpers.

## Routes

- `GET /register` — render the registration form — public
- `POST /register` — validate and create a user account — public

## Database changes

No schema changes.

The existing `users` table will be used:

- `name TEXT NOT NULL`
- `email TEXT NOT NULL UNIQUE`
- `password_hash TEXT NOT NULL`

Registration database logic must be implemented in `database/db.py`, not inline in `app.py`.

## Templates

- **Create:** No new templates.
- **Modify:** `templates/register.html`
  - Use `url_for('register')` for the form action.
  - Preserve the existing form field names: `name`, `email`, and `password`.
  - Display success or error feedback supplied by the route.

## Files to change

- `app.py`
- `database/db.py`
- `templates/register.html`

## Files to create

- No new files.

## New dependencies

No new dependencies.

Use Werkzeug's existing password hashing support and Python's existing `sqlite3` module.

## Rules for implementation

- No SQLAlchemy or other ORMs.
- Use parameterized queries only.
- Hash passwords with `werkzeug.security.generate_password_hash`.
- Never store plaintext passwords.
- Use SQLite's unique email constraint and handle duplicate-email registration as a form error.
- Validate that name, email, and password are present.
- Trim name and email before storing them.
- Use a minimum password length of 8 characters.
- Normalize email for uniqueness consistently, such as lowercasing it before database lookup and insert.
- Use CSS variables; never hardcode hex values in templates or CSS changes.
- All templates extend `base.html`.
- Keep database operations in `database/db.py`.
- Use `abort()` for HTTP errors where appropriate.
- Do not implement login, logout, profile, or expense behavior in this step.
- Preserve the existing `GET /register` page and responsive auth styling.

## Definition of done

- [ ] `GET /register` renders the existing registration page without errors.
- [ ] A valid name, email, and password creates a user in the `users` table.
- [ ] The stored password is a Werkzeug password hash and not plaintext.
- [ ] A duplicate email displays an error and does not create another user.
- [ ] Missing or blank name, email, or password displays a validation error.
- [ ] A password shorter than 8 characters displays a validation error.
- [ ] Successful registration redirects to the login page or displays an unambiguous success state.
- [ ] Existing `GET /login`, `GET /`, and footer routes remain accessible.
- [ ] All database writes use parameterized SQL.
- [ ] The app starts on port 5001 and the feature works through a browser or test client.
