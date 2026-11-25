# User Dashboard Implementation Plan

## Problem and proposed approach

SpendWise has a working login session and an `expenses` table, but no dashboard route. Add a dedicated, authenticated `/dashboard` page that previews current-month spending and gives users clear category and transaction details. For the current preview, use a fixed sample dataset in the route rather than querying saved expenses.

The user selected an **expense-only, hardcoded demo-data** scope. Do not add income storage, an income-entry route, or balance calculations. Label sample values prominently as demo data so they are not mistaken for saved transactions. Keep the dashboard route restricted to authenticated users and leave the expense-entry/edit/delete stubs untouched. The existing `.github/specs/04-user-dashboard.md` describes income tracking; this plan follows the user's current scope instead.

## Dashboard design

- Start with a greeting using the signed-in user's name, the current month, and a primary Add expense link generated with `url_for('add_expense')`. Leave the existing add-expense stub implementation untouched.
- Show four responsive summary cards: total spent this month; change against the previous month; this month's transaction count; and the top spending category. If there is no previous-month spending, show “No data last month” instead of a misleading percentage.
- Show current-month category totals as descending horizontal bars. Put rupee amount and percentage in text beside each bar so color and width are not the only source of information.
- Show the latest 10 expenses in a semantic table with date, description, category, and right-aligned amount. Do not show edit/delete controls or a “View all” link unless an actual destination exists.
- For a user with no expenses, replace the summary and transaction content with a friendly empty state and the Add expense action.
- Match existing paper/card colors, typography, spacing, CSS variables, and breakpoints. Use the existing dashboard skill's chart color classes/patterns where compatible with project CSS-variable rules; do not add a chart library. Keep the table usable on narrow screens without causing page-level horizontal overflow.
- The dashboard is server-rendered and uses in-memory sample records, so avoid a simulated client-side loading skeleton. Keep the explicit empty/error template states available for future data-backed behavior.

## Implementation tasks

1. **Create and summarize sample records in `app.py`.** Hardcode representative current- and previous-month expense records, derive month totals, change, category totals, and recent expenses from them, and do not query or seed dashboard data from SQLite.
2. **Add the protected dashboard flow in `app.py`.** Add `GET /dashboard`, redirect anonymous users to login with a safe `next` destination, and make the default successful-login redirect and already-authenticated login/registration redirects land on the dashboard. Register an `inr` template filter for Indian digit grouping; show whole rupees for summaries and retain paise for individual expenses when present.
3. **Build the page and navigation.** Create `templates/dashboard.html` extending `base.html`, add the authenticated-only Dashboard link to `templates/base.html`, and create `static/css/dashboard.css` linked through the template's head block. Use semantic headings/table headers, visible focus, sufficient contrast, text equivalents for chart values, and responsive styles aligned with the project's 900px/600px breakpoints. Leave JavaScript unchanged unless a concrete progressive enhancement is needed.
4. **Add focused tests.** Create `tests/test_dashboard.py` using the existing temporary SQLite database fixture pattern. Cover anonymous redirect and safe `next`, successful-login destination, current/previous month aggregation, category ordering and percentages, recent-row limit/order, user isolation, empty state, and INR grouping. Update `tests/test_login_logout.py` expectations that currently assert the landing page as the default authenticated destination.
5. **Validate.** Run the targeted dashboard and login/logout tests, then the full `pytest` suite. Start the app on its existing port (5001) and inspect desktop and approximately 375px layouts if browser tooling is available; confirm the expense stubs were not implemented.

## Files and scope

- **Create:** `templates/dashboard.html`, `static/css/dashboard.css`, `tests/test_dashboard.py`
- **Modify:** `app.py`, `templates/base.html`, `tests/test_login_logout.py`
- **Do not modify:** dashboard database queries or schema, income schema/routes, add/edit/delete expense stub implementations, or dependency manifests.

## Notes and considerations

- The current database already defines `expenses` with `user_id`, amount, category, ISO date, and optional description. The login stores `user_id` and `user_name` in the Flask session and defaults to the landing page. Any saved expenses, including the seeded dummy account's records, are intentionally not used by the demo dashboard.
- `templates/base.html` and `static/css/style.css` contain the shared navigation and existing design tokens/card/bar patterns. Existing login/logout tests use a `tmp_path` SQLite database and assert the current landing-page redirects.
- Keep all internal URLs generated with `url_for()` and retain the current safe-relative redirect validation. Never use a browser-supplied user ID to query financial data.
- The existing Step 04 spec conflicts with the user's selected expense-only scope. Do not silently implement its income features; reconcile the spec separately before implementation if needed.

## Implementation status

Implemented the authenticated dashboard with clearly labeled hardcoded sample data, INR formatting, responsive styling, and dashboard/login tests. The full test suite passes (36 tests). The dashboard route was verified with Flask's test client; a browser screenshot check was unavailable.
