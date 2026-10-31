"""Automated tests for Reliability & Recovery (Issue #33, NFR-04, NFR-09).

Verifies database connection management, transaction rollback on failure,
referential integrity enforcement, online backup & restore, and safe error handling.
"""

from __future__ import annotations

import os
import sqlite3

import pytest

from db import (
    backup_database,
    check_database_integrity,
    get_db,
    restore_database,
)


def test_foreign_key_constraints_enforced(app):
    """Foreign key enforcement prevents orphan records and preserves domain integrity (NFR-09)."""
    with app.app_context():
        db = get_db()
        # Attempt to insert a question pointing to a non-existent test ID 99999
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                INSERT INTO test_questions
                    (test_id, question_text, option_a, option_b, option_c, option_d, correct_option)
                VALUES
                    (99999, 'Orphan Question?', 'A', 'B', 'C', 'D', 'A')
                """
            )


def test_transaction_rollback_on_failed_operation(app):
    """Failed transactions roll back partial changes and do not corrupt data (NFR-04)."""
    with app.app_context():
        db = get_db()
        initial_tests = db.execute(
            "SELECT COUNT(*) AS cnt FROM aptitude_tests"
        ).fetchone()["cnt"]

        # Simulate a transaction that inserts one row then encounters an error
        try:
            db.execute(
                "INSERT INTO aptitude_tests (name, category, description, duration_minutes, difficulty, is_active) "
                "VALUES ('Rollback Test', 'Tech', 'Desc', 30, 'Easy', 1)"
            )
            # Intentionally violate foreign key constraint to trigger failure
            db.execute(
                "INSERT INTO test_questions (test_id, question_text, option_a, option_b, option_c, option_d, correct_option) "
                "VALUES (88888, 'Bad question', 'A', 'B', 'C', 'D', 'A')"
            )
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()

        # Verify that 'Rollback Test' was rolled back and count is unchanged
        current_tests = db.execute(
            "SELECT COUNT(*) AS cnt FROM aptitude_tests"
        ).fetchone()["cnt"]
        assert current_tests == initial_tests
        assert (
            db.execute(
                "SELECT id FROM aptitude_tests WHERE name = 'Rollback Test'"
            ).fetchone()
            is None
        )


def test_database_integrity_check_valid_and_invalid(app, tmp_path):
    """PRAGMA integrity_check and foreign_key_check detect healthy and corrupt states."""
    with app.app_context():
        ok, errors = check_database_integrity()
        assert ok is True
        assert len(errors) == 0

    # Test corrupted file detection
    corrupt_file = str(tmp_path / "corrupt.sqlite")
    with open(corrupt_file, "wb") as f:
        f.write(b"NOT A SQLITE DATABASE HEADER GIBBERISH DATA")

    ok_corrupt, err_corrupt = check_database_integrity(corrupt_file)
    assert ok_corrupt is False
    assert len(err_corrupt) > 0


def test_online_backup_creation(app, tmp_path):
    """Online backup creates an intact, consistent replica of active database (NFR-04)."""
    backup_file = str(tmp_path / "backup_test.sqlite")
    result_path = backup_database(app, backup_file)
    assert os.path.exists(result_path)

    # Verify backup passes integrity check
    ok, errors = check_database_integrity(result_path)
    assert ok is True
    assert len(errors) == 0

    # Verify data in backup
    conn = sqlite3.connect(result_path)
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert user_count >= 2


def test_database_restore_recovers_data(app, tmp_path):
    """Restoring from a backup recovers deleted data while preserving integrity."""
    backup_file = str(tmp_path / "restore_test.sqlite")
    backup_database(app, backup_file)

    # Simulate catastrophic accidental deletion in the working database
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM opportunities")
        db.commit()
        assert (
            db.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0] == 0
        )

    # Perform restoration
    success = restore_database(app, backup_file)
    assert success is True

    # Verify opportunities were restored
    with app.app_context():
        db = get_db()
        restored_count = db.execute(
            "SELECT COUNT(*) FROM opportunities"
        ).fetchone()[0]
        assert restored_count > 0


def test_restore_rejects_corrupted_backup_without_altering_database(
    app, tmp_path
):
    """Restore aborts if backup is corrupt, leaving working database safe."""
    corrupt_backup = str(tmp_path / "corrupt_backup.sqlite")
    with open(corrupt_backup, "wb") as f:
        f.write(b"CORRUPT HEADER CONTENT")

    with app.app_context():
        db = get_db()
        initial_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    with pytest.raises(ValueError, match="Cannot restore corrupt backup"):
        restore_database(app, corrupt_backup)

    # Working database must remain unharmed
    with app.app_context():
        db = get_db()
        current_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        assert current_users == initial_users


def test_cli_backup_restore_and_integrity_commands(runner, tmp_path):
    """Flask CLI commands for backup, integrity check, and restore execute successfully."""
    # 1. check-integrity
    res_check = runner.invoke(args=["check-integrity"])
    assert res_check.exit_code == 0
    assert "Database integrity: OK" in res_check.output

    # 2. backup-db
    backup_path = str(tmp_path / "cli_backup.sqlite")
    res_backup = runner.invoke(args=["backup-db", "--output", backup_path])
    assert res_backup.exit_code == 0
    assert "successfully backed up" in res_backup.output
    assert os.path.exists(backup_path)

    # 3. restore-db
    res_restore = runner.invoke(args=["restore-db", backup_path])
    assert res_restore.exit_code == 0
    assert "successfully restored" in res_restore.output


def test_internal_server_error_handler_masks_stacktrace(app, client):
    """500 errors must not expose stack traces, paths, or credentials (NFR-04, SR-02)."""
    from flask import abort

    # Register both routes before first request dispatch
    @app.get("/test-internal-error")
    def fail_route():
        abort(500)

    @app.get("/api/test-internal-error")
    def fail_api():
        abort(500)

    # HTML 500 response verification
    response = client.get("/test-internal-error")
    assert response.status_code == 500
    html = response.get_data(as_text=True)

    # User-facing message must be friendly
    assert "Something went wrong" in html
    assert "500" in html
    # Traceback details, file paths, and exception messages must be completely masked
    assert "Traceback" not in html
    assert "db_pwd" not in html

    # JSON API 500 response verification
    api_res = client.get("/api/test-internal-error")
    assert api_res.status_code == 500
    payload = api_res.get_json()
    assert payload["success"] is False
    assert payload["errorCode"] == "INTERNAL_ERROR"
    assert "An unexpected internal error occurred" in payload["message"]


def test_missing_records_handled_gracefully(auth_client):
    """Non-existent records return 404 without crashing the application."""
    assert auth_client.get("/opportunities/999999").status_code == 404
    assert auth_client.get("/aptitude-tests/999999").status_code == 404

    # Admin route requires admin login to verify 404
    auth_client.post("/logout")
    auth_client.post(
        "/login", data={"email": "admin@campus.edu", "password": "admin123"}
    )
    assert auth_client.get("/admin/tests/999999/questions").status_code == 404
