"""Team H3 - Online Internship & Placement Preparation Portal.

Covers Sprint 1 & Iteration 1/2 features:
    #6  User registration (FR-01, SR-02, SR-05, TC-01)
    #7  User login and logout (FR-02, TC-02)
    #9  Create and edit student profile (FR-04)
    #11 Display opportunities (FR-05)
    #12 Search and filter opportunities (FR-06, TC-04, NFR-03)
    #13 View opportunity details (FR-05)
    #15 Track application status (FR-07, FR-08, FR-16, TC-05, TC-06)
    #16 Display available aptitude tests (FR-09)
    #18 Calculate and display test results (FR-09, FR-10, TC-07)
    #21 Analytics Dashboard (FR-12, TC-08)
    #25 Manage Users (FR-15, SR-06, TC-14)
    #30 Performance requirements (tested in tests/test_performance.py)
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from functools import wraps
from urllib.parse import urlparse

import click
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import (
    backup_database,
    check_database_integrity,
    close_db,
    get_db,
    init_db,
    restore_database,
)


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
                if request.path.startswith("/api/"):
                    return (
                        jsonify(
                            {
                                "success": False,
                                "errorCode": "UNAUTHORIZED",
                                "message": "Authentication required.",
                            }
                        ),
                        401,
                    )
                next_url = request.full_path if request.query_string else request.path
                return redirect(url_for("login", next=next_url))
            return view(*args, **kwargs)

        return wrapped_view

    def admin_required(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not session.get("user_id"):
                if request.path.startswith("/api/"):
                    return (
                        jsonify(
                            {
                                "success": False,
                                "errorCode": "UNAUTHORIZED",
                                "message": "Authentication required.",
                            }
                        ),
                        401,
                    )
                next_url = request.full_path if request.query_string else request.path
                return redirect(url_for("login", next=next_url))
            if session.get("user_role") != "admin":
                if request.path.startswith("/api/"):
                    return (
                        jsonify(
                            {
                                "success": False,
                                "errorCode": "FORBIDDEN",
                                "message": "Administrator privileges required.",
                            }
                        ),
                        403,
                    )
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view

    def log_audit(
        action: str,
        details: str,
        result: str = "SUCCESS",
        actor_id: int | None = None,
        actor_email: str | None = None,
    ) -> None:
        """Insert an audit log entry for security and compliance (SR-06, TC-14)."""
        try:
            db = get_db()
            uid = actor_id if actor_id is not None else session.get("user_id")
            email = actor_email
            if email is None and uid:
                user_row = db.execute("SELECT email FROM users WHERE id = ?", (uid,)).fetchone()
                if user_row:
                    email = user_row["email"]
            if not email:
                email = "system@internal"
            ip = request.remote_addr or "127.0.0.1"
            db.execute(
                """
                INSERT INTO audit_logs (user_id, actor_email, action, details, result, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (uid, email, action, details, result, ip),
            )
            db.commit()
        except Exception:
            pass

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

            # Field-level validation for profile details (Task #10, SR-05, NFR-09)
            if usn:
                clean_usn = usn.replace("-", "").replace("_", "")
                if not (clean_usn.isalnum() and 5 <= len(usn) <= 20):
                    flash("Invalid USN format. USN must be 5-20 alphanumeric characters.", "error")
                    return render_template("profile.html", user=user, profile=request.form), 400

            if phone:
                digit_count = sum(1 for c in phone if c.isdigit())
                valid_chars = all(c.isdigit() or c in " +-()#" for c in phone)
                if not (valid_chars and 8 <= len(phone) <= 20 and digit_count >= 7):
                    flash("Invalid phone number format.", "error")
                    return render_template("profile.html", user=user, profile=request.form), 400

            if github_url:
                if not (github_url.startswith("http://") or github_url.startswith("https://")):
                    flash("GitHub URL must start with http:// or https://.", "error")
                    return render_template("profile.html", user=user, profile=request.form), 400

            if linkedin_url:
                if not (linkedin_url.startswith("http://") or linkedin_url.startswith("https://")):
                    flash("LinkedIn URL must start with http:// or https://.", "error")
                    return render_template("profile.html", user=user, profile=request.form), 400

            if bio and len(bio) > 1000:
                flash("Bio cannot exceed 1000 characters.", "error")
                return render_template("profile.html", user=user, profile=request.form), 400

            if skills and len(skills) > 500:
                flash("Skills cannot exceed 500 characters.", "error")
                return render_template("profile.html", user=user, profile=request.form), 400

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

        today_str = date.today().isoformat()
        sql = (
            "SELECT id, title, company, type, location, stipend, deadline, "
            "CAST(ROUND(julianday(deadline) - julianday(?)) AS INTEGER) AS days_left "
            "FROM opportunities "
            "WHERE is_open = 1 AND deadline >= ?"
        )
        params: list[str] = [today_str, today_str]

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

        return render_template(
            "opportunities.html",
            opportunities=rows,
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

        log_audit(
            action="APPLICATION_STATUS_UPDATE",
            details=f"Application #{application_id} status changed to '{new_status}'",
            result="SUCCESS",
        )

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

    # -----------------------------------------------------------------------
    # Task #27 · FR-14 Manage Aptitude Tests & Questions
    # -----------------------------------------------------------------------

    @app.get("/admin/tests")
    @admin_required
    def admin_aptitude_tests():
        """Admin overview of all active and inactive aptitude tests (FR-14)."""
        db = get_db()
        search_query = (request.args.get("q") or "").strip()
        active_category = (request.args.get("category") or "").strip()
        active_status = (request.args.get("status") or "").strip().lower()

        sql = """
            SELECT t.id, t.name, t.category, t.description, t.num_questions,
                   t.duration_minutes, t.difficulty, t.is_active,
                   (SELECT COUNT(*) FROM test_questions WHERE test_id = t.id) AS actual_questions_count,
                   (SELECT COUNT(*) FROM test_attempts WHERE test_id = t.id) AS attempts_count
            FROM aptitude_tests t
            WHERE 1=1
        """
        params: list[str] = []

        if active_category:
            sql += " AND t.category = ?"
            params.append(active_category)

        if active_status == "active":
            sql += " AND t.is_active = 1"
        elif active_status == "inactive":
            sql += " AND t.is_active = 0"

        if search_query:
            sql += " AND (t.name LIKE ? OR t.category LIKE ? OR t.description LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term])

        sql += " ORDER BY t.id ASC"

        tests = db.execute(sql, params).fetchall()

        cat_rows = db.execute(
            "SELECT DISTINCT category FROM aptitude_tests ORDER BY category ASC"
        ).fetchall()
        categories = [r["category"] for r in cat_rows]

        summary = db.execute(
            """
            SELECT
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_cnt,
                SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) AS inactive_cnt
            FROM aptitude_tests
            """
        ).fetchone()

        active_count = summary["active_cnt"] or 0 if summary else 0
        inactive_count = summary["inactive_cnt"] or 0 if summary else 0

        q_count_row = db.execute(
            "SELECT COUNT(*) AS cnt FROM test_questions"
        ).fetchone()
        total_questions = q_count_row["cnt"] if q_count_row else 0

        return render_template(
            "admin_tests.html",
            tests=tests,
            categories=categories,
            active_category=active_category,
            active_status=active_status,
            search_query=search_query,
            active_count=active_count,
            inactive_count=inactive_count,
            total_questions=total_questions,
        )

    @app.route("/admin/tests/new", methods=["GET", "POST"])
    @admin_required
    def admin_create_test():
        """Create a new aptitude assessment (FR-14)."""
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            category = (request.form.get("category") or "").strip()
            description = (request.form.get("description") or "").strip()
            difficulty = (request.form.get("difficulty") or "Medium").strip()
            duration_raw = request.form.get("duration_minutes") or "30"
            is_active_raw = request.form.get("is_active") or "1"

            if not name or len(name) < 2:
                flash("Test title must be at least 2 characters.", "error")
                return (
                    render_template(
                        "admin_test_form.html", mode="create", test=request.form
                    ),
                    400,
                )

            if not category:
                flash("Category is required.", "error")
                return (
                    render_template(
                        "admin_test_form.html", mode="create", test=request.form
                    ),
                    400,
                )

            if not description:
                flash("Description is required.", "error")
                return (
                    render_template(
                        "admin_test_form.html", mode="create", test=request.form
                    ),
                    400,
                )

            try:
                duration_minutes = int(duration_raw)
                if duration_minutes <= 0 or duration_minutes > 300:
                    raise ValueError()
            except ValueError:
                flash(
                    "Duration must be a positive number of minutes (1-300).",
                    "error",
                )
                return (
                    render_template(
                        "admin_test_form.html", mode="create", test=request.form
                    ),
                    400,
                )

            if difficulty not in ("Easy", "Medium", "Hard"):
                difficulty = "Medium"

            is_active = 1 if str(is_active_raw) == "1" else 0

            db = get_db()
            cursor = db.execute(
                """
                INSERT INTO aptitude_tests
                    (name, category, description, num_questions, duration_minutes, difficulty, is_active)
                VALUES
                    (?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    name,
                    category,
                    description,
                    duration_minutes,
                    difficulty,
                    is_active,
                ),
            )
            new_id = cursor.lastrowid
            db.commit()

            log_audit(
                action="CREATE_APTITUDE_TEST",
                details=(
                    f"Created test '{name}' (ID #{new_id}) in category"
                    f" '{category}'"
                ),
                result="SUCCESS",
            )
            flash(
                f"Test '{name}' created successfully. Now add questions below.",
                "success",
            )
            return redirect(url_for("admin_test_questions", test_id=new_id))

        return render_template(
            "admin_test_form.html", mode="create", test=None
        )

    @app.route("/admin/tests/<int:test_id>/edit", methods=["GET", "POST"])
    @admin_required
    def admin_edit_test(test_id: int):
        """Edit test metadata, time limit, and difficulty (FR-14)."""
        db = get_db()
        test = db.execute(
            "SELECT * FROM aptitude_tests WHERE id = ?", (test_id,)
        ).fetchone()
        if test is None:
            abort(404)

        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            category = (request.form.get("category") or "").strip()
            description = (request.form.get("description") or "").strip()
            difficulty = (request.form.get("difficulty") or "Medium").strip()
            duration_raw = request.form.get("duration_minutes") or "30"
            is_active_raw = request.form.get("is_active") or "1"

            if not name or len(name) < 2:
                flash("Test title must be at least 2 characters.", "error")
                return (
                    render_template(
                        "admin_test_form.html",
                        mode="edit",
                        test=dict(test, **request.form),
                    ),
                    400,
                )

            if not category:
                flash("Category is required.", "error")
                return (
                    render_template(
                        "admin_test_form.html",
                        mode="edit",
                        test=dict(test, **request.form),
                    ),
                    400,
                )

            if not description:
                flash("Description is required.", "error")
                return (
                    render_template(
                        "admin_test_form.html",
                        mode="edit",
                        test=dict(test, **request.form),
                    ),
                    400,
                )

            try:
                duration_minutes = int(duration_raw)
                if duration_minutes <= 0 or duration_minutes > 300:
                    raise ValueError()
            except ValueError:
                flash(
                    "Duration must be a positive number of minutes (1-300).",
                    "error",
                )
                return (
                    render_template(
                        "admin_test_form.html",
                        mode="edit",
                        test=dict(test, **request.form),
                    ),
                    400,
                )

            if difficulty not in ("Easy", "Medium", "Hard"):
                difficulty = "Medium"

            is_active = 1 if str(is_active_raw) == "1" else 0

            db.execute(
                """
                UPDATE aptitude_tests
                SET name = ?, category = ?, description = ?, duration_minutes = ?, difficulty = ?, is_active = ?
                WHERE id = ?
                """,
                (
                    name,
                    category,
                    description,
                    duration_minutes,
                    difficulty,
                    is_active,
                    test_id,
                ),
            )
            db.commit()

            log_audit(
                action="UPDATE_APTITUDE_TEST",
                details=f"Updated test #{test_id} ('{name}')",
                result="SUCCESS",
            )
            flash(f"Test '{name}' updated successfully.", "success")
            return redirect(url_for("admin_aptitude_tests"))

        return render_template(
            "admin_test_form.html", mode="edit", test=dict(test)
        )

    @app.post("/admin/tests/<int:test_id>/toggle")
    @admin_required
    def admin_toggle_test(test_id: int):
        """Toggle test publication status (active/inactive) (FR-14)."""
        db = get_db()
        test = db.execute(
            "SELECT id, name, is_active FROM aptitude_tests WHERE id = ?",
            (test_id,),
        ).fetchone()
        if test is None:
            abort(404)

        new_status = 1 if test["is_active"] == 0 else 0
        db.execute(
            "UPDATE aptitude_tests SET is_active = ? WHERE id = ?",
            (new_status, test_id),
        )
        db.commit()

        status_label = "Active" if new_status == 1 else "Inactive"
        log_audit(
            action="TOGGLE_APTITUDE_TEST",
            details=(
                f"Toggled test #{test_id} ('{test['name']}') status to"
                f" '{status_label}'"
            ),
            result="SUCCESS",
        )
        flash(f"Status for '{test['name']}' set to {status_label}.", "success")
        return redirect(url_for("admin_aptitude_tests"))

    @app.get("/admin/tests/<int:test_id>/questions")
    @admin_required
    def admin_test_questions(test_id: int):
        """Manage questions for a specific aptitude assessment (FR-14)."""
        db = get_db()
        test = db.execute(
            "SELECT * FROM aptitude_tests WHERE id = ?", (test_id,)
        ).fetchone()
        if test is None:
            abort(404)

        questions = db.execute(
            """
            SELECT id, test_id, question_text, option_a, option_b, option_c, option_d, correct_option
            FROM test_questions
            WHERE test_id = ?
            ORDER BY id ASC
            """,
            (test_id,),
        ).fetchall()

        return render_template(
            "admin_test_questions.html", test=dict(test), questions=questions
        )

    @app.post("/admin/tests/<int:test_id>/questions")
    @admin_required
    def admin_add_question(test_id: int):
        """Add a new multiple-choice question to an assessment (FR-14)."""
        db = get_db()
        test = db.execute(
            "SELECT id, name FROM aptitude_tests WHERE id = ?", (test_id,)
        ).fetchone()
        if test is None:
            abort(404)

        question_text = (request.form.get("question_text") or "").strip()
        option_a = (request.form.get("option_a") or "").strip()
        option_b = (request.form.get("option_b") or "").strip()
        option_c = (request.form.get("option_c") or "").strip()
        option_d = (request.form.get("option_d") or "").strip()
        correct_option = (
            request.form.get("correct_option") or ""
        ).strip().upper()

        if not question_text or len(question_text) < 4:
            flash("Question text must be at least 4 characters long.", "error")
            return (
                redirect(url_for("admin_test_questions", test_id=test_id)),
                400,
            )

        if not option_a or not option_b or not option_c or not option_d:
            flash("All four options (A, B, C, D) are required.", "error")
            return (
                redirect(url_for("admin_test_questions", test_id=test_id)),
                400,
            )

        if correct_option not in ("A", "B", "C", "D"):
            flash("Correct option must be A, B, C, or D.", "error")
            return (
                redirect(url_for("admin_test_questions", test_id=test_id)),
                400,
            )

        db.execute(
            """
            INSERT INTO test_questions
                (test_id, question_text, option_a, option_b, option_c, option_d, correct_option)
            VALUES
                (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                test_id,
                question_text,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_option,
            ),
        )
        db.execute(
            "UPDATE aptitude_tests SET num_questions = (SELECT COUNT(*) FROM"
            " test_questions WHERE test_id = ?) WHERE id = ?",
            (test_id, test_id),
        )
        db.commit()

        log_audit(
            action="ADD_TEST_QUESTION",
            details=f"Added question to test #{test_id} ('{test['name']}')",
            result="SUCCESS",
        )
        flash("Question added successfully.", "success")
        return redirect(url_for("admin_test_questions", test_id=test_id))

    @app.post("/admin/tests/<int:test_id>/questions/<int:question_id>/edit")
    @admin_required
    def admin_edit_question(test_id: int, question_id: int):
        """Edit question text, options, or correct answer (FR-14)."""
        db = get_db()
        q = db.execute(
            "SELECT id FROM test_questions WHERE id = ? AND test_id = ?",
            (question_id, test_id),
        ).fetchone()
        if q is None:
            abort(404)

        question_text = (request.form.get("question_text") or "").strip()
        option_a = (request.form.get("option_a") or "").strip()
        option_b = (request.form.get("option_b") or "").strip()
        option_c = (request.form.get("option_c") or "").strip()
        option_d = (request.form.get("option_d") or "").strip()
        correct_option = (
            request.form.get("correct_option") or ""
        ).strip().upper()

        if not question_text or len(question_text) < 4:
            flash("Question text must be at least 4 characters long.", "error")
            return (
                redirect(url_for("admin_test_questions", test_id=test_id)),
                400,
            )

        if not option_a or not option_b or not option_c or not option_d:
            flash("All four options (A, B, C, D) are required.", "error")
            return (
                redirect(url_for("admin_test_questions", test_id=test_id)),
                400,
            )

        if correct_option not in ("A", "B", "C", "D"):
            flash("Correct option must be A, B, C, or D.", "error")
            return (
                redirect(url_for("admin_test_questions", test_id=test_id)),
                400,
            )

        db.execute(
            """
            UPDATE test_questions
            SET question_text = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_option = ?
            WHERE id = ? AND test_id = ?
            """,
            (
                question_text,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_option,
                question_id,
                test_id,
            ),
        )
        db.commit()

        log_audit(
            action="UPDATE_TEST_QUESTION",
            details=f"Updated question #{question_id} for test #{test_id}",
            result="SUCCESS",
        )
        flash("Question updated successfully.", "success")
        return redirect(url_for("admin_test_questions", test_id=test_id))

    @app.post("/admin/tests/<int:test_id>/questions/<int:question_id>/delete")
    @admin_required
    def admin_delete_question(test_id: int, question_id: int):
        """Remove a question from an assessment (FR-14)."""
        db = get_db()
        q = db.execute(
            "SELECT id FROM test_questions WHERE id = ? AND test_id = ?",
            (question_id, test_id),
        ).fetchone()
        if q is None:
            abort(404)

        db.execute(
            "DELETE FROM test_questions WHERE id = ? AND test_id = ?",
            (question_id, test_id),
        )
        db.execute(
            "UPDATE aptitude_tests SET num_questions = (SELECT COUNT(*) FROM"
            " test_questions WHERE test_id = ?) WHERE id = ?",
            (test_id, test_id),
        )
        db.commit()

        log_audit(
            action="DELETE_TEST_QUESTION",
            details=f"Deleted question #{question_id} from test #{test_id}",
            result="SUCCESS",
        )
        flash("Question deleted.", "success")
        return redirect(url_for("admin_test_questions", test_id=test_id))

    @app.post("/api/tests")
    @admin_required
    def api_create_test():
        """Create aptitude test via REST API (FR-14)."""
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        category = (data.get("category") or "").strip()
        description = (data.get("description") or "").strip()
        difficulty = (data.get("difficulty") or "Medium").strip()
        duration_raw = data.get("duration_minutes", 30)
        is_active = 1 if data.get("is_active", 1) in (1, True, "1") else 0

        if not name or len(name) < 2:
            return (
                jsonify(
                    {
                        "success": False,
                        "errorCode": "VALIDATION_ERROR",
                        "message": (
                            "Field 'name' is required (min 2 characters)."
                        ),
                    }
                ),
                400,
            )

        if not category:
            return (
                jsonify(
                    {
                        "success": False,
                        "errorCode": "VALIDATION_ERROR",
                        "message": "Field 'category' is required.",
                    }
                ),
                400,
            )

        if not description:
            return (
                jsonify(
                    {
                        "success": False,
                        "errorCode": "VALIDATION_ERROR",
                        "message": "Field 'description' is required.",
                    }
                ),
                400,
            )

        try:
            duration_minutes = int(duration_raw)
            if duration_minutes <= 0 or duration_minutes > 300:
                raise ValueError()
        except (ValueError, TypeError):
            return (
                jsonify(
                    {
                        "success": False,
                        "errorCode": "VALIDATION_ERROR",
                        "message": (
                            "Field 'duration_minutes' must be a positive"
                            " integer between 1 and 300."
                        ),
                    }
                ),
                400,
            )

        if difficulty not in ("Easy", "Medium", "Hard"):
            difficulty = "Medium"

        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO aptitude_tests
                (name, category, description, num_questions, duration_minutes, difficulty, is_active)
            VALUES
                (?, ?, ?, 0, ?, ?, ?)
            """,
            (
                name,
                category,
                description,
                duration_minutes,
                difficulty,
                is_active,
            ),
        )
        new_id = cursor.lastrowid
        db.commit()

        log_audit(
            action="CREATE_APTITUDE_TEST",
            details=f"Created aptitude test '{name}' (ID #{new_id}) via API",
            result="SUCCESS",
        )

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "id": new_id,
                        "name": name,
                        "category": category,
                        "description": description,
                        "duration_minutes": duration_minutes,
                        "difficulty": difficulty,
                        "is_active": is_active,
                        "num_questions": 0,
                    },
                    "message": "Aptitude test created successfully.",
                }
            ),
            201,
        )

    @app.get("/api/tests")
    @login_required
    def api_list_tests():
        """List tests via REST API (FR-09). Students only see active tests without answer keys."""
        role = session.get("user_role", "student")
        db = get_db()
        if role == "admin":
            rows = db.execute(
                """
                SELECT id, name, category, description, num_questions, duration_minutes, difficulty, is_active,
                       (SELECT COUNT(*) FROM test_questions WHERE test_id = aptitude_tests.id) AS questions_count
                FROM aptitude_tests
                ORDER BY id ASC
                """
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT id, name, category, description, num_questions, duration_minutes, difficulty
                FROM aptitude_tests
                WHERE is_active = 1
                ORDER BY category ASC, name ASC
                """
            ).fetchall()

        return jsonify(
            {
                "success": True,
                "data": [dict(r) for r in rows],
                "message": "Aptitude tests retrieved successfully.",
            }
        )

    # -----------------------------------------------------------------------
    # Task #21 · FR-12 Analytics Dashboard
    # -----------------------------------------------------------------------

    def _get_student_stats(user_id: int) -> dict:
        db = get_db()

        # Application counts by status
        app_rows = db.execute(
            """
            SELECT status, COUNT(*) AS cnt
            FROM applications
            WHERE user_id = ?
            GROUP BY status
            """,
            (user_id,),
        ).fetchall()

        app_status = {
            "Submitted": 0,
            "Under Review": 0,
            "Shortlisted": 0,
            "Accepted": 0,
            "Rejected": 0,
        }
        for r in app_rows:
            if r["status"] in app_status:
                app_status[r["status"]] = r["cnt"]

        total_apps = sum(app_status.values())

        # Test attempts aggregation
        attempt_stats = db.execute(
            """
            SELECT
                COUNT(*) AS total_attempts,
                COUNT(DISTINCT test_id) AS distinct_tests,
                SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) AS passed_count,
                AVG(percentage) AS avg_score,
                MAX(percentage) AS best_score
            FROM test_attempts
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        total_attempts = attempt_stats["total_attempts"] if attempt_stats else 0
        distinct_tests = attempt_stats["distinct_tests"] if attempt_stats else 0
        passed_count = (
            attempt_stats["passed_count"]
            if (attempt_stats and attempt_stats["passed_count"])
            else 0
        )
        avg_score = (
            round(attempt_stats["avg_score"], 1)
            if (attempt_stats and attempt_stats["avg_score"] is not None)
            else 0.0
        )
        best_score = (
            round(attempt_stats["best_score"], 1)
            if (attempt_stats and attempt_stats["best_score"] is not None)
            else 0.0
        )

        # Total active aptitude tests
        active_tests_row = db.execute(
            "SELECT COUNT(*) AS total_active FROM aptitude_tests WHERE is_active = 1"
        ).fetchone()
        total_active_tests = (
            active_tests_row["total_active"] if active_tests_row else 0
        )

        # Honest readiness progress metric (FR-12 & SRS TC-08)
        if total_active_tests > 0:
            progress_percent = min(
                100, round((distinct_tests / total_active_tests) * 100)
            )
        else:
            progress_percent = 0

        if progress_percent == 0:
            readiness_status = "Not Started"
        elif progress_percent < 50:
            readiness_status = "Getting Started"
        elif progress_percent < 100:
            readiness_status = "Good Progress"
        else:
            readiness_status = "Placement Ready"

        # Assessment coverage breakdown for this student
        breakdown_rows = db.execute(
            """
            SELECT
                t.id,
                t.name,
                t.category,
                COUNT(ta.id) AS attempt_count,
                COALESCE(MAX(ta.percentage), 0) AS best_percentage,
                COALESCE(MAX(ta.passed), 0) AS has_passed
            FROM aptitude_tests t
            LEFT JOIN test_attempts ta ON t.id = ta.test_id AND ta.user_id = ?
            WHERE t.is_active = 1
            GROUP BY t.id, t.name, t.category
            ORDER BY t.category ASC, t.name ASC
            """,
            (user_id,),
        ).fetchall()
        test_breakdown = [dict(r) for r in breakdown_rows]

        # Recent applications (limit 5)
        recent_apps_rows = db.execute(
            """
            SELECT
                a.id,
                a.opportunity_id AS opp_id,
                a.status,
                a.applied_at,
                o.title,
                o.company
            FROM applications a
            JOIN opportunities o ON a.opportunity_id = o.id
            WHERE a.user_id = ?
            ORDER BY a.applied_at DESC
            LIMIT 5
            """,
            (user_id,),
        ).fetchall()
        recent_applications = [dict(r) for r in recent_apps_rows]

        # Recent test attempts (limit 5)
        recent_tests_rows = db.execute(
            """
            SELECT
                ta.id,
                ta.score,
                ta.total_questions,
                ta.percentage,
                ta.passed,
                ta.completed_at,
                t.name,
                t.category
            FROM test_attempts ta
            JOIN aptitude_tests t ON ta.test_id = t.id
            WHERE ta.user_id = ?
            ORDER BY ta.completed_at DESC
            LIMIT 5
            """,
            (user_id,),
        ).fetchall()
        recent_test_attempts = [dict(r) for r in recent_tests_rows]

        return {
            "total_apps": total_apps,
            "app_status": app_status,
            "total_attempts": total_attempts,
            "distinct_tests": distinct_tests,
            "passed_count": passed_count,
            "avg_score": avg_score,
            "best_score": best_score,
            "total_active_tests": total_active_tests,
            "progress_percent": progress_percent,
            "readiness_status": readiness_status,
            "test_breakdown": test_breakdown,
            "recent_applications": recent_applications,
            "recent_test_attempts": recent_test_attempts,
        }

    def _get_admin_stats() -> dict:
        db = get_db()

        # Users overview
        user_counts = db.execute(
            """
            SELECT
                COUNT(*) AS total_users,
                SUM(CASE WHEN role = 'student' THEN 1 ELSE 0 END) AS total_students,
                SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) AS total_admins
            FROM users
            """
        ).fetchone()

        total_users = user_counts["total_users"] if user_counts else 0
        total_students = (
            user_counts["total_students"]
            if (user_counts and user_counts["total_students"])
            else 0
        )
        total_admins = (
            user_counts["total_admins"]
            if (user_counts and user_counts["total_admins"])
            else 0
        )

        # Opportunities overview
        today_iso = date.today().isoformat()
        opp_counts = db.execute(
            """
            SELECT
                COUNT(*) AS total_opps,
                SUM(CASE WHEN is_open = 1 AND deadline >= ? THEN 1 ELSE 0 END) AS open_opps
            FROM opportunities
            """,
            (today_iso,),
        ).fetchone()

        total_opps = opp_counts["total_opps"] if opp_counts else 0
        open_opps = (
            opp_counts["open_opps"]
            if (opp_counts and opp_counts["open_opps"])
            else 0
        )

        # Applications by status
        app_rows = db.execute(
            """
            SELECT status, COUNT(*) AS cnt
            FROM applications
            GROUP BY status
            """
        ).fetchall()

        app_status = {
            "Submitted": 0,
            "Under Review": 0,
            "Shortlisted": 0,
            "Accepted": 0,
            "Rejected": 0,
        }
        for r in app_rows:
            if r["status"] in app_status:
                app_status[r["status"]] = r["cnt"]

        total_apps = sum(app_status.values())

        # Test attempts overall
        attempt_stats = db.execute(
            """
            SELECT
                COUNT(*) AS total_attempts,
                AVG(percentage) AS avg_score,
                SUM(CASE WHEN passed = 1 THEN 1.0 ELSE 0.0 END) AS passed_count
            FROM test_attempts
            """
        ).fetchone()

        total_attempts = attempt_stats["total_attempts"] if attempt_stats else 0
        overall_avg_score = (
            round(attempt_stats["avg_score"], 1)
            if (attempt_stats and attempt_stats["avg_score"] is not None)
            else 0.0
        )
        passed_count = (
            attempt_stats["passed_count"]
            if (attempt_stats and attempt_stats["passed_count"])
            else 0.0
        )
        overall_pass_rate = (
            round((passed_count / total_attempts) * 100, 1)
            if total_attempts > 0
            else 0.0
        )

        # Recent applications across the portal
        recent_app_rows = db.execute(
            """
            SELECT
                a.id,
                a.status,
                a.applied_at,
                u.name AS student_name,
                u.email AS student_email,
                o.title AS opp_title,
                o.company
            FROM applications a
            JOIN users u ON a.user_id = u.id
            JOIN opportunities o ON a.opportunity_id = o.id
            ORDER BY a.applied_at DESC
            LIMIT 6
            """
        ).fetchall()
        recent_applications = [dict(r) for r in recent_app_rows]

        # Recent security audit trail
        recent_log_rows = db.execute(
            """
            SELECT id, user_id, actor_email, action, details, result, timestamp
            FROM audit_logs
            ORDER BY timestamp DESC, id DESC
            LIMIT 6
            """
        ).fetchall()
        recent_audit_logs = [dict(r) for r in recent_log_rows]

        return {
            "total_users": total_users,
            "total_students": total_students,
            "total_admins": total_admins,
            "total_opps": total_opps,
            "open_opps": open_opps,
            "total_apps": total_apps,
            "app_status": app_status,
            "total_attempts": total_attempts,
            "overall_avg_score": overall_avg_score,
            "overall_pass_rate": overall_pass_rate,
            "recent_applications": recent_applications,
            "recent_audit_logs": recent_audit_logs,
        }

    @app.get("/dashboard")
    @login_required
    def dashboard():
        """Integrated Analytics Dashboard (FR-12, TC-08)."""
        role = session.get("user_role", "student")
        if role == "admin":
            stats = _get_admin_stats()
        else:
            stats = _get_student_stats(session["user_id"])
        return render_template("dashboard.html", role=role, stats=stats)

    @app.get("/api/analytics")
    @login_required
    def api_analytics():
        """REST endpoint returning dashboard analytics."""
        role = session.get("user_role", "student")
        if role == "admin":
            stats = _get_admin_stats()
        else:
            stats = _get_student_stats(session["user_id"])
        return jsonify(
            {
                "success": True,
                "data": stats,
                "message": "Analytics retrieved successfully.",
            }
        )

    # -----------------------------------------------------------------------
    # Task #25 · FR-15 User Administration (SR-06, TC-14)
    # -----------------------------------------------------------------------

    @app.get("/admin/users")
    @admin_required
    def admin_users():
        """User management directory with search and role filtering (FR-15)."""
        db = get_db()
        search_query = (request.args.get("q") or "").strip()
        active_role = (request.args.get("role") or "").strip().lower()

        sql = """
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                sp.usn,
                sp.department,
                sp.batch_year,
                sp.cgpa,
                (SELECT COUNT(*) FROM applications WHERE user_id = u.id) AS app_count,
                (SELECT COUNT(*) FROM test_attempts WHERE user_id = u.id) AS test_count
            FROM users u
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE 1=1
        """
        params: list[str] = []

        if active_role in ("student", "admin"):
            sql += " AND u.role = ?"
            params.append(active_role)

        if search_query:
            sql += " AND (u.name LIKE ? OR u.email LIKE ? OR sp.usn LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term])

        sql += " ORDER BY u.id ASC"

        users = db.execute(sql, params).fetchall()

        audit_logs = db.execute(
            """
            SELECT id, user_id, actor_email, action, details, result, timestamp
            FROM audit_logs
            ORDER BY timestamp DESC, id DESC
            LIMIT 20
            """
        ).fetchall()

        return render_template(
            "admin_users.html",
            users=users,
            search_query=search_query,
            active_role=active_role,
            audit_logs=audit_logs,
        )

    @app.post("/admin/users/<int:user_id>/role")
    @admin_required
    def admin_update_user_role(user_id: int):
        """Update a user's system role with privilege enforcement & audit logging (SR-06, TC-14)."""
        db = get_db()
        target_user = db.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if target_user is None:
            abort(404)

        new_role = (request.form.get("role") or "").strip().lower()
        if new_role not in ("student", "admin"):
            flash(
                "Invalid role specified. Allowed roles are 'student' or 'admin'.",
                "error",
            )
            return redirect(url_for("admin_users")), 400

        old_role = target_user["role"]

        # Prevent accidental lockout: Sole admin cannot demote themselves
        if user_id == session.get("user_id") and new_role != "admin":
            admin_count = db.execute(
                "SELECT COUNT(*) AS cnt FROM users WHERE role = 'admin'"
            ).fetchone()["cnt"]
            if admin_count <= 1:
                flash(
                    "Cannot remove admin privileges from the sole system administrator account.",
                    "error",
                )
                return redirect(url_for("admin_users")), 400

        if old_role != new_role:
            db.execute(
                "UPDATE users SET role = ? WHERE id = ?", (new_role, user_id)
            )
            db.commit()

            # Update session role if editing own account
            if user_id == session.get("user_id"):
                session["user_role"] = new_role

            log_audit(
                action="CHANGE_USER_ROLE",
                details=(
                    f"User #{user_id} ({target_user['email']}) role changed "
                    f"from '{old_role}' to '{new_role}'"
                ),
                result="SUCCESS",
            )
            flash(
                f"Updated role for {target_user['name']} to '{new_role}'.",
                "success",
            )
        else:
            flash(
                f"User {target_user['name']} already has role '{new_role}'.",
                "info",
            )

        return redirect(url_for("admin_users"))

    @app.get("/api/admin/users")
    @admin_required
    def api_admin_users():
        """REST endpoint returning user directory (SR-02: password hashes strictly omitted)."""
        db = get_db()
        search_query = (request.args.get("q") or "").strip()
        active_role = (request.args.get("role") or "").strip().lower()

        sql = """
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                sp.usn,
                sp.department,
                sp.batch_year,
                sp.cgpa,
                (SELECT COUNT(*) FROM applications WHERE user_id = u.id) AS app_count,
                (SELECT COUNT(*) FROM test_attempts WHERE user_id = u.id) AS test_count
            FROM users u
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE 1=1
        """
        params: list[str] = []

        if active_role in ("student", "admin"):
            sql += " AND u.role = ?"
            params.append(active_role)

        if search_query:
            sql += " AND (u.name LIKE ? OR u.email LIKE ? OR sp.usn LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term])

        sql += " ORDER BY u.id ASC"

        rows = db.execute(sql, params).fetchall()
        user_list = [dict(r) for r in rows]

        return jsonify(
            {
                "success": True,
                "data": user_list,
                "message": "Users retrieved successfully.",
            }
        )

    # -- Errors & maintenance commands (NFR-04, NFR-09) --------------------

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "success": False,
                        "errorCode": "NOT_FOUND",
                        "message": "The requested resource was not found.",
                    }
                ),
                404,
            )
        return render_template("404.html"), 404

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "success": False,
                        "errorCode": "FORBIDDEN",
                        "message": (
                            "You do not have permission to access this"
                            " resource."
                        ),
                    }
                ),
                403,
            )
        return render_template("404.html"), 403

    @app.errorhandler(500)
    def internal_server_error(error):
        """Rollback active transaction and present safe user message without stack traces (NFR-04)."""
        connection = g.get("db")
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                pass
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "success": False,
                        "errorCode": "INTERNAL_ERROR",
                        "message": (
                            "An unexpected internal error occurred. Please try"
                            " again later."
                        ),
                    }
                ),
                500,
            )
        return render_template("500.html"), 500

    @app.cli.command("reset-db")
    def reset_db_command():
        """Delete the database and recreate it with fresh demo data."""
        database = app.config["DATABASE"]
        if os.path.exists(database):
            os.remove(database)
        init_db(app)
        print(f"Reset {database} with fresh demo data.")

    @app.cli.command("backup-db")
    @click.option(
        "--output", default=None, help="Custom output path for backup file."
    )
    def backup_db_command(output: str | None):
        """Create a safe, verified SQLite online backup (NFR-04, NFR-09)."""
        try:
            path = backup_database(app, output)
            print(f"Database successfully backed up to: {path}")
        except Exception as exc:
            print(f"Backup failed: {exc}")

    @app.cli.command("restore-db")
    @click.argument("backup_path")
    def restore_db_command(backup_path: str):
        """Safely restore the active database from a verified backup (NFR-04, NFR-09)."""
        try:
            restore_database(app, backup_path)
            print(f"Database successfully restored from: {backup_path}")
        except Exception as exc:
            print(f"Restore failed: {exc}")

    @app.cli.command("check-integrity")
    def check_integrity_command():
        """Check SQLite B-tree, schema, and foreign-key integrity (NFR-04, NFR-09)."""
        ok, errors = check_database_integrity(app.config["DATABASE"])
        if ok:
            print(
                "Database integrity: OK (No corruptions or foreign-key"
                " violations)."
            )
        else:
            print(
                "Database integrity ERRORS found:\n"
                + "\n".join(f"- {e}" for e in errors)
            )

    return app


if __name__ == "__main__":
    create_app().run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
