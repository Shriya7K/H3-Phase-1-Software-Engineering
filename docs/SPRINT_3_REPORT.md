# Team H3 — Sprint 3 Activity & Quality Hardening Report
## Online Internship & Placement Preparation Portal

**Sprint Duration:** November 2 to November 6, 2026  
**Activity Category:** Quality Hardening, Test Expansion & Deliverables Finalization (Sprint 3)  
**Team Members:** Shriya K (PES1UG24CS448), Srivani Karanth (PES1UG24CS471), Sia Simran A (PES1UG24CS453)  
**Status:** **CLOSED & VERIFIED**  

---

## 1. Sprint Goal & Objectives

Sprint 3 was scheduled as an activity window to address any potential development spillovers from Sprint 1 and Sprint 2, perform system-wide regression testing, generate required formal IEEE test reports, and finalize all Phase-1 / Part-3 mini-project deliverables.

### Primary Objectives:
1. **Spillover Assessment:** Assess whether any user stories or functional backlog items from Sprint 1 or Sprint 2 remained incomplete.
2. **Test Cases Updation:** Update the formal Test Case Specification from the original 15 test cases to 33 comprehensive test cases covering all sprint additions.
3. **Automated Testing & Reporting:** Execute the full test suite and generate the required Unit Test Report, System Validation Report, Code Coverage Report, and Branch Coverage Report in the `docs/` folder.
4. **Performance & Query Optimization:** Profile large-scale listing queries (3,000+ opportunities) and verify sub-250ms median response times.
5. **Repository Cleanliness:** Remove any temporary/extraneous artifacts, verify git history integrity, and confirm build health.

---

## 2. Spillover Evaluation

An audit of the sprint backlog confirmed:
* **Sprint 1 Stories:** User Registration (FR-01), Authentication (FR-02), Profiles (FR-04), Opportunities (FR-05, FR-06), Applications (FR-07, FR-08), Test Taking (FR-09, FR-10), Analytics Dashboard (FR-12 / Issue #21), and User Management (FR-15 / Issue #25) were **100% completed and merged via PR #35**.
* **Sprint 2 Stories:** Manage Aptitude Tests & Question Bank (FR-14 / Issue #27) and Reliability & Recovery (NFR-04, NFR-09 / Issue #33) were **100% completed and merged via PR #38**.
* **Spillover Verdict:** Zero development backlog items spilled over. The core feature set is officially frozen.

---

## 3. Sprint 3 Completed Activities

### Activity 1: Test Cases Updation
* Expanded test case definitions from `TC-01`–`TC-15` to `TC-01`–`TC-33`.
* Added explicit verification procedures for:
  * Dynamic student readiness calculations (TC-22).
  * Administrator recruitment pipeline distribution (TC-23).
  * User directory search and filtering (TC-24).
  * Administrator role update and self-demotion lockout guard (TC-25, TC-26).
  * Aptitude test builder and duration validation (TC-27, TC-28).
  * Atomic transaction rollback on failure (TC-29).
  * Foreign key constraints and cascading deletions (TC-30).
  * Hot database backup creation and disaster recovery verification (TC-31, TC-32).
  * Central error handling and stack trace concealment (TC-33).
* Documented in [`docs/TEST_CASE_SPECIFICATION.md`](TEST_CASE_SPECIFICATION.md).

### Activity 2: Test Execution & Report Generation
* Executed complete test suite of **135 automated tests**:
  * **135 Passed / 135 Total (100% Pass Rate)**.
* Generated all required Part-3 reports:
  * **Unit Test Report:** [`docs/UNIT_TEST_REPORT.md`](UNIT_TEST_REPORT.md)
  * **System Validation Report:** [`docs/SYSTEM_VALIDATION_REPORT.md`](SYSTEM_VALIDATION_REPORT.md)
  * **Code Coverage Report:** [`docs/CODE_COVERAGE_REPORT.md`](CODE_COVERAGE_REPORT.md) (91% overall coverage)
  * **Branch Coverage Report:** [`docs/BRANCH_COVERAGE_REPORT.md`](BRANCH_COVERAGE_REPORT.md) (75% branch coverage)
  * **JUnit XML Report:** [`docs/junit_test_report.xml`](junit_test_report.xml)
  * **Interactive Coverage HTML:** [`docs/coverage_html/index.html`](coverage_html/index.html)

### Activity 3: Performance Hardening
* Optimized Jinja2 template link generation in `templates/opportunities.html`, reducing per-request template rendering time by eliminating repeated dynamic route lookups across bulk datasets.
* Re-verified performance benchmarks under 3,000 opportunities and 200 tests: median latency confirmed at **~140ms**, well within the 250ms limit.

---

## 4. Deliverables Summary

| Deliverable | Location | Status |
|:---|:---|:---|
| Test Case Specification | `docs/TEST_CASE_SPECIFICATION.md` | Complete |
| Unit Test Report | `docs/UNIT_TEST_REPORT.md` | Complete |
| System Validation Report | `docs/SYSTEM_VALIDATION_REPORT.md` | Complete |
| Code Coverage Report | `docs/CODE_COVERAGE_REPORT.md` | Complete |
| Branch Coverage Report | `docs/BRANCH_COVERAGE_REPORT.md` | Complete |
| JUnit Test Results | `docs/junit_test_report.xml` | Complete |
| Interactive Coverage HTML | `docs/coverage_html/` | Complete |
| UML Architecture Specification | `docs/UML_DIAGRAMS.md` | Complete |
| Sprint 3 Activity Summary | `docs/SPRINT_3_REPORT.md` | Complete |
