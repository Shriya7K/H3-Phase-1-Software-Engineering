"""Demo data for the placement portal.

Deadlines are generated relative to the day the database is first created, so
the demo always shows a realistic mix of open, closing-soon and expired items.
"""

from __future__ import annotations

from datetime import date, timedelta
import json
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
        "id": 1,
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
        "id": 2,
        "name": "Logical Reasoning",
        "category": "Reasoning",
        "description": "Number series, blood relations, syllogisms and seating arrangements.",
        "num_questions": 25,
        "duration_minutes": 35,
        "difficulty": "Medium",
        "is_active": 1,
    },
    {
        "id": 3,
        "name": "Verbal Ability",
        "category": "English",
        "description": "Reading comprehension, sentence correction and para jumbles.",
        "num_questions": 20,
        "duration_minutes": 25,
        "difficulty": "Easy",
        "is_active": 1,
    },
    {
        "id": 4,
        "name": "Data Interpretation",
        "category": "Aptitude",
        "description": "Tables, charts and caselets with calculation-heavy questions.",
        "num_questions": 15,
        "duration_minutes": 30,
        "difficulty": "Hard",
        "is_active": 1,
    },
    {
        "id": 5,
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
        "id": 6,
        "name": "Advanced SQL",
        "category": "Technical",
        "description": "Joins, window functions and query optimisation.",
        "num_questions": 20,
        "duration_minutes": 40,
        "difficulty": "Hard",
        "is_active": 0,
    },
]


QUESTIONS = [
    # Test 1: Quantitative Aptitude
    {
        "test_id": 1,
        "question_text": "If a shirt is marked at Rs 800 and sold at a 15% discount, what is the selling price?",
        "option_a": "Rs 680",
        "option_b": "Rs 700",
        "option_c": "Rs 650",
        "option_d": "Rs 720",
        "correct_option": "A",
    },
    {
        "test_id": 1,
        "question_text": "A train 180 metres long is running at 72 km/h. How many seconds will it take to pass a telegraph post?",
        "option_a": "8 seconds",
        "option_b": "9 seconds",
        "option_c": "10 seconds",
        "option_d": "12 seconds",
        "correct_option": "B",
    },
    {
        "test_id": 1,
        "question_text": "A and B can complete a work in 12 days and 24 days respectively. Working together, in how many days can they complete it?",
        "option_a": "6 days",
        "option_b": "8 days",
        "option_c": "10 days",
        "option_d": "9 days",
        "correct_option": "B",
    },
    {
        "test_id": 1,
        "question_text": "The average of five numbers is 27. If one number is excluded, the average becomes 25. The excluded number is:",
        "option_a": "30",
        "option_b": "32",
        "option_c": "35",
        "option_d": "40",
        "correct_option": "C",
    },
    {
        "test_id": 1,
        "question_text": "Two numbers are in the ratio 3 : 5. If their sum is 240, what is the larger number?",
        "option_a": "120",
        "option_b": "140",
        "option_c": "150",
        "option_d": "160",
        "correct_option": "C",
    },

    # Test 2: Logical Reasoning
    {
        "test_id": 2,
        "question_text": "Find the next number in the sequence: 4, 9, 19, 39, 79, ?",
        "option_a": "159",
        "option_b": "149",
        "option_c": "169",
        "option_d": "158",
        "correct_option": "A",
    },
    {
        "test_id": 2,
        "question_text": "Pointing to a photograph, Rohit said, 'She is the daughter of my grandfather's only son.' How is the girl related to Rohit?",
        "option_a": "Mother",
        "option_b": "Sister",
        "option_c": "Aunt",
        "option_d": "Cousin",
        "correct_option": "B",
    },
    {
        "test_id": 2,
        "question_text": "In a certain code, 'PYTHON' is written as 'QZWIPO'. How is 'JAVA' written in that code?",
        "option_a": "KZWZ",
        "option_b": "KBWB",
        "option_c": "KBWC",
        "option_d": "KCWC",
        "correct_option": "B",
    },
    {
        "test_id": 2,
        "question_text": "If South-East becomes North, North-East becomes West and so on, what will West become?",
        "option_a": "North-East",
        "option_b": "South-East",
        "option_c": "South-West",
        "option_d": "North-West",
        "correct_option": "B",
    },
    {
        "test_id": 2,
        "question_text": "Which word does not belong with the others: Apple, Banana, Carrot, Orange?",
        "option_a": "Apple",
        "option_b": "Banana",
        "option_c": "Carrot",
        "option_d": "Orange",
        "correct_option": "C",
    },

    # Test 3: Verbal Ability
    {
        "test_id": 3,
        "question_text": "Choose the word most nearly opposite in meaning to CANDID:",
        "option_a": "Blunt",
        "option_b": "Guarded",
        "option_c": "Sincere",
        "option_d": "Carefree",
        "correct_option": "B",
    },
    {
        "test_id": 3,
        "question_text": "Identify the grammatically correct sentence:",
        "option_a": "Neither of the students were present.",
        "option_b": "Neither of the students was present.",
        "option_c": "Neither of the students have been present.",
        "option_d": "Neither of students was present.",
        "correct_option": "B",
    },
    {
        "test_id": 3,
        "question_text": "Choose the synonym for METICULOUS:",
        "option_a": "Careless",
        "option_b": "Painstaking",
        "option_c": "Hasty",
        "option_d": "Fragile",
        "correct_option": "B",
    },
    {
        "test_id": 3,
        "question_text": "Fill in the blank: The committee _____ divided in their opinions.",
        "option_a": "was",
        "option_b": "were",
        "option_c": "is",
        "option_d": "has",
        "correct_option": "B",
    },
    {
        "test_id": 3,
        "question_text": "Select the correctly spelt word:",
        "option_a": "Accomodate",
        "option_b": "Accommodate",
        "option_c": "Acommodate",
        "option_d": "Accomadate",
        "correct_option": "B",
    },
]


def seed_database(connection: Connection) -> None:
    """Insert demo users, opportunities, aptitude tests, profiles, applications, and questions."""
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
            (id, name, category, description, num_questions, duration_minutes,
             difficulty, is_active)
        VALUES
            (:id, :name, :category, :description, :num_questions, :duration_minutes,
             :difficulty, :is_active)
        """,
        APTITUDE_TESTS,
    )

    # Demo student profile (user_id = 1)
    connection.execute(
        """
        INSERT INTO student_profiles
            (user_id, usn, phone, department, batch_year, cgpa, skills, bio, github_url, linkedin_url)
        VALUES
            (1, 'PES1UG24CS001', '+91 98765 43210', 'Computer Science and Engineering', 2027, 8.85,
             'Python, Flask, SQL, Data Structures, Git',
             'Pre-final year CSE student passionate about software engineering, backend systems, and web technologies.',
             'https://github.com/aditi-sharma',
             'https://linkedin.com/in/aditi-sharma')
        """
    )

    # Demo applications for student (user_id = 1)
    connection.executemany(
        """
        INSERT INTO applications (user_id, opportunity_id, status, notes, applied_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, 1, "Under Review", "Applied on campus drive day 1.", (date.today() - timedelta(days=2)).isoformat()),
            (1, 2, "Submitted", "Resume and GitHub portfolio attached.", (date.today() - timedelta(days=1)).isoformat()),
        ],
    )

    # Seed aptitude test questions
    connection.executemany(
        """
        INSERT INTO test_questions
            (test_id, question_text, option_a, option_b, option_c, option_d, correct_option)
        VALUES
            (:test_id, :question_text, :option_a, :option_b, :option_c, :option_d, :correct_option)
        """,
        QUESTIONS,
    )

    # Seed one completed test attempt for demo student
    connection.execute(
        """
        INSERT INTO test_attempts
            (user_id, test_id, score, total_questions, percentage, passed, answers_json, completed_at)
        VALUES
            (1, 1, 4, 5, 80.0, 1, ?, ?)
        """,
        (
            json.dumps({"1": "A", "2": "B", "3": "B", "4": "C", "5": "B"}),
            (date.today() - timedelta(days=1)).isoformat(),
        ),
    )

    connection.commit()
