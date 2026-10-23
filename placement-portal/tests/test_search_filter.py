"""Task #12 - Search and filter opportunities (FR-06, TC-04, NFR-03)."""

from __future__ import annotations


def test_search_by_job_title(auth_client):
    """TC-04: Search by keyword."""
    response = auth_client.get("/opportunities?q=Frontend")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Frontend Intern" in body
    assert "Graduate Software Engineer" not in body
    assert "Data Analyst" not in body


def test_search_by_company(auth_client):
    response = auth_client.get("/opportunities?q=PhonePe")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "PhonePe" in body
    assert "Product Management Trainee" in body
    assert "Deloitte" not in body


def test_search_by_skill_in_description(auth_client):
    """Search matches description (e.g. React, SQL, Java)."""
    response = auth_client.get("/opportunities?q=React")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Frontend Intern" in body  # Freshworks uses React
    assert "Infosys" not in body


def test_search_is_case_insensitive(auth_client):
    response = auth_client.get("/opportunities?q=freshworks")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Freshworks" in body


def test_filter_by_location(auth_client):
    response = auth_client.get("/opportunities?location=Hyderabad")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Data Analyst" in body
    assert "Hyderabad" in body
    assert "Infosys" not in body


def test_combined_search_and_type_filter(auth_client):
    # Both Internship type and Bengaluru location
    response = auth_client.get("/opportunities?type=Internship&location=Bengaluru")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Software Engineering Intern" in body
    assert "TCS" not in body  # TCS is Placement


def test_search_no_matches_renders_empty_state(auth_client):
    response = auth_client.get("/opportunities?q=NonExistentRoleXYZ")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "No opportunities to show" in body
    assert "No listings match your search criteria" in body
    assert "0 open" in body
