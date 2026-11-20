# Team H3 — Complete Test Case Specification (Updated Part-3)
## Online Internship & Placement Preparation Portal

**Document Version:** 2.0 (Post-Sprint 1 & Sprint 2 Updation)  
**Standard:** IEEE 829 Standard for Software and System Test Documentation  
**Authors:** Team H3 (Shriya K, Srivani Karanth, Sia Simran A)  
**Date:** November 2026  

---

## 1. Document Overview & Purpose

This document provides the formal Test Case Specification for the Online Internship & Placement Preparation Portal. Originally containing 15 baseline test cases (`03_COMPLETE_TEST_CASES_15.docx`), this updated specification reflects all architectural additions, functional expansions, security controls, and reliability measures implemented across Sprint 1 (Authentication, Profiles, Search/Filter, Applications, Test Evaluation, Dashboard #21, User Management #25) and Sprint 2 (Aptitude Test Management #27, Reliability & Recovery #33).

---

## 2. Test Cases Specification (TC-01 through TC-33)

| ID | Req ID | Test Type | Test Title | Precondition | Test Steps | Expected Output | Pass Criteria | Verification Method |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **TC-01** | FR-01, SR-02, SR-05 | Functional | Student & Admin Account Registration | Database initialized, email not registered | 1. Navigate to `/register`<br>2. Enter valid name, email, password, role<br>3. Submit form | Account created, PBKDF2 hash stored, redirected to login | User record exists with hashed password; duplicate email rejected | Automated (`test_registration.py`) |
| **TC-02** | FR-02 | Functional | User Login & Authentication | User account registered | 1. Navigate to `/login`<br>2. Submit valid credentials<br>3. Submit invalid password | Valid: authenticated session, redirect to `/dashboard`. Invalid: 401 Unauthorized with flash error | Role-appropriate dashboard displayed; invalid access denied | Automated (`test_auth.py`) |
| **TC-03** | FR-03, SR-03 | Security | Role-Based Access Control (RBAC) Guard | Logged in as `student` | 1. Access `/admin/users`<br>2. Access `/admin/tests`<br>3. Access `/api/admin/users` | HTTP 403 Forbidden returned; student redirected or blocked | No administrative view or privileged endpoint exposed to student | Automated (`test_admin_users.py`, `test_admin_aptitude_tests.py`) |
| **TC-04** | FR-05, FR-06 | Functional | Multi-Criteria Opportunity Search & Filter | Active opportunities exist in DB | 1. Navigate to `/opportunities`<br>2. Filter by Category (`Internship`)<br>3. Search keyword (`Python`) | Filtered opportunity cards displayed matching both criteria | Response time < 250ms; exact matches returned; count chip accurate | Automated (`test_search_filter.py`, `test_opportunities.py`) |
| **TC-05** | FR-07 | Functional | Opportunity Application Submission | Logged in student, open opportunity | 1. Open opportunity details<br>2. Submit statement of interest<br>3. Submit application form | Application stored with status `'Submitted'`; redirect to tracker | Exactly one valid application record stored in `applications` table | Automated (`test_applications.py`) |
| **TC-06** | FR-08, FR-16 | Functional | Application Status Tracking & Recruiter Updates | Active application submitted | 1. Student opens `/applications`<br>2. Admin/recruiter updates status to `'Shortlisted'` | Updated status reflected immediately in student UI | Displayed status matches database status; badge class updated | Automated (`test_applications.py`) |
| **TC-07** | FR-09, FR-10 | Functional | Practice Aptitude Test Taking & Instant Grading | Active test with questions in DB | 1. Navigate to `/tests/1/take`<br>2. Select answers for 5 questions<br>3. Submit before timer expires | Server calculates score, stores in `test_attempts`, shows result | Stored score and percentage match correct answer key; pass badge shown | Automated (`test_aptitude_tests.py`, `test_test_results.py`) |
| **TC-08** | FR-11, FR-12 | Functional | Student & Admin Analytics Dashboards | User has application and test records | 1. Student opens `/dashboard`<br>2. Admin opens `/dashboard` | Student: Readiness index & scores. Admin: Pipeline distribution & counts | Rendered metrics strictly equal database aggregate counts | Automated (`test_dashboard.py`) |
| **TC-09** | NFR-01, NFR-06 | Non-Functional | System Performance Under Scale | 3,000 opportunities, 200 tests seeded | 1. Execute multiple `/opportunities` requests<br>2. Double dataset to 6,000 rows | Median request latency stays under 250ms | Hard latency cap met; linear query execution confirmed | Automated (`test_performance.py`) |
| **TC-10** | NFR-02, SR-01 | Security | Protection Against Unauthorized Endpoint Access | User not authenticated | 1. Request `/dashboard`<br>2. Request `/profile`<br>3. Request `/applications` | HTTP 302 Redirect to `/login?next=...` | No sensitive student data leaked to unauthenticated client | Automated (`test_auth.py`) |
| **TC-11** | NFR-09, SR-05 | Security | Input Validation & Injection Prevention | Forms and API endpoints available | 1. Submit SQL injection payload (`' OR '1'='1`)<br>2. Submit XSS payload (`<script>`) | Form inputs sanitized and parameterized via SQLite parameters | No arbitrary SQL executed; inputs treated as literal strings | Automated (`test_registration.py`, `test_reliability_recovery.py`) |
| **TC-12** | SR-04 | Security | Session Expiration on Inactivity | Active session | 1. Idle for 30 minutes<br>2. Submit request to protected route | Session terminated; user prompted to log in again | Stale sessions invalidated; access denied | Automated (`test_auth.py`) |
| **TC-13** | SR-02 | Security | Password Storage Security Verification | Registered user account | 1. Inspect `users` table directly via SQL<br>2. Verify `password_hash` column | Salted PBKDF2-SHA256 string stored; plaintext absent | Zero plaintext passwords found in database | Automated (`test_auth.py`) |
| **TC-14** | SR-06 | Security | Administrative Security Audit Logging | Admin user logged in | 1. Change user role at `/admin/users/1/role`<br>2. Query `audit_logs` table | Log entry recorded with actor email, action, details, timestamp | Immutable audit log record created with result `'SUCCESS'` | Automated (`test_admin_users.py`) |
| **TC-15** | NFR-08 | Non-Functional | Cross-Browser Compatibility Validation | Web portal deployed | 1. Run UI smoke suite in Chrome, Firefox, Edge<br>2. Verify grid layout, forms, timers | Navigation, forms, test countdown timer, styles render cleanly | Zero critical layout breaks or functional script failures | Manual / Browser Verification |
| **TC-16** | FR-04 | Functional | Student Academic Profile Management | Logged in student | 1. Navigate to `/profile`<br>2. Enter USN, CGPA, department, skills<br>3. Save profile | Profile saved to `student_profiles`; success flash message shown | Profile values persist across sessions and appear on dashboard | Automated (`test_profile.py`) |
| **TC-17** | FR-05, FR-07 | Functional | Expired Opportunity Protection | Opportunity deadline in the past | 1. Access expired opportunity<br>2. Attempt application submission | Deadline marked "Closed"; application form disabled/rejected | Cannot apply to expired drives | Automated (`test_opportunities.py`) |
| **TC-18** | FR-07 | Functional | Duplicate Application Prevention | Student already applied to Opportunity #1 | 1. Submit application again for Opportunity #1 | HTTP 409 Conflict returned; flash error displayed | Unique database constraint prevents duplicate entry | Automated (`test_applications.py`) |
| **TC-19** | FR-09 | Functional | Test Catalog Categorization & Status Filter | Practice tests seeded | 1. Open `/tests`<br>2. Check active vs inactive tests | Only active tests displayed to students | Inactive tests hidden from student catalog | Automated (`test_aptitude_tests.py`) |
| **TC-20** | SR-01 | Security | Test Answer Concealment Prior to Submission | Active aptitude test | 1. Inspect HTML source of `/tests/1/take`<br>2. Inspect DOM and network payload | `correct_option` is absent from client payload | Correct answers never exposed prior to evaluation | Automated (`test_aptitude_tests.py`) |
| **TC-21** | FR-10 | Functional | Comprehensive Test Scorecard & Review | Test attempt submitted | 1. Navigate to `/tests/attempts/<id>` | Displays score, percentage, pass/fail status, question explanations | Review details match recorded attempt | Automated (`test_test_results.py`) |
| **TC-22** | FR-12 | Functional | Dynamic Placement Readiness Computation | Student with test and application history | 1. Open `/dashboard` as student | Dynamic readiness score computed (0-100%) with status badge | Accurate mathematical weighting of CGPA, tests, and apps | Automated (`test_dashboard.py`) |
| **TC-23** | FR-12 | Functional | Admin Recruitment Pipeline Analytics | Multiple student applications exist | 1. Open `/dashboard` as admin | Application breakdown by status ('Submitted', 'Shortlisted', etc.) | Metrics reflect true counts from DB | Automated (`test_dashboard.py`) |
| **TC-24** | FR-15 | Functional | Admin User Directory Filtering & Search | Multiple users registered | 1. Navigate to `/admin/users`<br>2. Filter by role `student`<br>3. Search by name/email | User table updates to display matching users | Instant match; count accurate | Automated (`test_admin_users.py`) |
| **TC-25** | FR-15, SR-06 | Functional | Admin Role Promotion & Demotion | Target student user exists | 1. Select user role `admin`<br>2. Submit POST `/admin/users/<id>/role` | User role updated; audit record logged | Role changes in DB; audit trail shows actor and change | Automated (`test_admin_users.py`) |
| **TC-26** | SR-03 | Security | Sole Administrator Self-Lockout Prevention | Only 1 admin account exists | 1. Logged in admin attempts to demote own account to `student` | Request rejected with flash error: cannot demote sole admin | Admin role preserved; system lockouts prevented | Automated (`test_admin_users.py`) |
| **TC-27** | FR-14 | Functional | Admin Aptitude Test Creation & Duration Validation | Logged in admin | 1. Navigate to `/admin/tests/new`<br>2. Submit test with title, duration (mins), category<br>3. Test negative duration (-5 mins) | Valid: test created, redirect to question builder. Invalid: form rejected | Positive duration enforced; record persisted | Automated (`test_admin_aptitude_tests.py`) |
| **TC-28** | FR-14 | Functional | Admin Question Bank Creation & Correct Option Setup | Aptitude test created | 1. Navigate to `/admin/tests/<id>/questions`<br>2. Enter question text, Options A-D, correct option | Question saved to `test_questions`; question count updated | Question appears in question bank with correct answer marker | Automated (`test_admin_aptitude_tests.py`) |
| **TC-29** | NFR-04 | Reliability | Atomic Transaction Commit & Rollback on Failure | Database connection active | 1. Execute transactional operation where 2nd statement fails<br>2. Check database state | Entire transaction rolls back; 1st statement changes undone | Database integrity preserved; zero orphaned records | Automated (`test_reliability_recovery.py`) |
| **TC-30** | NFR-09 | Reliability | Foreign Key Constraint Enforcement & Cascading | User with profile and applications | 1. Delete user from `users` table<br>2. Check `student_profiles` and `applications` | Dependent profile and application rows cascaded and deleted | No orphaned records; foreign key integrity verified | Automated (`test_reliability_recovery.py`) |
| **TC-31** | NFR-04 | Recovery | Hot Database Backup Generation | SQLite database active | 1. Execute `flask backup-db`<br>2. Verify created backup file | Timestamped `.sqlite` backup snapshot created in `instance/backups/` | Backup file is valid SQLite; PRAGMA integrity_check passes | Automated (`test_reliability_recovery.py`) |
| **TC-32** | NFR-04, NFR-09 | Recovery | Database Restoration & Integrity Verification | Valid backup snapshot exists | 1. Simulate database corruption<br>2. Execute `flask restore-db --file <backup>` | Database restored from snapshot; tables verified | 100% data recovered; application functions normally | Automated (`test_reliability_recovery.py`) |
| **TC-33** | NFR-02 | Reliability | Centralized Error Handling & Trace Concealment | Internal 500 error triggered | 1. Trigger simulated unhandled exception on route | HTTP 500 page rendered with friendly error message | Zero stack traces, file paths, or sensitive credentials leaked | Automated (`test_reliability_recovery.py`) |

---

## 3. Coverage Analysis

| Requirement Category | Covered Test Cases | Count | Status |
|---|---|---|---|
| **Authentication & RBAC** | TC-01, TC-02, TC-03, TC-10, TC-12, TC-13 | 6 | 100% Verified |
| **Student Profile & Tracking** | TC-16 | 1 | 100% Verified |
| **Opportunities & Search/Filter** | TC-04, TC-17 | 2 | 100% Verified |
| **Application Pipeline** | TC-05, TC-06, TC-18 | 3 | 100% Verified |
| **Aptitude Testing & Scoring** | TC-07, TC-19, TC-20, TC-21 | 4 | 100% Verified |
| **Analytics Dashboards** | TC-08, TC-22, TC-23 | 3 | 100% Verified |
| **Admin Management & Auditing** | TC-14, TC-24, TC-25, TC-26, TC-27, TC-28 | 6 | 100% Verified |
| **Reliability & Recovery** | TC-29, TC-30, TC-31, TC-32, TC-33 | 5 | 100% Verified |
| **Performance & Compatibility** | TC-09, TC-11, TC-15 | 3 | 100% Verified |
| **Total Test Cases** | **TC-01 through TC-33** | **33** | **100% Passing** |
