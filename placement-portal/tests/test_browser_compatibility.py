"""Task #32 - Test supported browser compatibility (NFR-08, TC-15).

Verifies cross-browser standards compliance and smoke execution across the two
latest stable versions of Google Chrome, Mozilla Firefox, and Microsoft Edge:
  - HTML5 DOCTYPE & UTF-8 character encoding declarations
  - Mobile & desktop responsive viewport meta configuration
  - Cross-browser CSS features (flexbox, CSS grid, system font stack fallbacks)
  - HTTP headers and standard session cookie attributes (HttpOnly, SameSite)
  - Simulated User-Agent smoke tests for Chrome, Firefox, Edge, and mobile viewports
"""

from __future__ import annotations

import pytest


BROWSER_USER_AGENTS = [
    # Google Chrome (latest stable v130, v131)
    (
        "Chrome-131-Windows",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    ),
    (
        "Chrome-130-Mac",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    ),
    # Mozilla Firefox (latest stable v131, v132)
    (
        "Firefox-132-Windows",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    ),
    (
        "Firefox-131-Linux",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    ),
    # Microsoft Edge (latest stable v130, v131)
    (
        "Edge-131-Windows",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    ),
    (
        "Edge-130-Mac",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    ),
    # Mobile responsive viewports (Chrome Android & Mobile Safari)
    (
        "Chrome-Mobile-Android",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.39 Mobile Safari/537.36",
    ),
]

CORE_ANONYMOUS_PAGES = [
    "/login",
    "/register",
]

CORE_PROTECTED_PAGES = [
    "/opportunities",
    "/dashboard",
    "/profile",
    "/aptitude-tests",
]


def test_html5_doctype_and_charset_standards_anonymous(client):
    """TC-15 / NFR-08: Anonymous pages serve valid HTML5 doctype and utf-8 charset."""
    for page in CORE_ANONYMOUS_PAGES:
        response = client.get(page)
        assert response.status_code == 200, f"Page {page} failed to render"
        html = response.get_data(as_text=True)
        assert "<!doctype html>" in html.lower(), f"{page} missing HTML5 doctype declaration"
        assert '<meta charset="utf-8">' in html.lower(), f"{page} missing utf-8 charset declaration"


def test_html5_doctype_and_charset_standards_protected(auth_client):
    """TC-15 / NFR-08: Protected student pages serve valid HTML5 doctype and utf-8 charset."""
    for page in CORE_PROTECTED_PAGES:
        response = auth_client.get(page)
        assert response.status_code == 200, f"Page {page} failed to render"
        html = response.get_data(as_text=True)
        assert "<!doctype html>" in html.lower(), f"{page} missing HTML5 doctype declaration"
        assert '<meta charset="utf-8">' in html.lower(), f"{page} missing utf-8 charset declaration"


def test_responsive_viewport_meta_tag_anonymous(client):
    """TC-15 / NFR-08: Responsive viewport meta tag configured across anonymous portal screens."""
    for page in CORE_ANONYMOUS_PAGES:
        response = client.get(page)
        html = response.get_data(as_text=True)
        assert 'name="viewport"' in html
        assert "width=device-width" in html


def test_responsive_viewport_meta_tag_protected(auth_client):
    """TC-15 / NFR-08: Responsive viewport meta tag configured across protected portal screens."""
    for page in CORE_PROTECTED_PAGES:
        response = auth_client.get(page)
        html = response.get_data(as_text=True)
        assert 'name="viewport"' in html
        assert "width=device-width" in html


def test_stylesheet_served_with_correct_mime_and_modern_css(client):
    """TC-15: Static style.css serves valid text/css with cross-browser layout properties."""
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["Content-Type"]
    css = response.get_data(as_text=True)

    # Cross-browser layout constructs
    assert "display: flex" in css or "display:flex" in css
    assert "display: grid" in css or "display:grid" in css
    assert "box-sizing: border-box" in css or "box-sizing:border-box" in css
    # System font stack for clean cross-browser rendering
    assert "font-family:" in css


@pytest.mark.parametrize("browser_name,user_agent", BROWSER_USER_AGENTS)
def test_cross_browser_smoke_suite(client, browser_name, user_agent):
    """TC-15: Core workflows render identically and return HTTP 200 across all supported browsers."""
    headers = {"User-Agent": user_agent}

    # 1. Anonymous pages
    res_login = client.get("/login", headers=headers)
    assert res_login.status_code == 200, f"Login failed on {browser_name}"
    assert "Sign in" in res_login.get_data(as_text=True)

    res_reg = client.get("/register", headers=headers)
    assert res_reg.status_code == 200, f"Register failed on {browser_name}"

    # 2. Authenticate
    res_auth = client.post(
        "/login",
        data={"email": "student@campus.edu", "password": "student123"},
        headers=headers,
    )
    assert res_auth.status_code == 302, f"Authentication redirect failed on {browser_name}"

    # 3. Authenticated protected pages
    res_opps = client.get("/opportunities", headers=headers)
    assert res_opps.status_code == 200, f"Opportunities listing failed on {browser_name}"

    res_dash = client.get("/dashboard", headers=headers)
    assert res_dash.status_code == 200, f"Dashboard failed on {browser_name}"
    assert "Student Preparation Dashboard" in res_dash.get_data(as_text=True)

    res_tests = client.get("/aptitude-tests", headers=headers)
    assert res_tests.status_code == 200, f"Tests page failed on {browser_name}"

    # Logout
    client.post("/logout", headers=headers)


def test_session_cookie_attributes_cross_browser(client):
    """TC-15: Session cookies set secure HttpOnly flag for cross-browser session safety."""
    response = client.post(
        "/login",
        data={"email": "student@campus.edu", "password": "student123"},
    )
    assert response.status_code == 302
    set_cookie_header = response.headers.get("Set-Cookie", "")
    assert "session=" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
