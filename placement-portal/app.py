"""Team H3 - Online Internship & Placement Preparation Portal.

Covers Sprint 1 / Iteration 1 features:
    #6  User registration (FR-01, SR-02, SR-05, TC-01)
    #7  User login and logout (FR-02, TC-02)
    #9  Create and edit student profile (FR-04)
    #11 Display opportunities (FR-05)
    #12 Search and filter opportunities (FR-06, TC-04, NFR-03)
    #13 View opportunity details (FR-05)
    #15 Track application status (FR-07, FR-08, FR-16, TC-05, TC-06)
    #16 Display available aptitude tests (FR-09)
    #18 Calculate and display test results (FR-09, FR-10, TC-07)
    #30 Performance requirements (tested in tests/test_performance.py)
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from functools import wraps
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

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

    def admin_required(view):
        """Admin/recruiter pages: students get a 403, anonymous users log in."""

        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not session.get("user_id"):
                next_url = request.full_path if request.query_string else request.path
                return redirect(url_for("login", next=next_url))
            if session.get("user_role") != "admin":
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view

    # -- Home ----------------------------------------------------------------

    @app.get("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("opportunities"))
        return redirect(url_for("login"))

    # -- #6 User registration (FR-01, SR-02, SR-05, TC-01) -------------------

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if session.get("user_id"):
            return redirect(url_for("opportunities"))

        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            confirm_password = request.form.get("confirm_password") or ""
            role = (request.form.get("role") or "student").strip().lower()

            if role not in ("student", "admin"):
                role = "student"

            # Input validation (SR-05)
            if not name or len(name) < 2:
                flash("Please provide a valid full name (at least 2 characters).", "error")
                return render_template("register.html", name=name, email=email), 400

            email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
            if not email or not re.match(email_pattern, email):
                flash("Please provide a valid email address.", "error")
                return render_template("register.html", name=name, email=email), 400

            if not password or len(password) < 6:
                flash("Password must be at least 6 characters long.", "error")
                return render_template("register.html", name=name, email=email), 400

            if password != confirm_password:
                flash("Passwords do not match. Please re-enter.", "error")
                return render_template("register.html", name=name, email=email), 400

            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing is not None:
                flash("An account with this email already exists.", "error")
                return render_template("register.html", name=name, email=email), 400

            # Store password as salted one-way hash (SR-02, TC-13)
            password_hash = generate_password_hash(password)
            cursor = db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name, email, password_hash, role),
            )
            new_user_id = cursor.lastrowid

            if role == "student":
                db.execute(
                    "INSERT OR IGNORE INTO student_profiles (user_id) VALUES (?)",
                    (new_user_id,),
                )

            db.commit()
            flash("Registration successful! Please sign in with your credentials.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.post("/api/auth/register")
    def api_register():
        """Architecture Section 3.3 REST API endpoint for user registration."""
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        role = (data.get("role") or "student").strip().lower()

        if role not in ("student", "admin"):
            role = "student"

        if not name or len(name) < 2 or not email or "@" not in email or not password or len(password) < 6:
            return jsonify({"success": False, "message": "Invalid input data"}), 400

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing is not None:
            return jsonify({"success": False, "message": "Email already exists"}), 400

        password_hash = generate_password_hash(password)
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, role),
        )
        new_id = cursor.lastrowid
        if role == "student":
            db.execute("INSERT OR IGNORE INTO student_profiles (user_id) VALUES (?)", (new_id,))
        db.commit()
        return jsonify({"success": True, "message": "Account created successfully", "userId": new_id}), 201

    # -- #7 Login / logout ---------------------------------------------------

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

    # -- #9 Create and edit student profile (FR-04) --------------------------

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        user_id = session["user_id"]
        db = get_db()
        user = db.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            usn = (request.form.get("usn") or "").strip()
            phone = (request.form.get("phone") or "").strip()
            department = (request.form.get("department") or "").strip()
            batch_str = (request.form.get("batch_year") or "").strip()
            cgpa_str = (request.form.get("cgpa") or "").strip()
            skills = (request.form.get("skills") or "").strip()
            bio = (request.form.get("bio") or "").strip()
            github_url = (request.form.get("github_url") or "").strip()
            linkedin_url = (request.form.get("linkedin_url") or "").strip()

            if not name or len(name) < 2:
                flash("Name cannot be empty.", "error")
                return render_template(
                    "profile.html", user=user, profile=request.form
                ), 400

            batch_year = None
            if batch_str:
                try:
                    batch_year = int(batch_str)
                    if not (2000 <= batch_year <= 2099):
                        flash("Graduation year must be between 2000 and 2099.", "error")
                        return render_template(
                            "profile.html", user=user, profile=request.form
                        ), 400
                except ValueError:
                    flash("Invalid graduation year.", "error")
                    return render_template(
                        "profile.html", user=user, profile=request.form
                    ), 400

            cgpa = None
            if cgpa_str:
                try:
                    cgpa = float(cgpa_str)
                    if not (0.0 <= cgpa <= 10.0):
                        flash("CGPA must be between 0.0 and 10.0.", "error")
                        return render_template(
                            "profile.html", user=user, profile=request.form
                        ), 400
                except ValueError:
                    flash("Invalid CGPA value.", "error")
                    return render_template(
                        "profile.html", user=user, profile=request.form
                    ), 400

            # Update display name
            db.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
            session["user_name"] = name

            # Upsert student profile
            db.execute(
                """
                INSERT INTO student_profiles
                    (user_id, usn, phone, department, batch_year, cgpa, skills,
                     bio, github_url, linkedin_url, updated_at)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    usn = excluded.usn,
                    phone = excluded.phone,
                    department = excluded.department,
                    batch_year = excluded.batch_year,
                    cgpa = excluded.cgpa,
                    skills = excluded.skills,
                    bio = excluded.bio,
                    github_url = excluded.github_url,
                    linkedin_url = excluded.linkedin_url,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    usn,
                    phone,
                    department,
                    batch_year,
                    cgpa,
                    skills,
                    bio,
                    github_url,
                    linkedin_url,
                ),
            )
            db.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("profile"))

        prof = db.execute(
            "SELECT * FROM student_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        profile_data = dict(prof) if prof else {}

        return render_template("profile.html", user=user, profile=profile_data)

    # -- #11 & #12 Display, search and filter opportunities (FR-05, FR-06) ---

    @app.get("/opportunities")
    @login_required
    def opportunities():
        # Filter parameters
        type_filter = (request.args.get("type") or "").strip().title()
        if type_filter not in ("Internship", "Placement"):
            type_filter = None

        search_query = (request.args.get("q") or "").strip()
        location_filter = (request.args.get("location") or "").strip()

        sql = (
            "SELECT id, title, company, type, location, stipend, deadline "
            "FROM opportunities "
            "WHERE is_open = 1 AND deadline >= ?"
        )
        params: list[str] = [date.today().isoformat()]

        if type_filter:
            sql += " AND type = ?"
            params.append(type_filter)

        if search_query:
            sql += (
                " AND (title LIKE ? OR company LIKE ? OR location LIKE ? OR description LIKE ?)"
            )
            term = f"%{search_query}%"
            params.extend([term, term, term, term])

        if location_filter:
            sql += " AND location = ?"
            params.append(location_filter)

        sql += " ORDER BY deadline ASC, id ASC"

        rows = get_db().execute(sql, params).fetchall()

        # Available distinct locations for filter dropdown
        loc_rows = get_db().execute(
            "SELECT DISTINCT location FROM opportunities WHERE is_open = 1 ORDER BY location ASC"
        ).fetchall()
        locations = [r["location"] for r in loc_rows]

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
            search_query=search_query,
            active_location=location_filter,
            locations=locations,
        )

    # -- #13 View opportunity details ---------------------------------------

    @app.get("/opportunities/<int:opportunity_id>")
    @login_required
    def opportunity_detail(opportunity_id: int):
        db = get_db()
        row = db.execute(
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

        app_row = db.execute(
            "SELECT id, status, notes, applied_at FROM applications WHERE user_id = ? AND opportunity_id = ?",
            (session["user_id"], opportunity_id),
        ).fetchone()

        return render_template(
            "opportunity_detail.html",
            opportunity=opportunity,
            application=dict(app_row) if app_row else None,
        )

    # -- #15 Submit application & track application status (FR-07, FR-08, FR-16)

    @app.post("/opportunities/<int:opportunity_id>/apply")
    @login_required
    def apply_opportunity(opportunity_id: int):
        db = get_db()
        user_id = session["user_id"]

        row = db.execute(
            "SELECT id, is_open, deadline FROM opportunities WHERE id = ?",
            (opportunity_id,),
        ).fetchone()
        if row is None:
            abort(404)

        deadline = datetime.strptime(row["deadline"], "%Y-%m-%d").date()
        if not row["is_open"] or deadline < date.today():
            flash("Applications for this opportunity are closed.", "error")
            opp = dict(row)
            opp["days_left"] = (deadline - date.today()).days
            opp["is_available"] = False
            return render_template("opportunity_detail.html", opportunity=opp, application=None), 400

        # Check duplicate application (TC-05)
        existing = db.execute(
            "SELECT id, status, notes, applied_at FROM applications WHERE user_id = ? AND opportunity_id = ?",
            (user_id, opportunity_id),
        ).fetchone()
        if existing is not None:
            flash("You have already applied for this opportunity.", "error")
            opp = dict(row)
            opp["days_left"] = (deadline - date.today()).days
            opp["is_available"] = bool(row["is_open"]) and opp["days_left"] >= 0
            return render_template("opportunity_detail.html", opportunity=opp, application=dict(existing)), 409

        notes = (request.form.get("notes") or "").strip()
        db.execute(
            "INSERT INTO applications (user_id, opportunity_id, status, notes) VALUES (?, ?, 'Submitted', ?)",
            (user_id, opportunity_id, notes),
        )
        db.commit()
        flash("Application submitted successfully! You can track its status below.", "success")
        return redirect(url_for("applications"))

    @app.get("/applications")
    @login_required
    def applications():
        user_id = session["user_id"]
        db = get_db()
        rows = db.execute(
            """
            SELECT a.id, a.status, a.notes, a.applied_at, a.updated_at,
                   o.id AS opportunity_id, o.title, o.company, o.type, o.location, o.stipend, o.deadline
            FROM applications a
            JOIN opportunities o ON a.opportunity_id = o.id
            WHERE a.user_id = ?
            ORDER BY a.applied_at DESC
            """,
            (user_id,),
        ).fetchall()
        return render_template("applications.html", applications=rows)

    @app.post("/applications/<int:application_id>/status")
    @login_required
    def update_application_status(application_id: int):
        """Privileged recruiter/admin endpoint to update application status (TC-06, FR-16)."""
        if session.get("user_role") != "admin":
            abort(403)

        new_status = (request.form.get("status") or "").strip()
        valid_statuses = ("Submitted", "Under Review", "Shortlisted", "Accepted", "Rejected")
        if new_status not in valid_statuses:
            flash("Invalid application status.", "error")
            return redirect(url_for("applications")), 400

        db = get_db()
        db.execute(
            "UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, application_id),
        )
        db.commit()
        flash(f"Application status updated to '{new_status}'.", "success")
        return redirect(url_for("applications"))

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

    # -- #18 Calculate and display test results (FR-09, FR-10, TC-07) ---------

    @app.get("/aptitude-tests/<int:test_id>")
    @login_required
    def take_aptitude_test(test_id: int):
        db = get_db()
        test = db.execute(
            "SELECT id, name, category, description, num_questions, duration_minutes, difficulty "
            "FROM aptitude_tests WHERE id = ? AND is_active = 1",
            (test_id,),
        ).fetchone()

        if test is None:
            abort(404)

        questions = db.execute(
            "SELECT id, test_id, question_text, option_a, option_b, option_c, option_d "
            "FROM test_questions WHERE test_id = ? ORDER BY id ASC",
            (test_id,),
        ).fetchall()

        return render_template("take_test.html", test=test, questions=questions)

    @app.post("/aptitude-tests/<int:test_id>/submit")
    @login_required
    def submit_aptitude_test(test_id: int):
        db = get_db()
        user_id = session["user_id"]

        test = db.execute(
            "SELECT id, name, category FROM aptitude_tests WHERE id = ? AND is_active = 1",
            (test_id,),
        ).fetchone()
        if test is None:
            abort(404)

        questions = db.execute(
            "SELECT id, question_text, correct_option FROM test_questions WHERE test_id = ? ORDER BY id ASC",
            (test_id,),
        ).fetchall()

        if not questions:
            flash("No questions found for this test.", "error")
            return redirect(url_for("aptitude_tests")), 400

        # Score calculation (TC-07)
        total_questions = len(questions)
        score = 0
        answers = {}

        for q in questions:
            qid = str(q["id"])
            selected = (request.form.get(f"question_{qid}") or "").strip().upper()
            answers[qid] = selected
            if selected == q["correct_option"]:
                score += 1

        percentage = round((score / total_questions) * 100.0, 1) if total_questions > 0 else 0.0
        passed = 1 if percentage >= 50.0 else 0

        cursor = db.execute(
            """
            INSERT INTO test_attempts
                (user_id, test_id, score, total_questions, percentage, passed, answers_json, completed_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, test_id, score, total_questions, percentage, passed, json.dumps(answers)),
        )
        attempt_id = cursor.lastrowid
        db.commit()

        flash(f"Test completed! You scored {score}/{total_questions} ({percentage}%).", "success")
        return redirect(url_for("test_attempt_result", test_id=test_id, attempt_id=attempt_id))

    @app.get("/aptitude-tests/<int:test_id>/results/<int:attempt_id>")
    @login_required
    def test_attempt_result(test_id: int, attempt_id: int):
        db = get_db()
        user_id = session["user_id"]

        attempt = db.execute(
            "SELECT * FROM test_attempts WHERE id = ? AND test_id = ? AND user_id = ?",
            (attempt_id, test_id, user_id),
        ).fetchone()
        if attempt is None:
            abort(404)

        test = db.execute(
            "SELECT id, name, category, difficulty FROM aptitude_tests WHERE id = ?",
            (test_id,),
        ).fetchone()

        questions = db.execute(
            "SELECT * FROM test_questions WHERE test_id = ? ORDER BY id ASC",
            (test_id,),
        ).fetchall()

        answers = json.loads(attempt["answers_json"] or "{}")
        breakdown = []
        for q in questions:
            selected = answers.get(str(q["id"]))
            is_correct = (selected == q["correct_option"])
            breakdown.append({
                "question": q,
                "selected_option": selected,
                "is_correct": is_correct,
            })

        return render_template(
            "test_result.html",
            test=test,
            attempt=dict(attempt),
            breakdown=breakdown,
        )

    @app.get("/test-results")
    @login_required
    def my_test_results():
        user_id = session["user_id"]
        db = get_db()
        attempts = db.execute(
            """
            SELECT ta.id, ta.test_id, ta.score, ta.total_questions, ta.percentage, ta.passed, ta.completed_at,
                   t.name AS test_name, t.category, t.difficulty
            FROM test_attempts ta
            JOIN aptitude_tests t ON ta.test_id = t.id
            WHERE ta.user_id = ?
            ORDER BY ta.completed_at DESC
            """,
            (user_id,),
        ).fetchall()
        return render_template("my_results.html", attempts=attempts)

    # -- #19 Track preparation progress (FR-11) ------------------------------

    @app.get("/progress")
    @login_required
    def progress():
        db = get_db()
        user_id = session["user_id"]

        summary = db.execute(
            """
            SELECT COUNT(*) AS attempts,
                   COALESCE(AVG(percentage), 0) AS avg_pct,
                   COALESCE(MAX(percentage), 0) AS best_pct,
                   COALESCE(SUM(passed), 0)    AS passed
            FROM test_attempts WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        application_total = db.execute(
            "SELECT COUNT(*) AS c FROM applications WHERE user_id = ?", (user_id,)
        ).fetchone()["c"]

        by_test = db.execute(
            """
            SELECT t.id AS test_id, t.name, t.category,
                   COUNT(*) AS attempts,
                   AVG(ta.percentage) AS avg_pct,
                   MAX(ta.percentage) AS best_pct
            FROM test_attempts ta
            JOIN aptitude_tests t ON ta.test_id = t.id
            WHERE ta.user_id = ?
            GROUP BY t.id
            ORDER BY t.category ASC, t.name ASC
            """,
            (user_id,),
        ).fetchall()

        recent = db.execute(
            """
            SELECT ta.id, ta.score, ta.total_questions, ta.percentage, ta.passed,
                   ta.completed_at, t.name AS test_name, t.id AS test_id
            FROM test_attempts ta
            JOIN aptitude_tests t ON ta.test_id = t.id
            WHERE ta.user_id = ?
            ORDER BY ta.completed_at DESC, ta.id DESC
            LIMIT 10
            """,
            (user_id,),
        ).fetchall()

        status_counts = db.execute(
            "SELECT status, COUNT(*) AS c FROM applications WHERE user_id = ? "
            "GROUP BY status ORDER BY c DESC",
            (user_id,),
        ).fetchall()

        return render_template(
            "progress.html",
            summary=summary,
            application_total=application_total,
            by_test=by_test,
            recent=recent,
            status_counts=status_counts,
        )

    # -- #26 Create and update opportunity listings (FR-13) ------------------

    def _opportunity_form_values(form):
        """Read the listing form and validate it. Returns (values, errors)."""
        values = {
            "title": (form.get("title") or "").strip(),
            "company": (form.get("company") or "").strip(),
            "type": (form.get("type") or "").strip(),
            "location": (form.get("location") or "").strip(),
            "stipend": (form.get("stipend") or "").strip(),
            "description": (form.get("description") or "").strip(),
            "eligibility": (form.get("eligibility") or "").strip(),
            "deadline": (form.get("deadline") or "").strip(),
            "is_open": 1 if form.get("is_open") else 0,
        }
        errors = [
            f"{label} is required."
            for field, label in (
                ("title", "Title"),
                ("company", "Company"),
                ("location", "Location"),
                ("stipend", "Stipend / CTC"),
                ("description", "Description"),
                ("eligibility", "Eligibility"),
                ("deadline", "Deadline"),
            )
            if not values[field]
        ]
        if values["type"] not in ("Internship", "Placement"):
            errors.append("Type must be Internship or Placement.")
        if values["deadline"]:
            try:
                datetime.strptime(values["deadline"], "%Y-%m-%d")
            except ValueError:
                errors.append("Deadline must be a valid date (YYYY-MM-DD).")
        return values, errors

    @app.get("/admin/opportunities")
    @admin_required
    def admin_opportunities():
        rows = get_db().execute(
            "SELECT id, title, company, type, location, deadline, is_open "
            "FROM opportunities "
            "ORDER BY is_open DESC, deadline ASC, id ASC"
        ).fetchall()
        today = date.today().isoformat()
        items = [
            dict(row) | {"is_expired": row["deadline"] < today} for row in rows
        ]
        return render_template("admin_opportunities.html", opportunities=items)

    @app.route("/admin/opportunities/new", methods=["GET", "POST"])
    @admin_required
    def admin_opportunity_new():
        if request.method == "POST":
            values, errors = _opportunity_form_values(request.form)
            if not errors:
                db = get_db()
                db.execute(
                    "INSERT INTO opportunities (title, company, type, location, stipend, "
                    "description, eligibility, deadline, is_open) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        values["title"], values["company"], values["type"],
                        values["location"], values["stipend"], values["description"],
                        values["eligibility"], values["deadline"], values["is_open"],
                    ),
                )
                db.commit()
                flash(f"Listing '{values['title']}' created.", "success")
                return redirect(url_for("admin_opportunities"))
            for error in errors:
                flash(error, "error")
            return render_template(
                "admin_opportunity_form.html", opportunity=values, mode="new"
            ), 400

        return render_template(
            "admin_opportunity_form.html",
            opportunity={"type": "Internship", "is_open": 1},
            mode="new",
        )

    @app.route("/admin/opportunities/<int:opportunity_id>/edit", methods=["GET", "POST"])
    @admin_required
    def admin_opportunity_edit(opportunity_id: int):
        db = get_db()
        row = db.execute(
            "SELECT id, title, company, type, location, stipend, description, "
            "eligibility, deadline, is_open FROM opportunities WHERE id = ?",
            (opportunity_id,),
        ).fetchone()
        if row is None:
            abort(404)

        if request.method == "POST":
            values, errors = _opportunity_form_values(request.form)
            if not errors:
                db.execute(
                    "UPDATE opportunities SET title = ?, company = ?, type = ?, "
                    "location = ?, stipend = ?, description = ?, eligibility = ?, "
                    "deadline = ?, is_open = ? WHERE id = ?",
                    (
                        values["title"], values["company"], values["type"],
                        values["location"], values["stipend"], values["description"],
                        values["eligibility"], values["deadline"], values["is_open"],
                        opportunity_id,
                    ),
                )
                db.commit()
                flash(f"Listing '{values['title']}' updated.", "success")
                return redirect(url_for("admin_opportunities"))
            for error in errors:
                flash(error, "error")
            values["id"] = opportunity_id
            return render_template(
                "admin_opportunity_form.html", opportunity=values, mode="edit"
            ), 400

        return render_template(
            "admin_opportunity_form.html", opportunity=dict(row), mode="edit"
        )

    # -- Errors & maintenance commands --------------------------------------

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("404.html"), 403

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
