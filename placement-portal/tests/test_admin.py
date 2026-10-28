"""Iteration 2 admin tasks.

    #26 Create and update opportunity listings
    #20 Manage test questions
    #28 Manage application records
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

import pytest

ADMIN_PAGES = [
    "/admin/opportunities",
    "/admin/opportunities/new",
    "/admin/opportunities/1/edit",
    "/admin/questions",
    "/admin/tests/1/questions",
    "/admin/tests/1/questions/new",
    "/admin/questions/1/edit",
    "/admin/applications",
]

VALID_OPPORTUNITY = {
    "title": "Machine Learning Intern",
    "company": "Nvidia",
    "type": "Internship",
    "location": "Bengaluru",
    "stipend": "Rs 40,000/month",
    "description": "Work on model evaluation tooling.",
    "eligibility": "B.Tech CSE · 2027 batch · CGPA 7.5+",
    "deadline": (date.today() + timedelta(days=21)).isoformat(),
    "is_open": "1",
}

VALID_QUESTION = {
    "question_text": "What is 15% of 200?",
    "option_a": "20",
    "option_b": "30",
    "option_c": "25",
    "option_d": "35",
    "correct_option": "B",
}


# -- Access control --------------------------------------------------------


@pytest.mark.parametrize("path", ADMIN_PAGES)
def test_admin_pages_redirect_anonymous_users(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


@pytest.mark.parametrize("path", ADMIN_PAGES)
def test_admin_pages_forbid_students(auth_client, path):
    assert auth_client.get(path).status_code == 403


@pytest.mark.parametrize("path", ADMIN_PAGES)
def test_admin_pages_allow_admins(admin_client, path):
    assert admin_client.get(path).status_code == 200


def test_student_cannot_create_opportunity(auth_client, app):
    response = auth_client.post("/admin/opportunities/new", data=VALID_OPPORTUNITY)
    assert response.status_code == 403
    db = sqlite3.connect(app.config["DATABASE"])
    count = db.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
    db.close()
    assert count == 9  # seed rows only


def test_admin_link_only_rendered_for_admins(auth_client, app):
    body = auth_client.get("/opportunities").get_data(as_text=True)
    assert 'href="/admin/opportunities"' not in body


def test_admin_link_visible_to_admins(admin_client):
    body = admin_client.get("/opportunities").get_data(as_text=True)
    assert 'href="/admin/opportunities"' in body


# -- #26 Create and update opportunity listings ----------------------------


def test_admin_list_shows_every_listing_including_closed(admin_client):
    body = admin_client.get("/admin/opportunities").get_data(as_text=True)
    assert "9 total" in body
    assert "QA Intern" in body       # expired
    assert "HR Intern" in body       # closed
    assert "Expired" in body
    assert "Closed" in body


def test_create_opportunity(admin_client, app):
    response = admin_client.post(
        "/admin/opportunities/new", data=VALID_OPPORTUNITY, follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/opportunities")

    db = sqlite3.connect(app.config["DATABASE"])
    row = db.execute(
        "SELECT title, company, type, is_open FROM opportunities WHERE title = ?",
        ("Machine Learning Intern",),
    ).fetchone()
    db.close()
    assert row == ("Machine Learning Intern", "Nvidia", "Internship", 1)


def test_created_listing_appears_for_students(admin_client, app):
    admin_client.post("/admin/opportunities/new", data=VALID_OPPORTUNITY)
    admin_client.post("/logout")

    student = admin_client  # same client, new session
    student.post("/login", data={"email": "student@campus.edu", "password": "student123"})
    body = student.get("/opportunities").get_data(as_text=True)
    assert "Machine Learning Intern" in body
    assert "8 open" in body


def test_create_with_missing_fields_is_rejected(admin_client, app):
    payload = dict(VALID_OPPORTUNITY)
    payload["title"] = "   "
    payload["company"] = ""

    response = admin_client.post("/admin/opportunities/new", data=payload)
    assert response.status_code == 400
    assert b"Title is required." in response.data
    assert b"Company is required." in response.data

    db = sqlite3.connect(app.config["DATABASE"])
    count = db.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
    db.close()
    assert count == 9


def test_create_with_invalid_type_is_rejected(admin_client):
    payload = dict(VALID_OPPORTUNITY, type="Contract")
    response = admin_client.post("/admin/opportunities/new", data=payload)
    assert response.status_code == 400
    assert b"Type must be Internship or Placement." in response.data


def test_create_with_invalid_deadline_is_rejected(admin_client):
    payload = dict(VALID_OPPORTUNITY, deadline="31-12-2026")
    response = admin_client.post("/admin/opportunities/new", data=payload)
    assert response.status_code == 400
    assert b"Deadline must be a valid date" in response.data


def test_edit_form_is_prefilled(admin_client):
    body = admin_client.get("/admin/opportunities/1/edit").get_data(as_text=True)
    assert "Software Engineering Intern" in body
    assert "Infosys" in body
    assert "Rs 25,000/month" in body


def test_update_opportunity(admin_client, app):
    payload = dict(VALID_OPPORTUNITY, title="Updated Title", location="Remote")
    response = admin_client.post("/admin/opportunities/1/edit", data=payload)
    assert response.status_code == 302

    db = sqlite3.connect(app.config["DATABASE"])
    row = db.execute(
        "SELECT title, location, company FROM opportunities WHERE id = 1"
    ).fetchone()
    db.close()
    assert row == ("Updated Title", "Remote", "Nvidia")


def test_closing_a_listing_hides_it_from_students(admin_client):
    payload = dict(VALID_OPPORTUNITY)
    payload.pop("is_open")  # unchecked checkbox
    admin_client.post("/admin/opportunities/1/edit", data=payload)
    admin_client.post("/logout")
    admin_client.post("/login", data={"email": "student@campus.edu", "password": "student123"})

    body = admin_client.get("/opportunities").get_data(as_text=True)
    assert "Updated Title" not in body
    assert "6 open" in body

    # but the detail page still resolves, marked closed
    assert b"Applications closed" in admin_client.get("/opportunities/1").data


def test_update_unknown_opportunity_returns_404(admin_client):
    assert admin_client.get("/admin/opportunities/9999/edit").status_code == 404


def test_update_with_invalid_data_changes_nothing(admin_client, app):
    payload = dict(VALID_OPPORTUNITY, title="")
    response = admin_client.post("/admin/opportunities/1/edit", data=payload)
    assert response.status_code == 400

    db = sqlite3.connect(app.config["DATABASE"])
    title = db.execute("SELECT title FROM opportunities WHERE id = 1").fetchone()[0]
    db.close()
    assert title == "Software Engineering Intern"


# -- #20 Manage test questions ---------------------------------------------


def test_question_picker_lists_tests_with_counts(admin_client):
    body = admin_client.get("/admin/questions").get_data(as_text=True)
    assert "Quantitative Aptitude" in body
    assert "Logical Reasoning" in body
    # 5 questions each for tests 1-3
    assert body.count(">5<") >= 3


def test_question_list_shows_options_and_correct_answer(admin_client):
    body = admin_client.get("/admin/tests/1/questions").get_data(as_text=True)
    assert "5 questions" in body
    assert "option-tag" in body
    assert "is-correct" in body


def test_add_question(admin_client, app):
    response = admin_client.post(
        "/admin/tests/1/questions/new", data=VALID_QUESTION, follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/tests/1/questions")

    db = sqlite3.connect(app.config["DATABASE"])
    row = db.execute(
        "SELECT test_id, question_text, correct_option FROM test_questions "
        "WHERE question_text = ?",
        (VALID_QUESTION["question_text"],),
    ).fetchone()
    count = db.execute(
        "SELECT COUNT(*) FROM test_questions WHERE test_id = 1"
    ).fetchone()[0]
    db.close()
    assert row == (1, "What is 15% of 200?", "B")
    assert count == 6


def test_add_question_missing_option_is_rejected(admin_client, app):
    payload = dict(VALID_QUESTION, option_c="")
    response = admin_client.post("/admin/tests/1/questions/new", data=payload)
    assert response.status_code == 400
    assert b"Option C is required." in response.data

    db = sqlite3.connect(app.config["DATABASE"])
    count = db.execute("SELECT COUNT(*) FROM test_questions").fetchone()[0]
    db.close()
    assert count == 15  # unchanged (3 tests x 5)


def test_add_question_invalid_correct_option_is_rejected(admin_client):
    payload = dict(VALID_QUESTION, correct_option="E")
    response = admin_client.post("/admin/tests/1/questions/new", data=payload)
    assert response.status_code == 400
    assert b"Correct option must be A, B, C or D." in response.data


def test_add_question_lowercase_correct_option_is_accepted(admin_client, app):
    payload = dict(VALID_QUESTION, correct_option="c")
    response = admin_client.post("/admin/tests/1/questions/new", data=payload)
    assert response.status_code == 302

    db = sqlite3.connect(app.config["DATABASE"])
    value = db.execute(
        "SELECT correct_option FROM test_questions WHERE question_text = ?",
        (VALID_QUESTION["question_text"],),
    ).fetchone()[0]
    db.close()
    assert value == "C"


def test_edit_question(admin_client, app):
    db = sqlite3.connect(app.config["DATABASE"])
    question_id = db.execute(
        "SELECT id FROM test_questions WHERE test_id = 1 ORDER BY id LIMIT 1"
    ).fetchone()[0]
    db.close()

    payload = dict(VALID_QUESTION, question_text="Edited question?", correct_option="D")
    response = admin_client.post(f"/admin/questions/{question_id}/edit", data=payload)
    assert response.status_code == 302

    db = sqlite3.connect(app.config["DATABASE"])
    row = db.execute(
        "SELECT question_text, correct_option FROM test_questions WHERE id = ?",
        (question_id,),
    ).fetchone()
    db.close()
    assert row == ("Edited question?", "D")


def test_edit_question_form_is_prefilled(admin_client):
    body = admin_client.get("/admin/questions/1/edit").get_data(as_text=True)
    assert 'name="question_text"' in body
    assert 'name="option_a"' in body


def test_delete_question(admin_client, app):
    db = sqlite3.connect(app.config["DATABASE"])
    question_id = db.execute(
        "SELECT id FROM test_questions WHERE test_id = 2 ORDER BY id LIMIT 1"
    ).fetchone()[0]
    db.close()

    response = admin_client.post(f"/admin/questions/{question_id}/delete")
    assert response.status_code == 302

    db = sqlite3.connect(app.config["DATABASE"])
    remaining = db.execute(
        "SELECT COUNT(*) FROM test_questions WHERE test_id = 2"
    ).fetchone()[0]
    db.close()
    assert remaining == 4


def test_delete_question_requires_post(admin_client):
    assert admin_client.get("/admin/questions/1/delete").status_code == 405


def test_unknown_test_or_question_returns_404(admin_client):
    assert admin_client.get("/admin/tests/9999/questions").status_code == 404
    assert admin_client.get("/admin/tests/9999/questions/new").status_code == 404
    assert admin_client.get("/admin/questions/9999/edit").status_code == 404
    assert admin_client.post("/admin/questions/9999/delete").status_code == 404


def test_added_question_is_served_on_the_test_page(admin_client):
    admin_client.post("/admin/tests/4/questions/new", data=VALID_QUESTION)
    body = admin_client.get("/aptitude-tests/4").get_data(as_text=True)
    assert "What is 15% of 200?" in body


# -- #28 Manage application records ----------------------------------------


def _seed_applications(database_path: str) -> None:
    """Two students, three applications in different statuses."""
    db = sqlite3.connect(database_path)
    db.execute("DELETE FROM applications")  # drop the seeded demo rows
    db.execute(
        "INSERT INTO users (name, email, password_hash, role) "
        "VALUES ('Rahul Verma', 'rahul@campus.edu', 'x', 'student')"
    )
    rahul_id = db.execute(
        "SELECT id FROM users WHERE email = 'rahul@campus.edu'"
    ).fetchone()[0]
    db.executemany(
        "INSERT INTO applications (user_id, opportunity_id, status, notes) "
        "VALUES (?, ?, ?, ?)",
        [
            (1, 1, "Submitted", "first choice"),
            (1, 2, "Shortlisted", ""),
            (rahul_id, 3, "Rejected", "not enough CGPA"),
        ],
    )
    db.commit()
    db.close()


def test_admin_sees_applications_from_every_student(admin_client, app):
    _seed_applications(app.config["DATABASE"])
    body = admin_client.get("/admin/applications").get_data(as_text=True)

    assert "3 of 3 applications" in body
    assert "Aditi Sharma" in body
    assert "Rahul Verma" in body
    assert "rahul@campus.edu" in body
    assert "Software Engineering Intern" in body


def test_admin_applications_filter_by_status(admin_client, app):
    _seed_applications(app.config["DATABASE"])

    body = admin_client.get("/admin/applications?status=Rejected").get_data(as_text=True)
    assert "1 of 3 applications" in body
    assert "Rahul Verma" in body
    assert "Aditi Sharma" not in body


def test_admin_applications_unknown_filter_shows_all(admin_client, app):
    _seed_applications(app.config["DATABASE"])
    body = admin_client.get("/admin/applications?status=Nonsense").get_data(as_text=True)
    assert "3 of 3 applications" in body


def test_admin_applications_empty_state(admin_client, app):
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("DELETE FROM applications")
    db.commit()
    db.close()

    body = admin_client.get("/admin/applications").get_data(as_text=True)
    assert "No applications to show" in body


def test_admin_can_update_status_from_records_page(admin_client, app):
    _seed_applications(app.config["DATABASE"])
    db = sqlite3.connect(app.config["DATABASE"])
    application_id = db.execute(
        "SELECT id FROM applications WHERE status = 'Submitted'"
    ).fetchone()[0]
    db.close()

    response = admin_client.post(
        f"/applications/{application_id}/status", data={"status": "Accepted"}
    )
    assert response.status_code == 302

    db = sqlite3.connect(app.config["DATABASE"])
    status = db.execute(
        "SELECT status FROM applications WHERE id = ?", (application_id,)
    ).fetchone()[0]
    db.close()
    assert status == "Accepted"


def test_student_cannot_change_another_students_application(auth_client, app):
    _seed_applications(app.config["DATABASE"])
    response = auth_client.post("/applications/1/status", data={"status": "Accepted"})
    assert response.status_code == 403
