"""Task #6 - User registration (FR-01, SR-02, SR-05, TC-01, TC-13)."""

from __future__ import annotations

import sqlite3
from werkzeug.security import check_password_hash


def test_registration_page_renders(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create account" in response.data
    assert b"Full Name" in response.data
    assert b"Campus Email" in response.data
    assert b"Password" in response.data


def test_already_logged_in_user_visiting_register_is_redirected(auth_client):
    response = auth_client.get("/register")
    assert response.status_code == 302
    assert "/opportunities" in response.headers["Location"]


def test_successful_user_registration(client, app):
    response = client.post(
        "/register",
        data={
            "name": "Rohan Deshmukh",
            "email": "rohan.d@campus.edu",
            "password": "securepassword123",
            "confirm_password": "securepassword123",
            "role": "student",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Registration successful!" in body

    # Verify user exists in database
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    user = db.execute(
        "SELECT * FROM users WHERE email = 'rohan.d@campus.edu'"
    ).fetchone()
    db.close()

    assert user is not None
    assert user["name"] == "Rohan Deshmukh"
    assert user["role"] == "student"


def test_password_is_stored_as_salted_hash_not_plaintext(client, app):
    """SR-02 & TC-13: Passwords must be salted one-way hashes, never plaintext."""
    raw_password = "MySuperSecretPassword#2026"
    client.post(
        "/register",
        data={
            "name": "Kavya Nair",
            "email": "kavya.n@campus.edu",
            "password": raw_password,
            "confirm_password": raw_password,
            "role": "student",
        },
    )

    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    user = db.execute(
        "SELECT password_hash FROM users WHERE email = 'kavya.n@campus.edu'"
    ).fetchone()
    db.close()

    assert user is not None
    stored_hash = user["password_hash"]
    # Plaintext must NOT appear in the database
    assert raw_password not in stored_hash
    # Must be valid hash verifiable by check_password_hash
    assert check_password_hash(stored_hash, raw_password) is True


def test_duplicate_registration_rejected(client):
    """TC-01: No duplicate account with the same email."""
    # student@campus.edu already exists in seed data
    response = client.post(
        "/register",
        data={
            "name": "Another Student",
            "email": "student@campus.edu",
            "password": "password123",
            "confirm_password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 400
    body = response.get_data(as_text=True)
    assert "An account with this email already exists" in body


def test_registration_password_mismatch_rejected(client):
    response = client.post(
        "/register",
        data={
            "name": "Test User",
            "email": "mismatch@campus.edu",
            "password": "password123",
            "confirm_password": "differentPassword456",
            "role": "student",
        },
    )
    assert response.status_code == 400
    body = response.get_data(as_text=True)
    assert "Passwords do not match" in body


def test_registration_short_password_rejected(client):
    response = client.post(
        "/register",
        data={
            "name": "Test User",
            "email": "short@campus.edu",
            "password": "123",
            "confirm_password": "123",
            "role": "student",
        },
    )
    assert response.status_code == 400
    body = response.get_data(as_text=True)
    assert "at least 6 characters" in body


def test_registration_invalid_email_rejected(client):
    response = client.post(
        "/register",
        data={
            "name": "Test User",
            "email": "invalid-email-format",
            "password": "password123",
            "confirm_password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 400
    body = response.get_data(as_text=True)
    assert "valid email address" in body


def test_registration_missing_name_rejected(client):
    response = client.post(
        "/register",
        data={
            "name": "   ",
            "email": "noname@campus.edu",
            "password": "password123",
            "confirm_password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 400
    body = response.get_data(as_text=True)
    assert "valid full name" in body


def test_newly_registered_user_can_login(client):
    client.post(
        "/register",
        data={
            "name": "Siddharth Rao",
            "email": "sid.rao@campus.edu",
            "password": "mypassword999",
            "confirm_password": "mypassword999",
            "role": "student",
        },
    )

    login_resp = client.post(
        "/login",
        data={"email": "sid.rao@campus.edu", "password": "mypassword999"},
        follow_redirects=True,
    )
    assert login_resp.status_code == 200
    body = login_resp.get_data(as_text=True)
    assert "Welcome back, Siddharth!" in body


def test_api_register_endpoint(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "API Candidate",
            "email": "api.candidate@campus.edu",
            "password": "apipassword123",
            "role": "student",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "Account created successfully" in data["message"]
