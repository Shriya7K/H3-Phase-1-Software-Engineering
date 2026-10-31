"""Task #31 - Test data integrity (NFR-09, SR-05, TC-11).

Automated tests for domain integrity, entity integrity, referential integrity,
and transaction safety across SQLite relational constraints:
  - Foreign key cascading deletes (user -> profile, apps, attempts; opp -> apps; test -> questions, attempts)
  - CHECK constraints (roles, opportunity types, test difficulties, options, CGPA scale, positive duration)
  - UNIQUE constraints (email uniqueness, one application per user per opportunity)
  - Transaction atomicity & rollback upon constraint violation
"""

from __future__ import annotations

import sqlite3
import pytest


def test_referential_integrity_user_cascade_deletion(app):
    """NFR-09: Deleting a user record cascades and removes profile, applications, and test attempts."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("PRAGMA foreign_keys = ON")
    db.row_factory = sqlite3.Row

    # Create temporary user
    db.execute(
        "INSERT INTO users (id, name, email, password_hash, role) "
        "VALUES (999, 'Delete Me', 'delete.me@campus.edu', 'hash', 'student')"
    )
    # Associate profile, application, attempt
    db.execute("INSERT INTO student_profiles (user_id, usn) VALUES (999, 'PES1UG24CS999')")
    db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (999, 1, 'Submitted')")
    db.execute("INSERT INTO test_attempts (user_id, test_id, score, total_questions, percentage, passed, answers_json) VALUES (999, 1, 5, 5, 100.0, 1, '{}')")
    db.commit()

    # Confirm records exist
    assert db.execute("SELECT COUNT(*) FROM student_profiles WHERE user_id = 999").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM applications WHERE user_id = 999").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM test_attempts WHERE user_id = 999").fetchone()[0] == 1

    # Delete user
    db.execute("DELETE FROM users WHERE id = 999")
    db.commit()

    # Verify cascading delete
    assert db.execute("SELECT COUNT(*) FROM student_profiles WHERE user_id = 999").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM applications WHERE user_id = 999").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM test_attempts WHERE user_id = 999").fetchone()[0] == 0
    db.close()


def test_referential_integrity_opportunity_cascade_deletion(app):
    """NFR-09: Deleting an opportunity cascades and removes related applications."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("PRAGMA foreign_keys = ON")

    db.execute(
        "INSERT INTO opportunities (id, title, company, type, location, stipend, description, eligibility, deadline) "
        "VALUES (888, 'Temp Role', 'Test Corp', 'Internship', 'Bangalore', '10k', 'Desc', 'None', '2027-01-01')"
    )
    db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (1, 888, 'Submitted')")
    db.commit()

    assert db.execute("SELECT COUNT(*) FROM applications WHERE opportunity_id = 888").fetchone()[0] == 1

    db.execute("DELETE FROM opportunities WHERE id = 888")
    db.commit()

    assert db.execute("SELECT COUNT(*) FROM applications WHERE opportunity_id = 888").fetchone()[0] == 0
    db.close()


def test_referential_integrity_test_cascade_deletion(app):
    """NFR-09: Deleting an aptitude test cascades and removes questions and attempts."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("PRAGMA foreign_keys = ON")

    db.execute(
        "INSERT INTO aptitude_tests (id, name, category, description, duration_minutes, difficulty) "
        "VALUES (777, 'Temp Test', 'Technical', 'Desc', 20, 'Easy')"
    )
    db.execute(
        "INSERT INTO test_questions (test_id, question_text, option_a, option_b, option_c, option_d, correct_option) "
        "VALUES (777, 'Q1?', 'A', 'B', 'C', 'D', 'A')"
    )
    db.execute(
        "INSERT INTO test_attempts (user_id, test_id, score, total_questions, percentage, passed, answers_json) "
        "VALUES (1, 777, 1, 1, 100.0, 1, '{}')"
    )
    db.commit()

    assert db.execute("SELECT COUNT(*) FROM test_questions WHERE test_id = 777").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM test_attempts WHERE test_id = 777").fetchone()[0] == 1

    db.execute("DELETE FROM aptitude_tests WHERE id = 777")
    db.commit()

    assert db.execute("SELECT COUNT(*) FROM test_questions WHERE test_id = 777").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM test_attempts WHERE test_id = 777").fetchone()[0] == 0
    db.close()


def test_domain_integrity_check_constraints(app):
    """NFR-09 / TC-11: SQLite CHECK constraints strictly reject illegal values."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("PRAGMA foreign_keys = ON")

    # 1. Invalid User Role
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO users (name, email, password_hash, role) VALUES ('X', 'x@c.edu', 'h', 'superadmin')")

    # 2. Invalid Opportunity Type
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO opportunities (title, company, type, location, stipend, description, eligibility, deadline) "
            "VALUES ('T', 'C', 'Freelance', 'L', 'S', 'D', 'E', '2027-01-01')"
        )

    # 3. Invalid Test Difficulty
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO aptitude_tests (name, category, description, duration_minutes, difficulty) "
            "VALUES ('T', 'C', 'D', 20, 'Impossible')"
        )

    # 4. Invalid Question Correct Option
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO test_questions (test_id, question_text, option_a, option_b, option_c, option_d, correct_option) "
            "VALUES (1, 'Q?', 'A', 'B', 'C', 'D', 'Z')"
        )

    # 5. Invalid CGPA (> 10.0 or < 0.0)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO student_profiles (user_id, cgpa) VALUES (1, 11.5)")

    # 6. Non-positive duration
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO aptitude_tests (name, category, description, duration_minutes, difficulty) "
            "VALUES ('T', 'C', 'D', 0, 'Easy')"
        )

    # 7. Invalid Application Status
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (1, 2, 'Pending Approval')")

    db.close()


def test_entity_integrity_unique_constraints(app):
    """NFR-09 / TC-11: Unique constraints prevent duplicate accounts and duplicate applications."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("PRAGMA foreign_keys = ON")

    # Duplicate email
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) "
            "VALUES ('Duplicate', 'student@campus.edu', 'hash', 'student')"
        )

    # Duplicate application for same user and opportunity
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO applications (user_id, opportunity_id, status) VALUES (1, 1, 'Submitted')")

    db.close()


def test_transaction_atomicity_and_rollback(app):
    """NFR-04 / NFR-09: Multi-step database transaction rolls back cleanly on mid-stream failure."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("PRAGMA foreign_keys = ON")

    initial_users_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    try:
        with db:
            db.execute("INSERT INTO users (name, email, password_hash, role) VALUES ('Step1', 'step1@campus.edu', 'h', 'student')")
            # Force violation in second step
            db.execute("INSERT INTO users (name, email, password_hash, role) VALUES ('Step2', 'step1@campus.edu', 'h', 'student')")
    except sqlite3.IntegrityError:
        pass

    final_users_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert initial_users_count == final_users_count, "Transaction failed to roll back partial inserts"
    db.close()
