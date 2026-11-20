"""Task #17 - Attempt a test (FR-09, Architecture Section 3.3, TC-07)."""

from __future__ import annotations

import sqlite3


def test_take_test_page_renders_with_questions_and_timer(auth_client):
    """FR-09: Student can access and attempt an active test with questions and timer."""
    response = auth_client.get("/aptitude-tests/1")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Quantitative Aptitude" in body
    assert "If a shirt is marked at Rs 800" in body
    assert "A train 180 metres long" in body
    assert "Submit Test &amp; Calculate Results" in body
    assert "timer-display" in body
    assert "Time:" in body


def test_take_test_route_alias(auth_client):
    """FR-09: Route alias /aptitude-tests/<id>/take also renders take_test page."""
    response = auth_client.get("/aptitude-tests/1/take")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Quantitative Aptitude" in body
    assert "Submit Test &amp; Calculate Results" in body


def test_take_test_requires_authentication(client):
    """FR-09: Unauthenticated users are redirected to login."""
    response = client.get("/aptitude-tests/1")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    post_resp = client.post("/aptitude-tests/1/submit", data={"question_1": "A"})
    assert post_resp.status_code == 302
    assert "/login" in post_resp.headers["Location"]


def test_take_inactive_test_returns_404(auth_client, app):
    """FR-09: Attempting an inactive test returns 404."""
    # Test 6 in seed data is is_active = 0 (Advanced SQL)
    response = auth_client.get("/aptitude-tests/6")
    assert response.status_code == 404

    submit_resp = auth_client.post("/aptitude-tests/6/submit", data={"question_1": "A"})
    assert submit_resp.status_code == 404


def test_submit_attempt_with_partial_answers(auth_client, app):
    """FR-09 / TC-07: Students can submit partial answers (skipping questions)."""
    # Test 1: Q1=A (correct), Q2=B (correct), rest unanswered
    response = auth_client.post(
        "/aptitude-tests/1/submit",
        data={
            "question_1": "A",
            "question_2": "B",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "2 / 5" in body
    assert "40.0%" in body
    assert "NEEDS IMPROVEMENT" in body

    # Verify database persistence
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    attempt = db.execute(
        "SELECT * FROM test_attempts WHERE user_id = 1 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    db.close()

    assert attempt is not None
    assert attempt["score"] == 2
    assert attempt["total_questions"] == 5
    assert attempt["percentage"] == 40.0
    assert attempt["passed"] == 0


def test_submit_attempt_all_correct(auth_client, app):
    """FR-09 / TC-07: Student attempts and answers all questions correctly."""
    # Test 1 questions: Q1=A, Q2=B, Q3=B, Q4=C, Q5=C
    response = auth_client.post(
        "/aptitude-tests/1/submit",
        data={
            "question_1": "A",
            "question_2": "B",
            "question_3": "B",
            "question_4": "C",
            "question_5": "C",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "5 / 5" in body
    assert "100.0%" in body
    assert "PASSED" in body


def test_api_list_tests(auth_client):
    """Architecture Section 3.3: GET /api/tests returns active aptitude tests."""
    response = auth_client.get("/api/tests")
    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data["success"] is True
    tests = json_data["data"]
    assert len(tests) >= 2
    # Ensure inactive test (id 6) is excluded
    test_ids = [t["id"] for t in tests]
    assert 1 in test_ids
    assert 2 in test_ids
    assert 6 not in test_ids


def test_api_list_tests_requires_auth(client):
    """Architecture Section 3.3: GET /api/tests requires authentication."""
    response = client.get("/api/tests")
    assert response.status_code == 302 or response.status_code == 401


def test_api_get_test_questions_does_not_leak_correct_option(auth_client):
    """Architecture Section 3.3: GET /api/tests/<id> returns questions without exposing answers."""
    response = auth_client.get("/api/tests/1")
    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data["success"] is True
    data = json_data["data"]
    assert data["test"]["name"] == "Quantitative Aptitude"
    questions = data["questions"]
    assert len(questions) == 5

    for q in questions:
        assert "question_text" in q
        assert "option_a" in q
        assert "option_b" in q
        assert "option_c" in q
        assert "option_d" in q
        # Crucial security check: correct_option must not be leaked to the client during attempt
        assert "correct_option" not in q


def test_api_get_test_not_found(auth_client):
    """Architecture Section 3.3: GET /api/tests/<id> returns 404 for missing test."""
    response = auth_client.get("/api/tests/9999")
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data["success"] is False


def test_api_submit_test_attempt_success(auth_client, app):
    """Architecture Section 3.3: POST /api/tests/<id>/attempts scores attempt and returns results."""
    # Test 1 questions: Q1=A, Q2=B, Q3=B, Q4=C, Q5=C
    payload = {
        "answers": {
            "1": "A",
            "2": "B",
            "3": "B",
            "4": "C",
            "5": "D",  # Wrong (correct is C)
        }
    }
    response = auth_client.post(
        "/api/tests/1/attempts",
        json=payload,
    )
    assert response.status_code == 201
    json_data = response.get_json()

    assert json_data["success"] is True
    data = json_data["data"]
    assert data["score"] == 4
    assert data["totalQuestions"] == 5
    assert data["percentage"] == 80.0
    assert data["passed"] is True
    assert "attemptId" in data

    # Verify attempt is in database
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    attempt = db.execute(
        "SELECT * FROM test_attempts WHERE id = ?", (data["attemptId"],)
    ).fetchone()
    db.close()

    assert attempt is not None
    assert attempt["score"] == 4
    assert attempt["percentage"] == 80.0
    assert attempt["passed"] == 1


def test_api_submit_test_attempt_invalid_test(auth_client):
    """Architecture Section 3.3: POST /api/tests/<id>/attempts with non-existent test returns 404."""
    response = auth_client.post(
        "/api/tests/9999/attempts",
        json={"answers": {}},
    )
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data["success"] is False
