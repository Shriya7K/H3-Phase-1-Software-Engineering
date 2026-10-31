"""Task #10 - Validate profile details (FR-04, SR-05, TC-11).

Tests server-side field-level validation and sanitization for student academic
and contact profile updates:
  - USN format (alphanumeric, length boundaries, special characters rejection)
  - Phone number validation (digits, allowed formatting chars, length limits)
  - Portfolio / social URL validation (http/https protocols, injection prevention)
  - Text length boundaries (bio <= 1000 chars, skills <= 500 chars)
  - XSS payload handling and rejection
"""

from __future__ import annotations

import sqlite3


def test_profile_update_valid_usn_formats(auth_client, app):
    """Valid alphanumeric USN formats (with optional hyphens) are accepted."""
    valid_usns = ["PES1UG24CS453", "1MS21CS001", "PES2-2024-999"]
    for usn in valid_usns:
        response = auth_client.post(
            "/profile",
            data={
                "name": "Sia Simran A",
                "usn": usn,
                "batch_year": "2026",
                "cgpa": "9.4",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Profile updated successfully!" in response.get_data(as_text=True)

        db = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
        prof = db.execute("SELECT usn FROM student_profiles WHERE user_id = 1").fetchone()
        db.close()
        assert prof["usn"] == usn


def test_profile_update_invalid_usn_rejected(auth_client):
    """USN with symbols or out-of-range length is rejected with HTTP 400."""
    invalid_usns = [
        "AB",                        # too short (< 5 chars)
        "PES1UG24CS453VERYLONGUSNEXCEEDING20CHARS",  # too long (> 20 chars)
        "PES@#$123!",                # invalid special characters
        "<script>alert(1)</script>", # script injection
    ]
    for usn in invalid_usns:
        response = auth_client.post(
            "/profile",
            data={"name": "Sia Simran", "usn": usn},
        )
        assert response.status_code == 400
        assert "Invalid USN format" in response.get_data(as_text=True)


def test_profile_update_valid_phone_formats(auth_client, app):
    """Standard phone numbers with optional country code, spaces or dashes are accepted."""
    valid_phones = [
        "+91 98765 43210",
        "+1-800-555-0199",
        "9876543210",
        "(080) 26721983",
    ]
    for phone in valid_phones:
        response = auth_client.post(
            "/profile",
            data={
                "name": "Sia Simran",
                "phone": phone,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Profile updated successfully!" in response.get_data(as_text=True)

        db = sqlite3.connect(app.config["DATABASE"])
        prof = db.execute("SELECT phone FROM student_profiles WHERE user_id = 1").fetchone()
        db.close()
        assert prof[0] == phone


def test_profile_update_invalid_phone_rejected(auth_client):
    """Alphabetic or malformed phone numbers are rejected with HTTP 400."""
    invalid_phones = [
        "phone-number",
        "123",               # too short (< 7 digits)
        "1234567890123456789012345", # too long (> 20 chars)
        "++91--$$$###",
    ]
    for phone in invalid_phones:
        response = auth_client.post(
            "/profile",
            data={"name": "Sia Simran", "phone": phone},
        )
        assert response.status_code == 400
        assert "Invalid phone number format" in response.get_data(as_text=True)


def test_profile_update_valid_urls(auth_client, app):
    """Standard HTTP and HTTPS URLs for GitHub and LinkedIn are accepted."""
    response = auth_client.post(
        "/profile",
        data={
            "name": "Sia Simran",
            "github_url": "https://github.com/siasimran-magic",
            "linkedin_url": "https://www.linkedin.com/in/sia-simran",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Profile updated successfully!" in response.get_data(as_text=True)

    db = sqlite3.connect(app.config["DATABASE"])
    prof = db.execute("SELECT github_url, linkedin_url FROM student_profiles WHERE user_id = 1").fetchone()
    db.close()
    assert prof[0] == "https://github.com/siasimran-magic"
    assert prof[1] == "https://www.linkedin.com/in/sia-simran"


def test_profile_update_invalid_urls_rejected(auth_client):
    """Disallowed URL schemes or non-HTTP protocols are rejected with HTTP 400."""
    # Invalid GitHub URL
    response = auth_client.post(
        "/profile",
        data={
            "name": "Sia Simran",
            "github_url": "javascript:alert(document.cookie)",
        },
    )
    assert response.status_code == 400
    assert "GitHub URL must start with http:// or https://" in response.get_data(as_text=True)

    # Invalid LinkedIn URL
    response = auth_client.post(
        "/profile",
        data={
            "name": "Sia Simran",
            "linkedin_url": "ftp://files.example.com/profile",
        },
    )
    assert response.status_code == 400
    assert "LinkedIn URL must start with http:// or https://" in response.get_data(as_text=True)


def test_profile_update_bio_and_skills_length_limits(auth_client):
    """Bio and skills exceeding character limits are rejected with HTTP 400."""
    long_bio = "B" * 1001
    response = auth_client.post(
        "/profile",
        data={"name": "Sia Simran", "bio": long_bio},
    )
    assert response.status_code == 400
    assert "Bio cannot exceed 1000 characters." in response.get_data(as_text=True)

    long_skills = "Python, " * 100  # > 500 chars
    response = auth_client.post(
        "/profile",
        data={"name": "Sia Simran", "skills": long_skills},
    )
    assert response.status_code == 400
    assert "Skills cannot exceed 500 characters." in response.get_data(as_text=True)
