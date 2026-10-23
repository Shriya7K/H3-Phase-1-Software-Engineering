"""Task #16 - display available aptitude tests."""

from __future__ import annotations

import sqlite3

EXPECTED = [
    "Quantitative Aptitude",
    "Logical Reasoning",
    "Verbal Ability",
    "Data Interpretation",
    "Programming Fundamentals",
]


def test_aptitude_tests_page_renders(auth_client):
    response = auth_client.get("/aptitude-tests")
    assert response.status_code == 200
    assert b"Aptitude tests" in response.data


def test_all_active_tests_are_listed(auth_client):
    body = auth_client.get("/aptitude-tests").get_data(as_text=True)
    for name in EXPECTED:
        assert name in body


def test_inactive_tests_are_hidden(auth_client):
    body = auth_client.get("/aptitude-tests").get_data(as_text=True)
    assert "Advanced SQL" not in body


def test_test_count_and_totals_are_shown(auth_client):
    body = auth_client.get("/aptitude-tests").get_data(as_text=True)
    assert "5 available" in body
    assert body.count('class="card test-card"') == 5


def test_test_metadata_is_rendered(auth_client):
    body = auth_client.get("/aptitude-tests").get_data(as_text=True)
    assert "Percentages, ratios, averages" in body
    assert ">20<" in body    # number of questions
    assert ">30<" in body    # duration
    assert "Easy" in body
    assert "Medium" in body
    assert "Hard" in body


def test_tests_are_grouped_by_category(auth_client):
    body = auth_client.get("/aptitude-tests").get_data(as_text=True)
    assert "Aptitude" in body
    assert "Reasoning" in body
    assert "English" in body
    assert "Technical" in body


def test_no_tests_empty_state(client, app):
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("UPDATE aptitude_tests SET is_active = 0")
    db.commit()
    db.close()

    client.post("/login", data={"email": "student@campus.edu", "password": "student123"})
    body = client.get("/aptitude-tests").get_data(as_text=True)
    assert "No aptitude tests yet" in body
    assert "0 available" in body


def test_aptitude_tests_require_login(client):
    response = client.get("/aptitude-tests")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
