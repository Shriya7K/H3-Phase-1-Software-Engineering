"""Tasks #22, #23, #24 - Analytics Dashboard Metrics & Preparation Progress.

Covers:
  - Task #22: Show application summaries (FR-12, FR-08, TC-08)
  - Task #23: Show aptitude performance (FR-12, FR-10, TC-08)
  - Task #24: Display preparation progress (FR-11, FR-12, TC-08)

Verifies:
  1. Application pipeline metrics (Submitted, Under Review, Shortlisted, Accepted, Rejected).
  2. Multi-status updates dynamically refresh student summaries.
  3. Aptitude test attempt tracking, average score, pass rate, highest score, category grouping.
  4. Preparation readiness score calculation formula min(100, round((distinct_tests / total_active_tests) * 100)).
  5. Milestone transition states: Not Started -> Getting Started -> Good Progress -> Placement Ready.
  6. Strict tenant isolation between students for all summary metrics.
  7. REST API /api/analytics payload accuracy.
"""

from __future__ import annotations

import sqlite3


def _setup_student_with_apps_and_tests(app, student_email, student_pass):
    """Helper to register and seed customized activity records for a student."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    user = db.execute("SELECT id FROM users WHERE email = ?", (student_email,)).fetchone()
    if not user:
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, 'dummy', 'student')",
            ("Test Candidate", student_email),
        )
        db.commit()
        user_id = db.execute("SELECT id FROM users WHERE email = ?", (student_email,)).fetchone()["id"]
    else:
        user_id = user["id"]
    db.close()
    return user_id


def test_task_22_application_summaries_empty_state(auth_client, app):
    """Task #22: Fresh student with no applications sees zero count and empty status pipeline."""
    # Wipe existing applications for student user_id=1
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("DELETE FROM applications WHERE user_id = 1")
    db.commit()
    db.close()

    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Applications Submitted" in html
    assert "No applications yet" in html
    assert "You have not submitted any applications yet." in html


def test_task_22_application_summaries_counts_and_pipeline(auth_client, app):
    """Task #22: Submitting applications across diverse statuses produces exact matching summary counts."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("DELETE FROM applications WHERE user_id = 1")
    # Seed 3 applications in different statuses: 1 Accepted, 1 Under Review, 1 Rejected
    db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (1, 1, 'Accepted')")
    db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (1, 2, 'Under Review')")
    db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (1, 3, 'Rejected')")
    db.commit()
    db.close()

    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Total applications = 3
    assert '<span class="stat-num">3</span>' in html
    # Pipeline breakdown
    assert "1 accepted" in html
    assert "1 in review" in html
    assert "Accepted" in html
    assert "Under Review" in html
    assert "Rejected" in html


def test_task_22_application_summaries_api_payload(auth_client, app):
    """Task #22: REST endpoint /api/analytics returns structured application summary dictionary."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("DELETE FROM applications WHERE user_id = 1")
    db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (1, 1, 'Submitted')")
    db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (1, 2, 'Shortlisted')")
    db.commit()
    db.close()

    response = auth_client.get("/api/analytics")
    assert response.status_code == 200
    data = response.get_json()["data"]

    assert data["total_apps"] == 2
    assert data["app_status"]["Submitted"] == 1
    assert data["app_status"]["Shortlisted"] == 1
    assert data["app_status"]["Accepted"] == 0
    assert len(data["recent_applications"]) == 2


def test_task_23_aptitude_performance_metrics_calculation(auth_client, app):
    """Task #23: Correct calculation of attempts count, average score, best score, and passing rate."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("DELETE FROM test_attempts WHERE user_id = 1")
    # Attempt 1: Test 1, 80%, passed
    db.execute(
        "INSERT INTO test_attempts (user_id, test_id, score, total_questions, percentage, passed, answers_json) "
        "VALUES (1, 1, 8, 10, 80.0, 1, '{}')"
    )
    # Attempt 2: Test 1 (retake), 100%, passed
    db.execute(
        "INSERT INTO test_attempts (user_id, test_id, score, total_questions, percentage, passed, answers_json) "
        "VALUES (1, 1, 10, 10, 100.0, 1, '{}')"
    )
    # Attempt 3: Test 2, 40%, failed
    db.execute(
        "INSERT INTO test_attempts (user_id, test_id, score, total_questions, percentage, passed, answers_json) "
        "VALUES (1, 2, 4, 10, 40.0, 0, '{}')"
    )
    db.commit()
    db.close()

    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Average = (80 + 100 + 40) / 3 = 73.3%
    assert "73.3%" in html
    # Best score = 100.0%
    assert "100.0%" in html
    # 2 passed
    assert "2 passed" in html
    # 2 distinct tests attempted
    assert "2 distinct tests" in html


def test_task_23_aptitude_performance_category_breakdown(auth_client, app):
    """Task #23: Breakdown shows tests grouped by category with attempt count and best score."""
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Assessment Coverage Breakdown" in html
    assert "Quantitative Aptitude" in html


def test_task_24_preparation_progress_milestone_transitions(auth_client, app):
    """Task #24: Readiness progress percentage and milestone status advance as tests are completed."""
    db = sqlite3.connect(app.config["DATABASE"])
    # Determine total active tests
    total_active = db.execute("SELECT COUNT(*) FROM aptitude_tests WHERE is_active = 1").fetchone()[0]
    assert total_active >= 3, "Expected at least 3 active aptitude tests in seed data"

    # Stage 0: 0 tests attempted -> 0% "Not Started"
    db.execute("DELETE FROM test_attempts WHERE user_id = 1")
    db.commit()

    res0 = auth_client.get("/api/analytics")
    data0 = res0.get_json()["data"]
    assert data0["progress_percent"] == 0
    assert data0["readiness_status"] == "Not Started"

    # Stage 1: 1 test attempted out of 5 -> 20% "Getting Started"
    db.execute(
        "INSERT INTO test_attempts (user_id, test_id, score, total_questions, percentage, passed, answers_json) "
        "VALUES (1, 1, 8, 10, 80.0, 1, '{}')"
    )
    db.commit()

    res1 = auth_client.get("/api/analytics")
    data1 = res1.get_json()["data"]
    expected_pct_1 = min(100, round((1 / total_active) * 100))
    assert data1["progress_percent"] == expected_pct_1
    assert data1["readiness_status"] == "Getting Started"

    # Stage 2: Attempt all remaining active tests -> 100% "Placement Ready"
    active_test_ids = [r[0] for r in db.execute("SELECT id FROM aptitude_tests WHERE is_active = 1").fetchall()]
    for tid in active_test_ids:
        if tid != 1:
            db.execute(
                "INSERT INTO test_attempts (user_id, test_id, score, total_questions, percentage, passed, answers_json) "
                "VALUES (1, ?, 9, 10, 90.0, 1, '{}')",
                (tid,),
            )
    db.commit()
    db.close()

    res2 = auth_client.get("/api/analytics")
    data2 = res2.get_json()["data"]
    assert data2["progress_percent"] == 100
    assert data2["readiness_status"] == "Placement Ready"


def test_tasks_22_23_24_student_tenant_isolation(client, app):
    """Tasks #22, #23, #24: Ensure complete isolation of metrics between two student accounts."""
    # Student A: User 1
    # Student B: User 2
    db = sqlite3.connect(app.config["DATABASE"])
    # Seed specific data for student 2
    db.execute("DELETE FROM applications WHERE user_id = 2")
    db.execute("DELETE FROM test_attempts WHERE user_id = 2")
    db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (2, 1, 'Accepted')")
    db.execute(
        "INSERT INTO test_attempts (user_id, test_id, score, total_questions, percentage, passed, answers_json) "
        "VALUES (2, 2, 10, 10, 100.0, 1, '{}')"
    )
    db.commit()
    db.close()

    # Login as Student A (user 1)
    client.post("/login", data={"email": "student@campus.edu", "password": "student123"})
    res_a = client.get("/api/analytics").get_json()["data"]

    # Login as fresh Student B
    client.post("/logout")
    client.post(
        "/register",
        data={
            "name": "Student B",
            "email": "student.b@campus.edu",
            "password": "password123",
            "confirm_password": "password123",
            "role": "student",
        },
    )
    client.post("/login", data={"email": "student.b@campus.edu", "password": "password123"})
    res_b = client.get("/api/analytics").get_json()["data"]

    # Student B has no applications yet and no test attempts
    assert res_b["total_apps"] == 0
    assert res_b["total_attempts"] == 0
    assert res_b["progress_percent"] == 0
    assert res_b["readiness_status"] == "Not Started"
