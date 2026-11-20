# Team H3 — Branch Coverage Report
## Online Internship & Placement Preparation Portal

**Document Version:** 1.0  
**Tool Used:** Coverage.py 7.17.0 with branch coverage tracking (`--branch`)  
**Execution Date:** November 2026  
**Total Decision Branches:** 296 branches  
**Branches Executed:** **221 branches covered (75% Branch Coverage)**  

---

## 1. Executive Summary

Branch coverage measures whether each decision point in the application code (e.g. `if/else`, loops, conditional expressions) has had both its `True` and `False` paths executed. The automated test suite achieves **75% branch coverage** across 296 branches in the application.

| Module | Total Branches | Fully Covered Branches | Partial / Missed | Branch Coverage |
|:---|:---|:---|:---|:---|
| `app.py` | 244 | 182 | 62 | **75%** |
| `db.py` | 38 | 25 | 13 | **66%** |
| `tests/test_admin_aptitude_tests.py` | 2 | 2 | 0 | **100%** |
| `tests/test_admin_users.py` | 2 | 2 | 0 | **100%** |
| `tests/test_aptitude_tests.py` | 2 | 2 | 0 | **100%** |
| `tests/test_auth.py` | 4 | 4 | 0 | **100%** |
| `tests/test_opportunities.py` | 2 | 2 | 0 | **100%** |
| `tests/test_performance.py` | 2 | 2 | 0 | **100%** |
| **TOTAL** | **296** | **221** | **75** | **75%** |

---

## 2. Key Branch Analysis in Core Modules

### 2.1 Authentication & Authorization Branches (`app.py`)
* `if not session.get('user_id'):`
  * **True Branch (Covered):** Anonymous requests blocked and redirected to `/login?next=...` (tested in `test_protected_pages_redirect_anonymous_users`).
  * **False Branch (Covered):** Logged in user allowed to proceed to protected route.
* `if session.get('user_role') != 'admin':`
  * **True Branch (Covered):** Student attempting to access admin routes receives HTTP 403 Forbidden (tested in `test_admin_users_access_control`).
  * **False Branch (Covered):** Admin allowed through to admin management dashboards.
* `if user is None or not check_password_hash(user['password_hash'], password):`
  * **Both branches tested:** Valid credentials login vs non-existent user and invalid password scenarios.

### 2.2 Opportunity Filtering & Query Construction (`app.py`)
* `if type_filter:`
  * **True Branch (Covered):** Category filter applied to SQL query (`AND type = ?`).
  * **False Branch (Covered):** "All" types query executed without type restriction.
* `if search_query:`
  * **True Branch (Covered):** Multi-column `LIKE` clause attached with query wildcard.
  * **False Branch (Covered):** No keyword filter applied when input is empty.
* `if location_filter:`
  * **True Branch (Covered):** Specific location criteria appended.
  * **False Branch (Covered):** All locations returned.

### 2.3 Application & Assessment Logic (`app.py`)
* `if existing_app:`
  * **True Branch (Covered):** Re-application detected; returns error flash or disabled form.
  * **False Branch (Covered):** First-time applicant proceeds to submission.
* `if percentage >= pass_threshold:`
  * **True Branch (Covered):** Sets `passed = 1` and displays green pass badge.
  * **False Branch (Covered):** Sets `passed = 0` and displays retry guidance.

### 2.4 Administrative Safety Guards (`app.py`)
* `if target_user['id'] == session.get('user_id') and new_role != 'admin':`
  * **True Branch (Covered):** Sole admin self-demotion blocked with flash error (tested in `test_self_demotion_lockout_guard`).
  * **False Branch (Covered):** Updating roles of other users proceeds normally.

---

## 3. Uncovered Branch Justification

The 75 unexercised branch paths consist of:
1. **Defensive Database Error Handling:** Catch blocks for SQLite locked/busy conditions and disk quota full conditions that cannot occur in standard testing environments.
2. **CLI Guard Branches:** Interactive confirmation checks (`if click.confirm(...)`) intended strictly for human terminal interactions during manual database resets.
3. **HTTP Exception Fallbacks:** Redundant HTTP 500 error propagation branches handled centrally by Flask's application error handler.

All critical business logic, security guards, input sanitizers, and transaction control branches have **100% path execution**.
