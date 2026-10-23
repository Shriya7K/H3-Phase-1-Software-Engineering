"""Task #18 - Calculate and display test results (FR-09, FR-10, TC-07)."""

from __future__ import annotations

import sqlite3


def test_take_test_page_renders_with_questions(auth_client):
    """FR-09: Student attempts available aptitude test."""
    response = auth_client.get("/aptitude-tests/1")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Quantitative Aptitude" in body
    assert "If a shirt is marked at Rs 800" in body
    assert "A train 180 metres long" in body
    assert "Submit Test &amp; Calculate Results" in body


def test_submit_test_calculates_and_stores_correct_score(auth_client, app):
    """TC-07: Attempt and submit test -> Score/result calculated and displayed. Stored score is correct."""
    # Test 1 questions have correct answers: Q1=A, Q2=B, Q3=B, Q4=C, Q5=C.
    # Let's answer 4 out of 5 correctly (Q1=A, Q2=B, Q3=B, Q4=C, Q5=A -> 4 correct).
    response = auth_client.post(
        "/aptitude-tests/1/submit",
        data={
            "question_1": "A",  # Correct
            "question_2": "B",  # Correct
            "question_3": "B",  # Correct
            "question_4": "C",  # Correct
            "question_5": "A",  # Wrong (correct is C)
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Test Results" in body
    assert "4 / 5" in body
    assert "80.0%" in body
    assert "PASSED" in body

    # Verify score persisted accurately in database (TC-07 pass criterion: Stored score is correct)
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    attempt = db.execute(
        "SELECT * FROM test_attempts WHERE user_id = 1 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    db.close()

    assert attempt is not None
    assert attempt["score"] == 4
    assert attempt["total_questions"] == 5
    assert attempt["percentage"] == 80.0
    assert attempt["passed"] == 1


def test_submit_test_failed_threshold(auth_client):
    """Score < 50% must be marked as failed / needs improvement."""
    # Only 1 correct answer (Q1=A)
    response = auth_client.post(
        "/aptitude-tests/1/submit",
        data={
            "question_1": "A",  # Correct
            "question_2": "D",  # Wrong
            "question_3": "D",  # Wrong
            "question_4": "D",  # Wrong
            "question_5": "D",  # Wrong
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "1 / 5" in body
    assert "20.0%" in body
    assert "NEEDS IMPROVEMENT" in body


def test_view_test_history_results(auth_client):
    """FR-10: Display aptitude-test scores/results history."""
    response = auth_client.get("/test-results")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "My Aptitude Test History" in body
    assert "Quantitative Aptitude" in body
    assert "PASSED" in body
    assert "View Scorecard" in body


def test_unknown_test_id_returns_404(auth_client):
    assert auth_client.get("/aptitude-tests/9999").status_code == 404
    assert auth_client.post("/aptitude-tests/9999/submit").status_code == 404
