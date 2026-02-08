# Dashboard E2E Tests for Splunk SimpleXML

## TL;DR

> **Quick Summary**: Create comprehensive E2E tests for 5 Splunk SimpleXML dashboard files. Tests validate XML structure, SPL syntax, macro references, and panel completeness using file-based analysis only (no live Splunk required).
> 
> **Deliverables**:
> - `tests/e2e/test_dashboard_xml.py` - Complete test suite (~300 LOC)
> - New fixtures: `dashboard_files`, `all_dashboard_paths`, `dashboard_path`
> - New pytest marker: `@pytest.mark.dashboard`
> 
> **Estimated Effort**: Medium (2-3 hours)
> **Parallel Execution**: NO - single file, sequential implementation
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4

---

## Context

### Original Request
Create E2E tests for Splunk SimpleXML dashboards (WITHOUT requiring live Splunk). Validate 7 categories: XML well-formedness, dashboard structure, panel completeness, SPL syntax, macro references, time picker tokens, theme consistency.

### Interview Summary
**Key Discussions**:
- File-based validation only (no live Splunk connection)
- Follow existing patterns from `test_saved_searches.py` and `test_lookup_files.py`
- Use existing fixtures from `conftest.py`
- Output file: `tests/e2e/test_dashboard_xml.py`

**Research Findings**:
- 5 dashboard XML files across 3 directories
- Existing test patterns use: class-based organization, `@pytest.mark.parametrize`, expected item lists
- `conftest.py` provides: `project_root`, `security_alert_path`, `parse_conf_file`, `macros` fixtures
- Dashboard structure: `<form>/<dashboard>` root, `<row>/<panel>/<search>/<query>` hierarchy
- Macros referenced in SPL with backticks: `` `macro_name` ``

### Self-Review Gap Analysis
**Identified Gaps (addressed in plan)**:
1. **Edge case**: `<dashboard>` vs `<form>` root elements - both are valid (addressed in Task 2)
2. **Edge case**: Dashboards without time picker - should not fail token validation (addressed in Task 5)
3. **Edge case**: Macro arguments like `` `macro(arg)` `` - regex must handle these (addressed in Task 4)
4. **Guardrail**: Don't validate SPL semantic correctness (only syntax delimiters)

---

## Work Objectives

### Core Objective
Create a comprehensive test file that validates all 5 SimpleXML dashboards for structural integrity, SPL syntax correctness, and configuration consistency.

### Concrete Deliverables
- `tests/e2e/test_dashboard_xml.py` (~300 LOC)
- Updated `tests/conftest.py` with new fixtures and marker

### Definition of Done
- [ ] `pytest tests/e2e/test_dashboard_xml.py -v` runs all tests successfully
- [ ] All 5 dashboards pass XML well-formedness
- [ ] All 7 test categories implemented
- [ ] Tests run without any network/Splunk dependency

### Must Have
- XML parsing with proper error messages
- Balanced delimiter validation (brackets, parentheses, backticks)
- Macro existence validation against macros.conf
- Class-based test organization following existing patterns

### Must NOT Have (Guardrails)
- **NO** live Splunk connections or SDK usage
- **NO** SPL semantic validation (only syntax structure)
- **NO** JavaScript/CSS validation in HTML panels
- **NO** query execution or result validation
- **NO** external API calls or network requests
- **NO** modification of existing test files (only additions)

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.
> ALL verification is executed by the agent using Bash commands.

### Test Decision
- **Infrastructure exists**: YES (pytest already configured)
- **Automated tests**: Tests-after (we're creating a test file, not TDDing the tests themselves)
- **Framework**: pytest (existing)

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

| Type | Tool | How Agent Verifies |
|------|------|-------------------|
| **Test execution** | Bash (pytest) | Run pytest, verify output, check exit code |
| **Syntax check** | Bash (python -m py_compile) | Verify no syntax errors |
| **Import check** | Bash (python -c "import...") | Verify imports work |

---

## Execution Strategy

### Sequential Execution

Tasks must be executed sequentially as each builds on the previous:

```
Task 1: Create fixtures in conftest.py
    ↓
Task 2: Implement XML well-formedness tests
    ↓
Task 3: Implement dashboard structure tests
    ↓
Task 4: Implement SPL validation + macro reference tests
    ↓ (can merge into Task 2-3 if simpler)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|------------|--------|
| 1 | None | 2, 3, 4 |
| 2 | 1 | 4 |
| 3 | 1, 2 | 4 |
| 4 | 1, 2, 3 | None (final) |

### Agent Dispatch Summary

| Task | Recommended Dispatch |
|------|---------------------|
| All | `delegate_task(category="quick", load_skills=[], run_in_background=false)` |

---

## TODOs

- [ ] 1. Add Dashboard Fixtures and Marker to conftest.py

  **What to do**:
  - Add `DASHBOARD_FILES` constant listing all 5 dashboard paths (relative to project root)
  - Add `dashboard_files()` fixture returning the list of dashboard file paths
  - Add `all_dashboard_paths(project_root)` fixture yielding resolved Path objects
  - Add `@pytest.mark.dashboard` marker registration in `pytest_configure()`

  **Dashboard paths to include**:
  ```python
  DASHBOARD_FILES = [
      "security_alert/default/data/ui/views/slack_test_dashboard.xml",
      "security_alert_user/default/data/ui/views/alert-management-dashboard.xml",
      "security_alert_user/default/data/ui/views/data-explorer-dashboard.xml",
      "configs/dashboards/alert-testing-dashboard.xml",
      "configs/dashboards/fortigate-production-alerts-dashboard.xml",
  ]
  ```

  **Must NOT do**:
  - Modify existing fixtures
  - Change marker behavior for existing markers
  - Add dependencies on external packages

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Small additive change to existing file
  - **Skills**: `[]`
    - Reason: Standard Python, no specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (first task)
  - **Blocks**: Tasks 2, 3, 4
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `tests/conftest.py:368-388` - `lookup_path` and `state_tracker_files` fixture pattern (follow this structure)
  - `tests/conftest.py:706-716` - `pytest_configure()` marker registration pattern (add `dashboard` marker here)

  **File Structure References**:
  - `tests/e2e/test_lookup_files.py:12-29` - `STATE_TRACKER_FILES` constant pattern (replicate for DASHBOARD_FILES)

  **WHY Each Reference Matters**:
  - `conftest.py:368-388`: Shows exact pattern for file list fixtures - use same structure for dashboard files
  - `conftest.py:706-716`: Shows where to add new pytest markers - add `dashboard` marker in same function
  - `test_lookup_files.py:12-29`: Shows constant naming and list structure convention - follow same style

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Fixtures are importable and return correct data
    Tool: Bash (python)
    Preconditions: Virtual environment activated
    Steps:
      1. python -c "from tests.conftest import DASHBOARD_FILES; print(len(DASHBOARD_FILES))"
      2. Assert: Output is "5"
      3. python -c "from tests.conftest import DASHBOARD_FILES; assert 'slack_test_dashboard.xml' in DASHBOARD_FILES[0]"
      4. Assert: Exit code 0
    Expected Result: DASHBOARD_FILES constant exists with 5 entries
    Evidence: Command outputs

  Scenario: Dashboard marker is registered
    Tool: Bash (pytest)
    Preconditions: pytest installed
    Steps:
      1. pytest --markers | grep -i dashboard
      2. Assert: Output contains "dashboard"
    Expected Result: Dashboard marker appears in registered markers
    Evidence: Grep output
  ```

  **Evidence to Capture:**
  - [ ] Command output showing 5 dashboard files
  - [ ] Marker registration output

  **Commit**: YES
  - Message: `test(e2e): add dashboard fixtures and marker to conftest`
  - Files: `tests/conftest.py`
  - Pre-commit: `python -m py_compile tests/conftest.py`

---

- [ ] 2. Create test_dashboard_xml.py with XML and Structure Tests

  **What to do**:
  - Create `tests/e2e/test_dashboard_xml.py`
  - Add module docstring explaining purpose
  - Import required modules: `xml.etree.ElementTree`, `pytest`, `re`, `Path`
  - Add `DASHBOARD_FILES` constant (same as conftest.py)
  - Implement `class TestDashboardXMLWellFormedness`:
    - `test_all_dashboard_files_exist()` - verify all 5 files exist
    - `test_dashboard_xml_parses_correctly()` - `@pytest.mark.parametrize` over files, use `ET.parse()`
  - Implement `class TestDashboardStructure`:
    - `test_dashboard_has_valid_root_element()` - root must be `<form>` or `<dashboard>`
    - `test_dashboard_has_version_attribute()` - version attribute present
    - `test_dashboard_has_label()` - `<label>` element exists
    - `test_dashboard_has_at_least_one_row()` - `<row>` element(s) exist

  **Must NOT do**:
  - Validate SPL query content (that's Task 4)
  - Check for specific panel types
  - Validate HTML content inside `<html>` panels

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Creating test file with standard pytest patterns
  - **Skills**: `[]`
    - Reason: Standard Python/pytest, well-documented patterns provided

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: Tasks 3, 4
  - **Blocked By**: Task 1

  **References**:

  **Pattern References**:
  - `tests/e2e/test_saved_searches.py:38-56` - Class-based test structure with parametrize (follow exact pattern)
  - `tests/e2e/test_saved_searches.py:58-72` - `@pytest.mark.parametrize` usage for individual items
  - `tests/e2e/test_lookup_files.py:32-42` - File existence test pattern (replicate for dashboards)

  **Dashboard Structure References**:
  - `security_alert/default/data/ui/views/slack_test_dashboard.xml:1-5` - Example `<form>` root structure with version and theme
  - `configs/dashboards/fortigate-production-alerts-dashboard.xml:1-5` - Similar structure for larger dashboard

  **Documentation References**:
  - Python stdlib: `xml.etree.ElementTree` - Use `ET.parse()` for file parsing, `ET.fromstring()` for string parsing

  **WHY Each Reference Matters**:
  - `test_saved_searches.py:38-56`: Exact class naming convention and test method structure to follow
  - `test_saved_searches.py:58-72`: Shows how to parametrize with list of expected items
  - `test_lookup_files.py:32-42`: File existence validation pattern - copy and adapt for XML files
  - Dashboard XML files: Show actual structure to validate - root element, version, label

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Test file has no syntax errors
    Tool: Bash (python)
    Preconditions: None
    Steps:
      1. python -m py_compile tests/e2e/test_dashboard_xml.py
      2. Assert: Exit code 0
    Expected Result: No syntax errors
    Evidence: Exit code

  Scenario: XML well-formedness tests pass
    Tool: Bash (pytest)
    Preconditions: Fixtures in conftest.py (Task 1)
    Steps:
      1. pytest tests/e2e/test_dashboard_xml.py::TestDashboardXMLWellFormedness -v
      2. Assert: Exit code 0
      3. Assert: Output contains "5 passed" or all individual passes
    Expected Result: All 5 dashboards parse correctly
    Evidence: Pytest output

  Scenario: Structure tests pass
    Tool: Bash (pytest)
    Preconditions: Test file created
    Steps:
      1. pytest tests/e2e/test_dashboard_xml.py::TestDashboardStructure -v
      2. Assert: Exit code 0
    Expected Result: All structure validations pass
    Evidence: Pytest output
  ```

  **Evidence to Capture:**
  - [ ] py_compile success output
  - [ ] pytest verbose output showing passed tests

  **Commit**: YES
  - Message: `test(e2e): add dashboard XML well-formedness and structure tests`
  - Files: `tests/e2e/test_dashboard_xml.py`
  - Pre-commit: `pytest tests/e2e/test_dashboard_xml.py -v --tb=short`

---

- [ ] 3. Add Panel Completeness and Theme Tests

  **What to do**:
  - Add to `tests/e2e/test_dashboard_xml.py`:
  - Implement `class TestPanelCompleteness`:
    - `test_panels_have_title()` - each `<panel>` should have `<title>` child
    - `test_panels_have_visualization_or_search()` - panel contains `<table>`, `<chart>`, `<single>`, `<html>`, or `<search>`
    - `test_search_elements_have_query()` - each `<search>` has `<query>` child
  - Implement `class TestDashboardTheme`:
    - `test_dashboard_uses_dark_theme()` - `theme="dark"` attribute on root (warn if missing, don't fail)
  - Implement `class TestTimeTokenConsistency`:
    - `test_time_picker_token_usage()` - if dashboard has time picker with token, searches should use that token

  **Must NOT do**:
  - Fail on missing dark theme (only warn/log)
  - Validate specific visualization options
  - Check panel positioning or layout

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Extending existing test file with similar patterns
  - **Skills**: `[]`
    - Reason: Standard pytest patterns, XML parsing

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: Task 4
  - **Blocked By**: Tasks 1, 2

  **References**:

  **Pattern References**:
  - `tests/e2e/test_dashboard_xml.py` (from Task 2) - Build on existing test classes
  - `tests/e2e/test_lookup_files.py:45-76` - Schema validation pattern with expected columns dict

  **Dashboard Structure References**:
  - `security_alert/default/data/ui/views/slack_test_dashboard.xml:26-43` - Panel structure: `<row><panel><title><table><search><query>`
  - `configs/dashboards/fortigate-production-alerts-dashboard.xml:5-13` - Time picker with `$time_picker.earliest$` token pattern

  **WHY Each Reference Matters**:
  - `test_lookup_files.py:45-76`: Shows pattern for expected schema validation - adapt for panel children
  - Dashboard files show: Panel structure hierarchy and time picker token naming convention

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Panel completeness tests pass
    Tool: Bash (pytest)
    Preconditions: Tasks 1, 2 complete
    Steps:
      1. pytest tests/e2e/test_dashboard_xml.py::TestPanelCompleteness -v
      2. Assert: Exit code 0
    Expected Result: All panels have required elements
    Evidence: Pytest output

  Scenario: Theme consistency tests run without error
    Tool: Bash (pytest)
    Preconditions: Tasks 1, 2 complete
    Steps:
      1. pytest tests/e2e/test_dashboard_xml.py::TestDashboardTheme -v
      2. Assert: Exit code 0 (warnings OK)
    Expected Result: Theme tests complete (may have warnings)
    Evidence: Pytest output

  Scenario: Time token tests pass
    Tool: Bash (pytest)
    Preconditions: Tasks 1, 2 complete
    Steps:
      1. pytest tests/e2e/test_dashboard_xml.py::TestTimeTokenConsistency -v
      2. Assert: Exit code 0
    Expected Result: Token usage is consistent
    Evidence: Pytest output
  ```

  **Evidence to Capture:**
  - [ ] pytest output for each test class

  **Commit**: YES
  - Message: `test(e2e): add dashboard panel and theme consistency tests`
  - Files: `tests/e2e/test_dashboard_xml.py`
  - Pre-commit: `pytest tests/e2e/test_dashboard_xml.py -v --tb=short`

---

- [ ] 4. Add SPL Syntax and Macro Reference Tests

  **What to do**:
  - Add to `tests/e2e/test_dashboard_xml.py`:
  - Create helper functions:
    - `_extract_queries(tree)` - extract all `<query>` text content from XML tree
    - `_check_balanced_delimiters(spl, char_open, char_close)` - count matching pairs
    - `_extract_macro_names(spl)` - regex to find backtick macros `` `name` `` or `` `name(args)` ``
  - Implement `class TestSPLSyntaxValidation`:
    - `test_spl_has_balanced_parentheses()` - count `(` and `)` match
    - `test_spl_has_balanced_brackets()` - count `[` and `]` match
    - `test_spl_has_balanced_backticks()` - backticks come in pairs
    - `test_spl_has_balanced_quotes()` - double quotes in pairs
  - Implement `class TestMacroReferences`:
    - `test_macro_references_exist_in_macros_conf()` - extract macro names from SPL, verify each exists in `macros` fixture

  **Regex for macro extraction**:
  ```python
  # Matches: `macro_name` or `macro_name(arg1, arg2)`
  MACRO_PATTERN = re.compile(r'`([a-z_][a-z0-9_]*(?:\([^)]*\))?)`', re.IGNORECASE)
  ```

  **Must NOT do**:
  - Validate SPL keywords or command syntax
  - Execute queries
  - Check field names or index references
  - Fail on macros defined in `local/` (only check `default/macros.conf`)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Adding helper functions and test classes to existing file
  - **Skills**: `[]`
    - Reason: Regex and string parsing, standard Python

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (final task)
  - **Blocks**: None
  - **Blocked By**: Tasks 1, 2, 3

  **References**:

  **Pattern References**:
  - `tests/conftest.py:687-698` - `macros` fixture that parses macros.conf (use this fixture)
  - `tests/e2e/test_saved_searches.py:84-95` - Regex-based validation pattern for cron format

  **Macro Definition References**:
  - `security_alert/default/macros.conf:6-93` - All macro stanza names (validate against these)

  **SPL References in Dashboards**:
  - `security_alert/default/data/ui/views/slack_test_dashboard.xml:30-35` - Example SPL with rex, eval commands
  - `configs/dashboards/fortigate-production-alerts-dashboard.xml:46-72` - Complex SPL with `index=fw`, stats, eval

  **WHY Each Reference Matters**:
  - `conftest.py:687-698`: The `macros` fixture already parses macros.conf - use it to get valid macro names
  - `test_saved_searches.py:84-95`: Regex validation pattern - adapt for delimiter counting
  - `macros.conf:6-93`: List of valid macro names to validate against
  - Dashboard SPL: Real examples of SPL syntax to understand delimiter patterns

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: SPL syntax tests pass for all dashboards
    Tool: Bash (pytest)
    Preconditions: Tasks 1-3 complete
    Steps:
      1. pytest tests/e2e/test_dashboard_xml.py::TestSPLSyntaxValidation -v
      2. Assert: Exit code 0
      3. Assert: Output shows tests for balanced delimiters
    Expected Result: All SPL has balanced delimiters
    Evidence: Pytest output

  Scenario: Macro reference tests pass
    Tool: Bash (pytest)
    Preconditions: Tasks 1-3 complete, macros fixture works
    Steps:
      1. pytest tests/e2e/test_dashboard_xml.py::TestMacroReferences -v
      2. Assert: Exit code 0 (or expected failures for local/ macros)
    Expected Result: All macro references validated
    Evidence: Pytest output

  Scenario: Full test suite passes
    Tool: Bash (pytest)
    Preconditions: All tasks complete
    Steps:
      1. pytest tests/e2e/test_dashboard_xml.py -v
      2. Assert: Exit code 0
      3. Assert: Output shows all test classes executed
    Expected Result: Complete test suite passes
    Evidence: Full pytest output
  ```

  **Evidence to Capture:**
  - [ ] pytest output for SPL syntax tests
  - [ ] pytest output for macro reference tests
  - [ ] Full test suite output with pass count

  **Commit**: YES
  - Message: `test(e2e): add SPL syntax and macro reference validation tests`
  - Files: `tests/e2e/test_dashboard_xml.py`
  - Pre-commit: `pytest tests/e2e/test_dashboard_xml.py -v`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `test(e2e): add dashboard fixtures and marker to conftest` | `tests/conftest.py` | `python -m py_compile tests/conftest.py` |
| 2 | `test(e2e): add dashboard XML well-formedness and structure tests` | `tests/e2e/test_dashboard_xml.py` | `pytest tests/e2e/test_dashboard_xml.py -v` |
| 3 | `test(e2e): add dashboard panel and theme consistency tests` | `tests/e2e/test_dashboard_xml.py` | `pytest tests/e2e/test_dashboard_xml.py -v` |
| 4 | `test(e2e): add SPL syntax and macro reference validation tests` | `tests/e2e/test_dashboard_xml.py` | `pytest tests/e2e/test_dashboard_xml.py -v` |

---

## Success Criteria

### Verification Commands
```bash
# Syntax check
python -m py_compile tests/e2e/test_dashboard_xml.py  # Expected: exit 0

# Run all dashboard tests
pytest tests/e2e/test_dashboard_xml.py -v  # Expected: all pass

# Run with marker filter
pytest -m dashboard tests/e2e/ -v  # Expected: dashboard tests only

# Verify no external dependencies
pytest tests/e2e/test_dashboard_xml.py --collect-only  # Expected: shows test items, no errors
```

### Final Checklist
- [ ] All 5 dashboards pass XML parsing
- [ ] All 7 test categories implemented:
  - [ ] XML well-formedness
  - [ ] Dashboard structure (form/dashboard, version, label)
  - [ ] Panel completeness (title, visualization/search, query)
  - [ ] SPL syntax (balanced delimiters)
  - [ ] Macro references (exist in macros.conf)
  - [ ] Time picker tokens (consistent usage)
  - [ ] Theme consistency (dark theme check)
- [ ] No live Splunk dependencies
- [ ] Follows existing test patterns
- [ ] All tests pass with `pytest tests/e2e/test_dashboard_xml.py -v`
