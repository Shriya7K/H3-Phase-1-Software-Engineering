"""Task #9 - Create and edit student profile (FR-04)."""

from __future__ import annotations

import sqlite3


def test_profile_requires_login(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_page_renders_with_existing_data(auth_client):
    response = auth_client.get("/profile")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Student Profile" in body
    assert "Aditi Sharma" in body
    assert "PES1UG24CS001" in body
    assert "Computer Science and Engineering" in body
    assert "8.85" in body
    assert "Python, Flask, SQL" in body


def test_successful_profile_update(auth_client, app):
    response = auth_client.post(
        "/profile",
        data={
            "name": "Aditi S. Sharma",
            "usn": "PES1UG24CS999",
            "phone": "+91 91234 56789",
            "department": "Artificial Intelligence & Machine Learning",
            "batch_year": "2027",
            "cgpa": "9.25",
            "skills": "Python, PyTorch, SQL, FastAPI, Docker",
            "bio": "AI & ML enthusiast focused on large-scale distributed systems.",
            "github_url": "https://github.com/aditi-ml",
            "linkedin_url": "https://linkedin.com/in/aditi-ml",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Profile updated successfully!" in body
    assert "Aditi S. Sharma" in body
    assert "PES1UG24CS999" in body
    assert "9.25" in body

    # Verify directly in SQLite
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    prof = db.execute("SELECT * FROM student_profiles WHERE user_id = 1").fetchone()
    user = db.execute("SELECT name FROM users WHERE id = 1").fetchone()
    db.close()

    assert user["name"] == "Aditi S. Sharma"
    assert prof["usn"] == "PES1UG24CS999"
    assert prof["cgpa"] == 9.25
    assert prof["department"] == "Artificial Intelligence & Machine Learning"
    assert prof["batch_year"] == 2027


def test_profile_update_invalid_cgpa_rejected(auth_client):
    response = auth_client.post(
        "/profile",
        data={
            "name": "Aditi Sharma",
            "cgpa": "11.5",  # Scale is 0.0 - 10.0
        },
    )
    assert response.status_code == 400
    assert "between 0.0 and 10.0" in response.get_data(as_text=True)


def test_profile_update_invalid_batch_year_rejected(auth_client):
    response = auth_client.post(
        "/profile",
        data={
            "name": "Aditi Sharma",
            "batch_year": "1890",
        },
    )
    assert response.status_code == 400
    assert "between 2000 and 2099" in response.get_data(as_text=True)


def test_profile_update_empty_name_rejected(auth_client):
    response = auth_client.post(
        "/profile",
        data={
            "name": "   ",
        },
    )
    assert response.status_code == 400
    assert "Name cannot be empty" in response.get_data(as_text=True)
