"""Shared pytest fixtures: every test gets an isolated database."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(tmp_path / "test.sqlite"),
        }
    )
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


STUDENT = {"email": "student@campus.edu", "password": "student123"}


@pytest.fixture()
def auth_client(client):
    """A client that is already signed in as the demo student."""
    response = client.post("/login", data=STUDENT)
    assert response.status_code == 302
    return client
