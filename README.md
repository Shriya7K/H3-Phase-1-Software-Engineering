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

![Online Internship & Placement Preparation Portal — Use Case Diagram](docs/images/use_case_diagram.png)

*Direct image file: [docs/images/use_case_diagram.png](docs/images/use_case_diagram.png) | [JPG](docs/images/use_case_diagram.jpg)*

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

*Associations show which role can initiate each function.*

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

