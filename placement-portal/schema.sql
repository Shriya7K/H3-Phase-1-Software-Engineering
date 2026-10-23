-- Team H3 · Online Internship & Placement Preparation Portal
-- Iteration 1 schema: users, opportunities, aptitude tests.

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
