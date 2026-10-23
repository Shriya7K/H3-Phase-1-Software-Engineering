"""SQLite helpers for the placement portal."""

from __future__ import annotations

import sqlite3

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
    """Close the request-scoped connection at the end of the request."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


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
