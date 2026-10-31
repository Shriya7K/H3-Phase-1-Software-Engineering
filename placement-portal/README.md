# Team H3 — Online Internship & Placement Preparation Portal

A Flask + SQLite web application for the Sprint 1 & Sprint 2 backlog of Team H3.
It implements the student-facing and core administrative workflows according to the IEEE SRS,
Architecture Specification, and Test Case Specifications.

## Implemented Backlog Items

### Sprint 1 Backlog Items

| Task | Title | Req ID | Where it lives |
|------|-------|--------|----------------|
| #6  | User registration | FR-01, SR-02, SR-05, TC-01 | `app.py` (`/register`, `/api/auth/register`), `templates/register.html`, `tests/test_registration.py` |
| #7  | User login and logout | FR-02, TC-02 | `app.py` (`/login`, `/logout`, `login_required`), `templates/login.html`, `tests/test_auth.py` |
| #9  | Create and edit student profile | FR-04 | `app.py` (`/profile`), `templates/profile.html`, `tests/test_profile.py` |
| #11 | Display opportunities | FR-05 | `app.py` (`/opportunities`), `templates/opportunities.html`, `tests/test_opportunities.py` |
| #12 | Search and filter opportunities | FR-06, TC-04, NFR-03 | `app.py` (`/opportunities?q=...&location=...`), `templates/opportunities.html`, `tests/test_search_filter.py` |
| #13 | View opportunity details | FR-05 | `app.py` (`/opportunities/<id>`), `templates/opportunity_detail.html`, `tests/test_opportunities.py` |
| #15 | Submit & track application status | FR-07, FR-08, FR-16, TC-05, TC-06 | `app.py` (`/applications`, `/opportunities/<id>/apply`, `/applications/<id>/status`), `templates/applications.html`, `tests/test_applications.py` |
| #16 | Display available aptitude tests | FR-09 | `app.py` (`/aptitude-tests`), `templates/aptitude_tests.html`, `tests/test_aptitude_tests.py` |
| #18 | Calculate and display test results | FR-09, FR-10, TC-07 | `app.py` (`/aptitude-tests/<id>`, `/aptitude-tests/<id>/submit`, `/test-results`), `templates/take_test.html`, `templates/test_result.html`, `templates/my_results.html`, `tests/test_test_results.py` |
| #30 | Test performance requirements | NFR-01, NFR-06, TC-09 | `tests/test_performance.py`, composite indexes in `schema.sql` |

### Sprint 2 Backlog Items

| Task | Title | Req ID | Where it lives |
|------|-------|--------|----------------|
| #8  | Role-based access control | FR-03, SR-03, TC-03 | `app.py` (`@admin_required`, `@login_required`), `tests/test_rbac_authorization.py` |
| #10 | Validate profile details | FR-04, SR-05, TC-11 | `app.py` (`/profile` input sanitization & boundary checks), `tests/test_profile_validation.py` |
| #21 | Display analytics dashboard | FR-12, TC-08 | `app.py` (`/dashboard`, `/api/analytics`), `templates/dashboard.html`, `tests/test_dashboard.py` |
| #22 | Show application summaries | FR-12, FR-08, TC-08 | `app.py` (`_get_student_stats`), `templates/dashboard.html`, `tests/test_analytics_metrics.py` |
| #23 | Show aptitude performance | FR-12, FR-10, TC-08 | `app.py` (`_get_student_stats`), `templates/dashboard.html`, `tests/test_analytics_metrics.py` |
| #24 | Display preparation progress | FR-11, FR-12, TC-08 | `app.py` (readiness score calculation), `templates/dashboard.html`, `tests/test_analytics_metrics.py` |
| #25 | Manage user accounts & RBAC | FR-15, SR-06, TC-14 | `app.py` (`/admin/users`, `/admin/users/<id>/role`), `templates/admin_users.html`, `tests/test_admin_users.py` |
| #27 | Manage aptitude tests & questions | FR-14 | `app.py` (`/admin/tests`, `/admin/tests/<id>/questions`), `templates/admin_tests.html`, `tests/test_admin_aptitude_tests.py` |
| #29 | Validate authorization & access controls | NFR-02, SR-01, SR-03, TC-10 | `tests/test_rbac_authorization.py`, security boundary checks |
| #31 | Test data integrity | NFR-09, SR-05, TC-11 | `tests/test_data_integrity.py`, `schema.sql` foreign keys, cascades, and check constraints |
| #32 | Test supported browser compatibility | NFR-08, TC-15 | `tests/test_browser_compatibility.py`, `docs/sprint-2/BROWSER_COMPATIBILITY_MATRIX.md` |
| #33 | Verify reliability and recovery | NFR-04, NFR-09 | `db.py` (backup/restore, transactions), `tests/test_reliability_recovery.py` |

## Quick Start

```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application (http://127.0.0.1:5000)
python app.py
```

The SQLite database (`instance/portal.sqlite`) is created and seeded automatically on first run.

### Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Student | `student@campus.edu` | `student123` |
| Admin | `admin@campus.edu` | `admin123` |

Passwords are stored as salted PBKDF2 hashes (Werkzeug `generate_password_hash`), satisfying Security Requirement `SR-02`.

### Useful Commands

```bash
# Wipe and re-seed the database
flask --app app reset-db

# Run full automated test suite (193 tests passing)
python -m pytest tests -v
```

## Route Map

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/` | — | Redirect to listing (or login page) |
| GET/POST | `/register` | — | User registration with input validation (Task #6) |
| POST | `/api/auth/register` | — | REST API endpoint for user registration (Task #6) |
| GET/POST | `/login` | — | Sign in; preserves `?next=` destination (Task #7) |
| POST | `/logout` | yes | Secure session termination (Task #7) |
| GET | `/dashboard` | yes | Role-aware Analytics Dashboard: student preparation metrics or admin pipeline (Tasks #21–24) |
| GET | `/api/analytics` | yes | REST endpoint returning aggregate dashboard analytics (Tasks #21–24) |
| GET/POST | `/profile` | yes | Student academic & contact profile management with field validation (Tasks #9 & #10) |
| GET | `/opportunities` | yes | Opportunity listing with keyword search & filters (Tasks #11 & #12) |
| GET | `/opportunities/<id>` | yes | Full details, eligibility, deadline, and application status (Tasks #13 & #15) |
| POST | `/opportunities/<id>/apply` | yes | Student application submission (Tasks #14 & #15) |
| GET | `/applications` | yes | Student application tracking with recruitment statuses (Task #15) |
| POST | `/applications/<id>/status` | admin | Status updater with audit logging (Tasks #15, #16, #25) |
| GET | `/aptitude-tests` | yes | Active practice test listing (Task #16) |
| GET | `/aptitude-tests/<id>` | yes | Interactive test interface with multiple-choice questions (Task #18) |
| POST | `/aptitude-tests/<id>/submit` | yes | Automated score calculation & persistence (Task #18) |
| GET | `/aptitude-tests/<id>/results/<aid>` | yes | Detailed scorecard & question-by-question breakdown (Task #18) |
| GET | `/test-results` | yes | History of past test attempts (Task #18) |
| GET | `/admin/users` | admin | User management directory with search and role filters (Task #25) |
| POST | `/admin/users/<id>/role` | admin | Update user role with sole-admin lockout prevention & audit log (Task #25) |
| GET | `/admin/tests` | admin | Assessment management dashboard listing all tests (Task #27) |
| GET/POST | `/admin/tests/new` | admin | Create new aptitude assessment with metadata validation (Task #27) |
| GET/POST | `/admin/tests/<id>/edit` | admin | Update test details, duration, category, and status (Task #27) |
| POST | `/admin/tests/<id>/toggle` | admin | Toggle test visibility between draft and published (Task #27) |
| GET/POST | `/admin/tests/<id>/questions` | admin | Question bank management: view and append questions (Task #27) |

## Quality & Security Verification

* **Input Validation & Integrity (`SR-05`, `NFR-09`, Tasks #10 & #31)**: Field-level validation on registration and profiles (USN, phone, CGPA, graduation batch, URLs), prevention of XSS via safe protocols, and strict SQLite relational constraints (foreign key cascades, CHECK constraints, UNIQUE constraints).
* **Role-Based Access Control (`FR-03`, `SR-03`, `NFR-02`, Tasks #8 & #29)**: Strict server-side route guarding (`@login_required`, `@admin_required`); unprivileged student access to admin routes returns HTTP 403 Forbidden. Anonymous access returns HTTP 302 or HTTP 401 for APIs.
* **Data Integrity & Rollback (`NFR-04`, `NFR-09`, Tasks #31 & #33)**: Multi-statement transaction atomicity, online database backup/restore commands, and automated cascade deletions.
* **Browser Compatibility (`NFR-08`, Task #32)**: Standards-compliant HTML5 DOCTYPE, UTF-8 encoding, responsive viewport configurations, and cross-browser smoke suite for Google Chrome, Mozilla Firefox, and Microsoft Edge.
* **Password Security (`SR-02`, `TC-13`)**: Salted PBKDF2 hashes verify credentials; plaintext passwords never touch database storage.
* **Testing Coverage**: 193 unit and integration tests across 12 test suites validating functional requirements, security boundaries, database integrity, and browser compatibility.
