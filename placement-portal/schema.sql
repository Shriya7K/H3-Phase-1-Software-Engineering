-- Team H3 · Online Internship & Placement Preparation Portal
-- Iteration 1 & Sprint 1 schema: users, opportunities, aptitude tests,
-- profiles, applications, and test questions/attempts.

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'student'
                  CHECK (role IN ('student', 'admin'))
);

CREATE TABLE IF NOT EXISTS opportunities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    company     TEXT NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('Internship', 'Placement')),
    location    TEXT NOT NULL,
    stipend     TEXT NOT NULL,          -- human readable, e.g. "Rs 25,000/month" or "7.0 LPA"
    description TEXT NOT NULL,
    eligibility TEXT NOT NULL,
    deadline    TEXT NOT NULL,          -- ISO date (YYYY-MM-DD)
    is_open     INTEGER NOT NULL DEFAULT 1 CHECK (is_open IN (0, 1)),
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Listing page filters on (is_open, deadline); the index keeps that query fast
-- even with a large number of opportunities (Iteration 1, task #30).
CREATE INDEX IF NOT EXISTS idx_opportunities_open_deadline
    ON opportunities (is_open, deadline);

CREATE INDEX IF NOT EXISTS idx_opportunities_type
    ON opportunities (type);

CREATE INDEX IF NOT EXISTS idx_opportunities_open_location
    ON opportunities (is_open, location);

CREATE TABLE IF NOT EXISTS aptitude_tests (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    category         TEXT NOT NULL,
    description      TEXT NOT NULL,
    num_questions    INTEGER NOT NULL CHECK (num_questions > 0),
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    difficulty       TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    is_active        INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- Task #9: Student profile management (FR-04)
CREATE TABLE IF NOT EXISTS student_profiles (
    user_id       INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    usn           TEXT,
    phone         TEXT,
    department    TEXT,
    batch_year    INTEGER,
    cgpa          REAL CHECK (cgpa IS NULL OR (cgpa >= 0.0 AND cgpa <= 10.0)),
    skills        TEXT,
    bio           TEXT,
    github_url    TEXT,
    linkedin_url  TEXT,
    updated_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Task #15: Application tracking & status management (FR-07, FR-08, FR-16)
CREATE TABLE IF NOT EXISTS applications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id  INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'Submitted'
                    CHECK (status IN ('Submitted', 'Under Review', 'Shortlisted', 'Accepted', 'Rejected')),
    notes           TEXT,
    applied_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, opportunity_id)
);

CREATE INDEX IF NOT EXISTS idx_applications_user
    ON applications (user_id);
CREATE INDEX IF NOT EXISTS idx_applications_opportunity
    ON applications (opportunity_id);

-- Task #18: Aptitude test questions and attempts (FR-09, FR-10)
CREATE TABLE IF NOT EXISTS test_questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id         INTEGER NOT NULL REFERENCES aptitude_tests(id) ON DELETE CASCADE,
    question_text   TEXT NOT NULL,
    option_a        TEXT NOT NULL,
    option_b        TEXT NOT NULL,
    option_c        TEXT NOT NULL,
    option_d        TEXT NOT NULL,
    correct_option  TEXT NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D'))
);

CREATE INDEX IF NOT EXISTS idx_test_questions_test
    ON test_questions (test_id);

CREATE TABLE IF NOT EXISTS test_attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    test_id         INTEGER NOT NULL REFERENCES aptitude_tests(id) ON DELETE CASCADE,
    score           INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    percentage      REAL NOT NULL,
    passed          INTEGER NOT NULL CHECK (passed IN (0, 1)),
    answers_json    TEXT,
    completed_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_test_attempts_user
    ON test_attempts (user_id);


-- SR-06 & TC-14: Audit logging for security-relevant administrative actions
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    actor_email TEXT NOT NULL,
    action      TEXT NOT NULL,
    details     TEXT,
    result      TEXT NOT NULL DEFAULT 'SUCCESS',
    ip_address  TEXT,
    timestamp   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
    ON audit_logs (timestamp);
