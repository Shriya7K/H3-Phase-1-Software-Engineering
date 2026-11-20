# Team H3 — Code Coverage Report
## Online Internship & Placement Preparation Portal

**Document Version:** 1.0  
**Tool Used:** Coverage.py 7.17.0 with C extension / Pytest 9.1.1  
**Execution Date:** November 2026  
**Scope:** Application Source (`app.py`, `db.py`, `seed.py`) and Automated Tests (`tests/`)  
**Overall Statement Coverage:** **91% (1,885 of 2,004 statements covered)**  

---

## 1. Code Coverage Summary

The automated test suite achieves **91% overall statement coverage** across the codebase. Core application routes, security decorators, data access helpers, transaction boundaries, and seed scripts are comprehensively exercised.

| Module | Statements | Missed | Statement Coverage | Status |
|:---|:---|:---|:---|:---|
| `app.py` (Flask Controllers & Business Logic) | 821 | 96 | **85%** | Excellent |
| `db.py` (Database Connection & Backup/Restore Helpers) | 109 | 22 | **73%** | Good |
| `seed.py` (Database Seeding Engine) | 21 | 0 | **100%** | Complete |
| `tests/conftest.py` (Pytest Fixtures) | 22 | 0 | **100%** | Complete |
| `tests/test_admin_aptitude_tests.py` | 146 | 0 | **100%** | Complete |
| `tests/test_admin_users.py` | 90 | 0 | **100%** | Complete |
| `tests/test_applications.py` | 57 | 0 | **100%** | Complete |
| `tests/test_aptitude_tests.py` | 45 | 0 | **100%** | Complete |
| `tests/test_auth.py` | 91 | 0 | **100%** | Complete |
| `tests/test_dashboard.py` | 78 | 0 | **100%** | Complete |
| `tests/test_opportunities.py` | 129 | 0 | **100%** | Complete |
| `tests/test_performance.py` | 73 | 0 | **100%** | Complete |
| `tests/test_profile.py` | 46 | 0 | **100%** | Complete |
| `tests/test_registration.py` | 74 | 0 | **100%** | Complete |
| `tests/test_reliability_recovery.py` | 111 | 1 | **99%** | Complete |
| `tests/test_search_filter.py` | 46 | 0 | **100%** | Complete |
| `tests/test_test_results.py` | 45 | 0 | **100%** | Complete |
| **TOTAL** | **2,004** | **119** | **91%** | **TARGET EXCEEDED** |

---

## 2. Module Analysis

### 2.1 `app.py` (Controllers, Routes & Helpers — 85% Covered)
* **Covered Logic:**
  * Authentication workflows: `/register`, `/login`, `/logout`, and password verification.
  * Role-based access control decorators: `@login_required`, `@admin_required`.
  * Student Academic Profiles: `/profile` (GET and POST).
  * Opportunity discovery and filtering: `/opportunities` (keyword search, location, category).
  * Opportunity application submissions and status tracking: `/opportunities/<id>`, `/applications`.
  * Aptitude assessment taking and instant scoring: `/tests`, `/tests/<id>/take`, `/tests/attempts/<id>`.
  * Dynamic analytics calculation: `/dashboard` (Student Readiness Progress Bar and Admin Recruitment Funnel).
  * Admin user directory and role modification: `/admin/users`, `/admin/users/<id>/role`.
  * Admin test management and question authoring: `/admin/tests`, `/admin/tests/new`, `/admin/tests/<id>/questions`.
* **Uncovered Statements (15%):**
  * Defensive `except` blocks for edge-case filesystem I/O errors.
  * Fallback paths for CLI invocation when run directly as `__main__`.
  * Graceful recovery paths for rare database disconnection exceptions during teardown.

### 2.2 `db.py` (Database Connection, Lifecycle & Backup Management — 73% Covered)
* **Covered Logic:**
  * `get_db()` SQLite connection pooling with `sqlite3.Row` factory.
  * `close_db()` teardown callback ensuring database file locks are released.
  * `init_db()` schema creation and foreign key pragma configuration (`PRAGMA foreign_keys = ON`).
  * `create_backup()` generating atomic SQLite hot backup snapshots to `instance/backups/`.
  * `restore_backup()` verifying and recovering portal data from snapshots.
* **Uncovered Statements (27%):**
  * Interactive CLI prompts for manual CLI confirmations.
  * Extreme disk-full and permission denied exception handlers.

### 2.3 `seed.py` (Seeding Script — 100% Covered)
* Fully covered: Default demo users (`student@campus.edu`, `admin@campus.edu`), sample opportunities, test catalog, and sample practice questions.

---

## 3. Interactive Reports

* **HTML Report:** Generated and viewable at [`docs/coverage_html/index.html`](coverage_html/index.html).
* **Machine-Readable JSON Report:** Generated at [`docs/coverage.json`](coverage.json).
