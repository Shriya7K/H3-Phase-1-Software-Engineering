"""Demo data for the placement portal.

Deadlines are generated relative to the day the database is first created, so
the demo always shows a realistic mix of open, closing-soon and expired items.
"""

from __future__ import annotations

from datetime import date, timedelta
from sqlite3 import Connection

from werkzeug.security import generate_password_hash


def _iso(days_from_today: int) -> str:
    return (date.today() + timedelta(days=days_from_today)).isoformat()


USERS = [
    # Demo accounts (documented on the login page and in the README).
    {
        "name": "Aditi Sharma",
        "email": "student@campus.edu",
        "password": "student123",
        "role": "student",
    },
    {
        "name": "Priya Menon",
        "email": "admin@campus.edu",
        "password": "admin123",
        "role": "admin",
    },
]


OPPORTUNITIES = [
    {
        "title": "Software Engineering Intern",
        "company": "Infosys",
        "type": "Internship",
        "location": "Bengaluru",
        "stipend": "Rs 25,000/month",
        "description": (
            "Work with the platform engineering team on internal developer tooling. "
            "You will write production Python, review code with a mentor and ship "
            "small features end to end."
        ),
        "eligibility": "B.Tech / BE (CSE, ISE, ECE) · 2027 batch · CGPA 7.0+",
        "deadline": _iso(12),
        "is_open": 1,
    },
    {
        "title": "Backend Developer Intern",
        "company": "Zoho",
        "type": "Internship",
        "location": "Chennai",
        "stipend": "Rs 30,000/month",
        "description": (
            "Join the backend team building APIs for Zoho's HR suite. Expect hands-on "
            "work with Java, REST endpoints and MySQL, plus a short internal training "
            "module in the first week."
        ),
        "eligibility": "B.Tech / BE (CSE, ISE) · 2026 or 2027 batch · CGPA 6.5+",
        "deadline": _iso(20),
        "is_open": 1,
    },
    {
        "title": "Graduate Software Engineer",
        "company": "TCS",
        "type": "Placement",
        "location": "Bengaluru",
        "stipend": "Rs 7.0 LPA",
        "description": (
            "Full-time software engineering role under TCS Digital. The first eight "
            "weeks are structured training, after which you are allocated to a project "
            "based on your preferences and assessment scores."
        ),
        "eligibility": "B.Tech / BE / MCA · 2026 batch · CGPA 6.0+ · no active backlogs",
        "deadline": _iso(5),
        "is_open": 1,
    },
    {
        "title": "Data Analyst",
        "company": "Deloitte",
        "type": "Placement",
        "location": "Hyderabad",
        "stipend": "Rs 8.5 LPA",
        "description": (
            "Support client analytics engagements: clean data, build dashboards and "
            "present findings with the consulting team. Expect to work directly with "
            "senior analysts during live projects."
        ),
        "eligibility": "B.Tech / BE any branch · 2026 batch · CGPA 7.0+ · SQL required",
        "deadline": _iso(27),
        "is_open": 1,
    },
    {
        "title": "Frontend Intern",
        "company": "Freshworks",
        "type": "Internship",
        "location": "Remote",
        "stipend": "Rs 20,000/month",
        "description": (
            "Build UI components in React for Freshworks' customer engagement "
            "products. You will pair with senior engineers and your work goes out in a "
            "real release at the end of the internship."
        ),
        "eligibility": "Any degree · 2027 batch · portfolio or GitHub with frontend projects",
        "deadline": _iso(9),
        "is_open": 1,
    },
    {
        "title": "Product Management Trainee",
        "company": "PhonePe",
        "type": "Placement",
        "location": "Bengaluru",
        "stipend": "Rs 12.0 LPA",
        "description": (
            "A rotational program across product, analytics and operations. Trainees "
            "own a small product area with guidance from a PM mentor and present a "
            "review at the end of each rotation."
        ),
        "eligibility": "B.Tech / BE · 2026 batch · CGPA 7.5+",
        "deadline": _iso(33),
        "is_open": 1,
    },
    {
        "title": "Cloud Support Associate",
        "company": "Amazon Web Services",
        "type": "Placement",
        "location": "Pune",
        "stipend": "Rs 9.5 LPA",
        "description": (
            "First-line support for AWS customers: troubleshoot networking and Linux "
            "issues, document fixes and escalate complex cases. Rotational shifts apply."
        ),
        "eligibility": "B.Tech / BE any branch · 2026 batch · CGPA 6.5+ · Linux basics",
        "deadline": _iso(16),
        "is_open": 1,
    },
    {
        # Expired listing: useful for checking that the listing hides it.
        "title": "QA Intern",
        "company": "Wipro",
        "type": "Internship",
        "location": "Bengaluru",
        "stipend": "Rs 18,000/month",
        "description": (
            "Assist the QA team with manual test cases and regression runs for a "
            "banking client."
        ),
        "eligibility": "B.Sc / BCA / B.Tech · 2027 batch",
        "deadline": _iso(-3),
        "is_open": 1,
    },
    {
        # Closed listing: useful for checking that the listing hides it.
        "title": "HR Intern",
        "company": "Accenture",
        "type": "Internship",
        "location": "Gurugram",
        "stipend": "Rs 15,000/month",
        "description": "Support campus hiring drives and maintain candidate trackers.",
        "eligibility": "MBA / any degree · 2027 batch",
        "deadline": _iso(14),
        "is_open": 0,
    },
]


APTITUDE_TESTS = [
    {
        "name": "Quantitative Aptitude",
        "category": "Aptitude",
        "description": (
            "Percentages, ratios, averages, time and work - the standard first round "
            "for most campus drives."
        ),
        "num_questions": 20,
        "duration_minutes": 30,
        "difficulty": "Easy",
        "is_active": 1,
    },
    {
        "name": "Logical Reasoning",
        "category": "Reasoning",
        "description": "Number series, blood relations, syllogisms and seating arrangements.",
        "num_questions": 25,
        "duration_minutes": 35,
        "difficulty": "Medium",
        "is_active": 1,
    },
    {
        "name": "Verbal Ability",
        "category": "English",
        "description": "Reading comprehension, sentence correction and para jumbles.",
        "num_questions": 20,
        "duration_minutes": 25,
        "difficulty": "Easy",
        "is_active": 1,
    },
    {
        "name": "Data Interpretation",
        "category": "Aptitude",
        "description": "Tables, charts and caselets with calculation-heavy questions.",
        "num_questions": 15,
        "duration_minutes": 30,
        "difficulty": "Hard",
        "is_active": 1,
    },
    {
        "name": "Programming Fundamentals",
        "category": "Technical",
        "description": "Output prediction, data structures and basic complexity analysis.",
        "num_questions": 20,
        "duration_minutes": 30,
        "difficulty": "Medium",
        "is_active": 1,
    },
    {
        # Inactive test: should not appear on the student-facing page.
        "name": "Advanced SQL",
        "category": "Technical",
        "description": "Joins, window functions and query optimisation.",
        "num_questions": 20,
        "duration_minutes": 40,
        "difficulty": "Hard",
        "is_active": 0,
    },
]


def seed_database(connection: Connection) -> None:
    """Insert demo users, opportunities and aptitude tests."""
    connection.executemany(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        [
            (
                user["name"],
                user["email"],
                generate_password_hash(user["password"]),
                user["role"],
            )
            for user in USERS
        ],
    )

    connection.executemany(
        """
        INSERT INTO opportunities
            (title, company, type, location, stipend, description, eligibility,
             deadline, is_open)
        VALUES
            (:title, :company, :type, :location, :stipend, :description,
             :eligibility, :deadline, :is_open)
        """,
        OPPORTUNITIES,
    )

    connection.executemany(
        """
        INSERT INTO aptitude_tests
            (name, category, description, num_questions, duration_minutes,
             difficulty, is_active)
        VALUES
            (:name, :category, :description, :num_questions, :duration_minutes,
             :difficulty, :is_active)
        """,
        APTITUDE_TESTS,
    )

    connection.commit()
