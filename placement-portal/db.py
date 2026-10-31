"""SQLite helpers for the placement portal."""

from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime

from flask import Flask, current_app, g


def get_db() -> sqlite3.Connection:
    """Return the request-scoped database connection, opening it if needed."""
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(exception: BaseException | None = None) -> None:
    """Close request-scoped connection, rolling back uncommitted changes on error (NFR-04)."""
    connection = g.pop("db", None)
    if connection is not None:
        if exception is not None:
            try:
                connection.rollback()
            except Exception:
                pass
        connection.close()


def check_database_integrity(
    db_path: str | None = None,
) -> tuple[bool, list[str]]:
    """Verify SQLite B-tree, schema, and foreign-key integrity (NFR-04, NFR-09)."""
    target = db_path or current_app.config["DATABASE"]
    errors: list[str] = []
    if not os.path.exists(target):
        return (False, [f"Database file does not exist: {target}"])

    conn = sqlite3.connect(target)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        # 1. Low-level B-tree & freelist integrity
        rows = conn.execute("PRAGMA integrity_check").fetchall()
        for r in rows:
            val = r[0]
            if val != "ok":
                errors.append(f"Integrity check failure: {val}")

        # 2. Referential integrity across foreign-key constraints
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        for v in fk_violations:
            errors.append(
                f"Foreign key violation: table '{v[0]}' rowid {v[1]} references '{v[2]}' (fkid {v[3]})"
            )

        return (len(errors) == 0, errors)
    except Exception as exc:
        return (False, [f"Database integrity inspection failed: {exc}"])
    finally:
        conn.close()


def backup_database(
    app: Flask | None = None, backup_path: str | None = None
) -> str:
    """Create a consistent online backup using SQLite's backup API (NFR-04, NFR-09)."""
    application = app or current_app
    db_file = application.config["DATABASE"]
    if not os.path.exists(db_file):
        raise FileNotFoundError(f"Source database not found: {db_file}")

    if backup_path is None:
        backup_dir = os.path.join(application.instance_path, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(
            backup_dir, f"portal_backup_{timestamp}.sqlite"
        )
    else:
        parent_dir = os.path.dirname(os.path.abspath(backup_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

    src = sqlite3.connect(db_file)
    dst = sqlite3.connect(backup_path)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    # Validate backup integrity before declaring success
    ok, errors = check_database_integrity(backup_path)
    if not ok:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise RuntimeError(f"Backup validation failed: {'; '.join(errors)}")

    return backup_path


def restore_database(app: Flask | None = None, backup_path: str = "") -> bool:
    """Safely restore the active database from a verified backup (NFR-04, NFR-09)."""
    application = app or current_app
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file does not exist: {backup_path}")

    # 1. Verify backup file integrity before touching active database
    ok, errors = check_database_integrity(backup_path)
    if not ok:
        raise ValueError(
            f"Cannot restore corrupt backup file: {'; '.join(errors)}"
        )

    db_file = application.config["DATABASE"]
    had_existing = os.path.exists(db_file)
    temp_safety_path = f"{db_file}.safety_{os.getpid()}"

    # 2. Take a temporary safety copy of active database
    if had_existing:
        shutil.copy2(db_file, temp_safety_path)

    try:
        src = sqlite3.connect(backup_path)
        dst = sqlite3.connect(db_file)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

        # 3. Validate restored database integrity
        ok_restored, rest_errors = check_database_integrity(db_file)
        if not ok_restored:
            raise RuntimeError(
                f"Restored database integrity failed: {'; '.join(rest_errors)}"
            )

        # 4. Clean up temporary safety file upon verified success
        if had_existing and os.path.exists(temp_safety_path):
            os.remove(temp_safety_path)

        return True
    except Exception:
        # Revert to safety copy if restoration encountered an error
        if had_existing and os.path.exists(temp_safety_path):
            shutil.copy2(temp_safety_path, db_file)
            os.remove(temp_safety_path)
        raise


def init_db(app: Flask) -> None:
    """Create the schema if needed and insert demo data into an empty database."""
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    try:
        with app.open_resource("schema.sql") as schema_file:
            connection.executescript(schema_file.read().decode("utf-8"))

        user_count = connection.execute(
            "SELECT COUNT(*) AS count FROM users"
        ).fetchone()["count"]

        if user_count == 0:
            from seed import seed_database

            seed_database(connection)

        connection.commit()
    finally:
        connection.close()
