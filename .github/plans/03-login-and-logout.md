# Implementation Plan: Login and Logout

## Objective

Implement Step 03 authentication with a working `GET`/`POST /login` flow,
Flask session state, and an idempotent logout route. The change should reuse
the existing registration and users schema without implementing profile or
expense functionality.

## Design

- Add an explicit Flask secret key in `app.py` so signed session cookies work
  consistently in development and tests.
- Keep database access out of routes:
  - Add a parameterized `authenticate_user(email, password)` helper in
    `database/db.py`.
  - Look up the normalized email and verify its Werkzeug password hash.
  - Return only safe user fields such as `id` and `name`, not the hash.
- Extend `app.py` login handling:
  - Render `login.html` for GET requests.
  - Trim and lowercase submitted email for lookup.
  - Validate that email and password are present; whitespace-only passwords
    should be rejected.
  - Use one generic invalid-credentials error for unknown email and wrong
    password.
  - Preserve a failed submission's submitted email while never repopulating
    password.
  - On success, store only `user_id` and `user_name` in the Flask session.
  - Redirect to the landing page by default, or to a safe relative `next`
    destination if one is supplied.
- Replace the logout placeholder:
  - Remove `user_id` and `user_name` without clearing unrelated session data.
  - Redirect to the landing page.
  - Keep logout safe and successful when no user is currently logged in.
- Conditionalize `templates/base.html` navigation:
  - Guest navigation shows Sign in and Get started.
  - Authenticated navigation shows the user's name and a logout link.
  - Require both session keys before rendering the authenticated state.
- Update `templates/login.html`:
  - Generate the form action with `url_for('login')`.
  - Bind failed-login email into the email input.
  - Keep password blank after every response.

## Files

- Modify `app.py`
  - Configure the session secret.
  - Import Flask session utilities and the authentication helper.
  - Implement GET/POST login.
  - Implement working logout.
- Modify `database/db.py`
  - Import `check_password_hash`.
  - Add the parameterized authenticated-user lookup and verification helper.
- Modify `templates/login.html`
  - Replace hardcoded form action.
  - Preserve failed-login email and retain route-provided errors.
- Modify `templates/base.html`
  - Render guest or authenticated navigation from session state.
  - Use `url_for()` for login, registration, and logout links.
- Create `tests/test_login_logout.py`
  - Use the repository's existing temporary-database Flask test fixture pattern.

## Test Plan

- Verify `GET /login` returns 200 and renders the login form.
- Verify a valid seeded or registered user can log in with a mixed-case,
  whitespace-padded email.
- Verify success creates a session containing only `user_id` and `user_name`.
- Verify successful login redirects to landing and updates navbar state.
- Verify unknown emails and wrong passwords return the same generic 200
  response and do not create a session.
- Verify missing or whitespace-only email/password fields return a validation
  error.
- Verify a failed login against an already authenticated session preserves the
  existing session keys.
- Verify `GET /logout` removes both authentication keys and redirects to `/`.
- Verify logout from an already logged-out state remains safe and redirects.
- Verify failed-login email is retained and password is not rendered back.
- Verify existing registration tests still pass.
- Verify public landing, registration, privacy-policy, and terms routes remain
  accessible.
- Run `pytest` for the focused login/logout tests and the full suite.

## Verification

- Login credentials work through the demo user and newly registered users.
- Password hashes are never exposed or stored in session values.
- Unknown-email and wrong-password responses are indistinguishable.
- Logout removes all authentication state and guest navigation returns.
- No database schema or package changes are introduced.
- Existing registration behavior remains unchanged.
- The app remains runnable on port 5001.

## Non-goals

Profile routes, expense CRUD, password reset, remember-me behavior, OAuth,
database migrations, server-side session storage packages, schema redesign,
JavaScript behavior, and visual redesign.
