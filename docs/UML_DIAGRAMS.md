# Team H3 — Software Architecture & UML Specifications
## Online Internship & Placement Preparation Portal

This document contains the complete unified Modeling Language (UML) specifications for the **Online Internship & Placement Preparation Portal**, tracing architectural components directly to the Software Requirements Specification (SRS), IEEE Test Plan, and the database schema.

---

## Table of Contents
1. [System Use Case Diagram](#1-system-use-case-diagram)
2. [Domain Class Diagram](#2-domain-class-diagram)
3. [System Sequence Diagrams](#3-system-sequence-diagrams)
   - [3.1 Authentication & Opportunity Discovery](#31-sequence-diagram-authentication--opportunity-discovery-fr-01-fr-02-fr-05-fr-06)
   - [3.2 Application Submission & Status Tracking](#32-sequence-diagram-application-submission--status-tracking-fr-07-fr-08-fr-16)
   - [3.3 Aptitude Assessment & Automated Scoring](#33-sequence-diagram-aptitude-assessment--automated-evaluation-fr-09-fr-10)
   - [3.4 Admin Aptitude Test & Question Bank Management](#34-sequence-diagram-admin-aptitude-test-management-fr-14--issue-27)
   - [3.5 Admin User Management & Audit Logging](#35-sequence-diagram-admin-user-management--audit-logging-fr-15-sr-06--issue-25)
4. [Component & Layered Architecture Diagram](#4-component--layered-architecture-diagram)
5. [State Transition Diagrams](#5-state-transition-diagrams)
   - [5.1 Application Lifecycle State Machine](#51-application-lifecycle-state-machine)
   - [5.2 Aptitude Assessment State Machine](#52-aptitude-assessment-state-machine)
6. [Entity-Relationship (ER) Diagram](#6-entity-relationship-er-diagram)
7. [Requirements Traceability Matrix](#7-requirements-traceability-matrix)

---

## 1. System Use Case Diagram

The use case diagram outlines interactions between actors (**Student**, **Recruiter**, and **Admin**) and the portal's core functional capabilities.

![Online Internship & Placement Preparation Portal — Use Case Diagram](images/use_case_diagram.png)

*Direct image files:*
* [docs/images/use_case_diagram.png](images/use_case_diagram.png)
* [docs/images/use_case_diagram.jpg](images/use_case_diagram.jpg)

### Interactive System Use Case Model

```mermaid
flowchart LR
    %% Actors
    Student(("fa:fa-user Student"))
    Recruiter(("fa:fa-user-tie Recruiter"))
    Admin(("fa:fa-user-gear Admin"))

    subgraph Portal["Online Internship & Placement Preparation Portal"]
        subgraph StudentCore["Student Operations"]
            UC1(["Register / Log in"])
            UC2(["Manage Student Profile"])
            UC3(["Browse / Search Opportunities"])
            UC4(["View Opportunity Details"])
            UC5(["Submit Application"])
            UC6(["Track Application Status"])
            UC7(["View / Attempt Aptitude Tests"])
            UC8(["View Test Results"])
        end

        subgraph StudentAnalytics["Student Analytics & Progress"]
            UC9(["View Student Dashboard"])
            UC10(["Track Preparation Progress"])
            UC11(["View Application Analytics"])
            UC12(["View Aptitude Performance"])
        end

        subgraph AdminRecruiter["Recruiter & Administrative Operations"]
            UC13(["Create / Edit Opportunities"])
            UC14(["Manage Applications"])
            UC15(["Manage User Accounts"])
            UC16(["Manage Aptitude Questions"])
            UC17(["Validate Role Permissions"])
        end
    end

    %% Student Associations
    Student --- UC1
    Student --- UC2
    Student --- UC3
    Student --- UC4
    Student --- UC5
    Student --- UC6
    Student --- UC7
    Student --- UC8
    Student --- UC9
    Student --- UC10
    Student --- UC11
    Student --- UC12

    %% Recruiter Associations
    UC13 --- Recruiter
    UC14 --- Recruiter

    %% Admin Associations
    UC13 --- Admin
    UC14 --- Admin
    UC15 --- Admin
    UC16 --- Admin
    UC17 --- Admin
```

*Note: Associations show which role can initiate each function.*

---

## 2. Domain Class Diagram

The class diagram models the structural domain entities, their primary attributes and operations, along with associations and multiplicities.

```mermaid
classDiagram
    class User {
        +Integer id
        +String name
        +String email
        +String password_hash
        +String role
        +register(name, email, password, role)
        +authenticate(email, password)
        +update_role(new_role, actor)
    }

    class StudentProfile {
        +Integer user_id
        +String usn
        +String phone
        +String department
        +Integer batch_year
        +Float cgpa
        +String skills
        +String bio
        +String github_url
        +String linkedin_url
        +DateTime updated_at
        +save_profile(details)
        +is_complete() Boolean
    }

    class Opportunity {
        +Integer id
        +String title
        +String company
        +String type
        +String location
        +String stipend
        +String description
        +String eligibility
        +Date deadline
        +Integer is_open
        +DateTime created_at
        +is_active() Boolean
        +days_until_deadline() Integer
    }

    class Application {
        +Integer id
        +Integer user_id
        +Integer opportunity_id
        +String status
        +String notes
        +DateTime applied_at
        +DateTime updated_at
        +submit_application(notes)
        +update_status(new_status)
    }

    class AptitudeTest {
        +Integer id
        +String name
        +String category
        +String description
        +Integer num_questions
        +Integer duration_minutes
        +String difficulty
        +Integer is_active
        +add_question(question_obj)
        +get_questions(include_answers)
        +evaluate_submission(submitted_answers)
    }

    class TestQuestion {
        +Integer id
        +Integer test_id
        +String question_text
        +String option_a
        +String option_b
        +String option_c
        +String option_d
        +String correct_option
        +verify_option(choice) Boolean
    }

    class TestAttempt {
        +Integer id
        +Integer user_id
        +Integer test_id
        +Integer score
        +Integer total_questions
        +Float percentage
        +Integer passed
        +String answers_json
        +DateTime completed_at
        +compute_grade()
        +get_detailed_review()
    }

    class AuditLog {
        +Integer id
        +Integer user_id
        +String actor_email
        +String action
        +String details
        +String result
        +String ip_address
        +DateTime timestamp
        +record(actor, action, details, result)
    }

    User "1" -- "0..1" StudentProfile : owns
    User "1" -- "0..*" Application : files
    Opportunity "1" -- "0..*" Application : receives
    AptitudeTest "1" -- "1..*" TestQuestion : contains
    User "1" -- "0..*" TestAttempt : completes
    AptitudeTest "1" -- "0..*" TestAttempt : evaluates
    User "1" -- "0..*" AuditLog : triggers
```

---

## 3. System Sequence Diagrams

### 3.1 Sequence Diagram: Authentication & Opportunity Discovery (FR-01, FR-02, FR-05, FR-06)

Illustrates secure login, password hash verification, session setup, and opportunity catalog querying with multi-criteria filters.

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (User)
    participant Browser as Web Browser (UI)
    participant AuthCtrl as Auth Controller (/login)
    participant OppCtrl as Opportunity Controller (/opportunities)
    participant DB as SQLite Database
    participant Session as Session Store

    Student->>Browser: Enter email and password
    Browser->>AuthCtrl: POST /login (email, password)
    AuthCtrl->>DB: SELECT id, password_hash, role FROM users WHERE email=?
    DB-->>AuthCtrl: User record (PBKDF2 hash, role)
    AuthCtrl->>AuthCtrl: check_password_hash(hash, password)
    alt Valid Credentials
        AuthCtrl->>Session: Set session['user_id'], session['user_role']
        AuthCtrl-->>Browser: 302 Redirect to /dashboard
        Browser->>Student: Display Dashboard
    else Invalid Credentials
        AuthCtrl-->>Browser: 401 Unauthorized / Render login.html with error
        Browser->>Student: Display "Invalid email or password"
    end

    Student->>Browser: Select Opportunities filter (Type="Internship", Search="Python")
    Browser->>OppCtrl: GET /opportunities?type=Internship&q=Python
    OppCtrl->>DB: SELECT * FROM opportunities WHERE is_open=1 AND type='Internship' AND ...
    DB-->>OppCtrl: Matching opportunities dataset
    OppCtrl-->>Browser: 200 OK (Render opportunities.html)
    Browser->>Student: Display filtered opportunities with deadline badges
```

---

### 3.2 Sequence Diagram: Application Submission & Status Tracking (FR-07, FR-08, FR-16)

Demonstrates how duplicate applications are rejected via database constraints and how status updates propagate to the student's tracker.

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student
    participant Browser as Web Browser
    participant AppCtrl as Application Controller
    participant DB as SQLite Database

    Student->>Browser: Open Opportunity Detail page (#3)
    Browser->>AppCtrl: GET /opportunities/3
    AppCtrl->>DB: Query opportunity details and existing applications for user
    DB-->>AppCtrl: Opportunity details (is_open=1, no prior application)
    AppCtrl-->>Browser: Render opportunity_detail.html

    Student->>Browser: Fill notes & click "Submit Application"
    Browser->>AppCtrl: POST /opportunities/3/apply (notes="Interested in full stack")
    AppCtrl->>DB: BEGIN IMMEDIATE TRANSACTION
    AppCtrl->>DB: INSERT INTO applications (user_id, opportunity_id, status, notes) VALUES (?, ?, 'Submitted', ?)
    alt First Time Application
        DB-->>AppCtrl: Commit successful (Application ID created)
        AppCtrl->>DB: COMMIT TRANSACTION
        AppCtrl-->>Browser: 302 Redirect to /applications (Flash: "Application submitted")
        Browser->>AppCtrl: GET /applications
        AppCtrl->>DB: SELECT a.*, o.title, o.company FROM applications a JOIN opportunities o ...
        DB-->>AppCtrl: Applications list
        AppCtrl-->>Browser: 200 OK (Render applications.html)
        Browser->>Student: Show application row with 'Submitted' badge
    else Duplicate Application
        DB-->>AppCtrl: IntegrityError (UNIQUE constraint failed: user_id, opportunity_id)
        AppCtrl->>DB: ROLLBACK TRANSACTION
        AppCtrl-->>Browser: 409 Conflict / Flash error "Already applied"
        Browser->>Student: Display error banner
    end
```

---

### 3.3 Sequence Diagram: Aptitude Assessment & Automated Evaluation (FR-09, FR-10)

Validates that students never receive answer keys client-side and demonstrates instant server-side grading.

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student
    participant Browser as Web Browser
    participant TestCtrl as Assessment Controller
    participant DB as SQLite Database

    Student->>Browser: Navigate to Aptitude Tests & click "Start Test"
    Browser->>TestCtrl: GET /tests/1/take
    TestCtrl->>DB: SELECT id, question_text, option_a, option_b, option_c, option_d FROM test_questions WHERE test_id=1
    Note over TestCtrl,DB: Security: correct_option is deliberately excluded from response
    DB-->>TestCtrl: 5 Questions with options A-D
    TestCtrl-->>Browser: Render take_test.html with JS countdown timer
    Browser->>Student: Display test form

    Student->>Browser: Choose options & click "Submit Test"
    Browser->>TestCtrl: POST /tests/1/take (answers: {q1: 'B', q2: 'C', ...})
    TestCtrl->>DB: SELECT id, correct_option FROM test_questions WHERE test_id=1
    DB-->>TestCtrl: Answer key (q1='B', q2='A', ...)
    TestCtrl->>TestCtrl: Compare answers, compute score (4/5 = 80%), pass=1
    TestCtrl->>DB: INSERT INTO test_attempts (user_id, test_id, score, total_questions, percentage, passed, answers_json)
    DB-->>TestCtrl: Attempt #15 created
    TestCtrl-->>Browser: 302 Redirect to /tests/attempts/15
    Browser->>TestCtrl: GET /tests/attempts/15
    TestCtrl->>DB: Fetch attempt #15 and questions for review
    DB-->>TestCtrl: Attempt details and explanations
    TestCtrl-->>Browser: 200 OK (Render test_result.html)
    Browser->>Student: Display Scorecard: 80% Passed, with question breakdown
```

---

### 3.4 Sequence Diagram: Admin Aptitude Test Management (FR-14 / Issue #27)

Outlines role-based test creation, question addition, input validation, and transactional persistence.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Administrator
    participant Browser as Web Browser
    participant TestAdminCtrl as Admin Test Controller
    participant DB as SQLite Database
    participant Audit as Audit Logger (SR-06)

    Admin->>Browser: Open "Manage Tests" -> Click "Create Test"
    Browser->>TestAdminCtrl: GET /admin/tests/new
    TestAdminCtrl->>TestAdminCtrl: Enforce session['user_role'] == 'admin'
    TestAdminCtrl-->>Browser: Render admin_test_form.html

    Admin->>Browser: Enter Title, Category, Duration (minutes), Difficulty
    Browser->>TestAdminCtrl: POST /admin/tests/new (form payload)
    TestAdminCtrl->>TestAdminCtrl: Validate positive duration & non-empty fields
    TestAdminCtrl->>DB: INSERT INTO aptitude_tests (name, category, description, duration_minutes, difficulty)
    DB-->>TestAdminCtrl: Test ID #4 created
    TestAdminCtrl->>Audit: record(admin_email, 'CREATE_TEST', 'Created test ID #4', 'SUCCESS')
    Audit->>DB: INSERT INTO audit_logs ...
    TestAdminCtrl-->>Browser: 302 Redirect to /admin/tests/4/questions

    Admin->>Browser: Add Multiple Choice Question & specify correct option
    Browser->>TestAdminCtrl: POST /admin/tests/4/questions (question_text, opts A-D, correct='C')
    TestAdminCtrl->>DB: INSERT INTO test_questions (test_id, question_text, opt_a..d, correct_option)
    TestAdminCtrl->>DB: UPDATE aptitude_tests SET num_questions = num_questions + 1 WHERE id=4
    DB-->>TestAdminCtrl: Question saved & count updated
    TestAdminCtrl-->>Browser: 200 OK (Render updated questions table)
    Browser->>Admin: Show new question in list with correct answer indicator
```

---

### 3.5 Sequence Diagram: Admin User Management & Audit Logging (FR-15, SR-06 / Issue #25)

Shows administrator role modifications, self-lockout prevention, and immutable security audit logging.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Administrator
    participant Browser as Web Browser
    participant UserAdminCtrl as Admin User Controller
    participant DB as SQLite Database
    participant Audit as Audit Logger (SR-06)

    Admin->>Browser: Navigate to Manage Users
    Browser->>UserAdminCtrl: GET /admin/users
    UserAdminCtrl->>UserAdminCtrl: Enforce session['user_role'] == 'admin'
    UserAdminCtrl->>DB: SELECT id, name, email, role FROM users ORDER BY id
    DB-->>UserAdminCtrl: Directory of registered users
    UserAdminCtrl->>DB: SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 25
    DB-->>UserAdminCtrl: Audit trail records
    UserAdminCtrl-->>Browser: 200 OK (Render admin_users.html)

    Admin->>Browser: Change User #3 role from 'student' to 'admin' -> Submit
    Browser->>UserAdminCtrl: POST /admin/users/3/role (role='admin')
    UserAdminCtrl->>DB: SELECT role FROM users WHERE id=3
    DB-->>UserAdminCtrl: Current role is 'student'
    UserAdminCtrl->>DB: UPDATE users SET role='admin' WHERE id=3
    DB-->>UserAdminCtrl: Success
    UserAdminCtrl->>Audit: record(actor_email, 'UPDATE_USER_ROLE', 'Updated user #3 to admin', 'SUCCESS')
    Audit->>DB: INSERT INTO audit_logs (user_id, actor_email, action, details, result)
    UserAdminCtrl-->>Browser: 302 Redirect to /admin/users (Flash: "Role updated")
    Browser->>Admin: Display updated table & newly recorded audit log
```

---

## 4. Component & Layered Architecture Diagram

Illustrates the high-cohesion, low-coupling tiered architecture conforming to the Software Architecture and Design Specification.

```mermaid
flowchart TD
    subgraph PresentationTier["Presentation Layer (Client & Templates)"]
        UI["Web Browser Client"]
        Templates["Jinja2 HTML Templates (base.html, dashboard.html, etc.)"]
        Styles["CSS Styling (style.css - PES Brand Design)"]
    end

    subgraph ControllerTier["Controller / Routing Layer (Flask)"]
        AuthRoutes["Auth Controller (/register, /login, /logout)"]
        ProfileRoutes["Profile Controller (/profile)"]
        OppRoutes["Opportunities Controller (/opportunities)"]
        AppRoutes["Applications Controller (/applications)"]
        TestRoutes["Aptitude Assessment Controller (/tests)"]
        DashRoutes["Analytics Dashboard Controller (/dashboard)"]
        AdminUserRoutes["Admin Users Controller (/admin/users)"]
        AdminTestRoutes["Admin Test Authoring Controller (/admin/tests)"]
    end

    subgraph SecurityTier["Security & Cross-Cutting Concerns"]
        RBACGuard["RBAC Guards (@login_required, @admin_required)"]
        CSRFProtection["Input Sanitization & Parameterization"]
        AuditService["Audit Trail Recorder (audit_logs)"]
        ErrorHandler["Central Error Handling (400, 403, 404, 500)"]
    end

    subgraph ServiceTier["Business Logic & Service Layer"]
        ScoreEngine["Automated Grading & Scoring Engine"]
        ReadinessEngine["Placement Readiness Calculation Engine"]
        BackupEngine["Database Reliability & Backup Service (db.py)"]
    end

    subgraph PersistenceTier["Persistence & Data Access Layer"]
        DBManager["Connection Manager (db.py / get_db / close_db)"]
        WAL["SQLite Write-Ahead Logging & Foreign Keys"]
        MainDB[("Main SQLite DB (portal.sqlite)")]
        BackupDB[("Backup Snapshots (instance/backups/)")]
    end

    %% Presentation to Controller
    UI --> Templates
    Templates --> Styles
    UI --> AuthRoutes
    UI --> ProfileRoutes
    UI --> OppRoutes
    UI --> AppRoutes
    UI --> TestRoutes
    UI --> DashRoutes
    UI --> AdminUserRoutes
    UI --> AdminTestRoutes

    %% Security Interceptors
    AuthRoutes & ProfileRoutes & OppRoutes & AppRoutes & TestRoutes & DashRoutes & AdminUserRoutes & AdminTestRoutes -.-> RBACGuard
    AdminUserRoutes & AdminTestRoutes --> AuditService
    ControllerTier -.-> ErrorHandler

    %% Controller to Services
    TestRoutes --> ScoreEngine
    DashRoutes --> ReadinessEngine
    AdminTestRoutes --> BackupEngine

    %% Controllers & Services to Data Access
    ControllerTier --> DBManager
    ScoreEngine --> DBManager
    ReadinessEngine --> DBManager
    AuditService --> DBManager
    BackupEngine --> DBManager

    %% Data Access to DB
    DBManager --> WAL
    WAL --> MainDB
    BackupEngine --> BackupDB
```

---

## 5. State Transition Diagrams

### 5.1 Application Lifecycle State Machine

Traces the states of an opportunity application from submission through final disposition.

```mermaid
stateDiagram-v2
    [*] --> Submitted: Student submits application (FR-07)
    
    Submitted --> UnderReview: Recruiter/Admin begins evaluation
    Submitted --> Withdrawn: Student cancels before review
    
    UnderReview --> Shortlisted: Candidate meets academic & skill criteria
    UnderReview --> Rejected: Candidate does not qualify (FR-16)
    
    Shortlisted --> Accepted: Candidate successfully clears interview / drive
    Shortlisted --> Rejected: Candidate does not clear final evaluation
    
    Accepted --> [*]
    Rejected --> [*]
    Withdrawn --> [*]
```

---

### 5.2 Aptitude Assessment State Machine

Traces the state of an aptitude test attempt.

```mermaid
stateDiagram-v2
    [*] --> Available: Admin publishes test (is_active=1)
    
    Available --> InProgress: Student clicks 'Start Test' (timer initialized)
    
    InProgress --> Submitted: Student submits answers before timer expires
    InProgress --> AutoSubmitted: Timer reaches 0:00 (auto-submission)
    
    Submitted --> Evaluated: Server compares answers against test_questions
    AutoSubmitted --> Evaluated: Server evaluates received answers
    
    Evaluated --> Recorded: Score and percentage stored in test_attempts
    Recorded --> Reviewed: Student views detailed scorecard with explanations
    
    Reviewed --> [*]
```

---

## 6. Entity-Relationship (ER) Diagram

Represents the physical SQLite relational schema, primary keys, foreign key constraints, cascade rules, and column data types.

```mermaid
erDiagram
    USERS ||--o| STUDENT_PROFILES : "owns (1:1)"
    USERS ||--o{ APPLICATIONS : "submits (1:N)"
    USERS ||--o{ TEST_ATTEMPTS : "takes (1:N)"
    USERS ||--o{ AUDIT_LOGS : "acts (1:N)"
    OPPORTUNITIES ||--o{ APPLICATIONS : "receives (1:N)"
    APTITUDE_TESTS ||--|{ TEST_QUESTIONS : "contains (1:N)"
    APTITUDE_TESTS ||--o{ TEST_ATTEMPTS : "records (1:N)"

    USERS {
        INTEGER id PK "AUTOINCREMENT"
        TEXT name "NOT NULL"
        TEXT email UK "NOT NULL, UNIQUE"
        TEXT password_hash "NOT NULL (PBKDF2-SHA256)"
        TEXT role "student | admin"
    }

    STUDENT_PROFILES {
        INTEGER user_id PK, FK "REFERENCES users(id) ON DELETE CASCADE"
        TEXT usn "University Serial Number"
        TEXT phone "Contact Number"
        TEXT department "Branch / Major"
        INTEGER batch_year "Graduation Year"
        REAL cgpa "0.0 to 10.0 scale"
        TEXT skills "Comma-separated list"
        TEXT bio "Student summary"
        TEXT github_url "Portfolio link"
        TEXT linkedin_url "Professional profile"
        TEXT updated_at "ISO-8601 Timestamp"
    }

    OPPORTUNITIES {
        INTEGER id PK "AUTOINCREMENT"
        TEXT title "NOT NULL"
        TEXT company "NOT NULL"
        TEXT type "Internship | Placement"
        TEXT location "NOT NULL"
        TEXT stipend "Human readable (e.g., Rs 25,000/mo)"
        TEXT description "Detailed JD"
        TEXT eligibility "CGPA and branch criteria"
        TEXT deadline "ISO Date (YYYY-MM-DD)"
        INTEGER is_open "0=Closed, 1=Open"
        TEXT created_at "ISO-8601 Timestamp"
    }

    APPLICATIONS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id FK "REFERENCES users(id) ON DELETE CASCADE"
        INTEGER opportunity_id FK "REFERENCES opportunities(id) ON DELETE CASCADE"
        TEXT status "Submitted | Under Review | Shortlisted | Accepted | Rejected"
        TEXT notes "Statement of interest"
        TEXT applied_at "ISO-8601 Timestamp"
        TEXT updated_at "ISO-8601 Timestamp"
    }

    APTITUDE_TESTS {
        INTEGER id PK "AUTOINCREMENT"
        TEXT name "NOT NULL"
        TEXT category "Quantitative | Verbal | Logical | Technical"
        TEXT description "Test scope and syllabus"
        INTEGER num_questions "Total question count"
        INTEGER duration_minutes "Time limit"
        TEXT difficulty "Easy | Medium | Hard"
        INTEGER is_active "0=Inactive, 1=Active"
    }

    TEST_QUESTIONS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER test_id FK "REFERENCES aptitude_tests(id) ON DELETE CASCADE"
        TEXT question_text "NOT NULL"
        TEXT option_a "NOT NULL"
        TEXT option_b "NOT NULL"
        TEXT option_c "NOT NULL"
        TEXT option_d "NOT NULL"
        TEXT correct_option "A | B | C | D"
    }

    TEST_ATTEMPTS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id FK "REFERENCES users(id) ON DELETE CASCADE"
        INTEGER test_id FK "REFERENCES aptitude_tests(id) ON DELETE CASCADE"
        INTEGER score "Correct answer count"
        INTEGER total_questions "Total questions asked"
        REAL percentage "Score percentage"
        INTEGER passed "0=Failed, 1=Passed"
        TEXT answers_json "Serialized student submissions"
        TEXT completed_at "ISO-8601 Timestamp"
    }

    AUDIT_LOGS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER user_id FK "REFERENCES users(id) ON DELETE SET NULL"
        TEXT actor_email "NOT NULL"
        TEXT action "NOT NULL (e.g. UPDATE_USER_ROLE)"
        TEXT details "Human-readable context"
        TEXT result "SUCCESS | FAILURE"
        TEXT ip_address "Client IP address"
        TEXT timestamp "ISO-8601 Timestamp"
    }
```

---

## 7. Requirements Traceability Matrix

| Requirement ID | Module / Subsystem | UML Design Artefact | Verification / Test Case |
|---|---|---|---|
| **FR-01** | User Registration | Use Case, Sequence 3.1, Class Diagram | `tests/test_registration.py` (`TC-01`) |
| **FR-02** | User Authentication | Use Case, Sequence 3.1, Component Diagram | `tests/test_auth.py` (`TC-02`) |
| **FR-03** | Role-Based Access Control | Component Diagram, Class Diagram | `tests/test_auth.py` (`TC-03`) |
| **FR-04** | Student Profile Management | Use Case, Class Diagram, ER Diagram | `tests/test_profile.py` |
| **FR-05** | Opportunity Browsing & Details | Use Case, Sequence 3.1, ER Diagram | `tests/test_opportunities.py` |
| **FR-06** | Opportunity Search & Filtering | Use Case, Sequence 3.1, Component Diagram | `tests/test_search_filter.py` (`TC-04`) |
| **FR-07** | Application Submission | Use Case, Sequence 3.2, State Machine 5.1 | `tests/test_applications.py` (`TC-05`) |
| **FR-08** | Application Status Tracking | Use Case, Sequence 3.2, State Machine 5.1 | `tests/test_applications.py` (`TC-06`) |
| **FR-09** | Aptitude Test Catalog & Taking | Use Case, Sequence 3.3, State Machine 5.2 | `tests/test_aptitude_tests.py` |
| **FR-10** | Automated Score Evaluation | Sequence 3.3, Class Diagram, ER Diagram | `tests/test_test_results.py` (`TC-07`) |
| **FR-12** | Analytics Dashboards | Use Case, Component Diagram | `tests/test_dashboard.py` (`TC-08`) |
| **FR-14** | Aptitude Test Management | Use Case, Sequence 3.4, Class Diagram | `tests/test_admin_aptitude_tests.py` |
| **FR-15** | User Directory & Role Management | Use Case, Sequence 3.5, Class Diagram | `tests/test_admin_users.py` (`TC-14`) |
| **FR-16** | Application Status Modification | Use Case, Sequence 3.2, State Machine 5.1 | `tests/test_applications.py` |
| **SR-02** | Credential Hashing (PBKDF2) | Class Diagram (`User.password_hash`) | `tests/test_auth.py` (`TC-13`) |
| **SR-06** | Administrative Audit Trail | Sequence 3.4, Sequence 3.5, ER Diagram | `tests/test_admin_users.py` (`TC-14`) |
| **NFR-04/09** | Reliability, Integrity & Recovery | Component Diagram, Sequence 3.4 | `tests/test_reliability_recovery.py` |
