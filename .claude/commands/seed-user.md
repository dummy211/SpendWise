---
description: Create a single dummy user in the database
---

From the repository root, read `database/db.py` and `app.py` to confirm the
users table schema and Flask database setup.

Generate one realistic Indian first and last name, then derive a Gmail address
from the name with a random 2-3 digit suffix. Use the existing Flask app and
database helper in a short Python script:

1. Import `app` from `app.py` and `get_db` from `database.db`.
2. Enter `app.app_context()` before calling `get_db()`.
3. Check whether the generated email already exists. If it does, generate a
   new suffix until it is unique.
4. Insert the user with a parameterized query, hash `"password123"` using
   `werkzeug.security.generate_password_hash`, and set `created_at` to the
   current datetime.
5. Commit the insert and print the new user's `id`, `name`, and `email`.

Run the script with the repository's Python interpreter. Do not modify
application source files or create additional users.
