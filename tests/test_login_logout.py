import pytest

from app import app
from database.db import create_user, get_db, init_db


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
    login_response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "secure123"},
    )
    assert login_response.status_code == 302

    if data is None:
        response = getattr(client, method)(path)
    else:
        response = getattr(client, method)(path, data=data)

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
    response = client.post(
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
    response = client.post("/login", data=credentials)

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
    response = client.post("/login", data=credentials)

    assert response.status_code == 200
    assert b"Email and password are required." in response.data


def test_failed_login_preserves_email_without_authenticating(client):
    response = client.post(
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
    safe_response = client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "secure123",
            "next": "/profile",
        },
    )
    unsafe_response = client.post(
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
    client.post(
        "/login",
        data={"email": "test@example.com", "password": "secure123"},
    )
    with client.session_transaction() as current_session:
        current_session["unrelated"] = "preserved"

    response = client.get("/logout")

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
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


@pytest.mark.parametrize(
    "path",
    ["/", "/register", "/privacy-policy", "/terms-and-conditions"],
)
def test_public_routes_remain_accessible(client, path):
    response = client.get(path)

    assert response.status_code == 200
