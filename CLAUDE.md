# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**FortiAnalyzer → Splunk HEC Integration with Advanced Correlation Engine**

Multi-phase security event processing system that collects FortiAnalyzer events, performs correlation analysis, automates threat response, and sends Slack notifications.

### System Flow
```
FortiAnalyzer (보안 이벤트 수집)
    ↓
Security Event Processor (위험도 분석, 상관관계 엔진)
    ├─ Multi-Factor Threat Score (abuse + geo + login + frequency)
    ├─ Repeated High-Risk Events (tstats on risk_score > 70)
    ├─ Weak Signal Combination (5 indicators)
    ├─ Geo + Attack Pattern (high-risk countries)
    ├─ Time-Based Anomaly (Z-score > 3)
    └─ Cross-Event Type Correlation (APT detection)
    ↓
├─→ Splunk HEC (fortigate_security 인덱스)
│   └─ Data Model Acceleration (Fortinet_Security)
│       └─ Summary Indexing (summary_fw)
└─→ Automated Response
    ├─ FortiGate API (IP 차단, score ≥ 90)
    └─ Slack (알림, score 80-89 또는 특정 패턴)
```

---

## 🏗️ Architecture (Domain-Driven Design Level 3)

### Entry Points (2가지 배포 옵션)

**1. `index.js` - Local/Docker 실행**
- Node.js 직접 실행: `npm start`
- HTTP 서버 (Health/Metrics endpoints)
- PM2 프로세스 관리 지원

**2. `src/worker.js` - Cloudflare Workers (권장 프로덕션)**
- 서버리스 배포: `npm run deploy:worker`
- Cron Trigger (매 1분 자동 실행)
- 글로벌 엣지 네트워크

### Core Domains

**`domains/integration/`** - 외부 시스템 연동
- `fortianalyzer-direct-connector.js` - FAZ REST API 클라이언트 (JSON-RPC)
- `splunk-api-connector.js` - Splunk HEC 클라이언트
- `splunk-rest-client.js` - Splunk REST API (대시보드 배포)
- `slack-connector.js` - Slack Bot API
- `splunk-queries.js` - 29개 프로덕션 SPL 쿼리
- `splunk-dashboards.js` - 4개 대시보드 템플릿

**`domains/security/`** - 보안 이벤트 처리 (핵심 도메인)
- `security-event-processor.js`
  - 이벤트 분석: severity, risk_score, event_type 분류
  - 알림 트리거: `shouldAlert()` 조건 평가
  - 상관관계 분석: `correlateEvent()` 다중 이벤트 연관
  - 배치 처리: `processEventBatch()` 큐 기반 처리 (5초마다)

**`domains/defense/`** - 안정성 패턴
- `circuit-breaker.js`
  - 상태: CLOSED → OPEN → HALF_OPEN
  - 장애 임계값: 5번 실패 시 OPEN
  - 복구 타임아웃: 60초

### Configuration Files (`configs/`)

| File | Purpose | Phase |
|------|---------|-------|
| `correlation-rules.conf` | 6개 상관관계 규칙 (19KB) | 4.1 |
| `datamodels.conf` | Fortinet_Security 데이터 모델 | 3.3 |
| `savedsearches-acceleration.conf` | Summary indexing, baselines | 3.3 |
| `savedsearches-auto-block.conf` | 자동 차단 규칙 (3개 searches) | 3.2 |

### Dashboards (`dashboards/`, `configs/dashboards/`)

| Dashboard | Panels | Phase | Key Features |
|-----------|--------|-------|--------------|
| `fortinet-dashboard.xml` | 28 | 1-2 | 기본 FortiGate 보안 대시보드 |
| `threat-intelligence-panels.xml` | 9 | 3.1 | AbuseIPDB, VirusTotal 통합 |
| `automated-response-panels.xml` | 10 | 3.2 | 자동 차단 현황, 감사 추적 |
| `correlation-analysis.xml` | 21 | 4.1 | 상관관계 분석, Slack 테스트 패널 |

### Python Scripts (`scripts/`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `fortigate_auto_block.py` | FortiGate API 자동 차단 | Splunk alert action |
| `fetch_abuseipdb_intel.py` | AbuseIPDB 위협 인텔리전스 | Cron (매시간) |
| `fetch_virustotal_intel.py` | VirusTotal 위협 인텔리전스 | Cron (매시간) |

---

## 🚀 Essential Commands

### Development & Deployment

```bash
# Local 실행 (Node.js 18+)
npm start

# Cloudflare Workers 개발 (hot reload)
npm run dev:worker

# Cloudflare Workers 배포 (프로덕션)
npm run deploy:worker

# 실시간 로그 확인
npm run tail:worker
```

### Cloudflare Workers Secrets 설정 (최초 1회)

```bash
npm run secret:faz-host        # FortiAnalyzer 호스트
npm run secret:faz-username    # admin
npm run secret:faz-password    # 비밀번호
npm run secret:splunk-host     # Splunk HEC 호스트
npm run secret:splunk-token    # HEC 토큰
npm run secret:slack-token     # xoxb-<example>
npm run secret:slack-channel   # #splunk-alerts
```

### Dashboard Validation & Deployment

```bash
# XML 유효성 검사
python3 -c "import xml.etree.ElementTree as ET; ET.parse('configs/dashboards/correlation-analysis.xml'); print('✅ Valid')"

# 전체 대시보드 검증 (커스텀 스크립트)
python3 /tmp/validate_dashboards.py

# Splunk REST API로 대시보드 배포
node scripts/deploy-dashboards.js
```

### Testing

```bash
# Mock 데이터 생성 및 Splunk 전송
node scripts/generate-mock-data.js --count=100 --send

# Slack 알림 테스트
node scripts/slack-alert-cli.js --test
node scripts/slack-alert-cli.js --channel="splunk-alerts" --message="Test"
```

---

## 📊 Phase Implementation Status

### Phase 3.1: Threat Intelligence Integration ✅
**Components**:
- Dashboard: `threat-intelligence-panels.xml` (9 panels)
- Lookups: `abuseipdb_lookup.csv`, `virustotal_lookup.csv`
- Scripts: `fetch_abuseipdb_intel.py`, `fetch_virustotal_intel.py`

**Key Queries**:
```spl
# AbuseIPDB 통합
| lookup abuseipdb_lookup.csv ip AS src_ip OUTPUT abuse_score, country, isp
| where abuse_score >= 90

# Geo-location risk scoring
| eval geo_risk = case(
    country IN ("CN", "RU", "KP", "IR"), 50,
    country IN ("VN", "BR", "IN"), 30,
    1=1, 20)
```

### Phase 3.2: Automated Response System ✅
**Components**:
- Dashboard: `automated-response-panels.xml` (10 panels)
- Script: `fortigate_auto_block.py` (400 LOC)
- Config: `savedsearches-auto-block.conf` (3 searches)

**Auto-Block Workflow**:
```python
# fortigate_auto_block.py
process_correlation_results()
  → load_whitelist() (IP 제외 목록)
  → load_blocked_ips() (중복 방지)
  → fg_client.block_ip(src_ip)
      → create_address_object()  # FortiGate 주소 객체 생성
      → create_deny_policy()     # 차단 정책 생성
  → save_blocked_ip()
  → send_slack_notification()
```

### Phase 3.3: Search Acceleration & Data Model ✅
**Components**:
- Data Model: `datamodels.conf` (Fortinet_Security)
- Saved Searches: `savedsearches-acceleration.conf` (6 searches)

**Data Model Structure**:
```
Fortinet_Security (acceleration: 7 days)
└── Security_Events (Root Dataset)
    ├─ src_ip, dst_ip, severity, attack_name, risk_score
    └─ index=fortigate_security sourcetype="fortinet:fortigate:traffic"
```

**Performance**: 10x faster (tstats vs raw search), CPU -60%

### Phase 4.1: Advanced Correlation Engine ✅
**Components**:
- Dashboard: `correlation-analysis.xml` (21 panels, 13 rows)
- Config: `correlation-rules.conf` (6 rules)
- Documentation: `DASHBOARD_OPTIMIZATION_PHASE4.1_REPORT.md` (58KB)

**6 Correlation Rules**:

| Rule | Detection Method | Threshold | Schedule | Action |
|------|------------------|-----------|----------|--------|
| Multi-Factor Threat Score | abuse + geo + login + frequency | ≥75 | */15 min | Script |
| Repeated High-Risk Events | tstats on risk_score > 70 | ≥80 | */10 min | Script |
| Weak Signal Combination | 5 indicators (abuse + login + scan + targets + freq) | ≥80 | */15 min | Slack |
| Geo + Attack Pattern | High-risk country + active attack | ≥85 | */10 min | Script |
| Time-Based Anomaly | Z-score > 3, spike ratio > 10x | ≥85 | */10 min | Script |
| Cross-Event Type | 3+ attack types = APT | ≥90 | */15 min | Script + Slack |

**Automated Response Thresholds**:
- **90-100**: AUTO_BLOCK (FortiGate 즉시 차단)
- **80-89**: REVIEW_AND_BLOCK (Slack 검토 요청)
- **75-79**: MONITOR (로그만 기록)

**Dashboard Row 12, 13** (Phase 4.1 추가):
- Slack 알림 테스트 패널 (Interactive button)
- 알림 히스토리 (24시간)
- 성공률 모니터링 (Color-coded single value)

---

## 🔧 Key Implementation Patterns

### 1. Zero-Dependency HTTP Client

모든 커넥터는 Node.js 내장 `https` 모듈만 사용 (외부 라이브러리 의존성 제로):

```javascript
import https from 'https';

function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(body));
        } else {
          reject(new Error(`HTTP ${res.statusCode}`));
        }
      });
    });
    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}
```

### 2. Circuit Breaker Pattern

```javascript
import CircuitBreaker from './domains/defense/circuit-breaker.js';

const breaker = new CircuitBreaker({
  failureThreshold: 5,
  resetTimeout: 60000
});

const result = await breaker.call(
  () => fazConnector.getEvents(),           // 실제 API 호출
  () => ({ events: [], fallback: true })    // Fallback (Circuit OPEN 시)
);
```

### 3. Event Processing Queue Pattern

```javascript
// security-event-processor.js
processor.addEvents(events);  // 큐에 추가
processor.startProcessing();  // 백그라운드 배치 처리 시작 (5초마다)

// 처리 흐름
addEvent() → enrichEvent() → eventQueue.push()
  ↓ (5초마다)
processEventBatch() → processEvent()
  ↓
├─ correlateEvent()         # 상관관계 분석
├─ shouldAlert() → triggerAlert() → Slack
└─ sendToSplunk()
```

### 4. ES Modules (중요!)

모든 파일은 ES Modules 사용 (`package.json:type = "module"`):

```javascript
// ✅ 올바른 import (.js 확장자 필수!)
import Connector from './domains/integration/fortianalyzer-direct-connector.js';

// ❌ 작동 안 함 (.js 확장자 누락)
import Connector from './domains/integration/fortianalyzer-direct-connector';

// ✅ Named export
export { SecurityEventProcessor };
export default SecurityEventProcessor;
```

---

## 🔔 Slack Integration (2가지 방식)

### 방식 1: Splunk Plugin (action.slack) - Dashboard용 ⭐

**설정**: `/opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf`

```ini
[slack]
param.token = xoxb-YOUR-BOT-TOKEN
param.channel = #splunk-alerts
param.from_user = Splunk FortiGate Alert
param.icon_emoji = :fire:
```

**사용 위치**:
- `correlation-rules.conf` 라인 197-199 (Weak Signal)
- `correlation-rules.conf` 라인 358-360 (Sophisticated Threat)
- Dashboard Row 12 테스트 버튼

**장점**: Dashboard에서 직접 사용 가능, Splunk Web UI 설정

### 방식 2: Python Script Webhook - 자동 차단용

**설정**: `.env` 파일의 `SLACK_WEBHOOK_URL`

**사용 위치**:
- `fortigate_auto_block.py` 라인 155-190 (`send_slack_notification()`)

**장점**: 완전한 커스터마이징, Plugin 설치 불필요

---

## 📝 Correlation Rules 수정 가이드

### 위치: `configs/correlation-rules.conf`

#### Rule 1: Multi-Factor Threat Score 조정

**Score 계산 공식 수정** (라인 38-47):
```ini
| eval abuse_component = coalesce(abuse_score, 0) * 0.4    # 40% 가중치
| eval geo_component = geo_risk * 0.2                      # 20% 가중치
| eval login_failures = if(match(msg, "..."), 30, 0)       # 30점
| eval frequency_component = case(                          # 최대 30점
    event_count > 100, 30,
    event_count > 50, 20,
    event_count > 10, 10,
    1=1, 0)
| eval correlation_score = round(abuse_component + geo_component + login_failures + frequency_component, 2)
```

**Threshold 조정** (라인 48-57):
```ini
| where correlation_score >= 75    # 이 값을 변경 (현재: 75)

| eval action_recommendation = case(
    max_correlation_score >= 90, "AUTO_BLOCK",      # AUTO_BLOCK threshold
    max_correlation_score >= 80, "REVIEW_AND_BLOCK", # REVIEW threshold
    1=1, "MONITOR")
```

#### Rule 3: Weak Signal Combination 수정

**5개 지표 조정** (라인 141-186):
```ini
# 1. Low abuse_score (라인 143-145)
| eval has_low_abuse = if(abuse_score > 0 AND abuse_score < 50, 1, 0)

# 2. Failed login (라인 148-150)
| eval has_failed_login = if(match(msg, "(?i)(failed.*login|authentication.*fail)"), 1, 0)

# 3. Port scan (라인 153-155)
| eval has_port_scan = if(match(msg, "(?i)(port.*scan|network.*scan)"), 1, 0)

# 4. Multiple targets (라인 158-160)
| eval has_multiple_targets = if(unique_dst_count > 5, 1, 0)  # 5개 이상 타겟

# 5. High frequency (라인 163-165)
| eval has_high_frequency = if(event_count > 20, 1, 0)  # 20개 이상 이벤트
```

---

## 🎨 Dashboard 수정 가이드

### XML Entity Encoding (중요!)

XML에서 특수 문자는 HTML 엔티티로 인코딩 필수:

```xml
<!-- ❌ 잘못된 예 (XML 파싱 오류) -->
<choice value="REVIEW_AND_BLOCK">Review & Block</choice>
"Low (<50)":"#32CD32"

<!-- ✅ 올바른 예 -->
<choice value="REVIEW_AND_BLOCK">Review &amp; Block</choice>
"Low (&lt;50)":"#32CD32"
```

**인코딩 규칙**:
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&apos;`

### Slack 테스트 버튼 추가 (Row 12 참고)

**위치**: `configs/dashboards/correlation-analysis.xml` 라인 527-604

```xml
<panel>
  <title>🚀 Slack 알림 실행</title>
  <html>
    <a href="/app/search/search?q=search%20index%3Dfortigate_security..."
       target="_blank"
       style="display: inline-block; background: ...; ">
      📤 Send Test Alert to Slack
    </a>
  </html>
</panel>
```

**동작 원리**:
1. 버튼 클릭 → Splunk Search 페이지 오픈
2. 테스트 데이터 생성 (correlation_score=95)
3. `summary_fw` 인덱스에 저장
4. Correlation Rule 트리거
5. `action.slack = 1` 실행
6. Slack #splunk-alerts 전송

---

## 🔍 Troubleshooting

### 1. Dashboard XML 파싱 오류

**증상**: "not well-formed (invalid token): line X"

**원인**: 특수 문자 미인코딩 (`&`, `<`, `>`, `"`)

**해결**:
```bash
# 검증 스크립트 실행
python3 /tmp/validate_dashboards.py

# 수동 검증
python3 -c "import xml.etree.ElementTree as ET; ET.parse('dashboards/fortinet-dashboard.xml')"
```

### 2. Correlation Rule이 실행되지 않음

**확인사항**:
```bash
# 1. Saved Search 존재 확인
splunk btool savedsearches list --debug | grep "Correlation_"

# 2. Cron 스케줄 확인
grep "cron_schedule" configs/correlation-rules.conf

# 3. 데이터 모델 가속화 상태
index=_internal source=*summarization.log | stats count by savedsearch_name

# 4. summary_fw 인덱스 데이터 확인
index=summary_fw marker="correlation_detection=*" | stats count by marker
```

### 3. FortiGate 자동 차단 실패

**확인사항**:
```bash
# 1. Python 스크립트 권한
ls -la scripts/fortigate_auto_block.py  # -rwxr-xr-x

# 2. 환경 변수 확인
grep "FORTIGATE_" .env

# 3. 스크립트 로그 확인
tail -f /opt/splunk/etc/apps/fortigate/logs/fortigate_auto_block.log

# 4. Whitelist 확인
cat /opt/splunk/etc/apps/fortigate/lookups/fortigate_whitelist.csv
```

### 4. Slack 알림 미수신

**확인사항**:
```bash
# 1. Bot Token 유효성
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"

# 2. Bot 채널 초대 확인
# Slack에서: /invite @Splunk FortiGate Alert

# 3. OAuth Scopes 확인 (필수: chat:write, channels:read, chat:write.public)
# https://api.slack.com/apps → Your App → OAuth & Permissions

# 4. Splunk alert action 로그
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep -i slack
```

### 5. Cloudflare Workers 배포 실패

**확인사항**:
```bash
# 1. wrangler.toml의 account_id 확인
grep "account_id" wrangler.toml

# 2. Secrets 설정 확인
wrangler secret list

# 3. 로컬 테스트
npm run dev:worker

# 4. 배포 로그 확인
npm run deploy:worker 2>&1 | tee deploy.log
```

---

## 📚 Key Documentation Files

### Phase Reports (Implementation History)
- `docs/DASHBOARD_OPTIMIZATION_PHASE3.1_REPORT.md` - Threat Intelligence (58KB)
- `docs/DASHBOARD_OPTIMIZATION_PHASE3.2_REPORT.md` - Automated Response (62KB)
- `docs/DASHBOARD_OPTIMIZATION_PHASE3.3_REPORT.md` - Data Model Acceleration (47KB)
- `docs/DASHBOARD_OPTIMIZATION_PHASE4.1_REPORT.md` - Correlation Engine (58KB)

### System Validation
- `docs/SYSTEM_HEALTH_VALIDATION_REPORT.md` - 전체 시스템 검증 (58KB)
- `docs/DASHBOARD_SLACK_INTEGRATION_GUIDE.md` - Slack 통합 완전 가이드 (28KB)

### Deployment Guides
- `docs/CLOUDFLARE_DEPLOYMENT.md` - Cloudflare Workers 배포 가이드
- `docs/PRD_DEPLOYMENT_GUIDE.md` - 프로덕션 배포 가이드

### Configuration Examples
- `configs/slack-alert-actions.conf.example` - Slack plugin 설정 템플릿
- `.env.example` - 환경 변수 템플릿

---

## 🎯 Development Workflow

### 1. 새로운 Correlation Rule 추가

```bash
# 1. correlation-rules.conf 편집
vim configs/correlation-rules.conf

# 2. 새로운 [Correlation_YOUR_RULE_NAME] 섹션 추가
# 3. SPL 쿼리 작성 (tstats 사용 권장)
# 4. action.script 또는 action.slack 설정
# 5. cron_schedule 설정

# 6. Git commit
git add configs/correlation-rules.conf
git commit -m "feat: Add new correlation rule for ..."
git push origin master
```

### 2. Dashboard 패널 추가

```bash
# 1. Dashboard XML 백업
cp configs/dashboards/correlation-analysis.xml configs/dashboards/correlation-analysis.xml.backup

# 2. XML 편집
vim configs/dashboards/correlation-analysis.xml

# 3. 새로운 <row> 및 <panel> 추가
# 4. SPL 쿼리 작성
# 5. 특수 문자 HTML 엔티티 인코딩 (& → &amp;, < → &lt;)

# 6. XML 유효성 검사
python3 /tmp/validate_dashboards.py

# 7. Git commit
git add configs/dashboards/correlation-analysis.xml
git commit -m "feat: Add new panel for ..."
git push origin master
```

### 3. Python Script 수정 (자동 차단 로직)

```bash
# 1. 스크립트 편집
vim scripts/fortigate_auto_block.py

# 2. 로컬 테스트 (Mock 데이터)
echo '{"src_ip": "192.168.1.100", "correlation_score": 95}' | python3 scripts/fortigate_auto_block.py

# 3. Git commit
git add scripts/fortigate_auto_block.py
git commit -m "fix: Improve auto-block logic for ..."
git push origin master
```

---

## ⚠️ Important Notes

### Entry Point 차이점 (`index.js` vs `src/worker.js`)

코드 수정 시 주의사항:

| 측면 | `index.js` | `src/worker.js` |
|------|-----------|-----------------|
| **환경 변수** | `process.env.VAR_NAME` | `env.VAR_NAME` (함수 파라미터) |
| **Import** | `import Connector from './domains/...'` | 클래스 인라인 정의 (import 불가) |
| **Cron** | 외부 cron 또는 setInterval | `wrangler.toml` crons 설정 |

**도메인 로직 변경 시**:
1. `domains/` 내 파일 수정 → `index.js`는 자동 반영
2. `src/worker.js`는 **수동으로 클래스 코드 복사** 필요

### Git Workflow

```bash
# 변경사항 확인
git status

# 스테이징 (백업 파일 제외)
git add -A
git reset *.backup *.bak *.old

# 커밋
git commit -m "feat: Add new feature"
git commit -m "fix: Resolve XML encoding issue"
git commit -m "docs: Update correlation rules guide"

# 푸시 (자동 pre-commit hook 실행)
git push origin master
```

**금지사항**:
- ❌ `.env` 파일 커밋
- ❌ `*.backup`, `*.bak`, `*.old` 파일 커밋
- ❌ Root 디렉토리에 문서 생성 (README.md, CLAUDE.md, CHANGELOG.md, LICENSE 제외)

---

**Status**: Production Ready
**Current Phase**: 4.1 (Correlation Engine)
**Next Phase**: 4.2 (Machine Learning Integration)
**Node.js**: 18+
**Runtime Dependencies**: 0 (Zero Dependencies)
**Updated**: 2025-10-22
