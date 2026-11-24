# Implementation Plan: Registration

## Objective

Implement Step 02 registration as a public `GET`/`POST /register` flow using
the existing `users` schema and responsive auth template.

## Design

- Validate required name, email, and password fields in `app.py`.
- Trim name and email, lowercase email, and require passwords of at least eight
  characters.
- Keep user creation in `database/db.py` with parameterized SQL.
- Hash passwords with Werkzeug before insertion.
- Convert duplicate email integrity errors into a form error.
- Preserve safe name/email values on failed submissions and never repopulate the
  password field.
- Redirect successful registration to the existing `/login` route.

## Files

- Modify `app.py` for POST handling and validation.
- Modify `database/db.py` for the registration database helper.
- Modify `templates/register.html` to use `url_for` and preserve safe values.
- Create `tests/test_registration.py` for focused registration coverage.

## Verification

- GET registration renders successfully.
- Valid registration creates one normalized-email user with a verifiable
  Werkzeug hash.
- Missing fields and short passwords are rejected.
- Duplicate emails, including case variants, are rejected without duplication.
- Successful registration redirects to login.
- Existing schema and unrelated routes remain unchanged.

## Non-goals

Login sessions, logout, profile, expense CRUD, schema changes, new packages,
JavaScript, and visual redesign.
