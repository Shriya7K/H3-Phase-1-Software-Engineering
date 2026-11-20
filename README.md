## Project Overview

The Online Internship & Placement Preparation Portal is a web-based
system designed to centralize internship and placement opportunity
discovery, applications, aptitude testing, preparation tracking,
and analytics.

## Team


Team H3
- Shriya K: PES1UG24CS448
- Srivani Karanth: PES1UG24CS471
- Sia Simran A: PES1UG24CS453

## Phase 1 Deliverables

- Software Requirements Specification
- Software Test Plan
- Test Case Specification
- Software Architecture & Design Specification

## Documentation

| Document | Description |
|---|---|
| 01_COMPLETE_SRS_IEEE_STYLE.docx | Complete SRS (IEEE format) |
| 02_COMPLETE_IEEE_TEST_PLAN.docx | IEEE-style Test Plan |
| 03_COMPLETE_TEST_CASES_15.docx | Baseline functional, NFR and security test cases |
| 04_COMPLETE_ARCHITECTURE_AND_DESIGN.docx | Architecture and Design Specification |
| [docs/UML_DIAGRAMS.md](docs/UML_DIAGRAMS.md) | Comprehensive UML Specifications (Use Case, Class, Sequence, Component, State & ER) |
| [docs/TEST_CASE_SPECIFICATION.md](docs/TEST_CASE_SPECIFICATION.md) | Updated Test Case Specification (TC-01 to TC-33 covering Sprints 1 & 2) |
| [docs/UNIT_TEST_REPORT.md](docs/UNIT_TEST_REPORT.md) | Unit Test Report (135/135 tests passing) |
| [docs/SYSTEM_VALIDATION_REPORT.md](docs/SYSTEM_VALIDATION_REPORT.md) | System Validation Report (100% requirements verified) |
| [docs/CODE_COVERAGE_REPORT.md](docs/CODE_COVERAGE_REPORT.md) | Code Coverage Report (91% statement coverage) |
| [docs/BRANCH_COVERAGE_REPORT.md](docs/BRANCH_COVERAGE_REPORT.md) | Branch Coverage Report (75% branch coverage) |
| [docs/SPRINT_3_REPORT.md](docs/SPRINT_3_REPORT.md) | Sprint 3 Quality Hardening & Part-3 Deliverables Report |

## UML Diagrams

> Full diagrams, detailed sequence flows, and traceability are documented in [docs/UML_DIAGRAMS.md](docs/UML_DIAGRAMS.md).

### 1. System Use Case Diagram

```mermaid
flowchart LR
    Student(("fa:fa-user Student"))
    Admin(("fa:fa-user-gear Administrator"))
    Recruiter(("fa:fa-building Placement/Recruiter"))

    subgraph AuthSubsystem["Authentication & Profile"]
        UC1(["Register Account (FR-01)"])
        UC2(["Login / Logout (FR-02)"])
        UC3(["Manage Profile (FR-04)"])
    end

    subgraph OppSubsystem["Opportunity Subsystem"]
        UC4(["Browse Opportunities (FR-05)"])
        UC5(["Search & Filter (FR-06)"])
        UC6(["View Details (FR-05)"])
        UC7(["Post Opportunity (FR-13)"])
    end

    subgraph AppSubsystem["Application Pipeline"]
        UC8(["Submit Application (FR-07)"])
        UC9(["Track Status (FR-08)"])
        UC10(["Update Status (FR-16)"])
    end

    subgraph TestSubsystem["Aptitude Assessment"]
        UC11(["View Practice Tests (FR-09)"])
        UC12(["Attempt Timed Test (FR-09)"])
        UC13(["Instant Evaluation (FR-10)"])
        UC14(["Manage Tests & Questions (FR-14)"])
    end

    subgraph AdminSubsystem["Analytics & Management"]
        UC15(["Readiness Dashboard (FR-12)"])
        UC16(["Admin Analytics (FR-12)"])
        UC17(["User Management (FR-15)"])
        UC18(["Audit Trail (SR-06)"])
        UC19(["Backup & Recovery (NFR-04/09)"])
    end

    Student --> UC1 & UC2 & UC3 & UC4 & UC5 & UC6 & UC8 & UC9 & UC11 & UC12 & UC13 & UC15
    Recruiter --> UC2 & UC4 & UC7 & UC10
    Admin --> UC2 & UC4 & UC7 & UC10 & UC14 & UC16 & UC17 & UC18 & UC19
```

### 2. Layered Component Architecture Diagram

```mermaid
flowchart TD
    subgraph PresentationTier["Presentation Layer"]
        UI["Web Browser Client (HTML5 / Jinja2 / CSS3)"]
    end

    subgraph ControllerTier["Controller & Routing Layer (Flask)"]
        Auth["Auth Controller (/register, /login)"]
        Profile["Profile Controller (/profile)"]
        Opps["Opportunities Controller (/opportunities)"]
        Apps["Applications Controller (/applications)"]
        Tests["Assessment Controller (/tests)"]
        Dash["Analytics Controller (/dashboard)"]
        AdminCtrl["Admin Management (/admin/users, /admin/tests)"]
    end

    subgraph SecurityTier["Security & Cross-Cutting"]
        RBAC["RBAC Guards (@login_required, @admin_required)"]
        Audit["Audit Logger (audit_logs / SR-06)"]
        Err["Central Error Handlers (400, 403, 404, 500)"]
    end

    subgraph DataTier["Data Access & Persistence"]
        DBMgr["Database Manager (db.py / SQLite WAL)"]
        DB[("portal.sqlite")]
        BackupStorage[("Backup Snapshots (instance/backups/)")]
    end

    UI --> ControllerTier
    ControllerTier -.-> SecurityTier
    ControllerTier --> DBMgr
    SecurityTier --> DBMgr
    DBMgr --> DB
    DBMgr --> BackupStorage
```

### 3. Entity-Relationship (ER) Diagram

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
        INTEGER id PK
        TEXT name
        TEXT email UK
        TEXT password_hash
        TEXT role
    }
    STUDENT_PROFILES {
        INTEGER user_id PK, FK
        TEXT usn
        TEXT phone
        TEXT department
        INTEGER batch_year
        REAL cgpa
        TEXT skills
    }
    OPPORTUNITIES {
        INTEGER id PK
        TEXT title
        TEXT company
        TEXT type
        TEXT location
        TEXT stipend
        TEXT deadline
        INTEGER is_open
    }
    APPLICATIONS {
        INTEGER id PK
        INTEGER user_id FK
        INTEGER opportunity_id FK
        TEXT status
        TEXT applied_at
    }
    APTITUDE_TESTS {
        INTEGER id PK
        TEXT name
        TEXT category
        INTEGER duration_minutes
        TEXT difficulty
        INTEGER is_active
    }
    TEST_QUESTIONS {
        INTEGER id PK
        INTEGER test_id FK
        TEXT question_text
        TEXT option_a
        TEXT option_b
        TEXT option_c
        TEXT option_d
        TEXT correct_option
    }
    TEST_ATTEMPTS {
        INTEGER id PK
        INTEGER user_id FK
        INTEGER test_id FK
        INTEGER score
        REAL percentage
        INTEGER passed
    }
    AUDIT_LOGS {
        INTEGER id PK
        INTEGER user_id FK
        TEXT actor_email
        TEXT action
        TEXT result
        TEXT timestamp
    }
```

## Sprint 1 Backlog Status: Closed

All Sprint 1 / Iteration 1 user stories, functional modules, and test suites have been implemented, merged, and verified.

- **Web Application**: [`placement-portal/`](placement-portal/) (Flask + SQLite)
- **Test Suite**: 91 unit and integration tests passing (`python -m pytest tests -v`)
- **Key Deliverables Completed**:
  - **Task #6**: User Registration & PBKDF2 Password Hashing (`FR-01`, `SR-02`, `SR-05`, `TC-01`)
  - **Task #7**: User Authentication (Login/Logout & Session Guard) (`FR-02`, `TC-02`)
  - **Task #9**: Student Academic Profile Management (`FR-04`)
  - **Tasks #11 & #12**: Opportunity Catalog, Keyword Search & Location Filtering (`FR-05`, `FR-06`, `TC-04`, `NFR-03`)
  - **Task #13**: Opportunity Details View (`FR-05`)
  - **Task #15**: Application Submission & Application Status Tracking (`FR-07`, `FR-08`, `FR-16`, `TC-05`, `TC-06`)
  - **Task #16**: Practice Aptitude Tests Listing (`FR-09`)
  - **Task #18**: Interactive Aptitude Testing, Automated Scoring & Scorecard Review (`FR-09`, `FR-10`, `TC-07`)
  - **Task #30**: Query Optimization, Indexing & Performance Benchmarks (`NFR-01`, `NFR-06`, `TC-09`)

