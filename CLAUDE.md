# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 프로젝트 개요

**FortiAnalyzer → Splunk HEC Integration** - FortiAnalyzer 보안 이벤트를 Splunk HTTP Event Collector로 실시간 전송하고 Critical/High 이벤트를 Slack으로 알림하는 시스템입니다.

### 핵심 목적
1. **FAZ HEC 설정 구현** - FortiAnalyzer에서 Splunk HEC로 보안 이벤트 전송
2. **Splunk 대시보드 고도화** - FAZ 보안 데이터 시각화 (29개 SPL 쿼리, 4개 대시보드)
3. **Slack 알림 설정** - 특정 로그 패턴 감지 시 실시간 Slack 알림

### 배포 옵션 (Entry Points)

이 프로젝트는 **2개의 독립적인 엔트리 포인트**를 제공합니다:

1. **`index.js`** - 로컬/Docker 실행
   - Node.js 직접 실행 또는 Docker 컨테이너
   - `FAZSplunkIntegration` 클래스 기반
   - HTTP 서버 (Health/Metrics endpoints)
   - PM2 프로세스 관리 지원

2. **`src/worker.js`** - Cloudflare Workers (권장)
   - 서버리스 배포
   - Cron Trigger (매 1분 자동 실행)
   - 글로벌 엣지 네트워크
   - 무료 티어: 100,000 requests/day

**선택 기준**:
- **로컬 개발/테스트**: `index.js` 사용
- **프로덕션 배포**: `src/worker.js` 사용 (권장)
- **온프레미스 요구사항**: `index.js` + Docker 사용
- **서버리스 선호**: `src/worker.js` 사용

## 🏗️ Architecture

### System Flow
```
FortiAnalyzer (보안 이벤트 수집)
    ↓
Security Event Processor
    ├─ 위험도 분석 (Risk Score 0-100)
    ├─ 이벤트 분류 (critical/high/medium/low)
    └─ 상관관계 분석
    ↓
├─→ Splunk HEC (fortigate_security 인덱스에 저장)
└─→ Slack (Critical/High 이벤트 알림)
```

### Domain-Driven Design Architecture (Level 3)

**핵심 설계 원칙**: 도메인별 책임 분리, 의존성 역전

```
domains/
├── integration/           # 외부 시스템 연동
│   ├── fortianalyzer-direct-connector.js  # FAZ REST API 클라이언트
│   ├── splunk-api-connector.js            # Splunk HEC 클라이언트
│   ├── splunk-rest-client.js              # Splunk REST API
│   ├── slack-connector.js                 # Slack Bot API
│   ├── slack-webhook-handler.js           # Slack Webhook 수신
│   ├── splunk-queries.js                  # 29개 프로덕션 SPL 쿼리
│   └── splunk-dashboards.js               # 4개 대시보드 템플릿
│
├── security/             # 보안 이벤트 처리 (핵심 도메인)
│   └── security-event-processor.js
│       - 이벤트 분석: severity, risk_score, event_type 분류
│       - 알림 트리거: shouldAlert() 조건 평가
│       - 상관관계 분석: correlateEvent() 다중 이벤트 연관
│       - 배치 처리: processEventBatch() 큐 기반 처리
│
└── defense/              # 안정성 패턴
    └── circuit-breaker.js
        - 상태: CLOSED → OPEN → HALF_OPEN
        - 장애 임계값: 5번 실패 시 OPEN
        - 복구 타임아웃: 60초 후 HALF_OPEN 시도
```

### 핵심 컴포넌트 설명

**SecurityEventProcessor** (`domains/security/security-event-processor.js`):
- 이벤트 큐 관리 (최대 10,000개)
- Risk Score 계산 로직:
  - Severity 기반: critical(40), high(30), medium(20), low(10)
  - Event Type 가산: intrusion_attempt(+30), malware_detected(+25), policy_violation(+20)
  - Source Reputation: malicious(+20)
- 알림 트리거 조건:
  - severity === 'critical' → 무조건 알림
  - severity === 'high' AND risk_score > 70 → 알림
  - event_type IN ['intrusion_attempt', 'malware_detected', 'data_exfiltration'] → 알림
- 상관관계 분석: 동일 source_ip, 시간 윈도우 내 이벤트 그룹화

**Circuit Breaker** (`domains/defense/circuit-breaker.js`):
- 외부 API 호출 실패 시 cascading failure 방지
- 모든 커넥터에서 사용 권장 (FAZ, Splunk, Slack)
- 사용 예제:
  ```javascript
  const breaker = new CircuitBreaker({ failureThreshold: 5, resetTimeout: 60000 });
  const result = await breaker.call(
    () => fazConnector.fetchEvents(),
    () => ({ events: [], fallback: true })
  );
  ```

### Entry Point 차이점 (중요!)

**`index.js` vs `src/worker.js`** - 코드 수정 시 고려사항:

| 측면 | `index.js` | `src/worker.js` |
|------|-----------|-----------------|
| **환경 변수** | `process.env.VAR_NAME` | `env.VAR_NAME` (함수 파라미터) |
| **커넥터 Import** | `import Connector from './domains/...'` | 클래스 인라인 정의 (import 불가) |
| **HTTP 서버** | `http.createServer()` 사용 | Cloudflare Workers fetch handler |
| **Cron** | 외부 cron 또는 setInterval | `wrangler.toml` crons 설정 |
| **로깅** | `console.log()` → stdout | `console.log()` → Cloudflare Logs |
| **에러 처리** | try-catch + process.exit() | try-catch + Response 반환 |
| **Health Check** | `/health` endpoint 직접 구현 | `GET /health` Cloudflare 요청 |

**코드 수정 시 주의사항**:
1. **도메인 로직 변경** (`domains/` 내 파일):
   - `index.js`는 자동으로 변경사항 반영 (import 기반)
   - `src/worker.js`는 **수동으로 클래스 코드 복사** 필요 (인라인 정의)

2. **환경 변수 추가**:
   - `index.js`: `.env` 파일에 추가
   - `src/worker.js`: `wrangler.toml` [vars] 섹션 + `wrangler secret put` 명령

3. **의존성 추가 금지**:
   - Zero Dependencies 아키텍처 유지
   - Node.js 내장 모듈만 사용
   - Cloudflare Workers 128MB 제한 고려

**예제: SecurityEventProcessor 수정 시 워크플로우**:
```bash
# 1. domains/security/security-event-processor.js 수정
vim domains/security/security-event-processor.js

# 2. index.js 테스트 (자동 반영)
npm start

# 3. src/worker.js 수정 (수동 동기화 필요!)
# SecurityEventProcessor 클래스 코드를 src/worker.js에 복사

# 4. Worker 테스트
npm run dev:worker

# 5. 배포
npm run deploy:worker
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# FortiAnalyzer
FAZ_HOST=your-fortianalyzer.example.com
FAZ_PORT=443
FAZ_USERNAME=admin
FAZ_PASSWORD=your_password

# Splunk HEC
SPLUNK_HEC_HOST=your-splunk.example.com
SPLUNK_HEC_PORT=8088
SPLUNK_HEC_TOKEN=your_hec_token
SPLUNK_HEC_SCHEME=https
SPLUNK_INDEX_FORTIGATE=fortigate_security

# Slack 알림
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=splunk-alerts
SLACK_ENABLED=true

# Processing
POLLING_INTERVAL=60000
EVENT_BATCH_SIZE=100

# Health Check
HEALTH_CHECK_PORT=8080
HEALTH_CHECK_ENABLED=true

# Metrics
METRICS_ENABLED=true
```

## 🚀 Essential Commands

### Configuration Validation

```bash
# 전체 설정 검증 (FAZ, Splunk HEC, Slack)
./scripts/validate-config.sh

# Slack 토큰 추출 (암호화된 ZIP에서)
./scripts/extract-slack-token.sh

# 출력 예시:
# ✓ FAZ_HOST: your-fortianalyzer.example.com
# ✓ Splunk HEC is healthy
# ✗ Slack API authentication failed → 토큰 업데이트 필요
```

### Local Development

```bash
# 환경 설정
cp .env.example .env
# .env 파일 편집 후:

# 설정 검증 (필수!)
./scripts/validate-config.sh

# 로컬 실행 (Node.js 18+)
npm start

# Health endpoint 확인
curl http://localhost:8080/health

# Metrics endpoint 확인 (Prometheus format)
curl http://localhost:8080/metrics
```

### Docker Deployment

```bash
# Docker Compose로 전체 스택 실행
docker-compose up -d

# 로그 확인
docker logs -f faz-splunk-integration

# 컨테이너 상태 확인
docker-compose ps

# 컨테이너 재시작 (설정 변경 후)
docker-compose restart

# 컨테이너 중지 및 제거
docker-compose down

# 이미지 재빌드 (코드 변경 후)
docker-compose build --no-cache
docker-compose up -d

# 컨테이너 내부 접근 (디버깅용)
docker exec -it faz-splunk-integration sh
```

### Cloudflare Workers Development

```bash
# 로컬 개발 서버 (hot reload)
npm run dev:worker

# 배포 (권장)
npm run deploy:worker

# 실시간 로그 확인
npm run tail:worker

# Secrets 설정 (한 번만 실행)
npm run secret:faz-host
npm run secret:faz-username
npm run secret:faz-password
npm run secret:splunk-host
npm run secret:splunk-token
npm run secret:slack-token
npm run secret:slack-channel
```

### Testing Individual Components

```bash
# Splunk HEC 연결 테스트
curl -k https://SPLUNK_HOST:8088/services/collector/health

# Slack 메시지 테스트
node scripts/slack-alert-cli.js --webhook="URL" --test

# Mock 데이터 생성 및 테스트
node scripts/generate-mock-data.js
```

### Splunk 대시보드 관리

```bash
# 대시보드 자동 배포 (Splunk REST API)
node scripts/deploy-dashboards.js

# 대시보드 백업 (현재 설정 다운로드)
node scripts/export-dashboards.js

# 테스트 데이터 생성 (개발용)
node scripts/generate-mock-data.js

# Slack 알림 테스트
node scripts/slack-alert-cli.js

# Mock 데이터 생성 및 Splunk 전송
node scripts/generate-mock-data.js --count=1000 --send
node scripts/generate-mock-data.js --count=100 --output=test-data.json

# Slack CLI 상세 사용법
node scripts/slack-alert-cli.js --webhook="https://hooks.slack.com/..." --test
node scripts/slack-alert-cli.js --channel="splunk-alerts" --message="Test alert"
```

### Utility Scripts

```bash
# Splunk 대시보드 배포 (프로그래밍 방식)
node scripts/deploy-dashboards.js

# Splunk 검색 쿼리 실행
node scripts/export-dashboards.js

# Python Alert Action (Splunk 내부에서 실행)
# 이 스크립트는 Splunk의 Alert Action으로 구성되어야 함
# 위치: $SPLUNK_HOME/etc/apps/search/bin/splunk-alert-action.py
```

## 📊 Splunk Resources

### 29개 프로덕션 쿼리 (6개 카테고리)

**카테고리별 주요 쿼리**:
- **Security** (5개): Critical 이벤트, 공격 출발지, 차단 트래픽, IPS, 지리적 분포
- **Traffic** (5개): 프로토콜, 대역폭, 애플리케이션, 서비스, 시간대별 패턴
- **Policy** (4개): 정책 히트, 미사용 정책, 정책 변경, Deny 정책
- **Device** (5개): 디바이스 상태, CPU, 메모리, 세션, HA
- **Threat** (5개): 멀웨어, Botnet, WebFilter, SSL, DNS
- **Performance** (5개): 대역폭, 지연, 패킷 손실, 연결, 처리량

### 프로그래밍 방식으로 쿼리 사용

```javascript
import SplunkQueries from './domains/integration/splunk-queries.js';

const queryLib = new SplunkQueries();

// 카테고리별 모든 쿼리 조회
const securityQueries = queryLib.getSecurityQueries();
const trafficQueries = queryLib.getTrafficQueries();

// 특정 쿼리 조회
const criticalQuery = queryLib.getQuery('security', 'criticalEvents');
console.log(criticalQuery.spl);      // SPL 쿼리 문자열
console.log(criticalQuery.description); // 쿼리 설명

// 키워드로 검색
const results = queryLib.searchQueries('malware');
results.forEach(q => console.log(q.name, q.category));

// 전체 쿼리 목록
const allQueries = queryLib.getAllQueries();
console.log(`Total queries: ${allQueries.length}`);
```

### 4개 프로덕션 대시보드

1. **Security Overview** (8 panels) - `fortigate-security-overview.xml`
2. **Threat Intelligence** (10 panels) - `threat-intelligence.xml`
3. **Traffic Analysis** (9 panels) - `traffic-analysis.xml`
4. **Performance Monitoring** (7 panels) - `performance-monitoring.xml`
5. **Fortinet Config Management (PRD)** - `fortinet-config-management-final.xml` (WCAG 준수, Slack 통합)

**대시보드 프로그래밍 방식 생성**:

```javascript
import SplunkDashboards from './domains/integration/splunk-dashboards.js';

const dashboards = new SplunkDashboards();

// Security Overview 대시보드 XML 생성
const securityXML = dashboards.getSecurityOverviewDashboard();

// Threat Intelligence 대시보드 XML 생성
const threatXML = dashboards.getThreatIntelligenceDashboard();

// 커스텀 대시보드 생성
const customXML = dashboards.createCustomDashboard({
  title: 'My Custom Dashboard',
  panels: [
    { title: 'Panel 1', query: 'index=fortigate_security | stats count' }
  ]
});
```

## 🔔 Slack 알림

### 알림 트리거 조건 (코드 기준)

`domains/security/security-event-processor.js:shouldAlert()` 메서드:

```javascript
shouldAlert(event) {
  // Critical 이벤트는 무조건 알림
  if (event.severity === 'critical') return true;

  // High severity + Risk Score > 70
  if (event.severity === 'high' && event.risk_score > 70) return true;

  // 특정 이벤트 타입은 항상 알림
  const alwaysAlertTypes = ['intrusion_attempt', 'malware_detected', 'data_exfiltration'];
  if (alwaysAlertTypes.includes(event.event_type)) return true;

  return false;
}
```

### Slack 메시지 형식

`domains/integration/slack-connector.js` 사용:

```javascript
import SlackConnector from './domains/integration/slack-connector.js';

const slack = new SlackConnector();
await slack.initialize();

// Security Alert 전송
await slack.sendSecurityAlert({
  severity: 'critical',
  event_type: 'intrusion_attempt',
  risk_score: 85,
  source_ip: '192.168.1.100',
  target_ip: '10.0.0.50',
  attack_name: 'SQL Injection Attempt',
  processed_at: Date.now()
});
```

**Rich Attachment 형식**:
- **Color**: critical(red), high(orange), medium(yellow), low(gray)
- **Fields**: Event Type, Risk Score, Source IP, Target IP, Attack Name, Time
- **Footer**: "FortiAnalyzer → Splunk HEC"
- **Timestamp**: Unix timestamp (자동)

## 🔧 Key Implementation Patterns

### 1. Event Processing Queue Pattern

**위치**: `domains/security/security-event-processor.js`

```javascript
// 이벤트 추가 (큐 기반)
processor.addEvent(event);       // 단일 이벤트
processor.addEvents(events);     // 배치 추가

// 자동 배치 처리 (5초마다)
processor.startProcessing();     // 백그라운드 처리 시작

// 이벤트 처리 흐름
addEvent() → enrichEvent() → eventQueue.push()
  ↓ (5초마다)
processEventBatch() → processEvent()
  ↓
├─ correlateEvent()
├─ shouldAlert() → triggerAlert() → Slack
└─ sendToSplunk()
```

### 2. Circuit Breaker Pattern

**위치**: `domains/defense/circuit-breaker.js`

```javascript
import CircuitBreaker from './domains/defense/circuit-breaker.js';

const breaker = new CircuitBreaker({
  failureThreshold: 5,      // 5번 실패 시 OPEN
  resetTimeout: 60000       // 60초 후 HALF_OPEN 시도
});

// API 호출 보호
const result = await breaker.call(
  async () => {
    // 실제 API 호출
    return await apiClient.fetch();
  },
  () => {
    // Fallback (Circuit OPEN 시)
    return { fallback: true, data: [] };
  }
);

// 상태 확인
const state = breaker.getState();
console.log(state.state);           // CLOSED | OPEN | HALF_OPEN
console.log(state.failureCount);    // 현재 실패 횟수
```

### 3. Zero-Dependency HTTP Client Pattern

**모든 커넥터는 Node.js 내장 `https` 모듈만 사용**:

```javascript
import https from 'https';

// Promise 기반 HTTPS 요청
function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(body));
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
        }
      });
    });

    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}
```

**이점**:
- ✅ 외부 라이브러리 의존성 제로
- ✅ 보안 취약점 노출 최소화
- ✅ 배포 패키지 크기 최소화 (Cloudflare Workers에 유리)

## 🚀 Deployment Options

### Option 1: Cloudflare Workers (권장) ⚡

**서버리스 배포 - 무료 티어 사용 가능**

```bash
# 1. Cloudflare 로그인
wrangler login

# 2. wrangler.toml에 Account ID 설정
# https://dash.cloudflare.com → Workers & Pages → Account ID 복사
# wrangler.toml: account_id = "your_account_id_here"

# 3. Secrets 설정
npm run secret:faz-host       # FortiAnalyzer host
npm run secret:faz-username   # admin
npm run secret:faz-password   # password
npm run secret:splunk-host    # splunk.jclee.me
npm run secret:splunk-token   # HEC token
npm run secret:slack-token    # xoxb-<example>
npm run secret:slack-channel  # splunk-alerts

# 4. 배포
npm run deploy:worker

# 5. 실시간 로그 확인
npm run tail:worker
```

**Worker 코드 구조** (`src/worker.js`):
- **Cron Trigger**: 매 1분마다 자동 실행 (`wrangler.toml:crons = ["* * * * *"]`)
- **Scheduled Handler**: `export default { async scheduled(event, env, ctx) { ... } }`
- **HTTP Endpoints**:
  - `GET /health` - Health check
  - `POST /trigger` - Manual event processing trigger
- **환경 변수**: `env.FAZ_HOST`, `env.SPLUNK_HEC_TOKEN`, etc.
- **CPU 제한**: 50ms (무료), 50ms-30s (유료)
- **메모리 제한**: 128MB

**장점**:
- ✅ Zero Server Management
- ✅ Global Edge Network (전 세계 분산)
- ✅ Auto-Scaling (무제한)
- ✅ Cost Efficient (무료: 100,000 requests/day)
- ✅ Built-in Cron (매 1분 자동 실행)

**상세 가이드**: `docs/CLOUDFLARE_DEPLOYMENT.md`

### Option 2: 로컬 서버 실행

```bash
# .env 설정
cp .env.example .env
nano .env

# 실행 (Node.js 18+)
npm start

# PM2로 백그라운드 실행
pm2 start index.js --name faz-splunk-integration
pm2 save
pm2 startup
```

**출력 예시**:
```
🚀 FAZ → Splunk HEC Integration 시작...
✅ 환경변수 확인 완료

🔌 커넥터 초기화 중...
  - FortiAnalyzer 연결...
  - Splunk HEC 연결...
  - Slack 연결...
  - SecurityEventProcessor 초기화...
✅ 모든 커넥터 초기화 완료

📊 이벤트 처리 시작
⏰ 이벤트 폴링 시작 (1분 간격)
🎯 Splunk HEC로 실시간 전송 중
📢 Critical/High 이벤트 → Slack 알림

🏥 Health endpoint: http://localhost:8080/health
📊 Metrics endpoint: http://localhost:8080/metrics

📊 현재 상태: (10초마다 출력)
   처리된 이벤트: 1,234
   Critical: 45
   High: 123
   오류: 0
```

## 🔧 FAZ HEC 설정

**옵션 1: FortiAnalyzer CLI 직접 설정**

`fortigate-hec-setup.conf` 파일 참고:

```bash
config system log-forward
    edit "splunk-hec"
        set mode forwarding
        set fwd-server-type splunk
        set fwd-reliable enable
        set server-name "your-splunk.example.com"
        set server-port 8088
        set server-scheme https
        set fwd-archive enable
    next
end

config system log-forward-service
    edit "splunk-hec"
        set device-filter "all"
        set log-filter "severity >= medium"
        set dest-id 1
    next
end
```

**옵션 2: 이 Node.js 애플리케이션 사용** (권장)

- FAZ API로 이벤트 수집 (1분마다)
- Splunk HEC로 전송
- Slack 알림 자동 처리
- Circuit Breaker 패턴으로 안정성 보장

**차이점**:
- CLI 설정: FAZ에서 직접 Splunk HEC로 전송 (필터링 제한적)
- Node.js 앱: FAZ → SecurityEventProcessor → Splunk HEC (고급 필터링, 상관관계 분석, Slack 통합)

## 🛠️ Troubleshooting

### FAZ 연결 실패

```bash
# FAZ API 연결 테스트
curl -k -X POST https://FAZ_HOST/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "method": "exec",
    "params": [{
      "url": "/sys/login/user",
      "data": {"user": "admin", "passwd": "password"}
    }],
    "id": 1
  }'

# 예상 응답: {"result": [{"status": {"code": 0}, "url": "/sys/login/user"}], "id": 1}
```

**일반적인 문제**:
- ❌ SSL 인증서 오류 → FAZ_SKIP_SSL_VERIFY=true 설정
- ❌ 인증 실패 → FAZ_USERNAME, FAZ_PASSWORD 확인
- ❌ 타임아웃 → FAZ_PORT 확인 (기본: 443)

### Splunk HEC 연결 실패

```bash
# HEC Health Check
curl -k https://SPLUNK_HEC_HOST:8088/services/collector/health

# 예상 응답: {"text":"HEC is healthy","code":17}

# HEC 이벤트 전송 테스트
curl -k https://SPLUNK_HEC_HOST:8088/services/collector/event \
  -H "Authorization: Splunk YOUR_HEC_TOKEN" \
  -d '{"event": "test", "sourcetype": "manual"}'
```

**일반적인 문제**:
- ❌ HEC 비활성화 → Splunk Web UI: Settings → Data Inputs → HTTP Event Collector → Global Settings → Enabled
- ❌ Invalid token → SPLUNK_HEC_TOKEN 재확인
- ❌ Index not found → SPLUNK_INDEX_FORTIGATE 인덱스 생성 필요

### Slack 알림 미수신

```bash
# .env 확인
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-<example>
SLACK_CHANNEL=splunk-alerts

# Bot이 채널에 초대되었는지 확인
# Slack에서: /invite @your-bot

# Slack API 테스트
curl -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER" \
  -H "Content-Type: application/json" \
  -d '{"channel": "splunk-alerts", "text": "Test message"}'
```

**일반적인 문제**:
- ❌ Bot 권한 부족 → Slack App: OAuth & Permissions → Scopes → `chat:write`, `channels:read` 추가
- ❌ 채널 미초대 → `/invite @your-bot`
- ❌ SLACK_ENABLED=false → .env에서 true로 변경

### Health Check 실패

```bash
# Health endpoint 확인
curl http://localhost:8080/health

# 예상 응답:
{
  "status": "healthy",
  "service": "faz-splunk-integration",
  "version": "1.0.0",
  "uptime_seconds": 123,
  "timestamp": "2025-10-14T12:34:56.789Z",
  "components": {
    "fortianalyzer": {"connected": true, "status": "healthy"},
    "splunk": {"connected": true, "status": "healthy"},
    "slack": {"connected": true, "status": "healthy"}
  },
  "metrics": {
    "processed_events": 1234,
    "critical_events": 45,
    "high_events": 123,
    "error_count": 0
  }
}
```

## 📝 Development Notes

### ES Modules

**모든 파일은 ES Modules 사용** (`package.json:type = "module"`):

```javascript
// ✅ 올바른 import (.js 확장자 필수)
import FortiAnalyzerConnector from './domains/integration/fortianalyzer-direct-connector.js';

// ❌ 잘못된 import (.js 확장자 없음)
import FortiAnalyzerConnector from './domains/integration/fortianalyzer-direct-connector';

// ✅ Named export
export { SecurityEventProcessor };
export default SecurityEventProcessor;

// ❌ CommonJS 사용 금지
const module = require('./module.js');  // 작동 안 함
```

**중요**: Node.js에서 ES Modules 사용 시 `.js` 확장자는 **필수**입니다.

### Zero Dependencies Architecture

**이 프로젝트는 런타임 의존성이 전혀 없습니다** (Zero Dependencies):

```json
// package.json
{
  "dependencies": {},  // 빈 객체!
  "devDependencies": {
    "wrangler": "^3.114.15"  // Cloudflare Workers CLI만 dev dependency
  }
}
```

**이점**:
- ✅ **보안**: npm 패키지 취약점으로부터 자유
- ✅ **경량**: 배포 패키지 크기 최소화 (Cloudflare Workers에 최적)
- ✅ **안정성**: 외부 라이브러리 버전 호환성 문제 없음
- ✅ **성능**: 네이티브 Node.js 모듈만 사용 (최적화됨)

**사용하는 Node.js 내장 모듈**:
- `https` - HTTP 클라이언트 (FortiAnalyzer, Splunk, Slack API 호출)
- `http` - Health/Metrics 서버

**대안 비교**:
- ❌ `axios` 사용 → `https` 내장 모듈로 대체
- ❌ `node-fetch` 사용 → `https.request()` Promise wrapper로 대체
- ❌ `winston` 로깅 → `console.log()` + 구조화된 출력

### Event Processing Flow (상세)

```
1. FortiAnalyzer Event Collection (매 1분)
   index.js:startEventProcessing()
   ↓
   fortianalyzer-direct-connector.js:getSecurityEvents({ timeRange: '-5m', limit: 100 })
   ↓
   JSON-RPC: /sys/login/user → /logview/adom/{adom}/logsearch → /sys/logout

2. Event Enrichment & Queueing
   security-event-processor.js:addEvents(events)
   ↓
   enrichEvent() → { ...event, processed_at, event_id, severity, risk_score }
   ↓
   eventQueue.push() (최대 10,000개)

3. Batch Processing (5초마다)
   security-event-processor.js:processEventBatch()
   ↓
   batch = eventQueue.splice(0, 100)
   ↓
   for (const event of batch) {
     processEvent(event)
       ├─ correlateEvent(event)          # 상관관계 분석
       ├─ shouldAlert(event) → triggerAlert()  # Slack 알림
       └─ sendToSplunk(event)            # HEC 전송
   }

4. Splunk HEC Transmission
   splunk-api-connector.js:sendEvent(event)
   ↓
   POST https://splunk.jclee.me:8088/services/collector/event
   Headers: { Authorization: "Splunk {token}" }
   Body: { sourcetype, index, event }

5. Slack Notification (조건 충족 시)
   slack-connector.js:sendSecurityAlert(event)
   ↓
   POST https://slack.com/api/chat.postMessage
   Headers: { Authorization: "Bearer {bot_token}" }
   Body: { channel, attachments: [{ color, fields, footer }] }
```

### Circuit Breaker 적용 예제

```javascript
import CircuitBreaker from './domains/defense/circuit-breaker.js';
import FortiAnalyzerConnector from './domains/integration/fortianalyzer-direct-connector.js';

class ResilientFAZClient {
  constructor() {
    this.faz = new FortiAnalyzerConnector();
    this.breaker = new CircuitBreaker({
      failureThreshold: 5,
      resetTimeout: 60000
    });
  }

  async getEvents() {
    return this.breaker.call(
      async () => {
        return await this.faz.getSecurityEvents({ timeRange: '-5m', limit: 100 });
      },
      () => {
        console.warn('Circuit OPEN: Using cached events');
        return { events: [], cached: true };
      }
    );
  }
}
```

## 🔍 Monitoring & Observability

### Prometheus Metrics

**Endpoint**: `http://localhost:8080/metrics`

**Available Metrics**:
```prometheus
# Service uptime
faz_splunk_uptime_seconds

# Event counters
faz_splunk_processed_events_total
faz_splunk_critical_events_total
faz_splunk_high_events_total
faz_splunk_error_count_total

# Component health (1=healthy, 0=unhealthy)
faz_splunk_component_status{component="fortianalyzer"}
faz_splunk_component_status{component="splunk"}
faz_splunk_component_status{component="slack"}
```

**Grafana 통합 예제**:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'faz-splunk-integration'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Health Checks

**Endpoint**: `http://localhost:8080/health`

**Response Schema**:
```json
{
  "status": "healthy" | "degraded" | "unhealthy",
  "service": "faz-splunk-integration",
  "version": "1.0.0",
  "uptime_seconds": 123,
  "timestamp": "ISO8601",
  "components": {
    "fortianalyzer": { "connected": true, "status": "healthy" },
    "splunk": { "connected": true, "status": "healthy" },
    "slack": { "connected": true, "status": "healthy" }
  },
  "metrics": {
    "processed_events": 1234,
    "critical_events": 45,
    "high_events": 123,
    "error_count": 0
  }
}
```

## ⚠️ Common Pitfalls & Best Practices

### 1. ES Modules Import Paths
```javascript
// ❌ 작동 안 함 - .js 확장자 누락
import Connector from './domains/integration/connector';

// ✅ 올바름 - .js 필수
import Connector from './domains/integration/connector.js';
```

### 2. Circuit Breaker 사용
```javascript
// ❌ 나쁨 - 외부 API 직접 호출 (cascading failure 위험)
const events = await fazConnector.getEvents();

// ✅ 좋음 - Circuit Breaker로 보호
const breaker = new CircuitBreaker({ failureThreshold: 5 });
const events = await breaker.call(
  () => fazConnector.getEvents(),
  () => ({ events: [], fallback: true })
);
```

### 3. Environment Variables
```javascript
// ❌ 하드코딩 금지
const splunkHost = 'splunk.jclee.me';

// ✅ 환경 변수 사용
const splunkHost = process.env.SPLUNK_HEC_HOST;

// ✅ Cloudflare Workers
const splunkHost = env.SPLUNK_HEC_HOST;
```

### 4. Event Queue 관리
```javascript
// ❌ 큐 크기 무시 (메모리 부족 위험)
events.forEach(e => processor.addEvent(e));

// ✅ 큐 크기 모니터링 (SecurityEventProcessor가 자동 관리)
processor.addEvents(events);  // 자동으로 maxQueueSize (10,000) 체크
```

### 5. Slack 알림 남발 방지
```javascript
// ❌ 모든 이벤트 알림 (Slack rate limit 초과)
if (event) await slack.sendAlert(event);

// ✅ 조건부 알림 (shouldAlert() 로직 사용)
if (processor.shouldAlert(event)) {
  await slack.sendAlert(event);
}
```

## 📚 Additional Documentation

### Configuration & Deployment
- **설정 검증**: `scripts/validate-config.sh` - 환경 변수 및 연결 테스트
- **유효한 설정 예제**: `docs/VALID_CONFIG_EXAMPLES.md` - GitHub 검색 기반 실제 설정
- **Cloudflare 배포**: `docs/CLOUDFLARE_DEPLOYMENT.md`
- **프로덕션 배포**: `docs/PRD_DEPLOYMENT_GUIDE.md`
- **Slack 프록시 설정**: `PROXY_SLACK_SETUP_GUIDE.md`

### Monitoring & Dashboards
- **활성 세션수 가이드**: `docs/ACTIVE_SESSIONS_GUIDE.md` - FortiGate 세션 모니터링 상세 설명
- **대시보드 가이드**: `README_DASHBOARDS.md`
- **파일 구조**: `FILE_ORGANIZATION.md`

## 🔄 Git Workflow & Repository Management

### Current Repository State

이 저장소는 최근 **대규모 정리 작업**을 거쳤습니다:
- Main branch: `master`
- 많은 legacy 파일이 삭제됨 (Cloudflare Pages, E2E tests, 이전 배포 문서 등)
- 핵심 기능에 집중하는 깔끔한 구조로 재구성

### Staging/Commit Workflow

```bash
# 현재 변경사항 확인
git status

# 변경된 파일 스테이징
git add .                           # 모든 변경사항
git add domains/                    # 특정 디렉토리만
git add index.js src/worker.js      # 특정 파일만

# 삭제된 파일 스테이징
git add -u                          # 삭제/수정된 파일만

# 커밋
git commit -m "feat: Add new security event processor"
git commit -m "fix: Resolve Slack notification issue"
git commit -m "docs: Update CLAUDE.md with deployment guides"

# 푸시
git push origin master
```

### Commit Message Convention

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드/설정 변경
```

### Branch Strategy

현재 single branch (`master`) 전략 사용:
- 직접 `master`에 커밋
- 프로덕션 배포 전 로컬 테스트 필수

**Feature branch 사용 시**:
```bash
# Feature branch 생성
git checkout -b feature/slack-rate-limiting

# 개발 및 커밋
git add .
git commit -m "feat: Implement Slack rate limiting"

# Master에 병합
git checkout master
git merge feature/slack-rate-limiting
git push origin master

# Feature branch 삭제
git branch -d feature/slack-rate-limiting
```

### 주의사항

**절대 커밋하지 말아야 할 파일**:
- `.env` - 환경 변수 (민감 정보 포함)
- `node_modules/` - 의존성 (`.gitignore`에 포함)
- `*.log` - 로그 파일
- `.DS_Store` - macOS 시스템 파일

**커밋 전 체크리스트**:
```bash
# 1. 민감 정보 검사
grep -r "password\|token\|secret" --include="*.js" --include="*.json" .

# 2. Linting (설정된 경우)
npm run lint

# 3. 로컬 테스트
npm start
curl http://localhost:8080/health

# 4. 환경 변수 예제 파일 업데이트
# .env.example이 최신 상태인지 확인
```

---

**Status**: Production Ready
**Version**: 1.0.0
**Updated**: 2025-10-20
**Node.js**: 18+
**Runtime Dependencies**: 0 (Zero Dependencies)
