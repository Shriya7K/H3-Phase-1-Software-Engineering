"""Tasks #11 and #13 - display opportunities and view opportunity details."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta


def _days_ahead(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


# -- Listing (#11) ---------------------------------------------------------


def test_listing_shows_open_opportunities(auth_client):
    response = auth_client.get("/opportunities")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    for title in (
        "Software Engineering Intern",
        "Backend Developer Intern",
        "Graduate Software Engineer",
        "Data Analyst",
        "Frontend Intern",
        "Product Management Trainee",
        "Cloud Support Associate",
    ):
        assert title in body


def test_listing_hides_expired_and_closed_opportunities(auth_client):
    response = auth_client.get("/opportunities")
    body = response.get_data(as_text=True)
    assert "QA Intern" not in body        # deadline passed
    assert "HR Intern" not in body        # is_open = 0


def test_listing_count_matches_visible_cards(auth_client):
    response = auth_client.get("/opportunities")
    body = response.get_data(as_text=True)
    assert body.count('class="card job-card"') == 7
    assert "7 open" in body


def test_listing_is_sorted_by_nearest_deadline(auth_client):
    body = auth_client.get("/opportunities").get_data(as_text=True)
    positions = [
        body.index(title)
        for title in (
            "Graduate Software Engineer",   # +5 days
            "Frontend Intern",              # +9 days
            "Software Engineering Intern",  # +12 days
            "Cloud Support Associate",      # +16 days
            "Backend Developer Intern",     # +20 days
            "Data Analyst",                 # +27 days
            "Product Management Trainee",   # +33 days
        )
    ]
    assert positions == sorted(positions)


def test_listing_filter_internships(auth_client):
    body = auth_client.get("/opportunities?type=Internship").get_data(as_text=True)
    assert "3 open" in body
    assert "Software Engineering Intern" in body
    assert "Graduate Software Engineer" not in body


def test_listing_filter_placements(auth_client):
    body = auth_client.get("/opportunities?type=Placement").get_data(as_text=True)
    assert "4 open" in body
    assert "Graduate Software Engineer" in body
    assert "Software Engineering Intern" not in body


def test_listing_filter_is_case_insensitive(auth_client):
    body = auth_client.get("/opportunities?type=internship").get_data(as_text=True)
    assert "3 open" in body


def test_listing_unknown_filter_falls_back_to_all(auth_client):
    body = auth_client.get("/opportunities?type=Contract").get_data(as_text=True)
    assert "7 open" in body


def test_listing_deadline_badges(auth_client):
    body = auth_client.get("/opportunities").get_data(as_text=True)
    assert "5 days left" in body
    assert "12 days left" in body
    assert 'class="deadline-chip is-soon"' in body    # 5 days -> <= 7 days
    assert 'class="deadline-chip is-normal"' in body  # 12+ days


def test_deadline_thresholds():
    from app import deadline_css, deadline_label

    assert deadline_css(0) == "is-urgent"
    assert deadline_css(3) == "is-urgent"
    assert deadline_css(4) == "is-soon"
    assert deadline_css(7) == "is-soon"
    assert deadline_css(8) == "is-normal"

    assert deadline_label(0) == "Closes today"
    assert deadline_label(1) == "1 day left"
    assert deadline_label(9) == "9 days left"


def test_urgent_badge_renders_for_near_deadline(client, app, auth_client):
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute(
        "INSERT INTO opportunities (title, company, type, location, stipend, "
        "description, eligibility, deadline, is_open) "
        "VALUES ('Urgent Role', 'Edge Co', 'Placement', 'Remote', 'Rs 1', "
        "'d', 'e', ?, 1)",
        (_days_ahead(2),),
    )
    db.commit()
    db.close()

    body = auth_client.get("/opportunities").get_data(as_text=True)
    assert "Urgent Role" in body
    assert "2 days left" in body
    assert 'class="deadline-chip is-urgent"' in body


def test_listing_empty_state(client, app):
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("UPDATE opportunities SET is_open = 0")
    db.commit()
    db.close()

    client.post("/login", data={"email": "student@campus.edu", "password": "student123"})
    body = client.get("/opportunities").get_data(as_text=True)
    assert "No opportunities to show" in body
    assert "0 open" in body


def test_listing_shows_opportunity_deadline_on_last_valid_day(client, app, auth_client):
    # A listing whose deadline is today must still be visible.
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute(
        "INSERT INTO opportunities (title, company, type, location, stipend, "
        "description, eligibility, deadline, is_open) "
        "VALUES ('Closing Today Role', 'Edge Co', 'Internship', 'Remote', "
        "'Rs 1/month', 'd', 'e', ?, 1)",
        (date.today().isoformat(),),
    )
    db.commit()
    db.close()

    body = auth_client.get("/opportunities").get_data(as_text=True)
    assert "Closing Today Role" in body
    assert "Closes today" in body


# -- Details (#13) ---------------------------------------------------------


def test_detail_page_shows_all_fields(auth_client):
    response = auth_client.get("/opportunities/1")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "Software Engineering Intern" in body
    assert "Infosys" in body
    assert "Bengaluru" in body
    assert "Rs 25,000/month" in body
    assert "Work with the platform engineering team" in body
    assert "B.Tech / BE (CSE, ISE, ECE)" in body
    assert "Internship" in body
    assert "days left" in body


def test_detail_displays_formatted_deadline(auth_client):
    body = auth_client.get("/opportunities/1").get_data(as_text=True)
    import datetime

    expected = (date.today() + timedelta(days=12)).strftime("%d %b %Y")
    assert expected in body
    assert datetime.datetime.strptime(
        _days_ahead(12), "%Y-%m-%d"
    ).strftime("%d %b") in body


def test_detail_unknown_opportunity_returns_404(auth_client):
    response = auth_client.get("/opportunities/99999")
    assert response.status_code == 404
    assert b"Page not found" in response.data


def test_detail_with_non_numeric_id_returns_404(auth_client):
    assert auth_client.get("/opportunities/abc").status_code == 404


def test_detail_shows_closed_banner_for_expired_listing(auth_client):
    # QA Intern (#8) exists but expired 3 days ago.
    response = auth_client.get("/opportunities/8")
    assert response.status_code == 200
    assert b"Applications closed" in response.data
    assert b"QA Intern" in response.data


def test_detail_shows_closed_banner_for_manually_closed_listing(auth_client):
    response = auth_client.get("/opportunities/9")
    assert response.status_code == 200
    assert b"Applications closed" in response.data


def test_detail_has_back_link_and_no_apply_button(auth_client):
    body = auth_client.get("/opportunities/2").get_data(as_text=True)
    assert "Back to opportunities" in body
    # Applying belongs to Iteration 2 (#14) and must not be in this build.
    assert "Apply now" not in body
    assert "Iteration 2" in body


def test_detail_requires_login(client):
    response = client.get("/opportunities/1")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_404_page_for_unknown_route(auth_client):
    response = auth_client.get("/this/route/does-not-exist")
    assert response.status_code == 404
    assert b"Page not found" in response.data
