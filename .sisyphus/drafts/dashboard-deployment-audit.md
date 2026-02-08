# Draft: Splunk Dashboard Deployment Audit

## Requirements (confirmed)

### User Request
- "splunk 대시보드 구성 점검 및 배포현황" (Splunk dashboard configuration check and deployment status)

### Critical Finding: Navigation References Missing Dashboards
The `default.xml` nav file references dashboards that **DO NOT EXIST** in tarball or server:

```xml
<view name="fortigate_comprehensive_alerts" />  <!-- ❌ MISSING -->
<view name="security_dashboard_simple" />        <!-- ❌ MISSING -->
<view name="slack_test_dashboard" />             <!-- ✅ EXISTS -->
```

## Research Findings

### 1. Dashboard Files in configs/dashboards/ (Local Project)

| File | Type | Nav Reference | In Tarball |
|------|------|---------------|------------|
| `fortigate-comprehensive-alerts.json` | Dashboard Studio | YES (`fortigate_comprehensive_alerts`) | ❌ NO |
| `security-dashboard-simple.json` | Dashboard Studio | YES (`security_dashboard_simple`) | ❌ NO |
| `slack-test-dashboard.json` | Dashboard Studio | NO (XML version used) | ❌ NO |
| `alert-testing-dashboard.xml` | Classic XML | NO | ❌ NO |
| `slack-alert-control.xml` | Classic XML | NO | ❌ NO |
| `fortigate-alerts-monitoring.xml` | Classic XML | NO | ❌ NO |
| `fortigate-monitoring.xml` | Classic XML | NO | ❌ NO |
| `fortigate-production-alerts-dashboard.xml` | Classic XML | NO | ❌ NO |
| `security-alert-monitoring.xml` | Classic XML | NO | ❌ NO |

### 2. Tarball Contents (security_alert/default/data/ui/views/)
- `slack_test_dashboard.xml` — **ONLY 1 FILE**

### 3. Deployment Scripts Analysis (from explore agent)

| Script | Method | Status | Recommended |
|--------|--------|--------|-------------|
| `deploy-dashboards-api.sh` | REST API + XML wrapper | **CURRENT** (2026-02-04) | ✅ For Studio JSON |
| `deploy-current-dashboards.js` | REST API | Comprehensive (2026-02-01) | ✅ For mixed XML/JSON |
| `deploy-dashboard-studio.py` | docker cp + reload | Legacy fallback | ⚠️ Slow |
| `deploy-dashboards.js` | REST API | **DEPRECATED** (missing target dir) | ❌ |

### 4. Server Status (LXC 150 - from user context)

| Location | Files |
|----------|-------|
| default/data/ui/views/ | `slack_test_dashboard.xml` (1 file) |
| local/data/ui/views/ | `slack_test_dashboard.xml`, `slack_test_dashboard_v2.xml` |

## Technical Decisions

### Dashboard Naming Convention
- Nav references use **underscores**: `fortigate_comprehensive_alerts`
- File names use **hyphens**: `fortigate-comprehensive-alerts.json`
- Deployment scripts convert: `tr '-' '_'` (see line 31 of deploy-dashboards-api.sh)

### Dashboard Format Strategy
- **Dashboard Studio (JSON)**: Preferred for complex visualizations
  - Requires XML wrapper for REST API deployment
  - Cannot be directly included in tarball (needs API deployment)
- **Classic XML**: Simpler, can be included in tarball
  - No special handling needed
  - Works with `<view name="X"/>` references

## Gap Analysis

### Problem 1: Nav References Non-Existent Dashboards
- `fortigate_comprehensive_alerts` → MISSING
- `security_dashboard_simple` → MISSING
- Result: **Broken UI** - users see empty/error entries in navigation

### Problem 2: Dashboard Files Not in Tarball
- All dashboards in `configs/dashboards/` are orphaned
- Only `slack_test_dashboard.xml` is packaged

### Problem 3: Deployment Script Confusion
- 5 different deployment scripts with overlapping purposes
- No clear "canonical" deployment method documented

## Decisions Made

1. **Deployment scope**: ALL 8 dashboards in configs/dashboards/
2. **Deployment method**: REST API deployment (not tarball)
3. **XML handling**: Extend deploy script to handle both JSON and XML
4. **Nav update**: Update default.xml to include all deployed dashboards
5. **Password**: Use `Splunk@150!` (from supermemory), not `admin123` in script

## Scope Boundaries

### INCLUDE
- Audit dashboard deployment status
- Identify nav→dashboard mismatches
- Fix deployment configuration
- Verify dashboards work in Splunk UI
- Document deployment process

### EXCLUDE
- Creating new dashboards from scratch
- Modifying dashboard content/visualizations
- FAZ/FMG integration changes
- Alert configuration changes

---

*Last Updated: 2026-02-04*
*Status: Gathering additional research from background agents*
