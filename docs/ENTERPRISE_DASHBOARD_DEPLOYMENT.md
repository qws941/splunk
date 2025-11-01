# Splunk Dashboard Studio - Enterprise Deployment Guide

**Date**: 2025-10-25
**Target**: Production Splunk Enterprise Environment
**Approach**: Phased, Risk-Mitigated Deployment
**Source**: Splunk Lantern Best Practices + Internal Standards

---

## 🎯 Overview

이 문서는 엔터프라이즈 운영 환경에서 **Dashboard Studio JSON 파일을 안전하게 배포**하기 위한 단계별 가이드입니다.

**핵심 원칙**:
- ✅ **Layer, don't replace**: 기존 대시보드를 삭제하지 않고 우선순위로 관리
- ✅ **Phased rollout**: 테스트 → 소규모 → 전체 단계별 배포
- ✅ **Monitoring first**: 각 단계마다 헬스 체크 및 모니터링
- ✅ **Rollback ready**: 언제든지 이전 버전으로 복원 가능

---

## 📋 Phase 0: Pre-Deployment Checklist

### 1. 변경 관리 (Change Management)

**CAB 승인 요청 항목**:
```yaml
Change Request Template:
  Title: "Splunk Dashboard Studio Migration - JavaScript 제거"
  Type: Standard Change (Low Risk)
  Impact: Low (기존 기능 유지, UI 개선)
  Risk Assessment:
    - Legacy XML dashboards 유지 (rollback 가능)
    - JavaScript 의존성 제거 (보안 강화)
    - 데이터 소스 동일 (index=fw)

  Rollback Plan:
    - Legacy XML 대시보드로 즉시 복원 가능
    - 복원 시간: < 5분 (REST API delete)

  Testing Evidence:
    - ✅ JSON validation 통과 (3/3 files)
    - ✅ 개발 환경 테스트 완료
    - ✅ Query 성능 검증 완료
```

### 2. 환경 검증

```bash
# Splunk 버전 확인 (Dashboard Studio requires 9.0+)
splunk version
# Expected: Splunk Enterprise 9.0.x or higher

# 인덱스 데이터 확인
splunk search "index=fortianalyzer earliest=-1h | stats count"
# Expected: count > 0 (데이터 유입 확인)

# REST API 접근 권한 확인
curl -k -u admin:password \
  https://splunk.jclee.me:8089/services/server/info
# Expected: HTTP 200 + XML response
```

### 3. 백업 (Critical!)

```bash
# 현재 운영 중인 대시보드 백업
mkdir -p ~/splunk-dashboard-backup-$(date +%Y%m%d)

# REST API를 통한 백업
curl -k -u admin:password \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views?output_mode=json&count=-1" \
  -o ~/splunk-dashboard-backup-$(date +%Y%m%d)/current-dashboards.json

# 백업 검증
jq '.entry | length' ~/splunk-dashboard-backup-$(date +%Y%m%d)/current-dashboards.json
# Expected: 현재 대시보드 개수 (예: 30)
```

---

## 🚀 Phase 1: Test Environment Deployment (Week 1)

**목표**: 개발/테스트 환경에서 완전한 기능 검증

### Step 1.1: 테스트 환경 배포

```bash
# Test Splunk instance (예: splunk-test.jclee.me:8089)
TEST_HOST="splunk-test.jclee.me"
TEST_USER="admin"

# 1개 대시보드만 먼저 배포 (가장 단순한 것)
curl -k -u $TEST_USER:password \
  -H "Content-Type: application/json" \
  -d @configs/dashboards/studio-production/01-fortigate-operations.json \
  https://$TEST_HOST:8089/servicesNS/nobody/search/data/ui/views

# 배포 확인
curl -k -u $TEST_USER:password \
  "https://$TEST_HOST:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations?output_mode=json"
```

### Step 1.2: 기능 검증

**테스트 체크리스트**:
```
[ ] Dashboard 로딩 시간 < 5초
[ ] 모든 패널에 데이터 표시됨
[ ] 시간 범위 선택기 동작 확인
[ ] Auto-refresh (30s) 동작 확인
[ ] Single Value sparkline 표시 확인
[ ] Table sorting/filtering 동작
[ ] 브라우저 JavaScript 비활성화 상태에서도 동작
[ ] 모바일 브라우저 (Chrome Android) 동작 확인
```

### Step 1.3: 성능 모니터링

```spl
# 대시보드 쿼리 성능 측정 (1주일)
index=_internal source=*metrics.log component=Dispatch
  dashboard="fortigate_operations" earliest=-7d
| stats avg(elapsed_ms) as avg_time_ms,
        max(elapsed_ms) as max_time_ms,
        p95(elapsed_ms) as p95_time_ms
| eval avg_time_sec=round(avg_time_ms/1000, 2),
       max_time_sec=round(max_time_ms/1000, 2),
       p95_time_sec=round(p95_time_ms/1000, 2)

# Target: avg < 3s, p95 < 10s, max < 30s
```

**Week 1 종료 시점 기준**:
- ✅ 모든 기능 테스트 통과
- ✅ 성능 기준 충족 (avg < 3s)
- ✅ 1주일간 에러 없음

---

## 🎯 Phase 2: Pilot Deployment (Week 2)

**목표**: 소규모 사용자 그룹(5-10명)에게 먼저 공개

### Step 2.1: Pilot Group 선정

```yaml
Pilot Users:
  - Security Team Lead (1명)
  - SOC Analyst (2-3명)
  - Network Engineer (1-2명)
  - IT Manager (1명)

Criteria:
  - Splunk 사용 경험 많음
  - 피드백 제공 가능
  - 업무 영향 적음 (Legacy 대시보드 병행 사용 가능)
```

### Step 2.2: Production 배포 (Pilot만 접근)

```bash
# Production에 배포하되, 특정 App에만 배포
PROD_HOST="splunk.jclee.me"
APP_NAME="search"  # 또는 pilot 전용 app 생성

# 3개 Studio 대시보드 모두 배포
for dashboard in configs/dashboards/studio-production/*.json; do
  dashboard_name=$(basename "$dashboard" .json)

  echo "Deploying: $dashboard_name"
  curl -k -u admin:password \
    -H "Content-Type: application/json" \
    -d @"$dashboard" \
    "https://$PROD_HOST:8089/servicesNS/nobody/$APP_NAME/data/ui/views"

  sleep 2  # API rate limiting 방지
done
```

### Step 2.3: 접근 권한 설정 (Pilot만)

```bash
# Dashboard 권한 설정: Pilot 그룹만 읽기 가능
# Splunk Web UI: Settings → User Interface → Views → Permissions

# 또는 REST API:
curl -k -u admin:password -X POST \
  -d "perms.read=pilot_group" \
  -d "perms.write=admin" \
  -d "sharing=app" \
  "https://$PROD_HOST:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations/acl"
```

### Step 2.4: Pilot 피드백 수집

**피드백 양식** (Slack 또는 Jira):
```markdown
## Dashboard Studio Pilot 피드백

**Dashboard**: [fortigate_operations / faz_fmg_monitoring / slack_alert_control]
**Date**: YYYY-MM-DD

### 1. 성능
- [ ] 로딩 속도 만족
- [ ] 데이터 업데이트 속도 만족
- [ ] 브라우저 성능 문제 없음

### 2. 사용성
- [ ] UI/UX 직관적
- [ ] 필요한 정보 모두 표시
- [ ] Legacy 대비 개선점: __________

### 3. 문제점
- 발견된 버그: __________
- 누락된 기능: __________
- 개선 제안: __________

### 4. 종합 평가
- [ ] 전체 팀 배포 가능 (Go)
- [ ] 수정 후 재검토 필요 (Hold)
- [ ] Legacy 유지 필요 (No-Go)
```

**Week 2 종료 시점 기준**:
- ✅ Pilot 5명 이상 피드백 수집
- ✅ 80% 이상 "Go" 평가
- ✅ Critical 버그 없음
- ✅ 성능 저하 없음

---

## 🌐 Phase 3: Full Production Deployment (Week 3)

**목표**: 전체 사용자에게 Studio 대시보드 공개

### Step 3.1: 전체 배포 준비

```bash
# 1. Legacy XML 대시보드 이름 변경 (삭제 아님!)
# Splunk Web UI: Settings → User Interface → Views
# fortigate_operations → fortigate_operations_legacy
# faz_fmg_monitoring → faz_fmg_monitoring_legacy
# slack_control → slack_control_legacy

# 2. Studio 대시보드 권한 변경 (전체 읽기)
curl -k -u admin:password -X POST \
  -d "perms.read=*" \
  -d "sharing=app" \
  "https://$PROD_HOST:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations/acl"

# 3. Dashboard 목록에 Studio 버전 우선 표시
# Dashboard Studio 대시보드는 자동으로 상단 표시됨
```

### Step 3.2: 사용자 공지

**공지 템플릿** (Slack #splunk-users):
```markdown
📊 **Splunk Dashboard 업그레이드 안내**

**변경일**: 2025-10-XX (수) 오후 2시
**영향**: FortiGate / FAZ/FMG / Slack Alert 대시보드

✨ **개선 사항**:
- ✅ JavaScript 제거 (보안 강화)
- ✅ 로딩 속도 개선 (30% 빠름)
- ✅ 모바일 반응형 지원
- ✅ 자동 새로고침 (30초)

📌 **사용 방법**:
1. Dashboards → "FortiGate Operations" 클릭
2. 기존과 동일한 기능 제공
3. 문제 발생 시 Legacy 버전 사용 가능 (이름에 "_legacy" 붙음)

🆘 **문제 발생 시**: #splunk-support 또는 jclee@example.com

**테스트 결과**: Pilot 10명, 2주 무장애 운영 ✅
```

### Step 3.3: 배포 당일 모니터링

```bash
# Real-time 대시보드 사용 모니터링
watch -n 10 "curl -k -s -u admin:password \
  'https://splunk.jclee.me:8089/services/server/introspection/search/dispatch?output_mode=json' \
  | jq '.entry[] | select(.content.label | contains(\"fortigate\")) | {user: .content.author, dashboard: .content.label, status: .content.dispatchState}'"

# 에러 로그 모니터링
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep -i "dashboard\|view\|error"

# 성능 모니터링 (30분 간격 체크)
splunk search 'index=_internal source=*metrics.log component=Dispatch dashboard="fortigate_operations" earliest=-30m
| stats avg(elapsed_ms) as avg_ms, count'
```

**배포 당일 Rollback 기준**:
- ❌ 에러율 > 5%
- ❌ 평균 로딩 시간 > 10초
- ❌ 사용자 불만 3건 이상
- ❌ 데이터 표시 안 됨

→ **즉시 Legacy 대시보드로 복원**

---

## 🔄 Phase 4: Post-Deployment (Week 4+)

### Step 4.1: 1주일 모니터링

```spl
# 대시보드 사용 통계 (Week 1)
index=_audit action=view object_type=dashboard earliest=-7d
| stats count as views, dc(user) as unique_users by object
| where object LIKE "%fortigate%" OR object LIKE "%faz%" OR object LIKE "%slack%"
| sort -views

# 에러율 확인
index=_internal source=*splunkd.log earliest=-7d
  (dashboard="fortigate_operations" OR dashboard="faz_fmg_monitoring" OR dashboard="slack_alert_control")
  (ERROR OR WARN)
| stats count by log_level, message
```

### Step 4.2: Legacy 대시보드 제거 계획

**제거 조건** (모두 충족 시):
- ✅ 4주간 무장애 운영
- ✅ Studio 대시보드 사용률 > 95%
- ✅ Legacy 대시보드 사용 < 5회/주
- ✅ 사용자 피드백 긍정적 (만족도 > 80%)

**제거 절차**:
```bash
# 1. Legacy 대시보드 숨김 처리 (삭제 아님, 2주 대기)
curl -k -u admin:password -X POST \
  -d "perms.read=admin" \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations_legacy/acl"

# 2. 2주 후 문제 없으면 최종 삭제
curl -k -u admin:password -X DELETE \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations_legacy"
```

### Step 4.3: 문서화 업데이트

**Wiki 업데이트 항목**:
- [ ] 운영 가이드: Studio 대시보드 사용법 추가
- [ ] Troubleshooting: FAQ 추가
- [ ] 아키텍처 문서: JavaScript 제거 내용 반영
- [ ] 교육 자료: 신규 대시보드 스크린샷 업데이트

---

## 🚨 Rollback Procedures

### Emergency Rollback (< 5분)

```bash
# 1. Studio 대시보드 즉시 숨김
for dashboard in fortigate_operations faz_fmg_monitoring slack_alert_control; do
  curl -k -u admin:password -X POST \
    -d "perms.read=admin" \
    "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/$dashboard/acl"
done

# 2. Legacy 대시보드 권한 복원
for dashboard_legacy in fortigate_operations_legacy faz_fmg_monitoring_legacy slack_control_legacy; do
  curl -k -u admin:password -X POST \
    -d "perms.read=*" \
    "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/$dashboard_legacy/acl"
done

# 3. 사용자 공지
echo "🚨 ALERT: Studio 대시보드 일시 중단, Legacy 대시보드 사용 바랍니다." | \
  slack-cli post #splunk-users
```

### Planned Rollback (문제 발견 시)

```bash
# 1. Incident 티켓 생성
# 2. 근본 원인 분석
# 3. 수정 후 Phase 1부터 재시작
```

---

## 📊 Success Metrics (KPI)

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Dashboard Load Time | < 3s avg | `index=_internal source=*metrics.log` |
| Query Performance | < 10s p95 | `component=Dispatch` |
| Error Rate | < 1% | `index=_internal ERROR dashboard=*` |
| Uptime | > 99.9% | Monitoring Console |

### Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| User Adoption | > 90% | `index=_audit action=view` |
| User Satisfaction | > 80% | Survey |
| Support Tickets | < 5/month | JIRA |
| Security Compliance | 100% | No JavaScript execution |

---

## 📚 References

**Splunk Official Documentation**:
- [Managing Enterprise Deployment - Splunk Lantern](https://lantern.splunk.com/Splunk_Platform/Getting_Started/Managing_your_Enterprise_deployment)
- [Setting up Deployment Server - Splunk Lantern](https://lantern.splunk.com/Splunk_Platform/Product_Tips/Administration/Setting_up_deployment_server_apps_for_the_enterprise_environment)
- [Dashboard Studio Guide - Splunk Docs](https://docs.splunk.com/Documentation/Splunk/latest/DashStudio)

**Internal Documentation**:
- `docs/DASHBOARD_MIGRATION_GUIDE.md` - Technical migration details
- `configs/dashboards/DASHBOARD_SUMMARY.md` - Dashboard cleanup summary
- `configs/dashboards/README.md` - Dashboard reference guide

---

**Prepared by**: JC Lee
**Approved by**: [SOC Manager Name]
**Reviewed by**: [IT Security Team]
**Version**: 1.0
**Last Updated**: 2025-10-25
**Next Review**: 2025-11-25 (또는 Phase 4 완료 후)
