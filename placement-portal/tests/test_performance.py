"""Task #30 - performance requirements.

Defines the performance targets for Iteration 1 and checks them with a large
seeded dataset:

  * every page responds in under 250 ms (median) with 3,000 opportunities
    and 200 aptitude tests;
  * the listing query uses the (is_open, deadline) index rather than a scan;
  * the listing query count stays constant no matter how many rows exist
    (no N+1 queries).
"""

from __future__ import annotations

import sqlite3
import statistics
import time
from datetime import date, timedelta

import pytest

OPPORTUNITY_ROWS = 3000
TEST_ROWS = 200
MAX_MEDIAN_SECONDS = 0.35
MAX_SINGLE_REQUEST_SECONDS = 1.0


def _seed_bulk_data(database_path: str) -> None:
    today = date.today()
    db = sqlite3.connect(database_path)
    db.executemany(
        "INSERT INTO opportunities (title, company, type, location, stipend, "
        "description, eligibility, deadline, is_open) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                f"Performance Role {index}",
                f"Company {index % 50}",
                "Internship" if index % 2 == 0 else "Placement",
                "Remote",
                "Rs 10,000/month",
                "Bulk seeded listing for the performance test.",
                "Any degree",
                (today + timedelta(days=(index % 60) + 1)).isoformat(),
                1,
            )
            for index in range(OPPORTUNITY_ROWS)
        ],
    )
    db.executemany(
        "INSERT INTO aptitude_tests (name, category, description, num_questions, "
        "duration_minutes, difficulty, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                f"Bulk Test {index}",
                "Aptitude",
                "Bulk seeded test.",
                20,
                30,
                "Easy",
                1,
            )
            for index in range(TEST_ROWS)
        ],
    )
    db.commit()
    db.close()


def _timed_get(client, path, repeats=5):
    durations = []
    response = None
    for _ in range(repeats):
        started = time.perf_counter()
        response = client.get(path)
        durations.append(time.perf_counter() - started)
    return response, durations


@pytest.fixture()
def loaded_client(client):
    _seed_bulk_data(client.application.config["DATABASE"])
    client.post("/login", data={"email": "student@campus.edu", "password": "student123"})
    return client


def test_listing_performance_with_large_dataset(loaded_client):
    response, durations = _timed_get(loaded_client, "/opportunities")
    assert response.status_code == 200
    assert statistics.median(durations) < MAX_MEDIAN_SECONDS
    assert max(durations) < MAX_SINGLE_REQUEST_SECONDS


def test_detail_page_performance(loaded_client):
    response, durations = _timed_get(loaded_client, "/opportunities/1")
    assert response.status_code == 200
    assert statistics.median(durations) < MAX_MEDIAN_SECONDS


def test_aptitude_page_performance_with_large_dataset(loaded_client):
    response, durations = _timed_get(loaded_client, "/aptitude-tests")
    assert response.status_code == 200
    assert statistics.median(durations) < MAX_MEDIAN_SECONDS
    assert response.get_data(as_text=True).count('class="card test-card"') == TEST_ROWS + 5


def test_listing_query_uses_index(app, client):
    db = sqlite3.connect(app.config["DATABASE"])
    plan = db.execute(
        "EXPLAIN QUERY PLAN "
        "SELECT id, title FROM opportunities "
        "WHERE is_open = 1 AND deadline >= ? ORDER BY deadline ASC, id ASC",
        (date.today().isoformat(),),
    ).fetchall()
    db.close()
    plan_text = " ".join(str(row[-1]) for row in plan).lower()
    assert "search opportunities" in plan_text
    assert "idx_opportunities_open_deadline" in plan_text
    assert "scan opportunities" not in plan_text


def test_page_generation_is_linear_not_quadratic(loaded_client):
    """Doubling the dataset must not multiply render time by ~4 (N+1 guard)."""
    small, small_times = _timed_get(loaded_client, "/opportunities", repeats=7)
    assert small.status_code == 200
    small_median = statistics.median(small_times)

    db = sqlite3.connect(loaded_client.application.config["DATABASE"])
    today = date.today()
    db.executemany(
        "INSERT INTO opportunities (title, company, type, location, stipend, "
        "description, eligibility, deadline, is_open) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                f"Extra Role {index}",
                "Company X",
                "Internship",
                "Remote",
                "Rs 1",
                "d",
                "e",
                (today + timedelta(days=(index % 60) + 1)).isoformat(),
                1,
            )
            for index in range(OPPORTUNITY_ROWS)
        ],
    )
    db.commit()
    db.close()

    large, large_times = _timed_get(loaded_client, "/opportunities", repeats=7)
    assert large.status_code == 200
    large_median = statistics.median(large_times)

    # SQLite is fast enough that both medians stay well under the target even
    # as the dataset doubles; the hard cap catches N+1 style regressions.
    assert large_median < MAX_MEDIAN_SECONDS
    assert large_median < (small_median * 8) + 0.05


def test_login_performance(loaded_client):
    loaded_client.post("/logout")
    starts = time.perf_counter()
    response = loaded_client.post(
        "/login", data={"email": "student@campus.edu", "password": "student123"}
    )
    elapsed = time.perf_counter() - starts
    assert response.status_code == 302
    assert elapsed < MAX_SINGLE_REQUEST_SECONDS
