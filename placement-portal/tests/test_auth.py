"""Task #7 - user login and logout."""

from __future__ import annotations

import pytest

from conftest import STUDENT


# -- Access control --------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    ["/opportunities", "/opportunities/1", "/aptitude-tests"],
)
def test_protected_pages_redirect_anonymous_users(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_index_redirects_anonymous_user_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in" in response.data


# -- Successful login ------------------------------------------------------


def test_login_with_valid_credentials(client):
    response = client.post("/login", data=STUDENT, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/opportunities")

    with client.session_transaction() as session:
        assert session["user_id"] is not None
        assert session["user_name"] == "Aditi Sharma"
        assert session["user_role"] == "student"


def test_login_is_case_insensitive_on_email_and_trims_spaces(client):
    response = client.post(
        "/login",
        data={"email": "  STUDENT@Campus.EDU  ", "password": "student123"},
    )
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session["user_role"] == "student"


def test_admin_can_log_in(client):
    response = client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session["user_role"] == "admin"


def test_already_logged_in_user_visiting_login_is_redirected(auth_client):
    response = auth_client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/opportunities")


def test_login_with_next_redirects_there(client):
    response = client.post(
        "/login?next=/aptitude-tests", data=STUDENT
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/aptitude-tests"


def test_login_with_external_next_is_ignored(client):
    for target in ("https://evil.example.com", "//evil.example.com", "javascript:alert(1)"):
        client.post("/logout")
        response = client.post(f"/login?next={target}", data=STUDENT)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/opportunities")


# -- Failed login ----------------------------------------------------------


def test_login_with_wrong_password(client):
    response = client.post(
        "/login", data={"email": "student@campus.edu", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert b"Invalid email or password" in response.data
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_login_with_unknown_email_uses_same_error_as_wrong_password(client):
    response = client.post(
        "/login", data={"email": "nobody@campus.edu", "password": "student123"}
    )
    assert response.status_code == 401
    assert b"Invalid email or password" in response.data
    # The message must not reveal whether the account exists.
    assert b"not found" not in response.data.lower()


def test_login_with_missing_fields(client):
    for payload in (
        {},
        {"email": "", "password": ""},
        {"email": "student@campus.edu", "password": ""},
        {"email": "", "password": "student123"},
    ):
        response = client.post("/login", data=payload)
        assert response.status_code == 401


def test_login_keeps_email_filled_after_failure(client):
    response = client.post(
        "/login", data={"email": "student@campus.edu", "password": "nope"}
    )
    assert b'value="student@campus.edu"' in response.data


# -- Logout ----------------------------------------------------------------


def test_logout_clears_session(auth_client):
    response = auth_client.post("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    with auth_client.session_transaction() as session:
        assert "user_id" not in session

    response = auth_client.get("/opportunities")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logout_requires_post(auth_client):
    assert auth_client.get("/logout").status_code == 405


def test_login_after_logout_works(auth_client):
    auth_client.post("/logout")
    response = auth_client.post("/login", data=STUDENT)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/opportunities")


def test_stale_session_for_deleted_user_is_cleared(client, app):
    """A session cookie pointing at a removed user must not grant access."""
    client.post("/login", data=STUDENT)
    with client.session_transaction() as session:
        session["user_id"] = 424242  # no such user

    response = client.get("/opportunities")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    with client.session_transaction() as session:
        assert "user_id" not in session
