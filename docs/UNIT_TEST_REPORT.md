# Team H3 — Unit Test Report
## Online Internship & Placement Preparation Portal

**Document Version:** 1.0  
**Date of Execution:** November 2026  
**Test Framework:** Pytest 9.1.1 on Python 3.14.8 (win32)  
**Execution Scope:** Full automated unit and functional test suite (`tests/`)  
**Overall Status:** **135 Passed / 135 Total (100% Pass Rate)**  

---

## 1. Executive Summary

All 135 automated unit and module integration tests executed cleanly with zero failures, zero errors, and zero warnings. The tests systematically exercise and validate authentication, role-based access control, profile persistence, opportunity filtering, application pipelines, aptitude test evaluation, dashboard analytics, administrative user management, admin test authoring, database reliability, and system performance.

| Metric | Value |
|---|---|
| **Total Test Modules** | 13 test suites |
| **Total Test Cases** | 135 tests |
| **Passed** | **135 (100%)** |
| **Failed** | **0 (0%)** |
| **Skipped** | **0 (0%)** |
| **Execution Time** | ~103 seconds |
| **Overall Statement Coverage** | **91%** |
| **Branch Coverage** | **75%** |

---

## 2. Test Suite Breakdown

### 2.1 Authentication & Security (`tests/test_auth.py` — 19 Tests)
* **Scope:** Login validation, PBKDF2 hash checking, session handling, protected route redirection, logout, next-URL safety.
* **Key Tests:**
  * `test_login_successful_student`: Authenticates valid student credentials and sets session.
  * `test_login_successful_admin`: Authenticates admin user with role assignment.
  * `test_login_invalid_password`: Rejects incorrect passwords with flash alert.
  * `test_login_nonexistent_email`: Prevents enumeration and rejects unknown accounts.
  * `test_protected_pages_redirect_anonymous_users`: Redirects unauthenticated requests to `/login?next=...`.
  * `test_safe_next_url_redirect`: Sanitizes open redirect attempts to prevent phishing.
  * `test_logout_clears_session`: Verifies session token eviction on logout.
* **Result:** 19/19 Passed (100%).

### 2.2 Student Registration (`tests/test_registration.py` — 11 Tests)
* **Scope:** Registration form validation, email uniqueness constraint, password strength, role restriction.
* **Key Tests:**
  * `test_registration_success`: Successfully creates student accounts.
  * `test_registration_duplicate_email`: Rejects duplicate email addresses gracefully.
  * `test_registration_weak_password`: Enforces minimum length and character requirements.
  * `test_registration_role_defaults`: Restricts student self-registration and prevents unauthorized admin creation.
* **Result:** 11/11 Passed (100%).

### 2.3 Student Academic Profile (`tests/test_profile.py` — 6 Tests)
* **Scope:** Profile retrieval, profile creation/updates, CGPA numeric validation (0.0 to 10.0), skill tags.
* **Key Tests:**
  * `test_profile_renders_logged_in`: Renders profile view with existing data.
  * `test_profile_update_successful`: Updates USN, batch year, department, and skills.
  * `test_profile_cgpa_boundary_validation`: Rejects negative CGPAs and values > 10.0.
* **Result:** 6/6 Passed (100%).

### 2.4 Opportunities Browsing (`tests/test_opportunities.py` — 22 Tests)
* **Scope:** Drive catalog, deadline computation, active status checks, detail view, markdown/content rendering.
* **Key Tests:**
  * `test_opportunities_listing_open_drives`: Displays only active listings where `is_open = 1`.
  * `test_opportunities_deadline_badge`: Computes remaining days and adds urgent badge when deadline <= 3 days.
  * `test_opportunity_detail_view`: Renders stipend, eligibility, and job description.
  * `test_expired_opportunity_closed`: Marks drives with past deadlines as closed.
* **Result:** 22/22 Passed (100%).

### 2.5 Search & Filtering (`tests/test_search_filter.py` — 7 Tests)
* **Scope:** Keyword query matching, category filter ('Internship' vs 'Placement'), location filter, empty state.
* **Key Tests:**
  * `test_search_by_keyword`: Filters listings by company, role title, and tech stack keywords.
  * `test_filter_by_type`: Filters drives by Internship or Placement type.
  * `test_combined_search_and_location`: Accurately intersects keyword and location parameters.
  * `test_empty_search_result`: Shows user-friendly empty state with clear filter links.
* **Result:** 7/7 Passed (100%).

### 2.6 Application Pipeline (`tests/test_applications.py` — 7 Tests)
* **Scope:** Application submission, duplicate submission prevention, status tracking, recruiter status update.
* **Key Tests:**
  * `test_submit_application_success`: Files application with status `'Submitted'`.
  * `test_duplicate_application_rejected`: Enforces unique constraint per student/opportunity pair.
  * `test_student_application_tracker`: Displays chronological list of submitted applications.
* **Result:** 7/7 Passed (100%).

### 2.7 Aptitude Test Taking (`tests/test_aptitude_tests.py` — 8 Tests)
* **Scope:** Practice test catalog, test attempt initialization, question countdown timer, answer concealment.
* **Key Tests:**
  * `test_aptitude_catalog_listing`: Displays available practice tests by category.
  * `test_questions_rendered_without_answers`: Verifies `correct_option` is absent from student DOM.
  * `test_anonymous_cannot_take_test`: Restricts test access to logged-in students.
* **Result:** 8/8 Passed (100%).

### 2.8 Test Scoring & Evaluation (`tests/test_test_results.py` — 5 Tests)
* **Scope:** Server-side grading, percentage computation, pass/fail threshold evaluation, scorecard generation.
* **Key Tests:**
  * `test_score_calculation_accurate`: Verifies 100% correct score calculation.
  * `test_pass_fail_threshold`: Sets pass badge when percentage >= passing mark.
  * `test_review_answers`: Displays explanation breakdown after attempt submission.
* **Result:** 5/5 Passed (100%).

### 2.9 Analytics Dashboards (`tests/test_dashboard.py` — 8 Tests)
* **Scope:** Student readiness index calculation, admin recruitment overview, pipeline status distribution.
* **Key Tests:**
  * `test_student_dashboard_readiness_calculation`: Evaluates readiness score (0-100%).
  * `test_admin_dashboard_metrics`: Computes total students, active drives, and application distribution.
  * `test_recent_activity_stream`: Displays latest submissions and attempt events.
* **Result:** 8/8 Passed (100%).

### 2.10 Admin User Management (`tests/test_admin_users.py` — 11 Tests)
* **Scope:** RBAC enforcement, directory search/filter, role updates, self-demotion prevention, audit log creation.
* **Key Tests:**
  * `test_admin_users_access_control`: Rejects non-admin users with HTTP 403.
  * `test_admin_updates_user_role`: Promotes student to admin and logs event in `audit_logs`.
  * `test_self_demotion_lockout_guard`: Prevents the sole admin from demoting themselves.
* **Result:** 11/11 Passed (100%).

### 2.11 Admin Test Authoring (`tests/test_admin_aptitude_tests.py` — 16 Tests)
* **Scope:** Test creation form, positive duration validation, question bank builder, option configuration.
* **Key Tests:**
  * `test_admin_creates_new_test`: Inserts new test and increments test catalog.
  * `test_admin_adds_questions`: Associates multiple choice questions with correct answer key.
  * `test_invalid_duration_rejected`: Enforces positive integer duration minutes.
* **Result:** 16/16 Passed (100%).

### 2.12 Reliability & Recovery (`tests/test_reliability_recovery.py` — 9 Tests)
* **Scope:** SQLite transaction atomicity, rollback on failure, foreign key cascades, backup creation, restore CLI, 500 error page.
* **Key Tests:**
  * `test_atomic_transaction_rollback`: Ensures failure in multi-statement transaction rolls back completely.
  * `test_foreign_key_cascade`: Confirms deleting user removes associated applications and attempts.
  * `test_hot_backup_creation`: Verifies `flask backup-db` produces an intact SQLite snapshot.
  * `test_database_restoration`: Confirms restoring from backup restores records and passes `PRAGMA integrity_check`.
  * `test_central_error_handler_500`: Verifies technical stack traces are concealed from client.
* **Result:** 9/9 Passed (100%).

### 2.13 Scalability & Performance Benchmarks (`tests/test_performance.py` — 6 Tests)
* **Scope:** Response latency under large datasets (3,000+ opportunities), linear scaling verification, N+1 query guard.
* **Key Tests:**
  * `test_opportunities_listing_latency`: Median latency < 250ms with 3,000 seeded opportunities.
  * `test_linear_scaling_not_quadratic`: Ensures rendering 6,000 items does not multiply runtime quadratically.
  * `test_login_performance`: Login request latency < 1.0 second under load.
* **Result:** 6/6 Passed (100%).

---

## 3. Summary Conclusion

The test suite thoroughly validates every functional requirement (FR-01 through FR-16) and non-functional requirement (NFR-01 to NFR-09) with **100% pass rate** across all 135 unit and integration tests.
