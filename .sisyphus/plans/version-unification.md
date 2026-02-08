# Version Unification Plan - Splunk Security Alert System

## TL;DR

> **Quick Summary**: Unify all version references to 4.2.3, correct AGENTS.md inaccuracies (15 alerts, 7 scripts), and update 11 legacy docs/ files from 2.0.x to 4.2.3.
>
> **Deliverables**:
> - 5 core files updated to 4.2.3
> - 1 AGENTS.md corrected (alerts: 32→15, scripts: 5→7)
> - 11 docs/ files with legacy version references updated
> - 2 wiki files with date updated to 2026-02
> - Single atomic commit
>
> **Estimated Effort**: Quick (text-only edits)
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Wave 1 (core) → Wave 4 (commit)

---

## Context

### Original Request
Splunk Security Alert System 프로젝트 전체 현행화 작업. app.conf = 4.2.3 기준으로 모든 버전 참조 통일, AGENTS.md 수치 오류 정정, 레거시 버전 참조 정리.

### Interview Summary
**Key Discussions**:
- app.conf 4.2.3이 정식 버전 (authoritative source)
- CHANGELOG.md 히스토리 내용은 수정 불필요 (역사적 기록)
- 코드 변경 없음 (문서/설정 파일만)
- n8n-integration.md 이미 제거됨 (확인 완료)

**Research Findings**:
- bin/*.py: 7개 스크립트 확인 (문서에는 5개로 기재)
- savedsearches.conf: 15개 알림 확인 (문서에는 32개로 기재)
- 루트 AGENTS.md: 이미 15 alerts로 수정됨 (OK)
- docs/: 11개 파일에서 28개 legacy 버전 참조 발견

### Metis Review
**Identified Gaps** (addressed):
- Badge URL format in README: Verified shields.io format compatible with 4.2.3
- Wiki submodule commit: Included in plan as separate step
- docs/ files scope: User explicitly marked HIGH priority - all 11 files to be updated
- Alert ID range: Keep (001-017) format (range convention, not enumeration)
- Date updates: Include 2026-02 update as part of modernization

---

## Work Objectives

### Core Objective
Synchronize all documentation to version 4.2.3 and correct factual inaccuracies in AGENTS.md.

### Concrete Deliverables
- `pyproject.toml`: version 4.2.2 → 4.2.3
- `README.md`: v2.0.4 → v4.2.3 (lines 1, 185)
- `security_alert/README.md`: v2.0.4 → v4.2.3 (lines 1, 118)
- `splunk.wiki/_Footer.md`: v2.0.4 → v4.2.3, 2026-01 → 2026-02
- `splunk.wiki/Home.md`: 2.0.4 → 4.2.3 (lines 5, 73), 2026-01 → 2026-02
- `security_alert/AGENTS.md`: 32→15 alerts, 5→7 scripts, 001-032→001-017
- 11 docs/*.md files: 2.0.4/2.0.5 → 4.2.3

### Definition of Done
- [ ] `grep -rE "2\.0\.[45]" --include="*.md" . | grep -v CHANGELOG | wc -l` = 0
- [ ] Version 4.2.3 present in all 5 core files
- [ ] AGENTS.md shows "15 saved searches", "7 bin/*.py", "(001-017)"
- [ ] Single commit with all changes
- [ ] Wiki submodule pointer updated

### Must Have
- All version strings updated to 4.2.3
- AGENTS.md factual corrections
- Single atomic commit

### Must NOT Have (Guardrails)
- **NO** CHANGELOG.md modifications (historical record)
- **NO** code file changes (.py, .sh, .conf)
- **NO** changes to bin/lib/, vendor/, extras/addons/
- **NO** multiple commits (single atomic commit only)
- **NO** line number shifts during edits (verify each file)

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**

### Test Decision
- **Infrastructure exists**: NO (documentation-only changes)
- **Automated tests**: None required (text edits)
- **Framework**: N/A

### Agent-Executed QA Scenarios (MANDATORY)

All verification commands are agent-executable via Bash.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately - Core Version Files):
├── Task 1: Update pyproject.toml (4.2.2 → 4.2.3)
├── Task 2: Update README.md (v2.0.4 → v4.2.3)
├── Task 3: Update security_alert/README.md (v2.0.4 → v4.2.3)
└── Task 4: Update security_alert/AGENTS.md (32→15, 5→7, 032→017)

Wave 2 (After Wave 1 - Wiki Files):
├── Task 5: Update splunk.wiki/_Footer.md
└── Task 6: Update splunk.wiki/Home.md

Wave 3 (After Wave 1 - Legacy Docs):
├── Task 7: Update docs/ legacy files (11 files)

Wave 4 (After All Waves - Commit):
└── Task 8: Git commit all changes

Critical Path: Wave 1 → Wave 4
Parallel Speedup: ~50% faster than sequential
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 8 | 2, 3, 4 |
| 2 | None | 8 | 1, 3, 4 |
| 3 | None | 8 | 1, 2, 4 |
| 4 | None | 8 | 1, 2, 3 |
| 5 | None | 8 | 6, 7 |
| 6 | None | 8 | 5, 7 |
| 7 | None | 8 | 5, 6 |
| 8 | 1-7 | None | None (final) |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1, 2, 3, 4 | `quick` category, parallel dispatch |
| 2 | 5, 6 | `quick` category, parallel dispatch |
| 3 | 7 | `quick` category (11 files, sed-like edits) |
| 4 | 8 | `quick` + `git-master` skill |

---

## TODOs

- [ ] 1. Update pyproject.toml version

  **What to do**:
  - Edit line 7: `version = "4.2.2"` → `version = "4.2.3"`

  **Must NOT do**:
  - Change quote style (keep double quotes)
  - Modify any other lines

  **Recommended Agent Profile**:
  - **Category**: `quick` - Single line edit
  - **Skills**: `[]` - No specialized skills needed
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed for edit, only for commit

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: Task 8
  - **Blocked By**: None

  **References**:
  - `pyproject.toml:7` - Target line with version string
  - `security_alert/default/app.conf:13` - Authoritative version source (4.2.3)

  **Acceptance Criteria**:
  - [ ] `grep "version = \"4.2.3\"" pyproject.toml` → matches

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Verify pyproject.toml version updated
    Tool: Bash
    Steps:
      1. grep "version = \"4.2.3\"" pyproject.toml
      2. Assert: Output contains version = "4.2.3"
    Expected Result: Version string matches 4.2.3
  ```

  **Commit**: YES (grouped with all)
  - Message: `docs: unify version to 4.2.3 and correct AGENTS.md`
  - Files: All modified files in single commit

---

- [ ] 2. Update README.md version references

  **What to do**:
  - Line 1: `# Security Alert System v2.0.4` → `# Security Alert System v4.2.3`
  - Line 185: `**v2.0.4** (2025-11-04)` → `**v4.2.3** (2026-02-04)`

  **Must NOT do**:
  - Change GitHub repository URL (already correct: jclee-homelab/splunk)
  - Modify alert descriptions or other content

  **Recommended Agent Profile**:
  - **Category**: `quick` - Two line edits
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Task 8
  - **Blocked By**: None

  **References**:
  - `README.md:1` - Title with version
  - `README.md:185-189` - Version history section

  **Acceptance Criteria**:
  - [ ] `grep "v4.2.3" README.md | wc -l` → 2
  - [ ] `grep "v2.0.4" README.md | wc -l` → 0

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Verify README.md version updated
    Tool: Bash
    Steps:
      1. grep -c "v4.2.3" README.md
      2. Assert: Count >= 2
      3. grep "v2.0.4" README.md
      4. Assert: No output (exit code 1)
    Expected Result: All v2.0.4 replaced with v4.2.3
  ```

  **Commit**: YES (grouped)

---

- [ ] 3. Update security_alert/README.md version references

  **What to do**:
  - Line 1: `# Security Alert System v2.0.4` → `# Security Alert System v4.2.3`
  - Line 118: `**v2.0.4** (2025-11-04)` → `**v4.2.3** (2026-02-04)`

  **Must NOT do**:
  - Change any other content

  **Recommended Agent Profile**:
  - **Category**: `quick` - Two line edits
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: Task 8
  - **Blocked By**: None

  **References**:
  - `security_alert/README.md:1` - Title
  - `security_alert/README.md:118` - Version section

  **Acceptance Criteria**:
  - [ ] `grep "v4.2.3" security_alert/README.md | wc -l` → 2
  - [ ] `grep "v2.0.4" security_alert/README.md | wc -l` → 0

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Verify security_alert/README.md version updated
    Tool: Bash
    Steps:
      1. grep -c "v4.2.3" security_alert/README.md
      2. Assert: Count >= 2
      3. grep "v2.0.4" security_alert/README.md
      4. Assert: No output
    Expected Result: All v2.0.4 replaced with v4.2.3
  ```

  **Commit**: YES (grouped)

---

- [ ] 4. Correct security_alert/AGENTS.md inaccuracies

  **What to do**:
  - Line 7: `Splunk app with 32 saved searches` → `Splunk app with 15 saved searches`
  - Line 19: `# 32 alerts` → `# 15 alerts`
  - Line 40: `(001-032)` → `(001-017)`
  - Line 98: `5 bin/*.py files` → `7 bin/*.py files`

  **Must NOT do**:
  - Change any other content or structure

  **Recommended Agent Profile**:
  - **Category**: `quick` - Four line edits
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocks**: Task 8
  - **Blocked By**: None

  **References**:
  - `security_alert/AGENTS.md:7,19,40,98` - Lines to correct
  - `security_alert/default/savedsearches.conf` - Actual 15 alerts source
  - `security_alert/bin/*.py` - Actual 7 scripts

  **Acceptance Criteria**:
  - [ ] `grep "15 saved searches" security_alert/AGENTS.md` → matches
  - [ ] `grep "# 15 alerts" security_alert/AGENTS.md` → matches
  - [ ] `grep "(001-017)" security_alert/AGENTS.md` → matches
  - [ ] `grep "7 bin/\*\.py" security_alert/AGENTS.md` → matches

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Verify AGENTS.md corrections
    Tool: Bash
    Steps:
      1. grep "15 saved searches" security_alert/AGENTS.md
      2. Assert: Output contains "15 saved searches"
      3. grep "(001-017)" security_alert/AGENTS.md
      4. Assert: Output contains "(001-017)"
      5. grep "7 bin/" security_alert/AGENTS.md
      6. Assert: Output contains "7 bin/"
      7. grep "32" security_alert/AGENTS.md
      8. Assert: No output (all 32s replaced)
    Expected Result: All four corrections applied
  ```

  **Commit**: YES (grouped)

---

- [ ] 5. Update splunk.wiki/_Footer.md

  **What to do**:
  - Line 5: `Version: v2.0.4 | Last Updated: 2026-01` → `Version: v4.2.3 | Last Updated: 2026-02`

  **Must NOT do**:
  - Change any links or other content

  **Recommended Agent Profile**:
  - **Category**: `quick` - Single line edit
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 6)
  - **Blocks**: Task 8
  - **Blocked By**: None

  **References**:
  - `splunk.wiki/_Footer.md:5` - Target line

  **Acceptance Criteria**:
  - [ ] `grep "v4.2.3" splunk.wiki/_Footer.md` → matches
  - [ ] `grep "2026-02" splunk.wiki/_Footer.md` → matches

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Verify wiki footer updated
    Tool: Bash
    Steps:
      1. grep "v4.2.3" splunk.wiki/_Footer.md
      2. Assert: Contains v4.2.3
      3. grep "2026-02" splunk.wiki/_Footer.md
      4. Assert: Contains 2026-02
    Expected Result: Footer shows v4.2.3 and 2026-02
  ```

  **Commit**: YES (grouped)

---

- [ ] 6. Update splunk.wiki/Home.md

  **What to do**:
  - Line 5: `version-2.0.4-blue.svg` → `version-4.2.3-blue.svg`
  - Line 73: `**Version**: 2.0.4 | **Updated**: 2026-01` → `**Version**: 4.2.3 | **Updated**: 2026-02`

  **Must NOT do**:
  - Change any other content or links

  **Recommended Agent Profile**:
  - **Category**: `quick` - Two line edits
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 5)
  - **Blocks**: Task 8
  - **Blocked By**: None

  **References**:
  - `splunk.wiki/Home.md:5` - Badge URL
  - `splunk.wiki/Home.md:73` - Version footer

  **Acceptance Criteria**:
  - [ ] `grep "4.2.3" splunk.wiki/Home.md | wc -l` → 2
  - [ ] `grep "2.0.4" splunk.wiki/Home.md | wc -l` → 0

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Verify wiki Home.md updated
    Tool: Bash
    Steps:
      1. grep -c "4.2.3" splunk.wiki/Home.md
      2. Assert: Count = 2
      3. grep "2.0.4" splunk.wiki/Home.md
      4. Assert: No output
    Expected Result: Both version references updated
  ```

  **Commit**: YES (grouped)

---

- [ ] 7. Update docs/ legacy version references (11 files)

  **What to do**:
  Replace version references in these files:
  
  | File | Changes |
  |------|---------|
  | `docs/VALIDATION-REPORT.md` | v2.0.4 → v4.2.3 (lines 1, 410) |
  | `docs/deployment-checklist.md` | v2.0.5 → v4.2.3 (line 1, 55) |
  | `docs/PROJECT-STRUCTURE.md` | v2.0.4 → v4.2.3 (line 225) |
  | `docs/DEPLOYMENT-GUIDE-GITHUB.md` | v2.0.5 → v4.2.3, v2.0.4 → v4.2.2 (historical comparison OK) |
  | `docs/slack-custom-action-research.md` | v2.0.4 → v4.2.3 (line 377) |
  | `docs/PROJECT-STATUS.md` | v2.0.5 → v4.2.3 (5 refs) |
  | `docs/CLEANUP-COMPLETED.md` | v2.0.4 → v4.2.3 (line 17) |
  | `docs/INSTALLATION-GUIDE.md` | 2.0.4 → 4.2.3 (line 4) |
  | `docs/phases/PHASE-2F-COMPLETION-REPORT.md` | v2.0.5 → v4.2.3 (line 180) |
  | `docs/phases/PHASE-10-SUMMARY.md` | v2.0.5 → v4.2.3 (5 refs) |
  | `docs/CLEANUP-PROPOSAL.md` | v2.0.4 → v4.2.3 (3 refs) |

  **Special Handling - DEPLOYMENT-GUIDE-GITHUB.md**:
  - Lines showing "Before (v2.0.4)" / "After (v2.0.5)" comparison tables should be:
    - "Before (v2.0.4)" → "Before (v4.2.2)" (previous version)
    - "After (v2.0.5)" → "After (v4.2.3)" (current version)
  - This preserves the comparison semantics while updating to current versions

  **Must NOT do**:
  - Touch CHANGELOG.md
  - Change content meaning, only version numbers

  **Recommended Agent Profile**:
  - **Category**: `quick` - Bulk text replacements
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (can run with Wave 2)
  - **Blocks**: Task 8
  - **Blocked By**: None

  **References**:
  - 11 files listed above with specific line numbers

  **Acceptance Criteria**:
  - [ ] `grep -rE "2\.0\.[45]" docs/ --include="*.md" | wc -l` → 0

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Verify all docs/ legacy versions removed
    Tool: Bash
    Steps:
      1. grep -rE "2\.0\.[45]" docs/ --include="*.md"
      2. Assert: Exit code 1 (no matches)
    Expected Result: Zero legacy version references in docs/

  Scenario: Verify version 4.2.3 propagated
    Tool: Bash
    Steps:
      1. grep -r "4.2.3" docs/ --include="*.md" | wc -l
      2. Assert: Count > 10
    Expected Result: Multiple 4.2.3 references exist
  ```

  **Commit**: YES (grouped)

---

- [ ] 8. Git commit all changes

  **What to do**:
  1. Stage all modified files: `git add -A`
  2. Verify staged files match expected list
  3. Create single atomic commit
  4. Update wiki submodule pointer

  **Must NOT do**:
  - Create multiple commits
  - Include CHANGELOG.md in changes
  - Push to remote (user will decide)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `['git-master']` - Atomic commit expertise
  - **Skills Evaluated but Omitted**:
    - Other skills not relevant to git operations

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (final, sequential)
  - **Blocks**: None
  - **Blocked By**: Tasks 1-7

  **References**:
  - All modified files from Tasks 1-7

  **Acceptance Criteria**:
  - [ ] `git status --porcelain | wc -l` → 0 (clean working tree)
  - [ ] `git log -1 --oneline` → contains "docs: unify version"
  - [ ] `git diff HEAD~1 --name-only | grep -v CHANGELOG | wc -l` → matches file count

  **Agent-Executed QA Scenarios**:
  ```
  Scenario: Verify clean commit created
    Tool: Bash
    Steps:
      1. git status --porcelain
      2. Assert: Empty output (clean working tree)
      3. git log -1 --format="%s"
      4. Assert: Message starts with "docs:"
      5. git diff HEAD~1 --name-only | grep CHANGELOG
      6. Assert: No output (CHANGELOG not modified)
    Expected Result: Single clean commit, CHANGELOG untouched
  ```

  **Commit**: This IS the commit task
  - Message: `docs: unify version to 4.2.3 and correct AGENTS.md documentation`
  - Files: pyproject.toml, README.md, security_alert/README.md, security_alert/AGENTS.md, splunk.wiki/_Footer.md, splunk.wiki/Home.md, docs/*.md (11 files)

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 8 (Final) | `docs: unify version to 4.2.3 and correct AGENTS.md documentation` | All 17+ files | `git status --porcelain` = empty |

---

## Success Criteria

### Verification Commands
```bash
# No legacy versions remain (except CHANGELOG)
grep -rE "2\.0\.[45]" --include="*.md" . | grep -v CHANGELOG.md | wc -l
# Expected: 0

# Version 4.2.3 in all core files
for f in pyproject.toml README.md security_alert/README.md splunk.wiki/_Footer.md splunk.wiki/Home.md; do
  grep -q "4\.2\.3" "$f" && echo "OK: $f" || echo "FAIL: $f"
done
# Expected: All 5 show OK

# AGENTS.md corrections verified
grep -E "15 saved searches|15 alerts|\(001-017\)|7 bin/" security_alert/AGENTS.md | wc -l
# Expected: 4

# CHANGELOG untouched
git diff HEAD~1 --name-only | grep CHANGELOG && echo "FAIL" || echo "OK"
# Expected: OK

# Clean working tree
git status --porcelain | wc -l
# Expected: 0
```

### Final Checklist
- [ ] All "Must Have" present (version 4.2.3, AGENTS.md corrections)
- [ ] All "Must NOT Have" absent (no CHANGELOG changes, no code changes)
- [ ] Single atomic commit created
- [ ] Wiki submodule pointer updated
