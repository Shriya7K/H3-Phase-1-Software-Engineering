# 4. System Design & UML Architecture

[![Software Engineering](https://img.shields.io/badge/Course-Software%20Engineering%20(UE24CS351AA2)-0052CC.svg)](https://pes.edu)
[![Student SRN](https://img.shields.io/badge/SRN-PES1UG24CS453-orange.svg)](https://github.com/siasimran-magic)
[![Standard](https://img.shields.io/badge/UML-2.5%20Standard-purple.svg)](https://www.omg.org/spec/UML/)

**Project**: Online Internship & Placement Preparation Portal (IPP)  
**Institution**: PES University | Department of Computer Science & Engineering  
**Student SRN**: PES1UG24CS453  

---

## 🏛️ 1. Architectural Pattern Recognition & Selection

### Evaluated Patterns Comparison
| Architectural Pattern | Advantages for IPP | Limitations / Trade-offs | Verdict & Justification |
|:---|:---|:---|:---:|
| **Traditional Monolith** | Simple to build and deploy locally | Tight coupling; a spike in exam submissions can degrade the job search board | ❌ Rejected for lack of fault isolation |
| **Pure Microservices** | High modularity; independent deployment | Excessive overhead for orchestration, inter-service network latency | ❌ Over-engineered for project scope |
| **Layered Client-Server (3-Tier) with Modular Services** | Strict separation of concerns (UI, Business Logic, Data); independent scaling of exam evaluation engine; rapid development | Requires careful API contract governance | ✅ **Selected Architecture** |

### Selected Architecture Justification
The **3-Tier Layered Architecture** with decoupled modular REST services is chosen because:
1. **Presentation Tier**: Provides a high-performance Single Page Application (SPA) responsive across desktop and mobile devices.
2. **Application Tier**: Encapsulates business rules into distinct functional controllers (`Auth`, `Opportunities`, `Tracker`, `ExamEngine`, `Analytics`).
3. **Data Tier**: Combines ACID-compliant relational data storage (`PostgreSQL`) with an in-memory session cache (`Redis`) to guarantee sub-second latency for live test sessions.

---

## 🧩 2. UML Component Architecture Diagram

```mermaid
graph TB
    subgraph Client_Tier["Client Presentation Layer"]
        SPA["<<component>>\nWeb Client (React / Vite)"]
    end

    subgraph Gateway_Tier["Routing & Security Layer"]
        Proxy["<<component>>\nNginx Reverse Proxy & Load Balancer"]
    end

    subgraph Service_Tier["Application Business Logic Layer"]
        AuthComp["<<component>>\nAuth & RBAC Module\n(JWT & Bcrypt)"]
        JobComp["<<component>>\nOpportunity Catalog\n(Filter & Search)"]
        TrackComp["<<component>>\nApplication Tracker\n(Kanban Engine)"]
        ExamComp["<<component>>\nExam & Quiz Engine\n(Timer & Scoring)"]
        AnlComp["<<component>>\nAnalytics Engine\n(Radar & Percentile)"]
    end

    subgraph Persistence_Tier["Data Persistence Layer"]
        RelDB[("<<database>>\nPostgreSQL\nRelational DB")]
        CacheStore[("<<cache>>\nRedis\nSession & Timers")]
        CloudStore[("<<storage>>\nS3 / Cloud Storage\nResume PDFs")]
    end

    SPA -->|HTTPS / JSON| Proxy
    Proxy --> AuthComp
    Proxy --> JobComp
    Proxy --> TrackComp
    Proxy --> ExamComp
    Proxy --> AnlComp

    AuthComp -->|SQL Queries| RelDB
    JobComp -->|SQL Queries| RelDB
    TrackComp -->|SQL Queries| RelDB
    TrackComp -->|Blob Upload| CloudStore
    ExamComp -->|Questions & Results| RelDB
    ExamComp -->|Session Heartbeat & Lock| CacheStore
    AnlComp -->|Aggregate Queries| RelDB
```

---

## 👥 3. UML Use Case Diagram

```mermaid
flowchart TD
    Student(("🎓 Student"))
    TPO(("🏢 Placement Officer (TPO)"))
    Recruiter(("💼 Recruiter"))
    Admin(("⚙️ Administrator"))

    subgraph Portal["Online Internship & Placement Preparation Portal (IPP)"]
        UC1(["UC-1: Search & Filter Opportunities"])
        UC2(["UC-2: Submit Application with Resume"])
        UC3(["UC-3: Track Application Status (Kanban)"])
        UC4(["UC-4: Take Timed Aptitude / Mock Exam"])
        UC5(["UC-5: Review Readiness Analytics & Radar"])
        UC6(["UC-6: Create & Publish Placement Drive"])
        UC7(["UC-7: Filter Eligible Candidate Roster"])
        UC8(["UC-8: Review Applications & Move Stages"])
        UC9(["UC-9: Manage Question Bank & Solution Keys"])
        UC10(["UC-10: System Auditing & User Management"])
    end

    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5

    TPO --> UC6
    TPO --> UC7
    TPO --> UC9

    Recruiter --> UC8
    Recruiter --> UC7

    Admin --> UC10
    Admin --> UC9
```

---

## 🔄 4. UML Sequence Diagram: Timed Aptitude Exam & Analytics Sync

```mermaid
sequenceDiagram
    autonumber
    actor S as Student
    participant UI as Web Client (React)
    participant API as Exam Engine API
    participant R as Redis Cache
    participant DB as PostgreSQL DB
    participant ANL as Analytics Aggregator

    S->>UI: Clicks "Start Aptitude Mock Test"
    UI->>API: POST /api/tests/start { testId, studentId }
    API->>DB: Query randomized test questions (MCQ pool)
    DB-->>API: Return question set (IDs, options, timer limit)
    API->>R: Initialize test session timer (TTL = 3600s)
    API-->>UI: 200 OK { sessionId, questions: [...], expiresAt }
    UI-->>S: Render test interface with countdown timer

    loop During Test Execution
        S->>UI: Selects option for Question [i]
        UI->>R: PUT /api/tests/autosave { sessionId, qId, selectedOption }
        R-->>UI: 200 OK (Draft Saved)
    end

    alt Student clicks Submit OR Timer Expires
        S->>UI: Clicks "Submit Assessment"
        UI->>API: POST /api/tests/submit { sessionId, responses }
    else Countdown reaches 00:00
        UI->>API: POST /api/tests/submit { sessionId, responses, timeout: true }
    end

    API->>R: Invalidate & delete session timer
    API->>DB: Grade responses against answer key & record test_submission
    API->>ANL: Trigger recompute_readiness_metrics(studentId)
    ANL->>DB: Query historical student test records & calculate domain percentiles
    ANL-->>API: Updated Readiness Index: 84.5% (+3.2%)
    API-->>UI: 200 OK { score: 42/50, accuracy: 84%, detailedSolutions: [...], readinessDelta: "+3.2%" }
    UI-->>S: Display Scorecard, Solutions & Updated Performance Radar Chart
```

---

## 🔌 5. RESTful API Endpoints Specification

| HTTP Method | Endpoint URL | Auth Required | Request Body / Parameters | Response Status & Payload |
|:---:|:---|:---:|:---|:---|
| `POST` | `/api/auth/login` | None | `{ email, password }` | `200 OK` `{ token, user: { id, role, name } }` |
| `POST` | `/api/auth/register` | None | `{ name, email, srn, password, branch, cgpa }` | `201 Created` `{ message, userId }` |
| `GET` | `/api/opportunities` | Student / All | Query: `?branch=CSE&minCgpa=8.0&type=internship` | `200 OK` `[ { driveId, company, role, ctc, deadline } ]` |
| `POST` | `/api/applications/apply` | Student | `{ driveId, resumeUrl }` | `201 Created` `{ applicationId, status: "Applied" }` |
| `GET` | `/api/applications/my` | Student | Header: `Bearer <token>` | `200 OK` `[ { appId, company, role, stage, updatedAt } ]` |
| `PATCH` | `/api/applications/:id/status`| Recruiter / TPO | `{ stage: "Shortlisted" \| "Interview" \| "Offer" }` | `200 OK` `{ updated: true, newStage }` |
| `GET` | `/api/tests/catalog` | Student | Query: `?category=quant\|logical\|technical` | `200 OK` `[ { testId, title, durationMinutes, totalMarks } ]` |
| `POST` | `/api/tests/start` | Student | `{ testId }` | `200 OK` `{ sessionId, questions, durationSeconds }` |
| `POST` | `/api/tests/submit` | Student | `{ sessionId, answers: [ { qId, selected } ] }` | `200 OK` `{ score, correctCount, analysis }` |
| `GET` | `/api/analytics/readiness` | Student | Header: `Bearer <token>` | `200 OK` `{ readinessScore, radarMetrics, recommendations }` |
| `POST` | `/api/tpo/drives` | TPO / Admin | `{ company, role, eligibility: { cgpa, branches }, deadline }` | `201 Created` `{ driveId, broadcastSent: true }` |
