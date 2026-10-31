"""Automated tests for FR-12 Analytics Dashboard (Issue #21, TC-08).

Verifies student dashboard, admin aggregate dashboard, empty state handling,
progress readiness metric calculation, and REST API access controls.
"""

from __future__ import annotations


def test_dashboard_requires_authentication(client):
    """Anonymous visitors must be redirected to the login page."""
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_api_analytics_unauthenticated_returns_401(client):
    """Unauthenticated API requests must receive JSON 401 Unauthorized."""
    response = client.get("/api/analytics")
    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["errorCode"] == "UNAUTHORIZED"


def test_student_dashboard_renders_metrics_and_readiness(auth_client):
    """Authenticated student sees personal application and test metrics."""
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Student Preparation Dashboard" in html
    assert "Placement Preparation Readiness" in html
    assert "Applications Submitted" in html
    assert "Assessments Attempted" in html
    assert "Curriculum Coverage" in html


def test_student_dashboard_empty_state_handling(client):
    """A fresh student with no activity sees clean, helpful empty states without errors."""
    # Register fresh student
    client.post(
        "/register",
        data={
            "name": "Fresh Student",
            "email": "fresh@campus.edu",
            "password": "password123",
            "confirm_password": "password123",
            "role": "student",
        },
    )
    client.post(
        "/login",
        data={"email": "fresh@campus.edu", "password": "password123"},
    )

    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "You have not submitted any applications yet." in html
    assert "You have not attempted any aptitude tests yet." in html
    assert "Status: Not Started" in html
    assert "0% Completed" in html


def test_admin_dashboard_renders_aggregate_pipeline(client):
    """Administrator sees aggregate metrics across all students and placement drives."""
    client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
    )

    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Administrator Analytics Dashboard" in html
    assert "Application Status Pipeline" in html
    assert "Registered Users" in html
    assert "Placement Drives" in html
    assert "Administrative Audit Trail" in html


def test_api_analytics_student_payload(auth_client):
    """Student receives JSON analytics strictly scoped to their own account."""
    response = auth_client.get("/api/analytics")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["success"] is True
    data = payload["data"]
    assert "total_apps" in data
    assert "app_status" in data
    assert "total_attempts" in data
    assert "progress_percent" in data
    assert "readiness_status" in data
    assert "test_breakdown" in data
    assert isinstance(data["test_breakdown"], list)


def test_api_analytics_admin_payload(client):
    """Administrator receives system-wide aggregate metrics in JSON."""
    client.post(
        "/login",
        data={"email": "admin@campus.edu", "password": "admin123"},
    )

    response = client.get("/api/analytics")
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["success"] is True
    data = payload["data"]
    assert "total_users" in data
    assert "total_students" in data
    assert "total_admins" in data
    assert "total_opps" in data
    assert "app_status" in data
    assert "overall_avg_score" in data


def test_student_dashboard_data_isolation(client):
    """Ensure student A cannot see candidate records of student B."""
    # Register Student A and submit application
    client.post(
        "/register",
        data={
            "name": "Alice Green",
            "email": "alice@campus.edu",
            "password": "password123",
            "confirm_password": "password123",
            "role": "student",
        },
    )
    client.post(
        "/login",
        data={"email": "alice@campus.edu", "password": "password123"},
    )
    # Apply to opportunity #1
    client.post("/opportunities/1/apply", data={"notes": "Alice Private Note"})
    client.post("/logout")

    # Register Student B and check dashboard
    client.post(
        "/register",
        data={
            "name": "Bob Blue",
            "email": "bob@campus.edu",
            "password": "password123",
            "confirm_password": "password123",
            "role": "student",
        },
    )
    client.post(
        "/login",
        data={"email": "bob@campus.edu", "password": "password123"},
    )

    response = client.get("/dashboard")
    html = response.get_data(as_text=True)
    assert "Alice Green" not in html
    assert "Alice Private Note" not in html
    assert "You have not submitted any applications yet." in html
