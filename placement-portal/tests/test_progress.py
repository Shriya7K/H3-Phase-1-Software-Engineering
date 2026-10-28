"""Task #19 - track preparation progress."""

from __future__ import annotations

import sqlite3

import pytest


def _clear(database_path, table):
    """Remove seeded demo rows so the assertions are deterministic."""
    db = sqlite3.connect(database_path)
    db.execute(f"DELETE FROM {table}")
    db.commit()
    db.close()


def _add_attempt(database_path, user_id, test_id, score, total, percentage, passed):
    db = sqlite3.connect(database_path)
    db.execute(
        "INSERT INTO test_attempts "
        "(user_id, test_id, score, total_questions, percentage, passed, answers_json) "
        "VALUES (?, ?, ?, ?, ?, ?, '{}')",
        (user_id, test_id, score, total, percentage, passed),
    )
    db.commit()
    db.close()


def _add_application(database_path, user_id, opportunity_id, status):
    db = sqlite3.connect(database_path)
    db.execute(
        "INSERT INTO applications (user_id, opportunity_id, status) VALUES (?, ?, ?)",
        (user_id, opportunity_id, status),
    )
    db.commit()
    db.close()


def test_progress_requires_login(client):
    response = client.get("/progress")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_progress_empty_state(auth_client, app):
    _clear(app.config["DATABASE"], "test_attempts")
    body = auth_client.get("/progress").get_data(as_text=True)
    assert "Preparation progress" in body
    assert "No practice attempts yet" in body
    assert "0.0%" in body  # average score with no attempts


def test_progress_totals(auth_client, app):
    db_path = app.config["DATABASE"]
    _clear(db_path, "test_attempts")
    _add_attempt(db_path, 1, 1, 8, 10, 80.0, 1)
    _add_attempt(db_path, 1, 1, 6, 10, 60.0, 0)
    _add_attempt(db_path, 1, 2, 10, 10, 100.0, 1)

    body = auth_client.get("/progress").get_data(as_text=True)
    assert "3</strong>" in body        # tests attempted
    assert "80.0%" in body             # average of 80, 60, 100
    assert "100.0%" in body            # best score
    assert "2</strong>" in body        # passed count


def test_progress_groups_by_test(auth_client, app):
    db_path = app.config["DATABASE"]
    _clear(db_path, "test_attempts")
    _add_attempt(db_path, 1, 1, 8, 10, 80.0, 1)
    _add_attempt(db_path, 1, 1, 6, 10, 60.0, 0)
    _add_attempt(db_path, 1, 2, 10, 10, 100.0, 1)

    body = auth_client.get("/progress").get_data(as_text=True)
    assert "Quantitative Aptitude" in body
    assert "Logical Reasoning" in body
    assert "Progress by category" in body
    # per-test attempts are 2 and 1
    assert ">2<" in body
    assert ">1<" in body


def test_progress_only_counts_own_attempts(auth_client, app):
    db_path = app.config["DATABASE"]
    _clear(db_path, "test_attempts")
    _add_attempt(db_path, 1, 1, 8, 10, 80.0, 1)      # student (self)
    _add_attempt(db_path, 2, 1, 2, 10, 20.0, 0)      # someone else
    _add_attempt(db_path, 2, 2, 3, 10, 30.0, 0)      # someone else

    body = auth_client.get("/progress").get_data(as_text=True)
    assert "80.0%" in body
    assert "20.0%" not in body
    assert "30.0%" not in body
    assert "1</strong>" in body  # exactly one attempt counted


def test_progress_shows_recent_attempts(auth_client, app):
    db_path = app.config["DATABASE"]
    _clear(db_path, "test_attempts")
    _add_attempt(db_path, 1, 3, 18, 20, 90.0, 1)

    body = auth_client.get("/progress").get_data(as_text=True)
    assert "Recent attempts" in body
    assert "Verbal Ability" in body
    assert "18/20" in body
    assert "Passed" in body


def test_progress_shows_application_breakdown(auth_client, app):
    db_path = app.config["DATABASE"]
    _clear(db_path, "applications")
    _add_application(db_path, 1, 1, "Submitted")
    _add_application(db_path, 1, 2, "Shortlisted")
    _add_application(db_path, 1, 3, "Shortlisted")

    body = auth_client.get("/progress").get_data(as_text=True)
    assert "Applications by status" in body
    assert "Shortlisted" in body
    assert "Submitted" in body
    assert "3</strong>" in body  # application total stat


def test_progress_is_linked_in_nav(auth_client):
    body = auth_client.get("/opportunities").get_data(as_text=True)
    assert 'href="/progress"' in body


def test_progress_page_has_no_server_errors_for_new_user(client, app):
    """A freshly registered student with no data must not trigger errors."""
    client.post(
        "/register",
        data={
            "name": "New Student",
            "email": "new.student@campus.edu",
            "password": "secret123",
            "confirm_password": "secret123",
        },
    )
    client.post(
        "/login",
        data={"email": "new.student@campus.edu", "password": "secret123"},
    )
    response = client.get("/progress")
    assert response.status_code == 200
    assert b"No practice attempts yet" in response.data
