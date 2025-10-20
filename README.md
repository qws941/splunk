# FortiAnalyzer → Splunk HEC Integration

**FortiAnalyzer 보안 이벤트를 Splunk HEC로 실시간 전송하고 Slack 알림을 제공합니다.**

## 🎯 프로젝트 목적

1. **FAZ HEC 설정 구현** - FortiAnalyzer에서 Splunk HEC로 보안 이벤트 전송
2. **Splunk 대시보드 고도화** - FAZ 보안 데이터 시각화
3. **Slack 알림** - Critical/High 이벤트 실시간 알림

## 🏗️ Architecture

```
FortiAnalyzer (보안 이벤트)
    ↓
Security Event Processor (위험도 분석)
    ↓
├─→ Splunk HEC (fortigate_security 인덱스)
└─→ Slack (Critical/High 이벤트 알림)
```

## 🚀 Quick Start

### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# 환경변수 설정
nano .env
```

**필수 환경변수:**
```bash
# FortiAnalyzer
FAZ_HOST=your-faz.example.com
FAZ_USERNAME=admin
FAZ_PASSWORD=your_password

# Splunk HEC
SPLUNK_HEC_HOST=your-splunk.example.com
SPLUNK_HEC_PORT=8088
SPLUNK_HEC_TOKEN=your_hec_token

# Splunk Index
SPLUNK_INDEX_FORTIGATE=fortigate_security

# Slack (선택사항)
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL=splunk-alerts
SLACK_ENABLED=true
```

### 2. 실행

```bash
# 설치 (dependencies 없음 - Node.js 내장 모듈만 사용)
npm install

# 실행
npm start
```

### 3. Splunk HEC Token 생성

Splunk Web UI:
1. Settings → Data Inputs → HTTP Event Collector
2. New Token 클릭
3. Name: `fortianalyzer-hec`
4. Source type: `fortigate:security`
5. Index: `fortigate_security`
6. Token 복사 → `.env`의 `SPLUNK_HEC_TOKEN`에 설정

## 📊 Splunk 대시보드

### 사용 가능한 대시보드

1. **Security Overview** (8 panels)
   - Critical 이벤트 타임라인
   - 공격 출발지 TOP 10
   - IPS 시그니처 히트
   - 차단된 트래픽 현황

2. **Threat Intelligence** (10 panels)
   - 멀웨어 탐지 현황
   - Botnet 활동
   - WebFilter 차단
   - 지리적 공격 분포

3. **Traffic Analysis** (9 panels)
   - 프로토콜별 트래픽
   - 대역폭 소비 TOP 10
   - 애플리케이션 사용 현황

4. **Performance Monitoring** (7 panels)
   - 대역폭 사용률
   - 지연시간 모니터링
   - 패킷 손실률

### 대시보드 배포

```javascript
import SplunkDashboards from './domains/integration/splunk-dashboards.js';

const dashboards = new SplunkDashboards();

// Security Overview 대시보드 XML
const xml = dashboards.getSecurityOverviewDashboard();

// Splunk Web UI에서:
// Settings → User Interface → Dashboards → Create New Dashboard
// → Source 모드에서 XML 붙여넣기
```

## 🔍 Splunk 쿼리 라이브러리

**29개 프로덕션 SPL 쿼리** (6개 카테고리)

### 사용 예제

```javascript
import SplunkQueries from './domains/integration/splunk-queries.js';

const queryLib = new SplunkQueries();

// Critical 이벤트 조회
const criticalQuery = queryLib.getQuery('security', 'criticalEvents');
console.log(criticalQuery.spl);

// 모든 보안 쿼리
const securityQueries = queryLib.getSecurityQueries();

// 키워드 검색
const results = queryLib.searchQueries('malware');
```

### 쿼리 카테고리

1. **Security** (5 queries) - Critical 이벤트, 공격 출발지, 차단 트래픽
2. **Traffic** (5 queries) - 프로토콜, 대역폭, 애플리케이션
3. **Policy** (4 queries) - 정책 히트, 미사용 정책, 정책 변경
4. **Device** (5 queries) - 디바이스 상태, CPU, 메모리, HA
5. **Threat** (5 queries) - 멀웨어, Botnet, WebFilter, DNS
6. **Performance** (5 queries) - 대역폭, 지연, 패킷 손실

## 🔔 Slack 알림

### 알림 트리거 조건

**자동 알림 대상:**
- ✅ Severity가 `critical`인 모든 이벤트
- ✅ Severity가 `high`이고 Risk Score > 70인 이벤트
- ✅ Event Type: `intrusion_attempt`, `malware_detected`, `data_exfiltration`

### 알림 메시지 형식

```
🔴 Security Alert: CRITICAL

Event Type: intrusion_attempt
Risk Score: 85/100
Source System: FortiAnalyzer
Time: 2025-10-14 22:30:00

Details:
{
  "source_ip": "192.168.1.100",
  "target_ip": "10.0.0.50",
  "attack_name": "SQL Injection Attempt"
}
```

### Slack Bot 설정

1. Slack App 생성: https://api.slack.com/apps
2. OAuth Scopes 추가:
   - `chat:write`
   - `channels:read`
3. Bot Token 복사 → `.env`의 `SLACK_BOT_TOKEN`
4. Bot을 채널에 초대: `/invite @your-bot`

## 📁 프로젝트 구조

```
/home/jclee/app/splunk/
├── index.js                    # 메인 진입점 (FAZ → Splunk → Slack)
├── package.json                # ES Modules, zero dependencies
├── .env.example                # 환경변수 템플릿
├── fortigate-hec-setup.conf    # FAZ HEC 설정 파일
├── CLAUDE.md                   # 프로젝트 설명
├── README.md                   # 이 파일
├── PROXY_SLACK_SETUP_GUIDE.md  # ⭐ Slack 프록시 설정 가이드 (PRD)
│
├── dashboards/                 # 📊 Splunk 대시보드 XML
│   ├── fortinet-config-management-final.xml  # ⭐ PRD 대시보드
│   ├── fortigate-security-overview.xml
│   ├── performance-monitoring.xml
│   ├── threat-intelligence.xml
│   ├── traffic-analysis.xml
│   ├── splunk-advanced-dashboard.xml
│   └── archive/                # 이전 버전
│       ├── fortinet-config-management-prd.xml
│       └── fortinet-config-management-enhanced.xml
│
├── docs/                       # 📚 문서
│   ├── CLOUDFLARE_DEPLOYMENT.md        # Cloudflare Workers 배포
│   ├── DEPLOYMENT_SUMMARY_FINAL.md     # 최종 배포 요약
│   ├── PRD_DEPLOYMENT_GUIDE.md         # 프로덕션 가이드
│   └── archive/                         # 이전 문서
│       └── DASHBOARD_SLACK_INTEGRATION.md
│
├── domains/                    # 🏗️ 도메인 주도 설계 (DDD Level 3)
│   ├── integration/            # API 커넥터
│   │   ├── fortianalyzer-direct-connector.js  # FAZ REST API
│   │   ├── splunk-api-connector.js            # Splunk HEC
│   │   ├── splunk-rest-client.js              # Splunk REST API
│   │   ├── splunk-queries.js                  # 29개 SPL 쿼리 라이브러리
│   │   ├── splunk-dashboards.js               # 4개 대시보드 템플릿
│   │   ├── slack-connector.js                 # Slack Bot API
│   │   └── slack-webhook-handler.js           # Slack Webhook
│   │
│   ├── security/               # 보안 이벤트 처리
│   │   └── security-event-processor.js        # 위험도 분석, 알림 트리거
│   │
│   └── defense/                # 안정성 패턴
│       └── circuit-breaker.js                  # API 장애 방지 (Circuit Breaker)
│
├── scripts/                    # 🔧 유틸리티 스크립트
│   ├── deploy-dashboards.js               # 대시보드 자동 배포
│   ├── export-dashboards.js               # 대시보드 백업
│   ├── generate-mock-data.js              # 테스트 데이터 생성
│   ├── slack-alert-cli.js                 # Slack 알림 테스트
│   └── splunk-alert-action.py             # Python Alert Action
│
└── src/                        # 🚀 Cloudflare Worker
    └── worker.js                           # 서버리스 배포
```

### 주요 파일 설명

| 파일/디렉토리 | 용도 |
|--------------|------|
| `PROXY_SLACK_SETUP_GUIDE.md` | **프로덕션 Slack 설정 가이드** (프록시 지원) |
| `dashboards/fortinet-config-management-final.xml` | **현재 사용 중인 PRD 대시보드** (WCAG, Slack 알림) |
| `domains/integration/splunk-queries.js` | **29개 프로덕션 SPL 쿼리** (6개 카테고리) |
| `domains/integration/splunk-dashboards.js` | **4개 대시보드 템플릿** (JS로 XML 생성) |
| `scripts/deploy-dashboards.js` | **대시보드 자동 배포** (Splunk REST API) |

## 🔧 FAZ HEC 설정

**FortiAnalyzer CLI 설정:**

```bash
# fortigate-hec-setup.conf 파일 참고

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

**또는 이 Node.js 애플리케이션 사용:**
- FAZ API로 이벤트 수집 (1분마다)
- Splunk HEC로 전송
- Slack 알림 자동 처리

## 🔍 Splunk 검색 예제

```spl
# 최근 1시간 Critical 이벤트
index=fortigate_security severity=critical earliest=-1h
| stats count by src_ip, dst_ip, attack_name
| sort -count

# 공격 출발지 TOP 10
index=fortigate_security action=blocked earliest=-24h
| stats count as attacks by src_ip
| sort -attacks
| head 10

# IPS 시그니처 히트 현황
index=fortigate_security attack_name=* earliest=-24h
| stats count as hits, dc(src_ip) as unique_sources by attack_name, severity
| sort -hits
```

## 📊 모니터링

### 실시간 상태 확인

```bash
# 애플리케이션 실행 중 10초마다 출력
📊 현재 상태:
   처리된 이벤트: 1,234
   Critical: 45
   High: 123
   오류: 0
```

### Grafana 통합 (선택사항)

```yaml
# 환경변수 설정
GRAFANA_HOST=grafana.jclee.me
PROMETHEUS_HOST=prometheus.jclee.me
METRICS_ENABLED=true
METRICS_PORT=9090
```

## 🛠️ Troubleshooting

### FAZ 연결 실패
```bash
# FAZ 연결 테스트
curl -k -X GET https://FAZ_HOST/api/v2/monitor/system/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Splunk HEC 연결 실패
```bash
# HEC Health Check
curl -k https://SPLUNK_HEC_HOST:8088/services/collector/health

# Expected: {"text":"HEC is healthy","code":17}
```

### Slack 알림 미수신
```bash
# .env 확인
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL=splunk-alerts

# Bot이 채널에 초대되었는지 확인
# Slack에서: /invite @your-bot
```

## 📝 개발 노트

### Zero Dependencies
- ✅ 외부 라이브러리 없음
- ✅ Node.js 내장 모듈만 사용 (`https`, `http`)
- ✅ 보안 취약점 노출 최소화

### ES Modules
```json
{
  "type": "module"
}
```
- 모든 imports는 `.js` 확장자 필수
- `import ... from '...'` 사용

### Event Processing Flow
1. FortiAnalyzer: 1분마다 보안 이벤트 수집
2. SecurityEventProcessor:
   - 이벤트 분류 (critical/high/medium/low)
   - Risk Score 계산 (0-100)
   - 상관관계 분석
3. Splunk HEC: 실시간 전송 (fortigate_security 인덱스)
4. Slack: 임계치 초과 시 알림

## 🚀 Production Deployment

### Option 1: Cloudflare Workers (권장) ⚡

**서버리스 배포 - 무료 티어 사용 가능**

```bash
# Cloudflare 로그인
wrangler login

# Secrets 설정
npm run secret:faz-host
npm run secret:faz-username
npm run secret:faz-password
npm run secret:splunk-host
npm run secret:splunk-token
npm run secret:slack-token

# 배포
npm run deploy:worker

# 실시간 로그 확인
npm run tail:worker
```

**장점:**
- ✅ **Zero Server Management** - 서버 관리 불필요
- ✅ **Global Edge Network** - 전 세계 분산 실행
- ✅ **Auto-Scaling** - 무제한 자동 스케일링
- ✅ **Cost Efficient** - 무료: 100,000 requests/day (현재 1,440/day)
- ✅ **Built-in Cron** - 매 1분 자동 실행

**상세 가이드**: `CLOUDFLARE_DEPLOYMENT.md`

### Option 2: 로컬 서버 실행

```bash
# 로컬 실행
npm start

# PM2로 백그라운드 실행
pm2 start index.js --name faz-splunk-integration
pm2 save
pm2 startup
```

### Option 3: Docker 배포 (예정)

```bash
# docker-compose.yml 생성 필요
docker-compose up -d
```

### 환경변수 검증
```bash
# 실행 전 필수 환경변수 자동 확인
✅ 환경변수 확인 완료
```

## 📄 License

Private - Internal Use Only

## 👤 Author

jclee

---

**Version**: 1.0.0
**Last Updated**: 2025-10-14
