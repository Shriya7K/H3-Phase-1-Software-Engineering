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
| `01_COMPLETE_SRS_IEEE_STYLE.docx` | Complete SRS |
| `02_COMPLETE_IEEE_TEST_PLAN.docx` | IEEE-style Test Plan |
| `03_COMPLETE_TEST_CASES_15.docx` | Functional, NFR and security test cases |
| `04_COMPLETE_ARCHITECTURE_AND_DESIGN.docx` | Architecture and Design Specification |
| [`docs/sprint-2/SPRINT_2_VERIFICATION_REPORT.md`](docs/sprint-2/SPRINT_2_VERIFICATION_REPORT.md) | Comprehensive Sprint 2 Engineering, RBAC, Data Integrity & Verification Report |
| [`docs/sprint-2/BROWSER_COMPATIBILITY_MATRIX.md`](docs/sprint-2/BROWSER_COMPATIBILITY_MATRIX.md) | Supported Browser Compatibility Matrix & Verification Report (Chrome, Firefox, Edge) |

## UML Diagrams

- Use Case Diagram
- Component Diagram
- Sequence Diagram: Login and Browse Opportunities
- Sequence Diagram: Apply for Opportunity

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

## Sprint 2 Backlog Status: Completed & Verified

All Sprint 2 / Iteration 2 backlog user stories, architectural matrices, validation rules, and automated/simulated verification test suites have been completed.

- **Web Application**: [`placement-portal/`](placement-portal/)
- **Test Suite**: 193 automated unit and integration tests passing (`python -m pytest tests -v`)
- **Key Deliverables Completed**:
  - **Task #8**: Role-Based Access Control Architecture & Permission Matrix (`FR-03`, `SR-03`, `TC-03`)
  - **Task #10**: Server-Side Profile Field Validation & Sanitization (`FR-04`, `SR-05`, `TC-11`)
  - **Task #21**: Integrated Analytics Dashboard (`FR-12`, `TC-08`)
  - **Task #22**: Student Application Summaries & Pipeline Tracking (`FR-12`, `FR-08`, `TC-08`)
  - **Task #23**: Aptitude Performance Metrics & Category Breakdown (`FR-12`, `FR-10`, `TC-08`)
  - **Task #24**: Placement Preparation Progress Algorithm & Milestones (`FR-11`, `FR-12`, `TC-08`)
  - **Task #25**: User Management Directory, Role Updates & Audit Logging (`FR-15`, `SR-06`, `TC-14`)
  - **Task #27**: Aptitude Test & Question Bank Management (`FR-14`)
  - **Task #29**: Authorization & Access Control Validation Suite (`NFR-02`, `SR-01`, `SR-03`, `TC-10`, `SV-01`, `SV-02`)
  - **Task #31**: Relational Database Integrity & Constraint Verification (`NFR-09`, `SR-05`, `TC-11`, `SO-03`)
  - **Task #32**: Supported Browser Compatibility Matrix & Smoke Suite (`NFR-08`, `TC-15`)
  - **Task #33**: Reliability, Transaction Rollback & Database Recovery (`NFR-04`, `NFR-09`)
