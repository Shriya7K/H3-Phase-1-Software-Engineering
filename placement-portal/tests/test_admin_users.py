"""Automated tests for FR-15 User Administration (Issue #25, SR-06, TC-14).

Verifies RBAC enforcement, search/filtering, role assignments, self-demotion protection,
audit logging for security-relevant actions, and data protection (no password exposure).
"""

from __future__ import annotations

from db import get_db


def test_admin_users_requires_authentication(client):
    """Anonymous visitors must be redirected to login."""
    response = client.get("/admin/users")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_users_student_forbidden(auth_client):
    """Students attempting to access user administration receive 403 Forbidden."""
    response = auth_client.get("/admin/users")
    assert response.status_code == 403


def test_admin_users_renders_directory_for_admin(client):
    """Administrator accesses directory, sees registered users and audit log."""
    client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
    )
    response = client.get("/admin/users")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Manage Registered Users" in html
    assert "User Directory" in html
    assert "Administrative Audit Trail" in html
    assert "Aditi Sharma" in html
    assert "Priya Menon" in html


def test_admin_users_search_and_role_filter(client):
    """Search query and role filter correctly narrow the user list."""
    client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
    )

    # Search for Aditi
    res_search = client.get("/admin/users?q=Aditi")
    assert res_search.status_code == 200
    html_search = res_search.get_data(as_text=True)
    assert "Aditi Sharma" in html_search

    # Filter for admins
    res_admin = client.get("/admin/users?role=admin")
    assert res_admin.status_code == 200
    html_admin = res_admin.get_data(as_text=True)
    assert "Priya Menon" in html_admin
    assert "Aditi Sharma" not in html_admin


def test_admin_updates_user_role_and_writes_audit_log(app, client):
    """Admin updates student role to admin; verify DB update and SR-06 audit log creation."""
    client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
    )

    with app.app_context():
        db = get_db()
        student = db.execute("SELECT id FROM users WHERE email = 'student@campus.edu'").fetchone()
        student_id = student["id"]

    # Change student role to admin
    response = client.post(
        f"/admin/users/{student_id}/role",
        data={"role": "admin"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Updated role for Aditi Sharma to &#39;admin&#39;." in response.get_data(as_text=True)

    # Verify database state and audit log
    with app.app_context():
        db = get_db()
        updated = db.execute("SELECT role FROM users WHERE id = ?", (student_id,)).fetchone()
        assert updated["role"] == "admin"

        audit = db.execute(
            "SELECT * FROM audit_logs WHERE action = 'CHANGE_USER_ROLE' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert audit is not None
        assert audit["actor_email"] == "admin@campus.edu"
        assert f"User #{student_id}" in audit["details"]
        assert "to 'admin'" in audit["details"]
        assert audit["result"] == "SUCCESS"


def test_admin_cannot_demote_sole_administrator(client):
    """Sole administrator cannot demote themselves, preventing accidental system lockout."""
    client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
    )

    # Priya Menon is user id 2 and currently the only admin
    response = client.post(
        "/admin/users/2/role",
        data={"role": "student"},
    )
    assert response.status_code == 400


def test_admin_update_invalid_role_rejected(client):
    """Submitting an invalid role string returns 400 Bad Request."""
    client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
    )
    response = client.post(
        "/admin/users/1/role",
        data={"role": "superuser"},
    )
    assert response.status_code == 400


def test_student_cannot_update_user_roles(auth_client, app):
    """Authenticated student cannot post to role update endpoint."""
    response = auth_client.post(
        "/admin/users/1/role",
        data={"role": "admin"},
    )
    assert response.status_code == 403


def test_api_admin_users_returns_json_and_never_leaks_passwords(client):
    """API endpoint returns JSON user listing with password hashes strictly excluded (SR-02)."""
    client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
    )

    response = client.get("/api/admin/users")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["success"] is True
    users = payload["data"]
    assert len(users) >= 2

    for u in users:
        assert "password" not in u
        assert "password_hash" not in u
        assert "email" in u
        assert "role" in u
        assert "name" in u


def test_api_admin_users_forbidden_for_student(auth_client):
    """Student requesting admin API receives JSON 403 Forbidden."""
    response = auth_client.get("/api/admin/users")
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["errorCode"] == "FORBIDDEN"


def test_audit_log_created_on_application_status_change(app, client):
    """Application status updates by admin generate an SR-06 audit log record (TC-14)."""
    client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
    )

    # Opportunity 1 has existing seed application or we can update application #1
    response = client.post(
        "/applications/1/status",
        data={"status": "Shortlisted"},
    )
    assert response.status_code == 302

    with app.app_context():
        db = get_db()
        log_entry = db.execute(
            """
            SELECT * FROM audit_logs
            WHERE action = 'APPLICATION_STATUS_UPDATE'
            ORDER BY id DESC LIMIT 1
            """
        ).fetchone()
        assert log_entry is not None
        assert "Application #1 status changed to 'Shortlisted'" in log_entry["details"]
        assert log_entry["actor_email"] == "admin@campus.edu"
