import re

import pytest

from app import app
from database.db import create_user, get_db, init_db


def _post_with_csrf(client, path, data=None, token_page=None):
    page = client.get(token_page or path, follow_redirects=True)
    match = re.search(rb'name="csrf_token" value="([^"]+)"', page.data)
    assert match is not None
    form_data = dict(data or {})
    form_data["csrf_token"] = match.group(1).decode()
    return client.post(path, data=form_data)


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "test.db"
    app.config.update(
        DATABASE=str(database_path),
        SECRET_KEY="test-secret-key",
        TESTING=True,
    )

    with app.app_context():
        init_db()
        create_user("Test User", "test@example.com", "secure123")

    with app.test_client() as test_client:
        yield test_client


def test_login_page_renders_form_with_generated_action(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b'action="/login"' in response.data
    assert b'name="csrf_token"' in response.data
    assert b'name="email"' in response.data
    assert b'name="password"' in response.data


def test_logged_out_users_can_access_login_and_registration(client):
    assert client.get("/login").status_code == 200
    assert client.get("/register").status_code == 200


@pytest.mark.parametrize(
    ("method", "path", "data"),
    [
        ("get", "/login", None),
        ("get", "/register", None),
        ("post", "/login", {"email": "test@example.com", "password": "secure123"}),
        (
            "post",
            "/register",
            {
                "name": "Another User",
                "email": "another@example.com",
                "password": "secure456",
            },
        ),
    ],
)
def test_authenticated_users_are_redirected_from_auth_routes(
    client, method, path, data
):
    login_response = _post_with_csrf(
        client,
        "/login",
        data={"email": "test@example.com", "password": "secure123"},
    )
    assert login_response.status_code == 302

    if data is None:
        response = getattr(client, method)(path)
    else:
        response = _post_with_csrf(client, path, data=data)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as current_session:
        assert current_session["user_id"] == 1
        assert current_session["user_name"] == "Test User"

    if path == "/register" and method == "post":
        with app.app_context():
            user = get_db().execute(
                "SELECT id FROM users WHERE email = ?",
                ("another@example.com",),
            ).fetchone()
        assert user is None


def test_login_accepts_normalized_email_and_sets_minimal_session(client):
    response = _post_with_csrf(
        client,
        "/login",
        data={
            "email": "  TEST@EXAMPLE.COM ",
            "password": "secure123",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as current_session:
        assert current_session["user_name"] == "Test User"
        assert current_session["user_id"] == 1
        assert set(current_session) == {"user_id", "user_name"}

    landing = client.get("/")
    assert b"Test User" in landing.data
    assert b'Sign out' in landing.data
    assert b"Get started" not in landing.data


@pytest.mark.parametrize(
    "credentials",
    [
        {"email": "unknown@example.com", "password": "secure123"},
        {"email": "test@example.com", "password": "wrongpass"},
    ],
)
def test_login_uses_same_error_for_unknown_email_and_wrong_password(
    client, credentials
):
    response = _post_with_csrf(client, "/login", data=credentials)

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    assert (
        b"unknown@example.com" in response.data
        or b"test@example.com" in response.data
    )
    with client.session_transaction() as current_session:
        assert "user_id" not in current_session
        assert "user_name" not in current_session


@pytest.mark.parametrize(
    "credentials",
    [
        {},
        {"email": "", "password": "secure123"},
        {"email": "test@example.com", "password": ""},
        {"email": "test@example.com", "password": "        "},
    ],
)
def test_login_rejects_missing_or_blank_credentials(client, credentials):
    response = _post_with_csrf(client, "/login", data=credentials)

    assert response.status_code == 200
    assert b"Email and password are required." in response.data


def test_failed_login_preserves_email_without_authenticating(client):
    response = _post_with_csrf(
        client,
        "/login",
        data={"email": "  TEST@example.com ", "password": "wrongpass"},
    )

    assert b'value="  TEST@example.com "' in response.data
    assert b"wrongpass" not in response.data
    with client.session_transaction() as current_session:
        assert "user_id" not in current_session
        assert "user_name" not in current_session


@pytest.mark.parametrize(
    "next_url",
    [
        "https://example.com",
        "//example.com",
        "/\\example.com",
        "javascript:alert(1)",
    ],
)
def test_login_redirects_only_to_safe_relative_next_url(client, next_url):
    safe_response = _post_with_csrf(
        client,
        "/login",
        data={
            "email": "test@example.com",
            "password": "secure123",
            "next": "/profile",
        },
    )
    unsafe_response = _post_with_csrf(
        client,
        "/login",
        data={
            "email": "test@example.com",
            "password": "secure123",
            "next": next_url,
        },
    )

    assert safe_response.headers["Location"].endswith("/profile")
    assert unsafe_response.headers["Location"].endswith("/dashboard")


def test_logout_clears_authentication_and_returns_to_guest_navigation(client):
    _post_with_csrf(
        client,
        "/login",
        data={"email": "test@example.com", "password": "secure123"},
    )
    with client.session_transaction() as current_session:
        current_session["unrelated"] = "preserved"

    response = _post_with_csrf(client, "/logout", token_page="/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as current_session:
        assert "user_id" not in current_session
        assert "user_name" not in current_session
        assert current_session["unrelated"] == "preserved"

    landing = client.get("/")
    assert b"Sign in" in landing.data
    assert b"Get started" in landing.data
    assert b"Sign out" not in landing.data


def test_logout_is_safe_when_user_is_not_logged_in(client):
    assert client.get("/logout").status_code == 405
    response = _post_with_csrf(client, "/logout", token_page="/login")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


@pytest.mark.parametrize("token", ["", "invalid-token"])
def test_logout_rejects_missing_or_invalid_csrf_token(client, token):
    client.get("/login")

    response = client.post("/logout", data={"csrf_token": token})

    assert response.status_code == 400


def test_login_rejects_missing_or_invalid_csrf_token(client):
    for token in ("", "invalid-token"):
        response = client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "secure123",
                "csrf_token": token,
            },
        )
        assert response.status_code == 400


@pytest.mark.parametrize("secret_key", [None, "dev-only-change-me"])
def test_requests_require_a_non_default_secret_key(client, monkeypatch, secret_key):
    monkeypatch.setitem(app.config, "SECRET_KEY", secret_key)

    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        client.get("/")


@pytest.mark.parametrize(
    "path",
    ["/", "/register", "/privacy-policy", "/terms-and-conditions"],
)
def test_public_routes_remain_accessible(client, path):
    response = client.get(path)

    assert response.status_code == 200
