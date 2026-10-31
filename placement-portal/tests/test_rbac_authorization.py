"""Tasks #8 & #29 - Role-based access control & Authorization validation.

Covers:
  - Task #8: Role-based access control (FR-03, SR-03, TC-03)
  - Task #29: Validate authorization and access controls (NFR-02, SR-01, SR-03, TC-10, SV-01, SV-02)

Verifies:
  1. Unauthenticated users cannot reach protected views (redirected to /login) or APIs (401).
  2. Students cannot reach any administrator or management endpoints (strictly rejected with 403).
  3. Privileged administrative actions (user management, test editing, status updates) require admin role.
  4. Session-based role integrity prevents privilege escalation.
"""

from __future__ import annotations

import pytest


PROTECTED_STUDENT_ROUTES = [
    "/opportunities",
    "/opportunities/1",
    "/applications",
    "/profile",
    "/aptitude-tests",
    "/dashboard",
    "/test-results",
]

PROTECTED_ADMIN_ROUTES = [
    "/admin/users",
    "/admin/tests",
    "/admin/tests/new",
    "/admin/tests/1/edit",
    "/admin/tests/1/questions",
]

PROTECTED_ADMIN_POST_ROUTES = [
    ("/admin/users/1/role", {"role": "student"}),
    ("/admin/tests/new", {"name": "Test", "category": "Quant", "duration_minutes": 30, "difficulty": "Medium"}),
    ("/admin/tests/1/edit", {"name": "Test Edit", "category": "Quant", "duration_minutes": 30, "difficulty": "Medium"}),
    ("/admin/tests/1/questions", {"question_text": "Q1?", "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D", "correct_option": "A"}),
    ("/applications/1/status", {"status": "Shortlisted"}),
]


@pytest.mark.parametrize("route", PROTECTED_STUDENT_ROUTES + PROTECTED_ADMIN_ROUTES)
def test_unauthenticated_requests_redirected_to_login(client, route):
    """TC-10 / SV-01: Anonymous access to any protected route redirects to login."""
    response = client.get(route)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_api_analytics_unauthenticated_returns_401(client):
    """TC-10 / SR-01: Anonymous API access returns 401 Unauthorized with standard error format."""
    response = client.get("/api/analytics")
    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["errorCode"] == "UNAUTHORIZED"


@pytest.mark.parametrize("route", PROTECTED_ADMIN_ROUTES)
def test_student_forbidden_from_admin_get_endpoints(auth_client, route):
    """TC-03 / TC-10 / SV-02: Authenticated student receives 403 Forbidden on all admin GET routes."""
    response = auth_client.get(route)
    assert response.status_code == 403


@pytest.mark.parametrize("route,payload", PROTECTED_ADMIN_POST_ROUTES)
def test_student_forbidden_from_admin_post_endpoints(auth_client, route, payload):
    """TC-03 / TC-10 / SV-02: Authenticated student receives 403 Forbidden on all admin POST actions."""
    response = auth_client.post(route, data=payload)
    assert response.status_code == 403


def test_student_forbidden_from_admin_apis(auth_client):
    """TC-10: Student invoking admin REST APIs receives 403 Forbidden."""
    # User management API
    res_users = auth_client.get("/api/admin/users")
    assert res_users.status_code == 403
    payload_users = res_users.get_json()
    assert payload_users["success"] is False
    assert payload_users["errorCode"] == "FORBIDDEN"

    # Test creation API
    res_tests = auth_client.post(
        "/api/tests",
        json={"name": "Hacked Test", "category": "Quant", "duration_minutes": 20, "difficulty": "Easy"},
    )
    assert res_tests.status_code == 403


def test_admin_can_access_all_management_endpoints(client):
    """TC-03: Authenticated administrator successfully accesses management endpoints."""
    # Login as admin
    client.post("/login", data={"email": "admin@campus.edu", "password": "admin123"})

    for route in PROTECTED_ADMIN_ROUTES:
        response = client.get(route)
        assert response.status_code == 200, f"Admin failed to access {route}"


def test_role_escalation_in_session_tampering_prevented(client, app):
    """SR-03: Direct tampering of session cookies or non-existent roles is safely rejected."""
    with client.session_transaction() as sess:
        sess["user_id"] = 999999  # Invalid user ID
        sess["user_role"] = "admin"

    response = client.get("/admin/users")
    # Must redirect to login or reject because user does not exist in DB
    assert response.status_code in (302, 401, 403)
