# Spec: User Dashboard

## Overview

Add a responsive, authenticated dashboard as the default destination after login. It gives each user a current-month view of recorded income, expenses, and balance, a six-month spending trend, recent income and expense transactions, and a category breakdown. Because the existing database stores expenses but has no income data or income-entry flow, this step adds a minimal per-user income ledger and a protected income-entry action so that income and balance figures are based on real user-provided data.

## Depends on

- Step 01 — Database Setup must provide the SQLite connection and existing `users` and `expenses` tables.
- Step 02 — Registration must provide user accounts.
- Step 03 — Login and Logout must provide the authenticated Flask session.

## Routes

- `GET /dashboard` — show the authenticated user's summaries and transactions — logged-in
- `POST /income/add` — validate and save an income record for the authenticated user, then redirect to the dashboard — logged-in

Unauthenticated dashboard and income requests must redirect to login with a safe `next` destination. A successful login without a valid explicit `next` destination must redirect to `/dashboard`.

## Database changes

Add an `incomes` table in `database/db.py`:

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `user_id INTEGER NOT NULL` referencing `users(id)`
- `amount REAL NOT NULL` with a positive-amount constraint
- `source TEXT NOT NULL`
- `date TEXT NOT NULL` in `YYYY-MM-DD` format
- `description TEXT` nullable
- `created_at TEXT` with a `datetime('now')` default

Enable the existing per-connection foreign-key enforcement. Add parameterized database helpers to record an income and retrieve the authenticated user's dashboard data. Do not alter the existing `expenses` schema. Calculate current-calendar-month income, expenses, and balance (income minus expenses); calculate the spending trend over the current and previous five calendar months; use the current month for category totals; and show the eight most recent income or expense records, ordered by date and then ID descending. Scope every query by the authenticated user's ID.

## Templates

- **Create:** `templates/dashboard.html` — extend `base.html`; render financial summaries, spending visualizations, recent transactions, an income-entry form, and explicit empty and error states.
- **Modify:** `templates/base.html` — add a dashboard navigation link for authenticated users.

## Files to change

- `app.py` — add protected dashboard and income-entry routes; redirect the default successful-login destination and authenticated visitors from login/registration to the dashboard.
- `database/db.py` — add the income schema, income persistence helper, and user-scoped dashboard queries.
- `templates/base.html` — expose dashboard navigation to authenticated users.
- `static/js/main.js` — provide accessible pending feedback for income-form submission without making the dashboard depend on JavaScript.
- `tests/test_login_logout.py` — update successful-login and authenticated auth-route expectations for the dashboard destination.

## Files to create

- `templates/dashboard.html`
- `static/css/dashboard.css`
- `tests/test_dashboard.py`

## New dependencies

No new dependencies. Use Flask, SQLite, Jinja, CSS, and vanilla JavaScript already in the project.

## Rules for implementation

- No SQLAlchemy or ORMs.
- Use parameterized queries only.
- Passwords must continue to be hashed with Werkzeug; do not change the existing password handling.
- Use CSS variables — never hardcode hex values in templates or CSS.
- All templates extend `base.html`.
- Keep routes in `app.py` and all database operations in `database/db.py`.
- Use the authenticated session's `user_id` for ownership; never accept an owner ID from submitted form data. Scope every financial query and write to that user.
- Validate income amount as a positive number, require a non-empty source, and accept only a valid date. Return useful form feedback without storing invalid data.
- Preserve the existing safe-relative-URL validation for `next`; use `/dashboard` as the fallback, not an unvalidated redirect target.
- Use Indian Rupees (`₹`) for displayed amounts. Never infer, fabricate, or seed income values; until the user records income, show a clear unrecorded-income state and do not imply that expenses alone are a net balance.
- Reuse the existing color, typography, spacing, and card conventions. Keep the layout usable on mobile, tablet, and desktop, and do not add a charting library.
- Make charts understandable without color alone and provide accessible labels or text summaries. Use semantic headings, visible focus, and keyboard-operable controls.
- Render useful empty states when the user has no income or expenses. Show an explicit error state and log unexpected dashboard database failures; do not silently substitute zero totals for failed queries.
- Provide pending feedback for income submission where JavaScript is available while preserving normal form submission if it is not.
- Do not implement the profile or expense add/edit/delete placeholder routes as part of this feature.

## Definition of done

- [ ] An unauthenticated request to `/dashboard` redirects to login with a safe `next` destination; after login, the user reaches the dashboard.
- [ ] An unauthenticated `POST /income/add` cannot create a record.
- [ ] A logged-in user can load the dashboard, and dashboard navigation is shown only in the authenticated navigation.
- [ ] Dashboard totals, six-month trend, current-month category breakdown, and recent transactions are calculated from persisted data belonging only to the signed-in user.
- [ ] Current-month balance equals recorded income minus expenses for that same month; absent income is clearly identified and is never fabricated.
- [ ] A valid income submission is saved against the signed-in user and appears in the dashboard; invalid, missing, non-positive, or malformed values do not create a record and produce useful feedback.
- [ ] Data from one user is not visible in another user's dashboard, even when both users have income and expense records.
- [ ] Empty income and expense data render helpful empty states; unexpected dashboard query failures produce a visible error response rather than misleading zero totals.
- [ ] The dashboard and its visualizations remain usable at mobile, tablet, and desktop widths and expose chart information accessibly.
- [ ] Income submission exposes a pending state with JavaScript enabled and remains functional without JavaScript.
- [ ] All displayed financial amounts use INR formatting, and no new dependencies are required.
- [ ] Existing registration, login validation, logout, landing, privacy, and terms behavior remains covered by the test suite.
