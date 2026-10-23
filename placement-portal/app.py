"""Team H3 - Online Internship & Placement Preparation Portal.

Iteration 1 scope (assigned tasks):
    #7  User login and logout
    #11 Display opportunities
    #13 View opportunity details
    #16 Display available aptitude tests
    #30 Performance requirements (covered by tests/test_performance.py)
"""

from __future__ import annotations

import os
from datetime import date, datetime
from functools import wraps
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from db import close_db, get_db, init_db


# ---------------------------------------------------------------------------
# Small template helpers
# ---------------------------------------------------------------------------


def deadline_label(days_left: int) -> str:
    """Human readable label for an application deadline."""
    if days_left <= 0:
        return "Closes today"
    if days_left == 1:
        return "1 day left"
    return f"{days_left} days left"


def deadline_css(days_left: int) -> str:
    """CSS modifier used to colour the deadline chip."""
    if days_left <= 3:
        return "is-urgent"
    if days_left <= 7:
        return "is-soon"
    return "is-normal"


def pretty_date(value: str | date) -> str:
    """Render an ISO date (or date object) as e.g. '23 Nov 2026'."""
    if isinstance(value, str):
        value = datetime.strptime(value, "%Y-%m-%d").date()
    return value.strftime("%d %b %Y")


def _safe_next(target: str | None) -> str | None:
    """Only allow local redirect targets (prevents open-redirect abuse)."""
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return None
    if not target.startswith("/") or target.startswith("//"):
        return None
    return target


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get(
            "SECRET_KEY", "dev-secret-key-change-before-deploying"
        ),
        DATABASE=os.path.join(app.instance_path, "portal.sqlite"),
        # Templates/CSS pick up edits without a restart during development.
        TEMPLATES_AUTO_RELOAD=True,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    init_db(app)
    app.teardown_appcontext(close_db)

    app.jinja_env.filters["pretty_date"] = pretty_date
    app.jinja_env.globals["deadline_label"] = deadline_label
    app.jinja_env.globals["deadline_css"] = deadline_css

    @app.before_request
    def load_logged_in_user():
        """Drop sessions that point at a user which no longer exists.

        One primary-key lookup per request; keeps a stale cookie (for example
        after `flask reset-db`) from looking like a valid login.
        """
        user_id = session.get("user_id")
        if user_id is None:
            return
        user = get_db().execute(
            "SELECT id, name, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            session.clear()
            return
        session["user_name"] = user["name"]
        session["user_role"] = user["role"]

    def login_required(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not session.get("user_id"):
                next_url = request.full_path if request.query_string else request.path
                return redirect(url_for("login", next=next_url))
            return view(*args, **kwargs)

        return wrapped_view

    # -- #7 Login / logout ---------------------------------------------------

    @app.get("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("opportunities"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id"):
            return redirect(url_for("opportunities"))

        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""

            user = None
            if email and password:
                user = get_db().execute(
                    "SELECT id, name, email, password_hash, role "
                    "FROM users WHERE email = ?",
                    (email,),
                ).fetchone()

            if user is None or not check_password_hash(
                user["password_hash"], password
            ):
                # Same message for unknown email and wrong password, so the form
                # does not reveal which accounts exist.
                flash("Invalid email or password. Please try again.", "error")
                return render_template("login.html", email=email), 401

            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]
            flash(f"Welcome back, {user['name'].split()[0]}!", "success")
            return redirect(_safe_next(request.args.get("next")) or url_for("opportunities"))

        return render_template("login.html")

    @app.post("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    # -- #11 Display opportunities ------------------------------------------

    @app.get("/opportunities")
    @login_required
    def opportunities():
        # ?type=Internship / ?type=Placement; anything else means "all".
        type_filter = (request.args.get("type") or "").strip().title()
        if type_filter not in ("Internship", "Placement"):
            type_filter = None

        sql = (
            "SELECT id, title, company, type, location, stipend, deadline "
            "FROM opportunities "
            "WHERE is_open = 1 AND deadline >= ?"
        )
        params: list[str] = [date.today().isoformat()]
        if type_filter:
            sql += " AND type = ?"
            params.append(type_filter)
        sql += " ORDER BY deadline ASC, id ASC"

        rows = get_db().execute(sql, params).fetchall()

        today = date.today()
        items = []
        for row in rows:
            item = dict(row)
            deadline = datetime.strptime(item["deadline"], "%Y-%m-%d").date()
            item["days_left"] = (deadline - today).days
            items.append(item)

        return render_template(
            "opportunities.html",
            opportunities=items,
            active_type=type_filter or "All",
        )

    # -- #13 View opportunity details ---------------------------------------

    @app.get("/opportunities/<int:opportunity_id>")
    @login_required
    def opportunity_detail(opportunity_id: int):
        row = get_db().execute(
            "SELECT id, title, company, type, location, stipend, description, "
            "eligibility, deadline, is_open "
            "FROM opportunities WHERE id = ?",
            (opportunity_id,),
        ).fetchone()

        if row is None:
            abort(404)

        opportunity = dict(row)
        deadline = datetime.strptime(opportunity["deadline"], "%Y-%m-%d").date()
        opportunity["days_left"] = (deadline - date.today()).days
        opportunity["is_available"] = (
            bool(opportunity["is_open"]) and opportunity["days_left"] >= 0
        )
        return render_template("opportunity_detail.html", opportunity=opportunity)

    # -- #16 Display available aptitude tests --------------------------------

    @app.get("/aptitude-tests")
    @login_required
    def aptitude_tests():
        tests = get_db().execute(
            "SELECT id, name, category, description, num_questions, "
            "duration_minutes, difficulty "
            "FROM aptitude_tests "
            "WHERE is_active = 1 "
            "ORDER BY category ASC, name ASC"
        ).fetchall()
        return render_template("aptitude_tests.html", tests=tests)

    # -- Errors & maintenance commands --------------------------------------

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.cli.command("reset-db")
    def reset_db_command():
        """Delete the database and recreate it with fresh demo data."""
        database = app.config["DATABASE"]
        if os.path.exists(database):
            os.remove(database)
        init_db(app)
        print(f"Reset {database} with fresh demo data.")

    return app


if __name__ == "__main__":
    create_app().run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
