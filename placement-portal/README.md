# Team H3 — Online Internship & Placement Preparation Portal

A small Flask + SQLite web app for the Iteration 1 backlog of Team H3. It covers
exactly the five items assigned for this iteration and deliberately leaves the
Iteration 2 features (applications, progress tracking, admin CRUD) out.

| Task | Title | Where it lives |
|------|-------|----------------|
| #7  | User login and logout | `app.py` (`/login`, `/logout`, `login_required`), `templates/login.html` |
| #11 | Display opportunities | `app.py` (`/opportunities`), `templates/opportunities.html` |
| #13 | View opportunity details | `app.py` (`/opportunities/<id>`), `templates/opportunity_detail.html` |
| #16 | Display available aptitude tests | `app.py` (`/aptitude-tests`), `templates/aptitude_tests.html` |
| #30 | Test performance requirements | `tests/test_performance.py`, indexes in `schema.sql` |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # http://127.0.0.1:5000
```

The SQLite database (`instance/portal.sqlite`) is created and seeded
automatically on first run.

### Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Student | `student@campus.edu` | `student123` |
| Admin | `admin@campus.edu` | `admin123` |

Passwords are stored as PBKDF2 hashes (Werkzeug `generate_password_hash`),
never in plain text.

### Useful commands

```bash
flask --app app reset-db     # wipe and re-seed the database
python -m pytest tests -q    # run the full test suite
```

## Routes

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/` | — | Redirect to the listing (or the login page) |
| GET/POST | `/login` | — | Sign in; `?next=` returns the user to the page they wanted |
| POST | `/logout` | yes | End the session (POST only, so links cannot log users out) |
| GET | `/opportunities` | yes | Open listings; `?type=Internship\|Placement` filters |
| GET | `/opportunities/<id>` | yes | Full description, eligibility, deadline; 404 if unknown |
| GET | `/aptitude-tests` | yes | Active practice tests |

## Behaviour notes

* **Listing** shows only opportunities where `is_open = 1` **and** the deadline
  has not passed, sorted by nearest deadline. Seed data includes one expired and
  one manually closed row so the filtering is visible.
* **Deadline chips** change colour as the deadline approaches: neutral, `is-soon`
  (≤ 7 days), `is-urgent` (≤ 3 days, plus "Closes today").
* **Details page** for a closed or expired listing still renders, with an
  "Applications closed" badge, so old links keep working.
* **Login errors** use one generic message for both unknown email and wrong
  password, so the form does not reveal which accounts exist.
* **Open redirects** are blocked: `/login?next=https://evil.example.com` falls
  back to the listing.
* **Stale sessions** (e.g. after `reset-db`) are detected and cleared.
* **Templates** escape all user data, so listing text cannot inject markup.

## Performance (task #30)

`tests/test_performance.py` seeds 3,000 opportunities and 200 aptitude tests and
asserts the targets below. Measured on the development machine with that
dataset:

| Page | Median | Max | Target |
|------|--------|-----|--------|
| `/opportunities` | ~97 ms | ~125 ms | < 250 ms |
| `/opportunities/1` | ~1 ms | ~7 ms | < 250 ms |
| `/aptitude-tests` | ~3 ms | ~6 ms | < 250 ms |

How the targets are met:

1. A composite index `(is_open, deadline)` covers the listing query — the test
   checks `EXPLAIN QUERY PLAN` to make sure SQLite uses it instead of scanning.
2. The listing issues a single query; there are no per-row queries (no N+1).
   A test doubles the dataset and asserts render time does not blow up.
3. Detail pages fetch by primary key, so they stay constant-time.
4. The stateless session cookie avoids server-side session storage lookups.

## Project structure

```
placement-portal/
├── app.py              # routes, login guard, template filters, app factory
├── db.py               # connection handling + schema/demo bootstrap
├── seed.py             # demo users, opportunities, aptitude tests
├── schema.sql          # tables + indexes
├── requirements.txt
├── templates/
│   ├── base.html       # shell, nav, flash messages
│   ├── login.html
│   ├── opportunities.html
│   ├── opportunity_detail.html
│   ├── aptitude_tests.html
│   └── 404.html
├── static/style.css    # single stylesheet, no external dependencies
└── tests/
    ├── conftest.py     # isolated database per test
    ├── test_auth.py            # #7
    ├── test_opportunities.py   # #11, #13
    ├── test_aptitude_tests.py  # #16
    └── test_performance.py     # #30
```

## Out of scope (Iteration 2)

Applying to opportunities (#14), preparation progress (#19), question
management (#20), listing CRUD (#26), and application records (#28) are not part
of this build. Nothing in the UI pretends otherwise — the detail page states
that applications arrive in Iteration 2.
