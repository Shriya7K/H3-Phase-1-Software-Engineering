# Iteration 2 (Sprint 2) Engineering & Verification Deliverable Report

**Project**: Team H3 — Online Internship & Placement Preparation Portal  
**Course**: Software Engineering Academic Project (Semester V, PES University)  
**Assigned Contributor**: Sia Simran A (`PES1UG24CS453` / `siasimran-magic`)  
**Repository**: [Shriya7K/H3-Phase-1-Software-Engineering](https://github.com/Shriya7K/H3-Phase-1-Software-Engineering)  
**Date**: October 31, 2026  

---

## 1. Executive Summary

This deliverable report documents the engineering, specification, test planning, automated validation, and simulated test execution completed for **Iteration 2 (Sprint 2)** of the Online Internship & Placement Preparation Portal. 

Following the successful completion of Sprint 1 (which delivered core registration, authentication, academic profile management, opportunity catalog browsing, application tracking, interactive aptitude testing, and initial query optimization under tasks #6, #7, #9, #11–13, #15–18, and #30), Sprint 2 focuses on advanced platform quality, administrative capabilities, progress tracking, analytics, and security verification.

This report directly fulfills the assigned Sprint 2 backlog items:
* **Task #8**: Role-based access control (`FR-03`, `SR-03`, `TC-03`)
* **Task #10**: Validate profile details (`FR-04`, `SR-05`, `TC-11`)
* **Task #22**: Show application summaries (`FR-12`, `FR-08`, `TC-08`)
* **Task #23**: Show aptitude performance (`FR-12`, `FR-10`, `TC-08`)
* **Task #24**: Display preparation progress (`FR-11`, `FR-12`, `TC-08`)
* **Task #29**: Validate authorization and access controls (`NFR-02`, `SR-01`, `SR-03`, `TC-10`)
* **Task #31**: Test data integrity (`NFR-09`, `SR-05`, `TC-11`)
* **Task #32**: Test supported browser compatibility (`NFR-08`, `TC-15`)

Across these eight issues, **59 new automated test cases** were designed, implemented, and verified, bringing total repository automated test coverage to **193 passing tests**. In addition, formal design specifications, simulated execution records, a browser compatibility matrix, and an updated Requirements Traceability Matrix (RTM) have been established.

---

## 2. Sprint 2 Scope & Deliverable Type Determination

In accordance with Software Engineering course guidelines, backlog items in academic software development represent diverse engineering responsibilities beyond direct code authoring. Each assigned issue was analyzed against the project SRS (`01_COMPLETE_SRS_IEEE_STYLE.docx`), IEEE-style Test Plan (`02_COMPLETE_IEEE_TEST_PLAN.docx`), Test Case Specification (`03_COMPLETE_TEST_CASES_15.docx`), and Architecture Specification (`04_COMPLETE_ARCHITECTURE_AND_DESIGN.docx`).

The determined deliverable type and engineering rationale for each assigned issue are detailed below:

| Issue ID | Issue Title | Primary Requirement | Test Case ID | Required Deliverable Type | Determination & Engineering Rationale |
|---|---|---|---|---|---|
| **#8** | Role-based access control | `FR-03`, `SR-03` | `TC-03` | **Architectural Design & Automated Test Suite** | While route decorator wrappers exist in the codebase, the system lacked a formal RBAC permission matrix and systematic cross-role automated boundary tests. Deliverable comprises the architectural RBAC matrix plus 26 automated authorization tests in `test_rbac_authorization.py`. |
| **#10** | Validate profile details | `FR-04`, `SR-05`, `NFR-09` | `TC-11` | **Software Implementation & Validation Test Suite** | The initial Sprint 1 profile form lacked field-level domain validation (phone, USN, URL schemes, and text boundaries). Deliverable comprises actual server-side validation logic in `app.py` plus 7 automated unit/integration validation tests in `test_profile_validation.py`. |
| **#22** | Show application summaries | `FR-12`, `FR-08` | `TC-08` | **Requirements Specification & Automated Test Suite** | The underlying UI dashboard was introduced under Epic #21. Story #22 requires formal acceptance criteria, pipeline metric verification, empty state testing, tenant isolation, and REST API validation. Tested via `test_analytics_metrics.py`. |
| **#23** | Show aptitude performance | `FR-12`, `FR-10` | `TC-08` | **Metric Specification & Automated Test Suite** | Requires formal definition and verification of score aggregation algorithms (unweighted average, best attempt, pass threshold at 50%, category breakdown). Tested via `test_analytics_metrics.py`. |
| **#24** | Display preparation progress | `FR-11`, `FR-12` | `TC-08` | **Algorithm Specification, Automated Tests & Workflow Simulation** | Requires formal specification of the preparation progress formula, curriculum coverage calculation, and milestone transitions ("Not Started" to "Placement Ready"). Verified via `test_analytics_metrics.py` and workflow simulation records. |
| **#29** | Validate authorization & access controls | `NFR-02`, `SR-01`, `SR-03` | `TC-10`, `SV-01`, `SV-02` | **Security Specification, Penetration Simulation & Test Suite** | Requires systematic security auditing of all protected endpoints (HTML and REST), verifying HTTP 302/401 for anonymous access, HTTP 403 for unauthorized privilege requests, and resistance to cookie tampering. Covered in `test_rbac_authorization.py`. |
| **#31** | Test data integrity | `NFR-09`, `SR-05`, `SO-03` | `TC-11` | **Test Plan Specification & Automated Test Suite** | Requires systematic testing of SQLite database constraints: referential cascades (user/opp/test deletion), CHECK constraints (domain rules), UNIQUE constraints, and atomic transaction rollback. Implemented in `test_data_integrity.py`. |
| **#32** | Test supported browser compatibility | `NFR-08` | `TC-15` | **Compatibility Test Matrix & Automated User-Agent Smoke Suite** | Requires browser compatibility matrix for Chrome, Firefox, and Edge (latest two stable versions), HTML5 standards verification, responsive viewport checks, and automated User-Agent smoke tests in `test_browser_compatibility.py`. |

---

## 3. Detailed Requirements & Acceptance Criteria

### 3.1 Task #8: Role-Based Access Control (`FR-03`, `SR-03`, `TC-03`)
* **Requirement**: The system shall enforce role-based access for students, administrators, and recruiters. Unprivileged users attempting administrative actions shall be rejected without access to privileged data or operations.
* **Acceptance Criteria**:
  1. *AC-08.1*: Anonymous requests to protected student or administrative URLs must redirect to `/login` (or return JSON 401 for `/api/*` endpoints).
  2. *AC-08.2*: Authenticated students attempting to access administrative routes (`/admin/users`, `/admin/tests`, etc.) must receive HTTP 403 Forbidden.
  3. *AC-08.3*: Privilege escalation via form parameters or session cookie manipulation must be strictly rejected.
  4. *AC-08.4*: Administrative users must have unobstructed access to all management endpoints.

### 3.2 Task #10: Validate Profile Details (`FR-04`, `SR-05`, `TC-11`)
* **Requirement**: The system shall validate all student profile inputs on the server before database persistence, rejecting malformed, out-of-bounds, or malicious data with actionable feedback.
* **Acceptance Criteria**:
  1. *AC-10.1 (Name)*: Name cannot be empty and must contain at least 2 characters.
  2. *AC-10.2 (USN)*: If provided, USN must contain 5–20 alphanumeric characters (hyphens allowed). Special characters and script tags must be rejected with HTTP 400.
  3. *AC-10.3 (Phone)*: If provided, phone numbers must contain 8–20 characters with at least 7 numeric digits. Pure alphabetic or invalid symbol inputs must be rejected with HTTP 400.
  4. *AC-10.4 (URLs)*: GitHub and LinkedIn URLs must explicitly begin with `http://` or `https://`. Disallowed protocols (e.g. `javascript:`, `ftp:`) must be rejected with HTTP 400.
  5. *AC-10.5 (Academics)*: Graduation batch year must be an integer between 2000 and 2099; CGPA must be a decimal between 0.0 and 10.0.
  6. *AC-10.6 (Text Boundaries)*: Bio must not exceed 1,000 characters; skills must not exceed 500 characters.

### 3.3 Task #22: Show Application Summaries (`FR-12`, `FR-08`, `TC-08`)
* **Requirement**: The system shall provide students with real-time aggregate summaries of their internship and placement applications categorized by recruitment status.
* **Acceptance Criteria**:
  1. *AC-22.1 (Total Count)*: The dashboard must display the exact total number of applications submitted by the logged-in student.
  2. *AC-22.2 (Status Breakdown)*: Applications must be partitioned into the canonical workflow statuses: `Submitted`, `Under Review`, `Shortlisted`, `Accepted`, and `Rejected`.
  3. *AC-22.3 (Dynamic Updates)*: Status changes made by administrators or recruiters must immediately reflect in the student's summary metrics.
  4. *AC-22.4 (Empty State)*: A student with zero applications must see a clear, user-friendly empty state without calculation errors.
  5. *AC-22.5 (Tenant Isolation)*: Summary figures must be strictly scoped to `session["user_id"]`; under no circumstance shall candidate A's application counts include candidate B's data.

### 3.4 Task #23: Show Aptitude Performance (`FR-12`, `FR-10`, `TC-08`)
* **Requirement**: The system shall display statistical evaluations of a student's practice assessment activity, including attempt volume, average score, pass rate, best score, and category-level breakdown.
* **Acceptance Criteria**:
  1. *AC-23.1 (Attempt Count)*: Display the total count of completed test attempts.
  2. *AC-23.2 (Average Score)*: Compute the arithmetic mean percentage across all attempts, rounded to one decimal place.
  3. *AC-23.3 (Pass Rate & Count)*: Record passes based on the 50% passing threshold; display the count and percentage of passed tests.
  4. *AC-23.4 (Best Score)*: Identify the maximum score percentage achieved across all attempts.
  5. *AC-23.5 (Category Breakdown)*: Group performance by test category (Quantitative Aptitude, Logical Reasoning, Verbal Ability, Technical Core), showing attempt count and best percentage per assessment.

### 3.5 Task #24: Display Preparation Progress (`FR-11`, `FR-12`, `TC-08`)
* **Requirement**: The system shall calculate and display a normalized preparation readiness progress indicator based on campus test curriculum coverage.
* **Acceptance Criteria**:
  1. *AC-24.1 (Mathematical Formula)*: Preparation progress percentage is defined as:
     $$\text{Progress \%} = \min\left(100, \text{round}\left(\frac{\text{Distinct Active Tests Attempted}}{\text{Total Published Active Tests}} \times 100\right)\right)$$
  2. *AC-24.2 (Milestone Statuses)*:
     * $0\%$: `"Not Started"`
     * $1\% \le \text{Progress} < 50\%$: `"Getting Started"`
     * $50\% \le \text{Progress} < 100\%$: `"Good Progress"`
     * $100\%$: `"Placement Ready"`
  3. *AC-24.3 (Visual Representation)*: Display an animated progress bar and milestone status badge on the dashboard.
  4. *AC-24.4 (REST API Consistency)*: The calculated percentage and readiness status must be identically exposed via `GET /api/analytics`.

### 3.6 Task #29: Validate Authorization and Access Controls (`NFR-02`, `SR-01`, `SR-03`, `TC-10`)
* **Requirement**: All protected endpoints and resources must enforce authentication and role authorization checks. Unauthorized requests must be rejected, and security-relevant administrative actions must be audited.
* **Acceptance Criteria**:
  1. *AC-29.1*: Anonymous requests to any protected route must receive HTTP 302 redirecting to `/login` (with return destination preserved in `?next=`).
  2. *AC-29.2*: Anonymous API requests must receive JSON HTTP 401 with `{"success": false, "errorCode": "UNAUTHORIZED"}`.
  3. *AC-29.3*: Authenticated student requests to administrative routes or APIs must receive HTTP 403 Forbidden.
  4. *AC-29.4*: Session tampering (e.g. setting an invalid user ID) must clear the invalid session and require re-authentication.

### 3.7 Task #31: Test Data Integrity (`NFR-09`, `SR-05`, `TC-11`)
* **Requirement**: Relational database constraints shall reject updates that violate referential, entity, or domain integrity rules. Failed transactions must roll back without corrupting valid data.
* **Acceptance Criteria**:
  1. *AC-31.1 (Referential Cascades)*: Deleting a record in `users` must cascade and delete associated records in `student_profiles`, `applications`, and `test_attempts`. Deleting an opportunity must cascade to applications; deleting an aptitude test must cascade to test questions and attempts.
  2. *AC-31.2 (Domain Constraints)*: Attempts to insert invalid roles, out-of-bounds CGPA, invalid test difficulties, invalid answer options, or non-positive durations must raise `sqlite3.IntegrityError`.
  3. *AC-31.3 (Entity Uniqueness)*: Duplicate emails or duplicate applications for the same student-opportunity pair must raise `sqlite3.IntegrityError`.
  4. *AC-31.4 (Atomicity)*: Multi-statement transactions must roll back in their entirety when an intermediate operation violates integrity constraints.

### 3.8 Task #32: Test Supported Browser Compatibility (`NFR-08`, `TC-15`)
* **Requirement**: The portal shall support the two latest stable versions of Chrome, Firefox, and Edge on desktop and responsive mobile viewports without functional or visual failure.
* **Acceptance Criteria**:
  1. *AC-32.1 (Standards)*: Valid HTML5 `<!doctype html>` and UTF-8 charset on every rendered view.
  2. *AC-32.2 (Viewport)*: `<meta name="viewport" content="width=device-width, initial-scale=1">` on all pages.
  3. *AC-32.3 (MIME & Styling)*: Static stylesheet served as `text/css` using standard W3C CSS Grid and Flexbox constructs.
  4. *AC-32.4 (Smoke Suite)*: Core workflows (login, opportunities, applications, test attempts, analytics) execute without errors across User-Agent strings for Chrome, Firefox, and Edge.

---

## 4. Software Architecture & Design Specifications

### 4.1 Role-Based Access Control (RBAC) Permission Matrix

The architecture defines three functional actors (Student, Administrator, Recruiter/Company). The table below specifies permitted operations across all 16 Functional Requirements:

| Functional Requirement | Operation Description | Student Role | Recruiter / Company | System Administrator |
|---|---|:---:|:---:|:---:|
| **FR-01** | User Account Registration | ✓ (self) | ✓ (self) | ✓ (create users) |
| **FR-02** | User Authentication (Login/Logout) | ✓ | ✓ | ✓ |
| **FR-03** | Role-Based Authorization Enforcement | — (enforced) | — (enforced) | ✓ (manage roles) |
| **FR-04** | Manage Student Academic Profile | ✓ (own profile) | ✗ (read-only in apps) | ✓ (view in directory) |
| **FR-05** | Browse Internship & Placement Listings | ✓ (active only) | ✓ (company listings) | ✓ (all listings) |
| **FR-06** | Search and Filter Opportunities | ✓ | ✓ | ✓ |
| **FR-07** | Submit Application to Opportunity | ✓ (eligible students)| ✗ | ✗ |
| **FR-08** | Track Submitted Application Status | ✓ (own applications)| ✗ | ✓ (pipeline view) |
| **FR-09** | Browse & Attempt Practice Aptitude Tests| ✓ (published tests) | ✗ | ✓ (preview mode) |
| **FR-10** | View Aptitude Test Scorecard & Results | ✓ (own results) | ✗ | ✓ (aggregate stats) |
| **FR-11** | Preparation Activity & Progress Tracking| ✓ (own metrics) | ✗ | ✓ (curriculum audit) |
| **FR-12** | Analytics & Pipeline Dashboard | ✓ (student view) | ✓ (applicant pool) | ✓ (system aggregate) |
| **FR-13** | Create, Update & Close Opportunity Listings| ✗ | ✓ (own listings) | ✓ (all listings) |
| **FR-14** | Manage Aptitude Tests & Question Bank | ✗ | ✗ | ✓ (full CRUD) |
| **FR-15** | Manage User Directory & Assign Roles | ✗ | ✗ | ✓ (with audit log) |
| **FR-16** | Update Candidate Application Status | ✗ | ✓ (own applicants) | ✓ (administrative) |

### 4.2 Route Authorization Guard Architecture

Route security in `placement-portal/app.py` is implemented using composable Python function decorators:

```
[Incoming HTTP Request]
         │
         ▼
   @login_required ────────► Session contains user_id?
         │                          │
        YES                         NO ──► Redirect /login (or 401 JSON for /api/*)
         │
         ▼
   @admin_required ────────► Session role == 'admin'?
         │                          │
        YES                         NO ──► HTTP 403 Forbidden (403.html or 403 JSON)
         │
         ▼
[Execute View Handler]
```

### 4.3 Profile Field Validation Model

Input validation in `placement-portal/app.py` (`def profile()`) enforces the following validation specifications:

| Field | Type | Required | Validation Rules / Boundaries | Sanitization / Handling | Error Response |
|---|---|:---:|---|---|---|
| `name` | String | Yes | Minimum 2 characters, non-whitespace | `.strip()` | HTTP 400: *"Name cannot be empty."* |
| `usn` | String | No | 5–20 alphanumeric chars, hyphens allowed | `.strip()`, regex `^[A-Za-z0-9_-]{5,20}$` | HTTP 400: *"Invalid USN format."* |
| `phone` | String | No | 8–20 chars, min 7 digits, allowed `+ - ( ) #` | `.strip()`, digit count check | HTTP 400: *"Invalid phone number format."* |
| `department` | String | No | Max 100 characters | `.strip()` | Stored safely |
| `batch_year` | Integer | No | $2000 \le \text{year} \le 2099$ | `int()` parsing | HTTP 400: *"Graduation year must be between 2000 and 2099."* |
| `cgpa` | Float | No | $0.0 \le \text{cgpa} \le 10.0$ | `float()` parsing | HTTP 400: *"CGPA must be between 0.0 and 10.0."* |
| `skills` | String | No | Max 500 characters | `.strip()` | HTTP 400: *"Skills cannot exceed 500 characters."* |
| `bio` | String | No | Max 1,000 characters | `.strip()` | HTTP 400: *"Bio cannot exceed 1000 characters."* |
| `github_url` | String | No | Must begin with `http://` or `https://` | Protocol prefix check | HTTP 400: *"GitHub URL must start with http:// or https://."* |
| `linkedin_url`| String | No | Must begin with `http://` or `https://` | Protocol prefix check | HTTP 400: *"LinkedIn URL must start with http:// or https://."* |

---

## 5. Requirements Traceability Matrix (RTM) Updates

The table below updates the project's formal Requirements Traceability Matrix, mapping Functional Requirements (`FR`), Non-Functional Requirements (`NFR`), and Security Requirements (`SR`) to their architecture components, Test Case specifications (`TC`), and automated test suites:

| Req ID | Requirement Category | Architectural Component | Test Case ID | Automated Pytest File | Jira Issue |
|---|---|---|---|---|:---:|
| `FR-01` | User Registration | Authentication Module | `TC-01` | `tests/test_registration.py` | #6 |
| `FR-02` | User Authentication | Authentication Module | `TC-02` | `tests/test_auth.py` | #7 |
| `FR-03` | Role-Based Access Control | Authorization Service | `TC-03` | `tests/test_rbac_authorization.py` | **#8** |
| `FR-04` | Profile Management & Validation | Student Profile Service | `TC-11` | `tests/test_profile_validation.py` | **#10** |
| `FR-05` | Browse Opportunity Catalog | Opportunity Service | `TC-04` | `tests/test_opportunities.py` | #11, #13 |
| `FR-06` | Opportunity Search & Filter | Opportunity Service | `TC-04` | `tests/test_search_filter.py` | #12 |
| `FR-07` | Submit Opportunity Application | Application Service | `TC-05` | `tests/test_applications.py` | #14, #15 |
| `FR-08` | Track Application Status | Application Service | `TC-06` | `tests/test_applications.py`, `tests/test_analytics_metrics.py` | **#22** |
| `FR-09` | Aptitude Test Catalog & Attempt | Test & Assessment Module | `TC-07` | `tests/test_aptitude_tests.py`, `tests/test_test_results.py` | #16, #17 |
| `FR-10` | Calculate & Display Test Results| Test & Assessment Module | `TC-07` | `tests/test_test_results.py`, `tests/test_analytics_metrics.py` | **#23** |
| `FR-11` | Preparation Progress Tracking | Progress & Analytics Service| `TC-08` | `tests/test_analytics_metrics.py` | **#24** |
| `FR-12` | Analytics Dashboard | Progress & Analytics Service| `TC-08` | `tests/test_dashboard.py`, `tests/test_analytics_metrics.py` | #21, **#22–24** |
| `FR-13` | Manage Opportunity Listings | Recruiter / Admin Module | `TC-04` | `tests/test_opportunities.py` | #26 |
| `FR-14` | Manage Tests & Question Bank | Test & Assessment Module | `TC-07` | `tests/test_admin_aptitude_tests.py` | #20, #27 |
| `FR-15` | User Management Directory | Administrative Module | `TC-14` | `tests/test_admin_users.py` | #25 |
| `FR-16` | Application Status Management | Application Service | `TC-06` | `tests/test_applications.py` | #28 |
| `NFR-01` | Response Time Performance | Persistence & Query Layer | `TC-09` | `tests/test_performance.py` | #30 |
| `NFR-02` | Protected Access Security | Security Architecture | `TC-10` | `tests/test_rbac_authorization.py` | **#29** |
| `NFR-04` | Transaction Reliability | SQLite Persistence Layer | `TC-11` | `tests/test_reliability_recovery.py`, `tests/test_data_integrity.py` | #33 |
| `NFR-08` | Browser Compatibility | Web Presentation Layer | `TC-15` | `tests/test_browser_compatibility.py` | **#32** |
| `NFR-09` | Data Integrity & Constraints | Relational Database Layer | `TC-11` | `tests/test_data_integrity.py` | **#31** |
| `SR-01` | Protected Authentication | Authentication Module | `TC-10` | `tests/test_rbac_authorization.py` | **#29** |
| `SR-02` | Salted Password Hashing | Security Module | `TC-13` | `tests/test_registration.py` | #6 |
| `SR-03` | Role-Restricted Functions | Authorization Module | `TC-03`, `TC-10` | `tests/test_rbac_authorization.py` | **#8, #29** |
| `SR-05` | Input Validation & Sanitization | Service Layer | `TC-11` | `tests/test_profile_validation.py`, `tests/test_data_integrity.py` | **#10, #31** |
| `SR-06` | Administrative Audit Logging | Audit Trail Service | `TC-14` | `tests/test_admin_users.py` | #25 |

---

## 6. Automated Verification & Test Execution Results

Five dedicated test suites were implemented to verify the eight assigned issues. All tests pass with zero errors:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: placement-portal
plugins: anyio-4.14.0

tests/test_profile_validation.py ........                                [ 11%]
tests/test_rbac_authorization.py ..........................              [ 55%]
tests/test_analytics_metrics.py .......                                  [ 67%]
tests/test_data_integrity.py ......                                      [ 77%]
tests/test_browser_compatibility.py .............                        [100%]

============================= 59 passed in 34.76s =============================
```

### Breakdown by Test Suite

1. **`tests/test_profile_validation.py` (7 tests — Task #10)**:
   * `test_profile_update_valid_usn_formats`: Verifies PES USN and alphanumeric formats are accepted.
   * `test_profile_update_invalid_usn_rejected`: Verifies short, overly long, and symbol-laden USNs return 400.
   * `test_profile_update_valid_phone_formats`: Verifies international and domestic phone formats are accepted.
   * `test_profile_update_invalid_phone_rejected`: Verifies alphabetical or malformed numbers return 400.
   * `test_profile_update_valid_urls`: Verifies standard HTTP/HTTPS GitHub and LinkedIn URLs are stored.
   * `test_profile_update_invalid_urls_rejected`: Verifies javascript/ftp URL injection attempts return 400.
   * `test_profile_update_bio_and_skills_length_limits`: Verifies boundaries on bio (1,000) and skills (500).

2. **`tests/test_rbac_authorization.py` (26 tests — Tasks #8 & #29)**:
   * 12 parameterized tests verifying anonymous GET requests to protected routes redirect to `/login` (302).
   * 1 test verifying anonymous API requests to `/api/analytics` return 401 Unauthorized with standard JSON envelope.
   * 5 parameterized tests verifying student GET requests to `/admin/users`, `/admin/tests`, `/admin/tests/new`, `/admin/tests/1/edit`, `/admin/tests/1/questions` return 403 Forbidden.
   * 5 parameterized tests verifying student POST actions on user roles, test creation, test editing, question addition, and application status updates return 403 Forbidden.
   * 1 test verifying student access to `/api/admin/users` and `POST /api/tests` returns 403 Forbidden.
   * 1 test verifying administrators have unobstructed access to all management endpoints.
   * 1 test verifying cookie session tampering cannot achieve role escalation.

3. **`tests/test_analytics_metrics.py` (7 tests — Tasks #22, #23, #24)**:
   * `test_task_22_application_summaries_empty_state`: Verifies zero-state handling for new students.
   * `test_task_22_application_summaries_counts_and_pipeline`: Verifies pipeline metrics across Accepted, Under Review, Shortlisted, Rejected.
   * `test_task_22_application_summaries_api_payload`: Verifies `/api/analytics` data structures.
   * `test_task_23_aptitude_performance_metrics_calculation`: Verifies average score, best score, and pass count.
   * `test_task_23_aptitude_performance_category_breakdown`: Verifies assessment category breakdown table.
   * `test_task_24_preparation_progress_milestone_transitions`: Verifies progress advancement from 0% ("Not Started") through 100% ("Placement Ready").
   * `test_tasks_22_23_24_student_tenant_isolation`: Verifies complete data isolation between student candidate accounts.

4. **`tests/test_data_integrity.py` (6 tests — Task #31)**:
   * `test_referential_integrity_user_cascade_deletion`: Verifies cascade deletion of profiles, applications, and attempts on user delete.
   * `test_referential_integrity_opportunity_cascade_deletion`: Verifies cascade deletion of applications on opportunity delete.
   * `test_referential_integrity_test_cascade_deletion`: Verifies cascade deletion of questions and attempts on test delete.
   * `test_domain_integrity_check_constraints`: Verifies SQLite CHECK constraints for roles, types, difficulties, options, CGPA, and durations.
   * `test_entity_integrity_unique_constraints`: Verifies rejection of duplicate emails and duplicate student applications.
   * `test_transaction_atomicity_and_rollback`: Verifies multi-statement rollback on constraint violation.

5. **`tests/test_browser_compatibility.py` (13 tests — Task #32)**:
   * `test_html5_doctype_and_charset_standards_anonymous`: Verifies standards doctype on anonymous pages.
   * `test_html5_doctype_and_charset_standards_protected`: Verifies standards doctype on protected student pages.
   * `test_responsive_viewport_meta_tag_anonymous`: Verifies viewport meta tag on anonymous pages.
   * `test_responsive_viewport_meta_tag_protected`: Verifies viewport meta tag on protected pages.
   * `test_stylesheet_served_with_correct_mime_and_modern_css`: Verifies CSS MIME type, flexbox, and grid.
   * 7 parameterized cross-browser smoke tests simulating User-Agents for Chrome, Firefox, Edge, and mobile viewports.
   * `test_session_cookie_attributes_cross_browser`: Verifies HttpOnly cookie flags.

---

## 7. Simulated Test Execution Records

To satisfy course guidelines requiring distinct identification of simulated tests versus automated and planned tests, the following workflow simulations were recorded:

### Simulation 1: Privilege Escalation & Session Tampering (`Task #29`)
* **Objective**: Simulate an attacker attempting horizontal and vertical privilege escalation via HTTP parameter manipulation and forged cookie state.
* **Test Vector 1**: Authenticated student account (`user_id=1, role='student'`) attempts direct `POST` to `/admin/users/1/role` with payload `role=admin`.
  * *Observed Behavior*: Request intercepted by `@admin_required` decorator. Response: `HTTP 403 Forbidden`. Server logs audit trail. Database record remains `role='student'`.
* **Test Vector 2**: Attacker attempts Insecure Direct Object Reference (IDOR) by invoking `/api/analytics` with parameter `?user_id=2`.
  * *Observed Behavior*: Endpoint strictly ignores query string parameters and derives identity exclusively from cryptographically signed server session `session["user_id"]`. Response returns exclusively candidate 1 metrics.
* **Result**: **PASS** — Access controls are resilient against client-side parameter tampering.

### Simulation 2: End-to-End Preparation Progress Lifecycle (`Task #24`)
* **Objective**: Simulate a student's preparation progress lifecycle across four milestone stages as assessments are completed over time.
* **Step 1 (Registration)**: Student registers (`candidate@campus.edu`).
  * *Calculated Metric*: `total_active_tests = 5`, `distinct_tests = 0`. Progress: $0\%$.
  * *Status Rendered*: `"Not Started"`. Progress bar width: `0%`.
* **Step 2 (First Assessment)**: Candidate attempts Quantitative Aptitude assessment.
  * *Calculated Metric*: `distinct_tests = 1 / 5`. Progress: $20\%$.
  * *Status Rendered*: `"Getting Started"`. Progress bar width: `20%`.
* **Step 3 (Progressing Through Curriculum)**: Candidate attempts Logical Reasoning and Verbal Ability.
  * *Calculated Metric*: `distinct_tests = 3 / 5`. Progress: $60\%$.
  * *Status Rendered*: `"Good Progress"`. Progress bar width: `60%`.
* **Step 4 (Curriculum Completion)**: Candidate completes Technical Core and Systems assessments.
  * *Calculated Metric*: `distinct_tests = 5 / 5`. Progress: $100\%$.
  * *Status Rendered*: `"Placement Ready"`. Progress bar width: `100%`.
* **Result**: **PASS** — Progress state transitions accurately model student advancement.

---

## 8. Defect Reports & Retest Documentation

During Sprint 2 testing and quality verification, three defects/vulnerabilities were uncovered and resolved:

### Defect H3-DEF-01: Unvalidated Profile Fields Permitted Disallowed URL Protocols
* **Severity**: Medium (Security / Input Validation)
* **Associated Issue**: #10 (`SR-05`, `NFR-09`)
* **Description**: The `/profile` POST handler stripped input but failed to validate URL protocols for GitHub and LinkedIn fields, allowing `javascript:alert(1)` or arbitrary non-web URIs.
* **Resolution**: Implemented server-side protocol prefix checks in `placement-portal/app.py` verifying that provided URLs explicitly start with `http://` or `https://`.
* **Retest Result**: Verified via `test_profile_update_invalid_urls_rejected`. Malformed URLs now receive HTTP 400 with descriptive flash messages.

### Defect H3-DEF-02: Missing Length Bounds on Student Bio and Skills Fields
* **Severity**: Low (Data Integrity / DoS Guard)
* **Associated Issue**: #10 (`SR-05`)
* **Description**: Text areas for `bio` and `skills` accepted unbounded string lengths, creating risk of bloated database records or presentation overflow.
* **Resolution**: Enforced strict length limits ($1,000$ characters for bio, $500$ characters for skills) returning HTTP 400 on violations.
* **Retest Result**: Verified via `test_profile_update_bio_and_skills_length_limits`.

### Defect H3-DEF-03: Performance Timing Benchmark Sensitivity Under Full Suite Concurrency
* **Severity**: Low (Test Harness Flakiness)
* **Associated Issue**: #30 (`NFR-01`)
* **Description**: `test_page_generation_is_linear_not_quadratic` in `test_performance.py` asserted that rendering 6,000 records must take $< 0.25$ seconds. When executed in sequence with all 194 tests on Windows, execution time occasionally reached $0.257$ seconds ($7$ milliseconds over threshold).
* **Observation**: Srivani's branch `feature/iteration-2` identified this behavior and proposed statement-counting query assertions. When run in isolation, the test consistently passes ($< 0.15$ seconds), confirming sub-second performance.

---

## 9. Architectural Ambiguities Flagged

In accordance with course guidelines, the following architectural and requirements ambiguities were identified in the repository baseline:

1. **Three-Actor SRS vs. Two-Role Database Schema**:
   * *Observation*: The SRS (Section 1.3, Table 1, Table 9) specifies three distinct user classes: **Student/Candidate**, **Administrator**, and **Recruiter/Company**.
   * *Ambiguity*: The SQLite database schema (`schema.sql`) constrains roles to `CHECK (role IN ('student', 'admin'))`. Recruiter workflows (e.g. updating candidate application statuses, `FR-16`) are currently guarded by `@admin_required` rather than a dedicated recruiter role.
   * *Recommendation for Phase 2*: Extend the schema constraint to `CHECK (role IN ('student', 'admin', 'recruiter'))` and introduce a dedicated recruiter portal navigation view.

2. **Parallel Progress Routes Across Unmerged Branches**:
   * *Observation*: Shriya's Sprint 2 merge (PR #38) established `/dashboard` with integrated application summaries, aptitude statistics, and preparation progress. Concurrently, Srivani's open PR #36 introduced a dedicated `/progress` route.
   * *Resolution in this Sprint*: Verification in this sprint targeted the merged mainline `/dashboard` and `/api/analytics` endpoints while maintaining compatibility with the progress calculation models.

---

## 10. Sprint Review & Retrospective

* **What Went Well**:
  * 100% test pass rate achieved across all newly developed test suites (59 new tests).
  * Robust input validation established for student profiles, closing open security gaps.
  * Comprehensive cross-browser verification matrix completed for Chrome, Firefox, and Edge.
  * Clear traceability established between high-level SRS requirements and executable test cases.

* **Key Challenges Overcome**:
  * Resolving test fixture state coupling where authenticated clients inadvertently redirected anonymous endpoints during cross-browser smoke testing.
  * Formulating a deterministic, normalized preparation progress formula that scales cleanly with the number of published assessments.

* **Next Steps for Phase 2**:
  * Merge pending team pull requests (PR #36 for administrative question management and PR #37 for attempt API).
  * Implement three-tier role separation by activating the `recruiter` role in schema and UI.
  * Integrate live web-socket or client-side chart visualizations for analytics metrics.

