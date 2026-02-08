# Splunk Dashboard Deployment Remediation

## TL;DR

> **Quick Summary**: Fix broken Splunk navigation by deploying all 8 dashboards from configs/dashboards/ to Splunk server via REST API, and update nav to include all dashboards.
> 
> **Deliverables**:
> - Extended `deploy-dashboards-api.sh` to handle both JSON and XML formats
> - All 8 dashboards deployed to Splunk (LXC 150)
> - Updated `default.xml` nav with all dashboard references
> - Verification that all dashboards load in Splunk UI
> 
> **Estimated Effort**: Medium (2-4 hours)
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4 → Task 5

---

## Context

### Original Request
사용자 요청: "splunk 대시보드 구성 점검 및 배포현황" (Splunk dashboard configuration check and deployment status)

### Interview Summary
**Key Discussions**:
- Nav references 3 dashboards but only 1 is deployed → **Broken UI**
- 8 dashboard files exist in configs/dashboards/ (3 JSON + 5 XML)
- User chose: Deploy ALL 8 via REST API, update nav

**Research Findings**:
- Dashboard Studio JSON requires XML wrapper (`<dashboard version="2">`)
- File names use hyphens, nav references use underscores (script converts)
- `deploy-dashboards-api.sh` only handles JSON (needs extension for XML)
- Password in script is wrong (`admin123` → should be `Splunk@150!`)

### Metis Review
**Identified Gaps** (addressed):
- Script only handles JSON → Plan includes XML support
- Password mismatch → Plan includes password fix
- Nav doesn't reference XML dashboards → Plan includes nav update
- SSH connectivity issues → Use REST API for verification, Playwright for UI

---

## Work Objectives

### Core Objective
Deploy all 8 dashboards from configs/dashboards/ to Splunk server and update navigation to expose them in the UI.

### Concrete Deliverables
1. Extended `scripts/deploy-dashboards-api.sh` supporting JSON + XML
2. 8 dashboards deployed to `security_alert` app on LXC 150
3. Updated `security_alert/default/data/ui/nav/default.xml`
4. Deployment documentation in AGENTS.md or README

### Definition of Done
- [ ] `curl` REST API returns HTTP 200 for all 8 dashboard endpoints
- [ ] Playwright browser test loads each dashboard without error
- [ ] Nav menu shows all 8 dashboards in correct collections

### Must Have
- All 8 dashboards accessible via Splunk UI
- No broken nav references
- Deployment repeatable via script

### Must NOT Have (Guardrails)
- ❌ Do NOT modify dashboard content/queries
- ❌ Do NOT create new dashboards (deploy existing only)
- ❌ Do NOT modify alert configurations
- ❌ Do NOT add excessive error handling beyond basic curl checks
- ❌ Do NOT backup dashboards (out of scope)
- ❌ Do NOT deploy to OPS server (air-gapped, different process)

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.
> The executing agent will directly verify each deliverable.

### Test Decision
- **Infrastructure exists**: N/A (shell/API verification)
- **Automated tests**: NO (not applicable for deployment tasks)
- **Framework**: Bash (curl) + Playwright

### Agent-Executed QA Scenarios (MANDATORY)

**Verification Tool by Deliverable Type:**

| Type | Tool | How Agent Verifies |
|------|------|-------------------|
| REST API Response | Bash (curl) | Send request, parse JSON, assert fields |
| Dashboard UI Load | Playwright | Navigate, wait for elements, screenshot |
| Nav Menu Display | Playwright | Check navigation structure |

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
├── Task 1: Extend deploy-dashboards-api.sh [no dependencies]
└── Task 2: Prepare nav update [no dependencies]

Wave 2 (After Wave 1):
├── Task 3: Deploy all dashboards [depends: 1]
└── Task 4: Update nav and deploy [depends: 2]

Wave 3 (After Wave 2):
└── Task 5: Verify all dashboards [depends: 3, 4]
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 3 | 2 |
| 2 | None | 4 | 1 |
| 3 | 1 | 5 | 4 |
| 4 | 2 | 5 | 3 |
| 5 | 3, 4 | None | None (final) |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1, 2 | `quick` category - simple script edits |
| 2 | 3, 4 | `quick` category - deployment execution |
| 3 | 5 | Playwright skill for browser verification |

---

## TODOs

- [ ] 1. Extend deploy-dashboards-api.sh to support XML files

  **What to do**:
  - Add a second loop to process `*.xml` files in addition to `*.json`
  - For XML files: POST directly without wrapper (already in correct format)
  - Fix hardcoded password: change `admin123` to use environment variable `SPLUNK_PASS`
  - Ensure dashboard ID conversion: `tr '-' '_'` applies to XML files too

  **Must NOT do**:
  - Do NOT change existing JSON handling logic
  - Do NOT add complex error handling beyond what exists
  - Do NOT modify dashboard content

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple script modification, single file change
  - **Skills**: [`git-master`]
    - `git-master`: For atomic commit after changes

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: Task 3
  - **Blocked By**: None

  **References**:
  - `scripts/deploy-dashboards-api.sh:1-80` - Current implementation to extend
  - `scripts/deploy-dashboards-api.sh:29-36` - deploy_dashboard function signature
  - `scripts/deploy-dashboards-api.sh:129` - JSON loop to duplicate for XML

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Script handles both JSON and XML files
    Tool: Bash
    Preconditions: Script modified with XML support
    Steps:
      1. Run: grep -c "\.xml" scripts/deploy-dashboards-api.sh
      2. Assert: Output > 0 (XML handling code exists)
      3. Run: grep -c "\.json" scripts/deploy-dashboards-api.sh
      4. Assert: Output > 0 (JSON handling still exists)
      5. Run: grep "SPLUNK_PASS" scripts/deploy-dashboards-api.sh
      6. Assert: Output contains SPLUNK_PASS (env var used)
    Expected Result: Script contains both JSON and XML processing
    Evidence: grep outputs captured

  Scenario: Script syntax is valid
    Tool: Bash
    Preconditions: Script modified
    Steps:
      1. Run: bash -n scripts/deploy-dashboards-api.sh
      2. Assert: Exit code 0
    Expected Result: No syntax errors
    Evidence: Exit code captured
  ```

  **Commit**: YES
  - Message: `feat(scripts): extend deploy-dashboards-api.sh to support XML dashboards`
  - Files: `scripts/deploy-dashboards-api.sh`
  - Pre-commit: `bash -n scripts/deploy-dashboards-api.sh`

---

- [ ] 2. Prepare updated nav file with all 8 dashboards

  **What to do**:
  - Edit `security_alert/default/data/ui/nav/default.xml`
  - Add nav references for all 8 dashboards
  - Organize into logical collections (Operations, Alerts, Testing, etc.)
  - Use underscore naming convention (matching dashboard IDs)

  **Dashboard to Nav mapping:**
  | Dashboard File | Nav ID | Suggested Collection |
  |---------------|--------|---------------------|
  | fortigate-comprehensive-alerts.json | fortigate_comprehensive_alerts | Dashboards |
  | security-dashboard-simple.json | security_dashboard_simple | Dashboards |
  | slack-test-dashboard.json | slack_test_dashboard | Testing |
  | alert-testing-dashboard.xml | alert_testing_dashboard | Testing |
  | fortigate-alerts-monitoring.xml | fortigate_alerts_monitoring | Monitoring |
  | fortigate-monitoring.xml | fortigate_monitoring | Monitoring |
  | fortigate-production-alerts-dashboard.xml | fortigate_production_alerts_dashboard | Dashboards |
  | security-alert-monitoring.xml | security_alert_monitoring | Monitoring |
  | slack-alert-control.xml | slack_alert_control | Testing |

  **Must NOT do**:
  - Do NOT remove existing `search` view reference
  - Do NOT change nav color or theme

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple XML edit, clear structure
  - **Skills**: [`git-master`]
    - `git-master`: For atomic commit

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Task 4
  - **Blocked By**: None

  **References**:
  - `security_alert/default/data/ui/nav/default.xml` - Current nav (only 3 views)

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Nav contains all 8 dashboard references
    Tool: Bash
    Preconditions: Nav file updated
    Steps:
      1. Run: grep -c '<view name=' security_alert/default/data/ui/nav/default.xml
      2. Assert: Output >= 9 (8 dashboards + search)
      3. Run: grep 'fortigate_comprehensive_alerts' default.xml
      4. Assert: Match found
      5. Run: grep 'security_dashboard_simple' default.xml
      6. Assert: Match found
      7. Run: grep 'fortigate_monitoring' default.xml
      8. Assert: Match found
    Expected Result: All dashboards referenced in nav
    Evidence: grep outputs captured

  Scenario: Nav XML is valid
    Tool: Bash
    Preconditions: Nav file updated
    Steps:
      1. Run: python3 -c "import xml.etree.ElementTree as ET; ET.parse('security_alert/default/data/ui/nav/default.xml')"
      2. Assert: Exit code 0
    Expected Result: Valid XML syntax
    Evidence: Exit code captured
  ```

  **Commit**: YES
  - Message: `feat(nav): add all 8 dashboards to navigation menu`
  - Files: `security_alert/default/data/ui/nav/default.xml`
  - Pre-commit: `python3 -c "import xml.etree.ElementTree as ET; ET.parse('security_alert/default/data/ui/nav/default.xml')"`

---

- [ ] 3. Deploy all 8 dashboards via REST API

  **What to do**:
  - Run extended `deploy-dashboards-api.sh` with correct credentials
  - Set environment: `SPLUNK_PASS=Splunk@150!`
  - Monitor output for success/failure of each dashboard
  - Retry any failures

  **Must NOT do**:
  - Do NOT use SSH to deploy (REST API only)
  - Do NOT deploy to any server other than 192.168.50.150

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Script execution, single command
  - **Skills**: []
    - No special skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 4)
  - **Blocks**: Task 5
  - **Blocked By**: Task 1

  **References**:
  - `scripts/deploy-dashboards-api.sh` - Deployment script (after Task 1)
  - Supermemory: Password is `Splunk@150!`, server is `192.168.50.150:8089`

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: All 8 dashboards exist via REST API
    Tool: Bash (curl)
    Preconditions: Deployment script ran
    Steps:
      1. For each dashboard in [fortigate_comprehensive_alerts, security_dashboard_simple, slack_test_dashboard, alert_testing_dashboard, fortigate_alerts_monitoring, fortigate_monitoring, fortigate_production_alerts_dashboard, security_alert_monitoring, slack_alert_control]:
         a. curl -s -k -u "admin:Splunk@150!" \
              "https://192.168.50.150:8089/servicesNS/nobody/security_alert/data/ui/views/{name}?output_mode=json"
         b. Assert: HTTP 200 and response contains "name":"{name}"
    Expected Result: All 8 dashboards return valid responses
    Evidence: Response bodies saved to .sisyphus/evidence/

  Scenario: Dashboard count increased
    Tool: Bash (curl)
    Preconditions: Deployment complete
    Steps:
      1. curl -s -k -u "admin:Splunk@150!" \
           "https://192.168.50.150:8089/servicesNS/nobody/security_alert/data/ui/views?output_mode=json&count=0" \
           | jq '.entry | length'
      2. Assert: Output >= 8
    Expected Result: At least 8 dashboards deployed
    Evidence: Count value captured
  ```

  **Commit**: NO (deployment action, no code changes)

---

- [ ] 4. Deploy updated nav file to Splunk

  **What to do**:
  - Copy updated nav file to Splunk container via REST API or docker cp
  - Reload Splunk app to pick up nav changes
  - Verify nav appears correctly

  **Deploy command (REST API method):**
  ```bash
  # Read nav file content
  NAV_CONTENT=$(cat security_alert/default/data/ui/nav/default.xml)
  
  # POST to Splunk
  curl -s -k -u "admin:Splunk@150!" \
    -X POST \
    --data-urlencode "eai:data=${NAV_CONTENT}" \
    "https://192.168.50.150:8089/servicesNS/nobody/security_alert/data/ui/nav/default"
  ```

  **Alternative (docker cp method via SSH hop):**
  ```bash
  # From Rocky Linux dev machine
  ssh -p 1111 root@192.168.50.150 \
    "docker cp /tmp/default.xml splunk:/opt/splunk/etc/apps/security_alert/default/data/ui/nav/default.xml"
  ```

  **Must NOT do**:
  - Do NOT modify local/ directory (changes go to default/)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single deployment command
  - **Skills**: []
    - No special skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 3)
  - **Blocks**: Task 5
  - **Blocked By**: Task 2

  **References**:
  - `security_alert/default/data/ui/nav/default.xml` - Source file
  - Supermemory: Docker container name is `splunk`

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Nav file exists on server
    Tool: Bash (curl)
    Preconditions: Nav deployed
    Steps:
      1. curl -s -k -u "admin:Splunk@150!" \
           "https://192.168.50.150:8089/servicesNS/nobody/security_alert/data/ui/nav/default?output_mode=json"
      2. Assert: HTTP 200
      3. Assert: Response contains "fortigate_comprehensive_alerts"
    Expected Result: Nav deployed with all references
    Evidence: Response body saved
  ```

  **Commit**: NO (deployment action, no new code changes)

---

- [ ] 5. Verify all dashboards load in Splunk UI

  **What to do**:
  - Use Playwright to navigate to each dashboard URL
  - Verify page loads without error
  - Take screenshots as evidence
  - Check nav menu displays all dashboards

  **Dashboard URLs to verify:**
  - http://192.168.50.150:8000/en-US/app/security_alert/fortigate_comprehensive_alerts
  - http://192.168.50.150:8000/en-US/app/security_alert/security_dashboard_simple
  - http://192.168.50.150:8000/en-US/app/security_alert/slack_test_dashboard
  - http://192.168.50.150:8000/en-US/app/security_alert/alert_testing_dashboard
  - http://192.168.50.150:8000/en-US/app/security_alert/fortigate_alerts_monitoring
  - http://192.168.50.150:8000/en-US/app/security_alert/fortigate_monitoring
  - http://192.168.50.150:8000/en-US/app/security_alert/fortigate_production_alerts_dashboard
  - http://192.168.50.150:8000/en-US/app/security_alert/security_alert_monitoring
  - http://192.168.50.150:8000/en-US/app/security_alert/slack_alert_control

  **Must NOT do**:
  - Do NOT modify any dashboard settings during verification
  - Do NOT save dashboard state changes

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Browser UI verification task
  - **Skills**: [`playwright`]
    - `playwright`: Required for browser automation

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (Sequential, final)
  - **Blocks**: None (final task)
  - **Blocked By**: Task 3, Task 4

  **References**:
  - Supermemory: Splunk URL is http://192.168.50.150:8000, login admin/Splunk@150!

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Login to Splunk
    Tool: Playwright
    Preconditions: Splunk running on 192.168.50.150:8000
    Steps:
      1. Navigate to: http://192.168.50.150:8000
      2. Wait for: login form visible
      3. Fill: input[name="username"] → "admin"
      4. Fill: input[name="password"] → "Splunk@150!"
      5. Click: input[type="submit"] or button with "Sign In"
      6. Wait for: dashboard or home page (timeout: 30s)
      7. Assert: URL contains /app/ or /en-US/
    Expected Result: Successfully logged in
    Evidence: .sisyphus/evidence/task-5-login.png

  Scenario: Each dashboard loads (repeat for all 9)
    Tool: Playwright
    Preconditions: Logged in to Splunk
    Steps:
      1. Navigate to: http://192.168.50.150:8000/en-US/app/security_alert/{dashboard_id}
      2. Wait for: .dashboard-header, .dashboard-body, or [data-view="dashboard"] (timeout: 30s)
      3. Assert: No "Page not found" or "Error" text visible
      4. Assert: No JavaScript console errors with "Error" level
      5. Screenshot: .sisyphus/evidence/task-5-{dashboard_id}.png
    Expected Result: Dashboard renders without errors
    Evidence: Screenshot saved

  Scenario: Nav menu shows all dashboards
    Tool: Playwright
    Preconditions: Logged in, on any security_alert page
    Steps:
      1. Click: nav menu or app navigation
      2. Wait for: menu dropdown/panel visible
      3. Assert: "Dashboards" collection visible
      4. Assert: Text "FortiGate Comprehensive Alerts" visible in nav
      5. Assert: Text "Security Dashboard Simple" visible in nav
      6. Screenshot: .sisyphus/evidence/task-5-nav-menu.png
    Expected Result: Nav menu shows all dashboard entries
    Evidence: Screenshot saved
  ```

  **Commit**: NO (verification only, no code changes)

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat(scripts): extend deploy-dashboards-api.sh to support XML dashboards` | scripts/deploy-dashboards-api.sh | `bash -n scripts/deploy-dashboards-api.sh` |
| 2 | `feat(nav): add all 8 dashboards to navigation menu` | security_alert/default/data/ui/nav/default.xml | XML parse check |

---

## Success Criteria

### Verification Commands
```bash
# Check dashboards via REST API
for name in fortigate_comprehensive_alerts security_dashboard_simple slack_test_dashboard \
            alert_testing_dashboard fortigate_alerts_monitoring fortigate_monitoring \
            fortigate_production_alerts_dashboard security_alert_monitoring slack_alert_control; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -k -u "admin:Splunk@150!" \
    "https://192.168.50.150:8089/servicesNS/nobody/security_alert/data/ui/views/${name}")
  echo "${name}: ${STATUS}"
done
# Expected: All return 200

# Count dashboards
curl -s -k -u "admin:Splunk@150!" \
  "https://192.168.50.150:8089/servicesNS/nobody/security_alert/data/ui/views?output_mode=json&count=0" \
  | jq '.entry | length'
# Expected: >= 9 (8 new + possibly existing)
```

### Final Checklist
- [ ] All 8 dashboards return HTTP 200 from REST API
- [ ] All 8 dashboards load in browser without errors
- [ ] Nav menu displays all dashboards in correct collections
- [ ] No regression: `slack_test_dashboard` still works
- [ ] Deploy script supports both JSON and XML
- [ ] Commits created with proper messages

---

## Rollback Plan

If deployment causes issues:

```bash
# Remove deployed dashboards via REST API
for name in <problematic_dashboard>; do
  curl -s -k -u "admin:Splunk@150!" -X DELETE \
    "https://192.168.50.150:8089/servicesNS/nobody/security_alert/data/ui/views/${name}"
done

# Revert nav to original
git checkout HEAD~1 -- security_alert/default/data/ui/nav/default.xml
# Re-deploy original nav
```

---

*Plan Generated: 2026-02-04*
*Author: Prometheus*
