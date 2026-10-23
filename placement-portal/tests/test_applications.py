"""Task #15 - Submit application and track application status (FR-07, FR-08, FR-16, TC-05, TC-06)."""

from __future__ import annotations

import sqlite3


def test_applications_requires_login(client):
    response = client.get("/applications")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_student_can_view_submitted_applications(auth_client):
    """FR-08: Student views application status."""
    response = auth_client.get("/applications")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Track Application Status" in body
    assert "Infosys" in body
    assert "Under Review" in body
    assert "Zoho" in body
    assert "Submitted" in body


def test_submit_new_application(auth_client, app):
    """TC-05: Eligible logged-in student submits application; stored once."""
    # Opportunity #3 is TCS Graduate Software Engineer (open)
    response = auth_client.post(
        "/opportunities/3/apply",
        data={"notes": "Strong interest in system architecture."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Application submitted successfully!" in body
    assert "TCS" in body
    assert "Submitted" in body

    # Verify directly in SQLite
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    app_record = db.execute(
        "SELECT * FROM applications WHERE user_id = 1 AND opportunity_id = 3"
    ).fetchone()
    db.close()

    assert app_record is not None
    assert app_record["status"] == "Submitted"
    assert app_record["notes"] == "Strong interest in system architecture."


def test_duplicate_application_is_rejected(auth_client):
    """TC-05: Exactly one valid application stored; prevent duplicates."""
    # Seed data already contains application for Opportunity #1 (Infosys)
    response = auth_client.post(
        "/opportunities/1/apply",
        data={"notes": "Second attempt"},
    )
    assert response.status_code == 409
    body = response.get_data(as_text=True)
    assert "already applied" in body


def test_apply_to_expired_opportunity_is_rejected(auth_client):
    # Opportunity #8 is expired QA Intern
    response = auth_client.post("/opportunities/8/apply")
    assert response.status_code == 400
    body = response.get_data(as_text=True)
    assert "closed" in body


def test_recruiter_updates_status_and_student_sees_update(client, app):
    """TC-06: Recruiter changes status; student checks -> updated status shown."""
    # 1. Admin signs in
    admin_login = client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
        follow_redirects=True,
    )
    assert admin_login.status_code == 200

    # 2. Admin changes Application #1 status to 'Shortlisted'
    update_resp = client.post(
        "/applications/1/status",
        data={"status": "Shortlisted"},
        follow_redirects=True,
    )
    assert update_resp.status_code == 200
    body_text = update_resp.get_data(as_text=True)
    assert "Shortlisted" in body_text

    # 3. Admin logs out, student logs in and checks status
    client.post("/logout")
    student_login = client.post(
        "/login",
        data={"email": "student@campus.edu", "password": "student123"},
        follow_redirects=True,
    )
    assert student_login.status_code == 200

    student_view = client.get("/applications")
    assert student_view.status_code == 200
    body = student_view.get_data(as_text=True)

    assert "Shortlisted" in body
    assert "Infosys" in body


def test_non_admin_cannot_update_application_status(auth_client):
    """TC-03 & SR-03: Student cannot perform admin/recruiter status update."""
    response = auth_client.post(
        "/applications/1/status",
        data={"status": "Accepted"},
    )
    assert response.status_code == 403
