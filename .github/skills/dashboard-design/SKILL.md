---
name: dashboard-design
description: Design and build the logged-in user dashboard for the SpendWise (Spendly) Flask expense tracker, the page a user lands on after login that shows their own expenses. Use this skill whenever the user asks for a dashboard, home screen, "after login" page, expense overview, spending summary, expense list or category breakdown in SpendWise, even if they don't say "dashboard" explicitly. Covers the route, auth guard, per-user database queries, the Jinja template, vanilla CSS/JS, INR formatting, empty states, responsiveness and pytest tests, all within the project's conventions.
---

# SpendWise user dashboard

Build the page a signed-in user sees: a clear picture of *their own* spending. The app is small and deliberately simple (Flask + SQLite + Jinja + vanilla JS), so the goal is a dashboard that feels native to it, not a bolted-on admin template.

## Before writing anything

Read these, because the repo's rules are strict and the code moves between steps:

- `.github/copilot-instructions.md` (the project's CLAUDE.md): architecture, tech constraints, stub-route policy.
- `app.py`, `database/db.py`, `templates/base.html`, `static/css/style.css`, and one existing test (`tests/test_login_logout.py`) for the fixture pattern.

Then confirm what already exists (don't assume): whether a `/dashboard` route, an expenses query helper or a `dashboard.css` is already there.

## Hard constraints (from the repo)

These come from the project's own rules; breaking them gets the change rejected:

- Routes live in `app.py` only, no blueprints. Route functions fetch data, render, return.
- All SQL lives in `database/db.py`, parameterized with `?`. Never f-strings in SQL.
- Vanilla JS only, no npm packages, no CDN chart libraries. Use CSS bars or inline SVG for charts.
- No new pip packages.
- Templates extend `base.html` and use `url_for()` for every internal link, never hardcoded paths.
- Page-specific styles go in a new CSS file (`static/css/dashboard.css`), linked from the `{% block head %}` block, not inline `<style>` tags. Reuse variables from `style.css`.
- Currency is INR. Display `₹`, never `$`.
- Do not implement stub routes (`/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) unless asked. The dashboard may *link* to `add_expense` via `url_for`, but do not build the add/edit/delete features, and do not render edit/delete controls until those steps exist (the delete stub is a GET route, so never wire it to a one-click link).

## What the dashboard shows

Order matters: the most useful number first, detail below.

1. **Greeting header**: "Good morning, {{ session.user_name }}" plus the current month, and a primary "Add expense" button (`url_for('add_expense')`).
2. **Summary cards** (a row of 3 to 4, same visual language as the landing page `.mock-stat` cards):
   - Total spent this month
   - Change vs last month (percentage, arrow; use `#de6d85` for up/worse, `#63bfa6` for down/better, matching the landing page trend colors)
   - Number of transactions this month
   - Top category this month
3. **Spending by category**: horizontal bars (same pattern as `.mock-bar-row`), sorted descending, with the rupee amount and percentage of the month's total. Cycle the bar colors `#f2a529`, `#62a2d8`, `#8a79c5`, then fall back to `--accent`.
4. **Recent expenses**: a table of the latest 8 to 10 rows (date, description, category, amount, right-aligned and tabular numerals). Show a "View all" link only if a route for it exists.
5. **Empty state**: for a new user with no expenses, replace the cards and table with a friendly message and the Add expense button. A new user is the first thing a real user sees, so this state is not optional.

Keep it to one screen of essentials. Resist adding filters, date pickers or budgets unless the user asks.

## Implementation steps

### 1. Data layer (`database/db.py`)
Add small, single-purpose functions that take `user_id` and return plain dicts/lists, for example `get_month_summary(user_id, year, month)`, `get_category_totals(user_id, year, month)`, `get_recent_expenses(user_id, limit=10)`. Rules that prevent real bugs:

- **Every query filters by `user_id`.** Cross-user leakage is the most serious bug this page can have.
- Dates are stored as ISO `YYYY-MM-DD` text, so month filtering works with `date >= ? AND date < ?` using the first day of the month and first day of next month. Don't use `LIKE` or string slicing.
- Use `COALESCE(SUM(amount), 0)` so empty months return `0`, not `None`.
- Compute last-month change in Python, guarding division by zero (no previous spend: show "No data last month" rather than a percentage).

### 2. Route (`app.py`)
```python
@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login", next=url_for("dashboard")))
    ...  # fetch via db helpers, render_template("dashboard.html", ...)
```
The login view already supports a `next` value and validates it as a safe relative path, so reuse that rather than inventing another mechanism.

Then make login land users here. Today a successful login falls back to `url_for("landing")`; change that fallback to `url_for("dashboard")`, and consider doing the same in the "already signed in" redirects on `/login` and `/register`. Also add a "Dashboard" link in the signed-in navbar in `base.html`. Existing tests assert the old redirect target, so update them in the same change and mention it in your summary.

### 3. Template (`templates/dashboard.html`)
Extend `base.html`, set `{% block title %}Dashboard · SpendWise{% endblock %}`, link `dashboard.css` in `{% block head %}`. Use semantic elements (`<section>`, `<table>` with `<th scope>`, headings in order) and give bars a text equivalent (the amount and percentage in text next to the bar), so meaning never depends on color or width alone. Jinja autoescapes; don't use `|safe` on user-supplied text such as descriptions.

Format money with a Jinja filter registered in `app.py`, not scattered string formatting. Indian grouping puts the first comma after three digits and then every two (`₹1,23,456`):

```python
@app.template_filter("inr")
def inr(value):
    amount = int(round(value or 0))
    digits = str(abs(amount))
    head, tail = digits[:-3], digits[-3:]
    if head:
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        tail = ",".join(groups) + "," + tail
    return f"{'-' if amount < 0 else ''}₹{tail}"
```
Show whole rupees on summary cards; show paise only where a single expense actually has them.

### 4. Styles (`static/css/dashboard.css`)
Match the existing look: warm paper background, white cards with `1px solid var(--border)`, `--radius-md` corners, `DM Serif Display` for the page title and big headings, `DM Sans` for everything else, deep green `--accent` for primary actions. Reuse `.btn-primary` for the Add expense button. Don't introduce new fonts, a dark theme, or a different palette.

Layout: a centered container using `var(--max-width)`, summary cards in a CSS grid. The project's existing breakpoints are `900px` and `600px`; use the same: 4 cards to 2 columns at 900px, single column at 600px, and let the table scroll horizontally in a wrapper (or reflow rows into stacked cards) on phones. Nothing should cause page-level horizontal scroll at 360px.

### 5. JS (`static/js/main.js`, only if needed)
The page works fully without JS. A small enhancement, such as animating bar widths from 0 on load (the existing `.mock-bar` already has a width transition), is fine. Guard any selector so `main.js` doesn't throw on pages that lack the element, since this file loads on every page.

### 6. Tests (`tests/test_dashboard.py`)
Follow the existing fixture (temp SQLite DB via `tmp_path`, `app.config.update(DATABASE=..., TESTING=True)`). Cover at least:

- Logged-out request to `/dashboard` redirects to `/login` with a `next` parameter.
- Successful login redirects to the dashboard.
- Totals and category breakdown are correct for known expenses, including an expense dated last month that must be excluded from "this month".
- **Isolation**: user A never sees user B's expenses.
- Empty state renders for a user with no expenses.
- Amounts render with the `₹` symbol and Indian grouping.

Run `pytest` and fix failures before reporting. Then start the app (`python app.py`, port 5001) and check the page in a browser or screenshot at desktop and ~375px width if you can; passing tests do not show that the layout looks right.

## Finishing up

Summarize in a few lines: what was added, which files changed, any existing tests you updated (and why), and what you deliberately left alone (add/edit/delete). Suggest a commit message in the repo's style, e.g. `feat: add user dashboard with monthly expense summary`. Do not commit unless asked.

## Common mistakes to avoid

- Querying expenses without `user_id`, or trusting a `user_id` from the URL or form rather than the session.
- Hardcoding `/dashboard` or `/login` in templates or redirects.
- Using `$`, `USD`, or Western digit grouping (`1,234,567`) for rupees.
- Pulling in Chart.js or any framework "just for the bars".
- Leaving the new-user empty state as an empty table with headers and no message.
- Checking login with a truthiness test; compare `session.get("user_id") is None`, as the existing code does.