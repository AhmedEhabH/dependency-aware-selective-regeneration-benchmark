# TODO

## Phase 0 — Bootstrap and Environment

### T001 — Create Repository Structure
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Create directories: src/benchmark, tests, notebooks, scripts, reports
- **Acceptance Criteria:** All directories exist with __init__.py files
- **Dependencies:** None
- **Status:** COMPLETE_STATICALLY
- **Owner:** OpenCode
- **Evidence:** Directories verified via Get-ChildItem

### T002 — Create State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, PROTOCOL_VERSION.md, docs/MASTER_IMPLEMENTATION_PLAN.md, docs/HUMAN_DECISIONS_REQUIRED.md
- **Acceptance Criteria:** All files present with required content
- **Dependencies:** T001
- **Status:** COMPLETE_STATICALLY
- **Owner:** OpenCode
- **Evidence:** Files written to disk

### T003 — Create Environment Files
- **Priority:** HIGH
- **Category:** Environment
- **Description:** Create environment.yml, requirements-dev.txt, requirements-kaggle.txt
- **Acceptance Criteria:** All three files present with correct package lists
- **Dependencies:** T001
- **Status:** COMPLETE_STATICALLY
- **Owner:** OpenCode
- **Evidence:** Files written to disk

### T004 — Create Conda Environment
- **Priority:** HIGH
- **Category:** Environment
- **Description:** Create `selective-regen-benchmark` with Python 3.11 via conda
- **Acceptance Criteria:** Environment exists and is activatable
- **Dependencies:** T003
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** conda env list output, environment.yml resolution

### T005 — Install Local Engineering Dependencies
- **Priority:** HIGH
- **Category:** Environment
- **Description:** Install packages from requirements-dev.txt inside the project Conda environment via pip
- **Acceptance Criteria:** All packages installed without conflicts
- **Dependencies:** T004
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** pip list output, pip check passing

### T006 — Validate Environment
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run pip check, import smoke tests, version checks, duplicate inspection, optional dependency checks
- **Acceptance Criteria:** All checks pass; no unresolved conflicts
- **Dependencies:** T005
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Check outputs, LOCAL_ENVIRONMENT_REPORT.md

### T007 — Create Environment Report
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/LOCAL_ENVIRONMENT_REPORT.md with all required sections
- **Acceptance Criteria:** Report contains all sections listed in Section 4.3 of the guide
- **Dependencies:** T006
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** File exists with complete content

### T008 — Create Phase Report
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/latest_phase_report.md summarizing Phase 0
- **Acceptance Criteria:** Report lists completed tasks, created files, checks passed, next task
- **Dependencies:** T007
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** File exists with complete content

### T009 — Initialize Git Repository
- **Priority:** MEDIUM
- **Category:** VCS
- **Description:** Initialize Git repo, create .gitignore, make initial bootstrap commit
- **Acceptance Criteria:** Git repo exists with initial commit on main branch
- **Dependencies:** T001-T008
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** git log output

### T010 — Final Review and Handoff
- **Priority:** HIGH
- **Category:** Process
- **Description:** Review all files, verify environment, produce final message
- **Acceptance Criteria:** All files reviewed; environment activation command verified
- **Dependencies:** T009
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Final message with handoff statement
