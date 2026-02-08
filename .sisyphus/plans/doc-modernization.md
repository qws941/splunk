# Documentation Modernization - GitHub 기준 현행화

## TL;DR

> **Quick Summary**: Splunk 프로젝트 문서를 GitHub 기준으로 현행화. CHANGELOG 날짜 수정, Wiki n8n 문서 GitLab→GitHub 웹훅 변경, 중복 파일 삭제.
>
> **Deliverables**:
> - CHANGELOG.md 날짜 수정 (2025-01-XX → 2026-02-01)
> - n8n-integration.md GitLab CI 웹훅 → GitHub Actions 웹훅 변경
> - docs/PROJECT_STRUCTURE.md(언더스코어) 삭제
> - 2개 커밋 생성 (Wiki + 메인 레포 분리)
>
> **Estimated Effort**: Quick
> **Parallel Execution**: NO - 순차 실행 (Wiki 먼저, 메인 레포 후)
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4

---

## Context

### Original Request
Splunk Security Alert System 프로젝트의 모든 문서를 GitHub 기준으로 현행화.

### Interview Summary
**Key Discussions**:
- CHANGELOG.md 날짜: `2025-01-XX` → `2026-02-01` (오늘 날짜)
- n8n-integration.md: GitLab CI 웹훅 참조 → GitHub Actions 웹훅으로 변경
- 중복 파일: PROJECT_STRUCTURE.md(언더스코어) 삭제, PROJECT-STRUCTURE.md(하이픈) 유지
- Wiki: 별도 git 레포이므로 분리 커밋 필수
- 외부 문서 링크(docs.gitlab.com): 유지 (참고용)
- 스코프: 문서만 수정 (n8n 실제 설정 변경 제외)

**Research Findings**:
- grep 결과: GitLab 참조 15건 중 실제 수정 필요한 것은 n8n-integration.md만
- 히스토리/마이그레이션 문서의 GitLab 참조는 Before/After 예시 - 의도적 유지
- qws941 URL: 이미 수정 완료 (grep 결과 0건)
- PROJECT-STRUCTURE.md가 2025-11-05로 최신, PROJECT_STRUCTURE.md는 구버전
- PROJECT_STRUCTURE.md는 자기 자신만 참조 (삭제 안전)
- Wiki remote 설정 확인: github.com/jclee-homelab/splunk.wiki.git (정상)

### Metis Review
**Identified Gaps** (addressed):
- Wiki는 별도 git 레포 → 분리 커밋으로 변경
- n8n-integration.md GitLab 참조 ~12곳 → 외부 문서 링크는 유지, 웹훅 URL만 변경
- CI/CD 실제 설정 스코프 → 문서만으로 한정

---

## Work Objectives

### Core Objective
Splunk 프로젝트 문서를 GitHub 기준으로 현행화하여 모든 활성 콘텐츠가 현재 GitHub 구조와 일치하도록 업데이트

### Concrete Deliverables
- `CHANGELOG.md` Line 1: 날짜 수정
- `splunk.wiki/docs/guides/05-integrations/n8n-integration.md`: GitLab CI 웹훅 → GitHub Actions 웹훅
- `docs/PROJECT_STRUCTURE.md` 삭제
- Wiki 레포 커밋 1개
- 메인 레포 커밋 1개

### Definition of Done
- [ ] `grep "2025-01-XX" CHANGELOG.md` → 0 matches
- [ ] `grep "gitlab-ci-webhook" splunk.wiki/docs/guides/05-integrations/n8n-integration.md` → 0 matches
- [ ] `ls docs/PROJECT_STRUCTURE.md` → "No such file or directory"
- [ ] `ls docs/PROJECT-STRUCTURE.md` → File exists
- [ ] `git -C splunk.wiki log -1 --oneline` → 관련 커밋 존재
- [ ] `git log -1 --oneline` → 관련 커밋 존재

### Must Have
- CHANGELOG 날짜가 유효한 날짜 형식 (YYYY-MM-DD)
- n8n-integration.md의 모든 `gitlab-ci-webhook` → `github-actions-webhook`
- 중복 파일 삭제

### Must NOT Have (Guardrails)
- ❌ docs/DEPLOYMENT-GUIDE-GITHUB.md의 GitLab 참조 수정 (의도적 Before/After 예시)
- ❌ docs/PROJECT-STATUS.md의 GitLab 참조 수정 (Git 히스토리 인용)
- ❌ CHANGELOG.md의 다른 GitLab 참조 수정 (이슈 설명)
- ❌ n8n-integration.md의 외부 문서 링크(docs.gitlab.com) 수정 (참고용 유지)
- ❌ PROJECT-STRUCTURE.md(하이픈) 수정 또는 삭제
- ❌ Wiki의 다른 파일 수정 (REFACTORING-PLAN.md, AGENTS.md 등)
- ❌ n8n 실제 설정 변경 (문서만)

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: YES (bash, grep)
- **User wants tests**: Manual-only (자동 검증)
- **Framework**: Bash commands (grep, ls, git)

### Automated Verification (Agent-Executable)

모든 검증은 bash 명령으로 자동 수행:

```bash
# 검증 1: CHANGELOG 날짜 수정됨
grep "2.0.5.*2026-02-01" /home/jclee/dev/splunk/CHANGELOG.md
# Assert: 1 line match

# 검증 2: GitLab CI 웹훅 참조 제거됨
grep -c "gitlab-ci-webhook" /home/jclee/dev/splunk/splunk.wiki/docs/guides/05-integrations/n8n-integration.md
# Assert: 0

# 검증 3: GitHub Actions 웹훅으로 변경됨
grep -c "github-actions-webhook" /home/jclee/dev/splunk/splunk.wiki/docs/guides/05-integrations/n8n-integration.md
# Assert: > 0

# 검증 4: PROJECT_STRUCTURE.md 삭제됨
ls /home/jclee/dev/splunk/docs/PROJECT_STRUCTURE.md 2>&1
# Assert: "No such file or directory"

# 검증 5: PROJECT-STRUCTURE.md 유지됨
ls /home/jclee/dev/splunk/docs/PROJECT-STRUCTURE.md
# Assert: File exists

# 검증 6: 의도적 GitLab 참조 유지됨
grep -c "GitLab" /home/jclee/dev/splunk/docs/DEPLOYMENT-GUIDE-GITHUB.md
# Assert: > 0 (should remain)

# 검증 7: 외부 문서 링크 유지됨
grep -c "docs.gitlab.com" /home/jclee/dev/splunk/splunk.wiki/docs/guides/05-integrations/n8n-integration.md
# Assert: > 0 (should remain)
```

---

## Execution Strategy

### Sequential Execution (No Parallelization)

```
Task 1: n8n-integration.md 수정
        ↓
Task 2: Wiki 커밋 생성
        ↓
Task 3: 메인 레포 변경 (CHANGELOG + 파일 삭제)
        ↓
Task 4: 메인 레포 커밋 + 검증
```

**Why Sequential**:
- Wiki 커밋이 메인 레포 커밋보다 먼저 완료되어야 함
- 각 단계의 성공 확인 후 다음 단계 진행

---

## TODOs

- [ ] 1. Wiki n8n-integration.md 수정

  **What to do**:
  - `splunk.wiki/docs/guides/05-integrations/n8n-integration.md` 파일 열기
  - 모든 `gitlab-ci-webhook` → `github-actions-webhook` 변경
  - 모든 "GitLab Pipeline Webhook" → "GitHub Actions Webhook" 변경
  - 모든 "GitLab Webhook 수신" → "GitHub Actions Webhook 수신" 변경
  - 모든 "GitLab → Settings → Webhooks" → "GitHub → Settings → Webhooks" 변경
  - 모든 "GitLab Personal Access Token" → "GitHub Personal Access Token" 변경
  - **유지**: docs.gitlab.com 외부 링크 (Line 557)

  **Must NOT do**:
  - 외부 문서 링크(docs.gitlab.com) 수정
  - 파일 구조나 다른 내용 변경

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 단일 파일 텍스트 치환 작업
  - **Skills**: []
    - 특별한 스킬 불필요 (기본 텍스트 편집)

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Step 1)
  - **Blocks**: Task 2
  - **Blocked By**: None

  **References**:
  - `splunk.wiki/docs/guides/05-integrations/n8n-integration.md:58` - GitLab Pipeline Webhook 첫 참조
  - `splunk.wiki/docs/guides/05-integrations/n8n-integration.md:88` - curl 예시의 gitlab-ci-webhook
  - `splunk.wiki/docs/guides/05-integrations/n8n-integration.md:219` - 설정 섹션
  - `splunk.wiki/docs/guides/05-integrations/n8n-integration.md:557` - 외부 문서 링크 (유지)
  - `splunk.wiki/docs/guides/05-integrations/n8n-integration.md:829` - Webhook 설정 체크리스트

  **WHY Each Reference Matters**:
  - Line 58, 88, 219, 829: 실제 변경 대상 라인
  - Line 557: **수정하지 말 것** - 외부 참고 문서

  **Acceptance Criteria**:
  ```bash
  # AC1: gitlab-ci-webhook 제거됨
  grep -c "gitlab-ci-webhook" /home/jclee/dev/splunk/splunk.wiki/docs/guides/05-integrations/n8n-integration.md
  # Assert: 0

  # AC2: github-actions-webhook 추가됨
  grep -c "github-actions-webhook" /home/jclee/dev/splunk/splunk.wiki/docs/guides/05-integrations/n8n-integration.md
  # Assert: >= 4

  # AC3: 외부 문서 링크 유지됨
  grep -c "docs.gitlab.com" /home/jclee/dev/splunk/splunk.wiki/docs/guides/05-integrations/n8n-integration.md
  # Assert: >= 1
  ```

  **Commit**: NO (groups with Task 2)

---

- [ ] 2. Wiki 커밋 생성

  **What to do**:
  - Wiki 디렉토리로 이동: `cd splunk.wiki`
  - `git status`로 변경 확인
  - `git add docs/guides/05-integrations/n8n-integration.md`
  - `git commit -m "docs: update n8n integration guide for GitHub Actions webhooks"`
  - `git push origin master` (또는 main)

  **Must NOT do**:
  - 다른 파일 커밋에 포함
  - 메인 레포 디렉토리에서 실행

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 단순 git 커밋 작업
  - **Skills**: [`git-master`]
    - `git-master`: git 커밋/푸시 작업

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Step 2)
  - **Blocks**: Task 3
  - **Blocked By**: Task 1

  **References**:
  - `splunk.wiki/.git/` - Wiki는 별도 git 레포
  - Wiki remote: `https://github.com/jclee-homelab/splunk.wiki.git`

  **WHY Each Reference Matters**:
  - Wiki가 별도 레포임을 확인하고 올바른 디렉토리에서 커밋

  **Acceptance Criteria**:
  ```bash
  # AC1: Wiki 커밋 생성됨
  git -C /home/jclee/dev/splunk/splunk.wiki log -1 --oneline | grep -i "github actions"
  # Assert: 1 line match

  # AC2: Wiki clean 상태
  git -C /home/jclee/dev/splunk/splunk.wiki status --porcelain
  # Assert: Empty (no uncommitted changes)
  ```

  **Commit**: YES (Wiki 레포)
  - Message: `docs: update n8n integration guide for GitHub Actions webhooks`
  - Files: `docs/guides/05-integrations/n8n-integration.md`
  - Pre-commit: None (MD 파일)

---

- [ ] 3. 메인 레포 변경 (CHANGELOG + 파일 삭제)

  **What to do**:
  - `CHANGELOG.md` Line 1 수정: `## [2.0.5] - 2025-01-XX` → `## [2.0.5] - 2026-02-01`
  - `docs/PROJECT_STRUCTURE.md` 파일 삭제
  - 변경 사항 확인

  **Must NOT do**:
  - CHANGELOG.md의 다른 GitLab 참조 수정 (Line 77, 96, 208, 210은 의도적)
  - PROJECT-STRUCTURE.md(하이픈) 수정 또는 삭제
  - docs/DEPLOYMENT-GUIDE-GITHUB.md 수정
  - docs/PROJECT-STATUS.md 수정

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 단순 텍스트 수정 + 파일 삭제
  - **Skills**: []
    - 특별한 스킬 불필요

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Step 3)
  - **Blocks**: Task 4
  - **Blocked By**: Task 2

  **References**:
  - `CHANGELOG.md:1` - 날짜 수정 대상 라인
  - `docs/PROJECT_STRUCTURE.md` - 삭제 대상
  - `docs/PROJECT-STRUCTURE.md` - **삭제하지 말 것** (유지 대상)

  **WHY Each Reference Matters**:
  - Line 1만 수정, 나머지 GitLab 참조는 의도적 유지
  - 언더스코어 버전만 삭제, 하이픈 버전 유지

  **Acceptance Criteria**:
  ```bash
  # AC1: CHANGELOG 날짜 수정됨
  grep "2.0.5.*2026-02-01" /home/jclee/dev/splunk/CHANGELOG.md
  # Assert: 1 line match

  # AC2: 이전 날짜 제거됨
  grep "2025-01-XX" /home/jclee/dev/splunk/CHANGELOG.md
  # Assert: 0 matches

  # AC3: PROJECT_STRUCTURE.md 삭제됨
  ls /home/jclee/dev/splunk/docs/PROJECT_STRUCTURE.md 2>&1
  # Assert: "No such file or directory"

  # AC4: PROJECT-STRUCTURE.md 유지됨
  ls /home/jclee/dev/splunk/docs/PROJECT-STRUCTURE.md
  # Assert: File exists

  # AC5: 의도적 GitLab 참조 유지됨
  grep -c "gitlab" /home/jclee/dev/splunk/CHANGELOG.md
  # Assert: >= 4 (Line 77, 96, 208, 210)
  ```

  **Commit**: NO (groups with Task 4)

---

- [ ] 4. 메인 레포 커밋 + 검증

  **What to do**:
  - `git status`로 변경 확인
  - `git add CHANGELOG.md`
  - `git rm docs/PROJECT_STRUCTURE.md` (이미 삭제된 경우 `git add -u`)
  - `git commit -m "docs: modernize documentation for GitHub (date fix, duplicate removal)"`
  - 전체 검증 스크립트 실행

  **Must NOT do**:
  - 다른 파일 커밋에 포함
  - `git push` 자동 실행 (사용자 확인 후)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 단순 git 커밋 + 검증
  - **Skills**: [`git-master`]
    - `git-master`: git 커밋 작업

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Step 4 - Final)
  - **Blocks**: None
  - **Blocked By**: Task 3

  **References**:
  - 이전 작업의 모든 검증 명령어

  **WHY Each Reference Matters**:
  - 최종 검증으로 모든 변경 사항 확인

  **Acceptance Criteria**:
  ```bash
  # AC1: 메인 레포 커밋 생성됨
  git -C /home/jclee/dev/splunk log -1 --oneline | grep -i "modernize\|github"
  # Assert: 1 line match

  # AC2: 메인 레포 clean 상태
  git -C /home/jclee/dev/splunk status --porcelain
  # Assert: Empty or only untracked files

  # 전체 검증
  echo "=== Final Verification ==="

  # V1: CHANGELOG
  echo "CHANGELOG date check:"
  grep "2.0.5.*2026-02-01" /home/jclee/dev/splunk/CHANGELOG.md && echo "✅ PASS" || echo "❌ FAIL"

  # V2: n8n GitLab webhook removed
  echo "n8n gitlab-ci-webhook check:"
  [ $(grep -c "gitlab-ci-webhook" /home/jclee/dev/splunk/splunk.wiki/docs/guides/05-integrations/n8n-integration.md) -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL"

  # V3: n8n GitHub webhook added
  echo "n8n github-actions-webhook check:"
  [ $(grep -c "github-actions-webhook" /home/jclee/dev/splunk/splunk.wiki/docs/guides/05-integrations/n8n-integration.md) -gt 0 ] && echo "✅ PASS" || echo "❌ FAIL"

  # V4: PROJECT_STRUCTURE.md deleted
  echo "PROJECT_STRUCTURE.md deleted check:"
  [ ! -f /home/jclee/dev/splunk/docs/PROJECT_STRUCTURE.md ] && echo "✅ PASS" || echo "❌ FAIL"

  # V5: PROJECT-STRUCTURE.md retained
  echo "PROJECT-STRUCTURE.md retained check:"
  [ -f /home/jclee/dev/splunk/docs/PROJECT-STRUCTURE.md ] && echo "✅ PASS" || echo "❌ FAIL"

  # V6: Intentional GitLab refs retained
  echo "Intentional GitLab refs check:"
  [ $(grep -c "gitlab" /home/jclee/dev/splunk/docs/DEPLOYMENT-GUIDE-GITHUB.md) -gt 0 ] && echo "✅ PASS" || echo "❌ FAIL"
  ```

  **Evidence to Capture**:
  - [ ] 전체 검증 스크립트 출력
  - [ ] `git log -1 --oneline` 양쪽 레포

  **Commit**: YES (메인 레포)
  - Message: `docs: modernize documentation for GitHub (date fix, duplicate removal)`
  - Files: `CHANGELOG.md`, `docs/PROJECT_STRUCTURE.md` (deleted)
  - Pre-commit: None (MD 파일)

---

## Commit Strategy

| After Task | Repository | Message | Files |
|------------|------------|---------|-------|
| 2 | splunk.wiki | `docs: update n8n integration guide for GitHub Actions webhooks` | n8n-integration.md |
| 4 | splunk | `docs: modernize documentation for GitHub (date fix, duplicate removal)` | CHANGELOG.md, docs/PROJECT_STRUCTURE.md (deleted) |

---

## Success Criteria

### Verification Commands
```bash
# 1. CHANGELOG 날짜
grep "2.0.5.*2026-02-01" CHANGELOG.md  # Expected: 1 match

# 2. GitLab CI 웹훅 제거
grep -c "gitlab-ci-webhook" splunk.wiki/docs/guides/05-integrations/n8n-integration.md  # Expected: 0

# 3. GitHub Actions 웹훅 추가
grep -c "github-actions-webhook" splunk.wiki/docs/guides/05-integrations/n8n-integration.md  # Expected: >= 4

# 4. 중복 파일 삭제
ls docs/PROJECT_STRUCTURE.md 2>&1  # Expected: No such file

# 5. 정상 파일 유지
ls docs/PROJECT-STRUCTURE.md  # Expected: File exists

# 6. 의도적 GitLab 참조 유지
grep -c "gitlab" docs/DEPLOYMENT-GUIDE-GITHUB.md  # Expected: > 0
```

### Final Checklist
- [ ] CHANGELOG.md 날짜가 2026-02-01로 수정됨
- [ ] n8n-integration.md에서 gitlab-ci-webhook 모두 github-actions-webhook으로 변경됨
- [ ] docs/PROJECT_STRUCTURE.md 삭제됨
- [ ] docs/PROJECT-STRUCTURE.md 유지됨
- [ ] 의도적 GitLab 참조(히스토리/마이그레이션 문서) 유지됨
- [ ] 외부 문서 링크(docs.gitlab.com) 유지됨
- [ ] Wiki 커밋 완료
- [ ] 메인 레포 커밋 완료
