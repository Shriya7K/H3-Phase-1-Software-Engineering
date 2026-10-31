"""Automated tests for FR-14 Aptitude Test Administration (Issue #27).

Verifies administrative creation, editing, question management, toggle status,
student access prohibition (RBAC), and answer concealment.
"""

from __future__ import annotations

from db import get_db


def test_admin_tests_requires_authentication(client):
    """Anonymous visitors must be redirected to the login page."""
    response = client.get("/admin/tests")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_tests_student_forbidden(auth_client):
    """Students attempting to access aptitude test management receive 403 Forbidden."""
    response = auth_client.get("/admin/tests")
    assert response.status_code == 403


def test_admin_tests_renders_all_assessments_including_inactive(client):
    """Administrators see both active and inactive tests with management controls."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )
    response = client.get("/admin/tests")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Manage Aptitude Tests" in html
    assert "Quantitative Aptitude" in html
    # Inactive test 'Advanced SQL' must be listed for admins
    assert "Advanced SQL" in html
    assert "Inactive" in html


def test_admin_create_test_success(app, client):
    """Administrator creates a new aptitude test; verify database and audit log."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )

    response = client.post(
        "/admin/tests/new",
        data={
            "name": "Cloud Architecture Basics",
            "category": "Technical",
            "description": "AWS and GCP fundamental computing concepts.",
            "duration_minutes": "45",
            "difficulty": "Medium",
            "is_active": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/admin/tests/" in response.headers["Location"]
    assert "/questions" in response.headers["Location"]

    with app.app_context():
        db = get_db()
        test_row = db.execute(
            "SELECT * FROM aptitude_tests WHERE name = 'Cloud Architecture Basics'"
        ).fetchone()
        assert test_row is not None
        assert test_row["category"] == "Technical"
        assert test_row["duration_minutes"] == 45
        assert test_row["is_active"] == 1

        audit = db.execute(
            "SELECT * FROM audit_logs WHERE action = 'CREATE_APTITUDE_TEST' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert audit is not None
        assert "Cloud Architecture Basics" in audit["details"]


def test_admin_create_test_validation_errors(client):
    """Submitting invalid or missing fields must return 400 Bad Request."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )

    # Empty name
    res1 = client.post(
        "/admin/tests/new",
        data={
            "name": "",
            "category": "Technical",
            "description": "Desc",
            "duration_minutes": "30",
        },
    )
    assert res1.status_code == 400

    # Negative duration
    res2 = client.post(
        "/admin/tests/new",
        data={
            "name": "Valid Title",
            "category": "Technical",
            "description": "Desc",
            "duration_minutes": "-5",
        },
    )
    assert res2.status_code == 400


def test_admin_edit_test_details(app, client):
    """Administrator edits test details and changes persist."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )

    # Edit test #1
    response = client.post(
        "/admin/tests/1/edit",
        data={
            "name": "Quantitative Aptitude Advanced",
            "category": "Aptitude",
            "description": "Updated math syllabus and speed tests.",
            "duration_minutes": "50",
            "difficulty": "Hard",
            "is_active": "1",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        updated = db.execute(
            "SELECT * FROM aptitude_tests WHERE id = 1"
        ).fetchone()
        assert updated["name"] == "Quantitative Aptitude Advanced"
        assert updated["duration_minutes"] == 50
        assert updated["difficulty"] == "Hard"


def test_admin_toggle_test_publication_status(app, client):
    """Administrator toggles test active/inactive status."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )

    # Test 6 is inactive (0) by default in seed data
    response = client.post("/admin/tests/6/toggle", follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        test_6 = db.execute(
            "SELECT is_active FROM aptitude_tests WHERE id = 6"
        ).fetchone()
        assert test_6["is_active"] == 1


def test_admin_add_question_and_sync_count(app, client):
    """Adding a question stores it in test_questions and updates num_questions on test."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )

    response = client.post(
        "/admin/tests/1/questions",
        data={
            "question_text": "What is 25 percent of 400?",
            "option_a": "50",
            "option_b": "100",
            "option_c": "150",
            "option_d": "200",
            "correct_option": "B",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        q = db.execute(
            "SELECT * FROM test_questions WHERE test_id = 1 AND question_text = 'What is 25 percent of 400?'"
        ).fetchone()
        assert q is not None
        assert q["correct_option"] == "B"

        test_row = db.execute(
            "SELECT num_questions FROM aptitude_tests WHERE id = 1"
        ).fetchone()
        actual_count = db.execute(
            "SELECT COUNT(*) AS cnt FROM test_questions WHERE test_id = 1"
        ).fetchone()["cnt"]
        assert test_row["num_questions"] == actual_count


def test_admin_add_question_validation(client):
    """Invalid question data (missing options or invalid correct key) returns 400."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )

    # Missing option_d
    res = client.post(
        "/admin/tests/1/questions",
        data={
            "question_text": "A valid question prompt?",
            "option_a": "Option 1",
            "option_b": "Option 2",
            "option_c": "Option 3",
            "option_d": "",
            "correct_option": "A",
        },
    )
    assert res.status_code == 400

    # Invalid correct option
    res2 = client.post(
        "/admin/tests/1/questions",
        data={
            "question_text": "A valid question prompt?",
            "option_a": "A",
            "option_b": "B",
            "option_c": "C",
            "option_d": "D",
            "correct_option": "Z",
        },
    )
    assert res2.status_code == 400


def test_admin_edit_question(app, client):
    """Administrator edits question text and options."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )

    # Edit question #1
    response = client.post(
        "/admin/tests/1/questions/1/edit",
        data={
            "question_text": "Updated question prompt for Q1?",
            "option_a": "Choice A",
            "option_b": "Choice B",
            "option_c": "Choice C",
            "option_d": "Choice D",
            "correct_option": "D",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        q = db.execute(
            "SELECT * FROM test_questions WHERE id = 1"
        ).fetchone()
        assert q["question_text"] == "Updated question prompt for Q1?"
        assert q["correct_option"] == "D"


def test_admin_delete_question(app, client):
    """Deleting a question removes it and decrements num_questions on test."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )

    with app.app_context():
        db = get_db()
        initial_count = db.execute(
            "SELECT COUNT(*) AS cnt FROM test_questions WHERE test_id = 1"
        ).fetchone()["cnt"]

    response = client.post(
        "/admin/tests/1/questions/1/delete", follow_redirects=True
    )
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        q = db.execute(
            "SELECT id FROM test_questions WHERE id = 1"
        ).fetchone()
        assert q is None

        new_count = db.execute(
            "SELECT COUNT(*) AS cnt FROM test_questions WHERE test_id = 1"
        ).fetchone()["cnt"]
        assert new_count == initial_count - 1

        test_row = db.execute(
            "SELECT num_questions FROM aptitude_tests WHERE id = 1"
        ).fetchone()
        assert test_row["num_questions"] == new_count


def test_student_forbidden_on_all_admin_test_endpoints(auth_client):
    """Ensure student cannot perform any administrative test management action."""
    assert auth_client.get("/admin/tests").status_code == 403
    assert auth_client.get("/admin/tests/new").status_code == 403
    assert (
        auth_client.post(
            "/admin/tests/new", data={"name": "Hacked Test"}
        ).status_code
        == 403
    )
    assert auth_client.get("/admin/tests/1/edit").status_code == 403
    assert (
        auth_client.post(
            "/admin/tests/1/edit", data={"name": "Hacked Test"}
        ).status_code
        == 403
    )
    assert auth_client.post("/admin/tests/1/toggle").status_code == 403
    assert auth_client.get("/admin/tests/1/questions").status_code == 403
    assert (
        auth_client.post(
            "/admin/tests/1/questions", data={"question_text": "Bad"}
        ).status_code
        == 403
    )
    assert (
        auth_client.post(
            "/admin/tests/1/questions/1/delete"
        ).status_code
        == 403
    )


def test_correct_answers_never_exposed_to_student_taking_test(auth_client):
    """Ensure student test-taking page does not leak correct answer keys in HTML source."""
    response = auth_client.get("/aptitude-tests/1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "correct_option" not in html
    assert "✓ (Correct)" not in html
    assert "correct-answer" not in html


def test_api_create_test_admin(client):
    """Administrator creates aptitude test via REST API (FR-14)."""
    client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )

    response = client.post(
        "/api/tests",
        json={
            "name": "System Design Fundamentals",
            "category": "Technical",
            "description": "Scalability, caching, and load balancing.",
            "duration_minutes": 35,
            "difficulty": "Hard",
            "is_active": 1,
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["name"] == "System Design Fundamentals"
    assert payload["data"]["difficulty"] == "Hard"


def test_api_create_test_student_forbidden(auth_client):
    """Student cannot create tests via REST API."""
    response = auth_client.post(
        "/api/tests",
        json={"name": "Disallowed Test", "category": "Technical"},
    )
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["errorCode"] == "FORBIDDEN"


def test_api_list_tests(auth_client):
    """Student receives active tests; Admin receives all tests with questions count."""
    # Student view
    res_student = auth_client.get("/api/tests")
    assert res_student.status_code == 200
    student_data = res_student.get_json()["data"]
    # Advanced SQL is inactive in seed data, so student should not receive it
    names = [t["name"] for t in student_data]
    assert "Advanced SQL" not in names
    for t in student_data:
        assert "correct_option" not in t

    # Switch to Admin view
    auth_client.post("/logout")
    auth_client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )
    res_admin = auth_client.get("/api/tests")
    assert res_admin.status_code == 200
    admin_data = res_admin.get_json()["data"]
    admin_names = [t["name"] for t in admin_data]
    assert "Advanced SQL" in admin_names
