# Spec: Login and Logout

## Overview

This feature implements account authentication for SpendWise by converting the existing login page into a working credential-validation flow and replacing the logout placeholder with session termination. It is the third roadmap step and establishes the logged-in state needed by profile and expense features.

## Depends on

- Step 01 — Database Setup must provide the `users` table and database connection helpers.
- Step 02 — Registration must allow users to exist with normalized emails and Werkzeug password hashes.

## Routes

- `GET /login` — render the login form — public
- `POST /login` — validate credentials and start a logged-in session — public
- `GET /logout` — clear the logged-in session and redirect — logged-in

## Database changes

No database schema changes.

The existing `users` table will be used:

- `id`
- `name`
- `email`
- `password_hash`

Add a database helper in `database/db.py` that looks up a user by normalized email and verifies the submitted password with Werkzeug.

## Templates

- **Create:** No new templates.
- **Modify:** `templates/login.html`
  - Use `url_for('login')` for the form action.
  - Preserve `email` and `password` field names.
  - Preserve a submitted email value after a failed login.
  - Display authentication errors supplied by the route.
- **Modify:** `templates/base.html`
  - Show login and registration links for logged-out visitors.
  - Show the user's name and a logout link for logged-in users.
  - Use `url_for()` for every internal link.

## Files to change

- `app.py`
- `database/db.py`
- `templates/login.html`
- `templates/base.html`

## Files to create

- `tests/test_login_logout.py`

## New dependencies

No new dependencies.

Use Flask sessions and Werkzeug's existing `check_password_hash` support.

## Rules for implementation

- No SQLAlchemy or other ORMs.
- Use parameterized queries only.
- Hash passwords with Werkzeug; never store plaintext passwords.
- Verify passwords with `werkzeug.security.check_password_hash`.
- Normalize submitted emails by trimming and lowercasing them.
- Use Flask's server-side session configuration to store only the authenticated user's ID and name.
- Configure a stable Flask secret key suitable for development and tests.
- Failed login must not reveal whether the email or password was incorrect; use a generic invalid-credentials error.
- Missing email or password must display a validation error.
- Successful login must redirect to the landing page or the next protected destination when one is specified.
- Logout must remove authentication data from the session and redirect to the landing page.
- Keep database operations in `database/db.py`.
- Use CSS variables; never hardcode hex values in templates or CSS changes.
- All templates extend `base.html`.
- Use `abort()` for HTTP errors where appropriate.
- Do not implement profile or expense routes in this step.
- Preserve existing registration and public page behavior.

## Definition of done

- [ ] `GET /login` renders the existing login page without errors.
- [ ] A valid registered email and password creates a logged-in Flask session.
- [ ] Successful login redirects to a defined destination and shows the authenticated state in navigation.
- [ ] An unregistered email displays a generic invalid-credentials error.
- [ ] An incorrect password displays a generic invalid-credentials error.
- [ ] Missing or blank email or password displays a validation error.
- [ ] Failed login does not create a session or remove an existing session unexpectedly.
- [ ] The login form action uses `url_for('login')`.
- [ ] `GET /logout` clears the session and redirects to the landing page.
- [ ] After logout, navigation no longer shows authenticated-user controls.
- [ ] Password verification uses the Werkzeug hash and never stores plaintext credentials.
- [ ] All database reads use parameterized SQL.
- [ ] Existing registration, landing, privacy, and terms routes remain accessible.
- [ ] The app starts on port 5001 and the feature works through a browser or test client.
