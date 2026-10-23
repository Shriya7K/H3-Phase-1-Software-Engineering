# Team H3 — Online Internship & Placement Preparation Portal

A Flask + SQLite web application for the Sprint 1 / Iteration 1 backlog of Team H3.
It implements the student-facing and core administrative workflows according to the IEEE SRS,
Architecture Specification, and Test Case Specifications.

## Implemented Backlog Items

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

# Run full test suite (91 tests across all Sprint 1 tasks)
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
| GET/POST | `/profile` | yes | Student academic & contact profile management (Task #9) |
| GET | `/opportunities` | yes | Opportunity listing with keyword search & filters (Tasks #11 & #12) |
| GET | `/opportunities/<id>` | yes | Full details, eligibility, deadline, and application status (Tasks #13 & #15) |
| POST | `/opportunities/<id>/apply` | yes | Student application submission (Tasks #14 & #15) |
| GET | `/applications` | yes | Student application tracking with recruitment statuses (Task #15) |
| POST | `/applications/<id>/status` | admin | Privruiter/admin status updater (TC-06) |
| GET | `/aptitude-tests` | yes | Active practice test listing (Task #16) |
| GET | `/aptitude-tests/<id>` | yes | Interactive test interface with multiple-choice questions (Task #18) |
| POST | `/aptitude-tests/<id>/submit` | yes | Automated score calculation & persistence (Task #18) |
| GET | `/aptitude-tests/<id>/results/<aid>` | yes | Detailed scorecard & question-by-question breakdown (Task #18) |
| GET | `/test-results` | yes | History of past test attempts (Task #18) |

## Quality & Security Verification

* **Input Validation & Integrity (`SR-05`, `NFR-09`)**: Input validation across forms, email normalization, CGPA and batch constraints, and SQLite foreign key constraints with cascade deletes.
* **Role-Based Access Control (`FR-03`, `SR-03`, `TC-03`)**: Restricted routes require appropriate role permissions; unprivileged users cannot modify application statuses.
* **Password Security (`SR-02`, `TC-13`)**: PBKDF2 salted hashes verify credentials; plaintext passwords never touch database storage.
* **Testing Coverage**: 91 unit and integration tests across 7 test suites validating all functional requirements, security boundaries, and response time thresholds.
