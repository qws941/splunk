# 📁 파일 구조 및 용도별 정리

## 📋 목차
1. [핵심 실행 파일](#1-핵심-실행-파일)
2. [환경 설정 파일](#2-환경-설정-파일)
3. [도메인 모듈 (DDD Level 3)](#3-도메인-모듈-ddd-level-3)
4. [Splunk 대시보드](#4-splunk-대시보드)
5. [유틸리티 스크립트](#5-유틸리티-스크립트)
6. [문서](#6-문서)
7. [배포 관련](#7-배포-관련)
8. [테스트/샘플 데이터](#8-테스트샘플-데이터)

---

## 1. 핵심 실행 파일

### `index.js` ⭐ **메인 진입점**
**용도**: 로컬 실행 시 메인 애플리케이션
```bash
# 실행 방법
npm start
```

**주요 기능**:
- FAZSplunkIntegration 클래스 초기화
- FortiAnalyzer → Splunk → Slack 파이프라인 구축
- Health Check 엔드포인트 제공 (`:8080/health`, `:8080/metrics`)
- 1분마다 이벤트 폴링 및 처리

**의존성**:
- `domains/integration/fortianalyzer-direct-connector.js`
- `domains/integration/splunk-api-connector.js`
- `domains/integration/slack-connector.js`
- `domains/security/security-event-processor.js`

---

### `src/worker.js` ⭐ **Cloudflare Workers 진입점**
**용도**: 서버리스 배포 시 메인 애플리케이션 (권장 배포 방식)
```bash
# 배포 방법
npm run deploy:worker
```

**주요 기능**:
- index.js와 동일한 로직 (서버리스 환경 최적화)
- Cloudflare Workers Cron Trigger (1분마다 자동 실행)
- HTTP 요청 핸들러 (health, metrics 엔드포인트)

**장점**:
- Zero Server Management
- Global Edge Network
- Auto-Scaling
- 무료 티어: 100,000 requests/day

---

## 2. 환경 설정 파일

### `.env.example` 📝 **환경변수 템플릿**
**용도**: 환경변수 설정 가이드 (실제 값은 `.env`에 저장)

**필수 환경변수**:
```bash
# FortiAnalyzer
FAZ_HOST=your-fortianalyzer.example.com
FAZ_USERNAME=admin
FAZ_PASSWORD=your_password

# Splunk HEC
SPLUNK_HEC_HOST=your-splunk.example.com
SPLUNK_HEC_PORT=8088
SPLUNK_HEC_TOKEN=your_hec_token
SPLUNK_INDEX_FORTIGATE=fortigate_security

# Slack
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL=splunk-alerts
SLACK_ENABLED=true
```

**사용법**:
```bash
cp .env.example .env
nano .env  # 실제 값 입력
```

---

### `wrangler.toml` ⚙️ **Cloudflare Workers 설정**
**용도**: Cloudflare Workers 배포 설정

**주요 설정**:
- `name = "faz-splunk-hec-proxy"` - Worker 이름
- `main = "src/worker.js"` - 진입점
- `compatibility_date = "2024-01-01"` - 호환성 날짜
- `[triggers]` - Cron 스케줄 (매 1분: `"* * * * *"`)
- `[[unsafe.bindings]]` - 환경변수 바인딩

**Secrets 관리**:
```bash
# Secrets 설정 (민감 정보는 wrangler secret으로 관리)
npm run secret:faz-host
npm run secret:faz-username
npm run secret:faz-password
npm run secret:splunk-host
npm run secret:splunk-token
npm run secret:slack-token
```

---

### `fortigate-hec-setup.conf` 📄 **FortiAnalyzer CLI 설정 파일**
**용도**: FortiAnalyzer에서 직접 Splunk HEC로 로그 전송 설정

**사용 시나리오**:
- **이 Node.js 앱 사용 안 함** (FAZ → Splunk 직접 전송)
- FortiAnalyzer CLI에서 수동 설정

**설정 명령**:
```bash
config system log-forward
    edit "splunk-hec"
        set mode forwarding
        set fwd-server-type splunk
        set server-name "your-splunk.example.com"
        set server-port 8088
    next
end
```

**권장**: 이 앱을 사용하면 Circuit Breaker, 알림 트리거, Risk Score 계산 등 추가 기능 제공

---

### `package.json` 📦 **Node.js 프로젝트 설정**
**용도**: 프로젝트 메타데이터, 스크립트, 의존성 관리

**주요 스크립트**:
```json
{
  "start": "node index.js",
  "dev:worker": "wrangler dev src/worker.js",
  "deploy:worker": "wrangler deploy",
  "tail:worker": "wrangler tail",
  "secret:faz-host": "wrangler secret put FAZ_HOST",
  "secret:splunk-token": "wrangler secret put SPLUNK_HEC_TOKEN"
}
```

**의존성**:
- **Zero Runtime Dependencies** (Node.js 내장 모듈만 사용)
- **DevDependencies**: `wrangler` (Cloudflare Workers CLI)

---

## 3. 도메인 모듈 (DDD Level 3)

### 📂 `domains/integration/` - **외부 API 연동**

#### `fortianalyzer-direct-connector.js` 🔌
**용도**: FortiAnalyzer REST API 연동
- 세션 인증 관리
- 보안 이벤트 조회 (`getSecurityEvents()`)
- 로그 필터링 (시간, severity 기준)

**핵심 메서드**:
```javascript
await faz.initialize();  // 인증
const events = await faz.getSecurityEvents({ timeRange: '-5m', limit: 100 });
```

---

#### `splunk-api-connector.js` 🔌
**용도**: Splunk HTTP Event Collector (HEC) 연동
- 이벤트 배치 전송
- HEC Health Check
- Circuit Breaker 통합

**핵심 메서드**:
```javascript
await splunk.sendEvents([event1, event2, ...]);
```

---

#### `splunk-rest-client.js` 🔌
**용도**: Splunk REST API 클라이언트 (관리 작업용)
- 대시보드 배포
- 검색 쿼리 실행
- 인덱스 관리

**사용처**: `scripts/deploy-dashboards.js`에서 사용

---

#### `splunk-queries.js` 📊 **29개 프로덕션 SPL 쿼리 라이브러리**
**용도**: 재사용 가능한 Splunk 쿼리 모음

**카테고리** (6개):
1. **Security** (5개): Critical 이벤트, 공격 출발지, 차단 트래픽
2. **Traffic** (5개): 프로토콜, 대역폭, 애플리케이션
3. **Policy** (4개): 정책 히트, 미사용 정책
4. **Device** (5개): CPU, 메모리, HA 상태
5. **Threat** (5개): 멀웨어, Botnet, WebFilter
6. **Performance** (5개): 대역폭, 지연, 패킷 손실

**사용 예제**:
```javascript
import SplunkQueries from './domains/integration/splunk-queries.js';

const queryLib = new SplunkQueries();
const query = queryLib.getQuery('security', 'criticalEvents');
console.log(query.spl);
// index=fortigate_security severity=critical earliest=-1h
// | stats count by src_ip, dst_ip, attack_name
```

---

#### `splunk-dashboards.js` 📊 **4개 프로덕션 대시보드 템플릿**
**용도**: JavaScript로 Splunk 대시보드 XML 생성

**대시보드**:
1. **Security Overview** (8 panels)
2. **Threat Intelligence** (10 panels)
3. **Traffic Analysis** (9 panels)
4. **Performance Monitoring** (7 panels)

**사용 예제**:
```javascript
import SplunkDashboards from './domains/integration/splunk-dashboards.js';

const dashboards = new SplunkDashboards();
const xml = dashboards.getSecurityOverviewDashboard();
// Splunk Web UI에서 XML 붙여넣기
```

---

#### `slack-connector.js` 🔔
**용도**: Slack Bot API 연동
- 채널 메시지 전송
- Rich Attachment 지원
- Severity별 색상 (🔴 Red / 🟠 Orange)

**핵심 메서드**:
```javascript
await slack.sendAlert({
  severity: 'critical',
  eventType: 'intrusion_attempt',
  riskScore: 85,
  details: { source_ip, target_ip, attack_name }
});
```

---

#### `slack-webhook-handler.js` 🔔
**용도**: Slack Incoming Webhook 연동
- 간단한 메시지 전송 (Bot API 대안)
- 프록시 서버 지원

---

### 📂 `domains/security/` - **보안 이벤트 처리**

#### `security-event-processor.js` 🛡️ **핵심 비즈니스 로직**
**용도**: 보안 이벤트 분석 및 처리

**주요 기능**:
1. **Risk Score 계산** (0-100)
   - Severity 가중치
   - Event Type 점수
   - 공격 패턴 분석

2. **이벤트 분류**
   - critical / high / medium / low

3. **알림 트리거 판단**
   - Severity: `critical` → 무조건 알림
   - Severity: `high` + Risk Score > 70 → 알림
   - Event Type: `intrusion_attempt`, `malware_detected` → 알림

4. **Event Queue 관리**
   - 최대 10,000개 이벤트
   - 5초마다 배치 처리

**핵심 메서드**:
```javascript
await processor.processEvent(event);
// 자동으로:
// 1. Risk Score 계산
// 2. Splunk HEC 전송
// 3. 필요 시 Slack 알림
```

---

### 📂 `domains/defense/` - **안정성 패턴**

#### `circuit-breaker.js` ⚡ **API 장애 방지**
**용도**: Circuit Breaker 패턴 구현

**동작 원리**:
- **CLOSED**: 정상 (API 호출 허용)
- **OPEN**: 장애 (API 호출 차단, 즉시 실패)
- **HALF_OPEN**: 복구 시도 (제한적 호출 허용)

**설정**:
- Failure Threshold: 5회 연속 실패
- Reset Timeout: 60초

**사용 예제**:
```javascript
import CircuitBreaker from './domains/defense/circuit-breaker.js';

const breaker = new CircuitBreaker({ threshold: 5, timeout: 60000 });
const result = await breaker.execute(() => apiCall());
```

---

## 4. Splunk 대시보드

### 📂 `dashboards/` - **Splunk XML 대시보드**

#### `fortinet-config-management-final.xml` ⭐ **PRD 대시보드 (22 KB)**
**용도**: Fortinet 설정 관리 대시보드 (Slack 알림 통합)

**주요 패널**:
- 📋 Slack 프록시 설정 가이드 (상시 표시)
- 📋 Slack 쿼리 복사 도구 (행 클릭 시 표시)
- 설정 변경 이력 (cfgpath/cfgobj/cfgattr 파싱)
- 방화벽 정책, VPN, 인터페이스 변경 추적
- 관리자 활동, Critical 이벤트
- 실시간 이벤트 스트림 (15분, 30초 자동 갱신)

**특징**:
- WCAG 접근성 준수
- Drilldown 클릭 → Slack 알림 자동 전송
- 프록시 설정 없이 curl 명령어 복사 가능

---

#### `fortigate-security-overview.xml` (6.5 KB)
**용도**: Security Overview 대시보드

**패널**:
- 총 보안 이벤트, Critical 이벤트, 차단 공격
- 보안 이벤트 타임라인 (4시간)
- 공격 출발지 TOP 10
- IPS 시그니처 히트
- 지리적 공격 분포 (World Map)

---

#### `threat-intelligence.xml` (4.7 KB)
**용도**: Threat Intelligence 대시보드

**패널**:
- 멀웨어 탐지, Botnet 통신, 악성 DNS
- Top 멀웨어 패밀리, 감염된 호스트
- Botnet C&C 서버, Botnet 타임라인
- WebFilter 차단 (카테고리별)

---

#### `traffic-analysis.xml` (5.0 KB)
**용도**: Network Traffic Analysis 대시보드

**패널**:
- 총 트래픽 (GB), 활성 세션, Connections/Sec
- 대역폭 사용 타임라인
- Top 대역폭 소비자, Top 애플리케이션
- 프로토콜별/서비스 포트별 트래픽

---

#### `performance-monitoring.xml` (5.0 KB)
**용도**: FortiGate Performance Monitoring 대시보드

**패널**:
- CPU, 메모리, 지연시간, 활성 세션
- 디바이스별 CPU/메모리 사용률 타임라인
- 활성 세션 타임라인, 네트워크 처리량

---

#### `splunk-advanced-dashboard.xml` (24 KB)
**용도**: 고급 대시보드 (모든 패널 통합)

---

### 📂 `dashboards/archive/` - **이전 버전 (참고용)**

---

## 5. 유틸리티 스크립트

### 📂 `scripts/` - **관리 도구**

#### `deploy-dashboards.js` 🚀 **대시보드 자동 배포**
**용도**: Splunk REST API로 대시보드 배포

**사용법**:
```bash
# .env에 설정 필요
SPLUNK_HOST=splunk.jclee.me
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your_password

# 실행
node scripts/deploy-dashboards.js
```

**배포 대시보드**:
1. fortigate-security-overview
2. threat-intelligence
3. traffic-analysis
4. performance-monitoring
5. fortinet-config-management-final

**주의**: Slack 설정은 포함 안 됨 (XML만 업로드)

---

#### `export-dashboards.js` 📤 **대시보드 백업**
**용도**: Splunk에서 대시보드 XML 추출

**사용법**:
```bash
node scripts/export-dashboards.js
# dashboards/*.xml 파일 생성
```

---

#### `generate-mock-data.js` 🧪 **테스트 데이터 생성**
**용도**: FortiAnalyzer 이벤트 시뮬레이션

**사용법**:
```bash
node scripts/generate-mock-data.js
# mock-events-sample.json 생성
```

---

#### `slack-alert-cli.js` 📢 **Slack 알림 테스트**
**용도**: Slack Webhook 연결 테스트

**사용법**:
```bash
# 연결 테스트
node scripts/slack-alert-cli.js \
  --webhook="https://hooks.slack.com/..." \
  --test

# 알림 전송
node scripts/slack-alert-cli.js \
  --webhook="https://hooks.slack.com/..." \
  --message="설정 변경 감지" \
  --severity=high \
  --data='{"장비":"FW-01"}'
```

---

#### `splunk-alert-action.py` 🐍 **Splunk Alert Action (Python)**
**용도**: Splunk에서 Python으로 Slack 알림 전송

**배포 위치**: `$SPLUNK_HOME/bin/scripts/`

---

### `deploy-to-splunk.sh` 🚀 **통합 배포 스크립트**
**용도**: Splunk에 앱/대시보드 배포

---

### `start-demo.sh` 🎬 **데모 실행**
**용도**: 빠른 데모 시작

```bash
./start-demo.sh
# 1. Mock 데이터 생성
# 2. 애플리케이션 시작
# 3. Health Check
```

---

## 6. 문서

### 📂 `docs/` - **상세 문서**

#### `CLOUDFLARE_DEPLOYMENT.md` ☁️ **Cloudflare Workers 배포 가이드**
**용도**: 서버리스 배포 완벽 가이드

**포함 내용**:
- wrangler 설치 및 로그인
- Secrets 설정 방법
- 배포 및 모니터링
- 트러블슈팅

---

#### `DEPLOYMENT_SUMMARY_FINAL.md` 📊 **최종 배포 요약**
**용도**: 배포 결과 및 성공 지표

---

#### `PRD_DEPLOYMENT_GUIDE.md` 📋 **프로덕션 배포 가이드**
**용도**: 프로덕션 환경 배포 체크리스트

---

### `README.md` 📖 **프로젝트 메인 문서**
**용도**: 프로젝트 소개, 설치, 사용법

**주요 섹션**:
- 🎯 프로젝트 목적
- 🏗️ Architecture
- 🚀 Quick Start
- 📊 Splunk 대시보드
- 🔍 Splunk 쿼리 라이브러리
- 🔔 Slack 알림
- 📁 프로젝트 구조

---

### `README_DASHBOARDS.md` 📊 **대시보드 배포 가이드**
**용도**: Splunk 대시보드 배포 상세 설명

**포함 내용**:
- 5개 대시보드 개요
- 자동 배포 방법 (Splunk REST API)
- 수동 업로드 방법 (Web UI)
- Slack 알람 설정
- Troubleshooting

---

### `PROXY_SLACK_SETUP_GUIDE.md` 🔧 **Slack 프록시 설정 가이드**
**용도**: Slack Webhook 프록시 서버 설정

**시나리오**: Splunk에서 외부 Slack Webhook 직접 호출 불가 시

---

### `CLAUDE.md` 🤖 **Claude Code 가이드**
**용도**: 미래 Claude Code 인스턴스를 위한 프로젝트 가이드

**포함 내용**:
- Essential Commands
- Architecture Deep Dive
- Core Components
- Implementation Patterns
- Troubleshooting

---

## 7. 배포 관련

### `Dockerfile` 🐳 **Docker 이미지 빌드**
**용도**: Docker 컨테이너 배포

**사용법**:
```bash
docker build -t faz-splunk-integration .
docker run -d --env-file .env faz-splunk-integration
```

---

### `docker-compose.yml` 🐳 **Docker Compose 설정**
**용도**: 다중 컨테이너 배포

**서비스**:
- faz-splunk-integration
- (선택) prometheus, grafana

---

### `.docker-context/` 📂 **Docker 빌드 컨텍스트**
**용도**: Docker 빌드 시 필요한 추가 파일

---

## 8. 테스트/샘플 데이터

### `mock-events-sample.json` 🧪 **샘플 이벤트**
**용도**: 테스트용 FortiAnalyzer 이벤트 샘플

**생성 방법**:
```bash
node scripts/generate-mock-data.js
```

**사용 시나리오**:
- 로컬 개발 테스트
- Splunk 쿼리 검증
- Slack 알림 테스트

---

## 📊 파일 크기별 분류

### Large (>10 KB)
- `dashboards/fortinet-config-management-final.xml` (22 KB) - PRD 대시보드
- `dashboards/splunk-advanced-dashboard.xml` (24 KB) - 고급 대시보드

### Medium (5-10 KB)
- `dashboards/fortigate-security-overview.xml` (6.5 KB)
- `dashboards/traffic-analysis.xml` (5.0 KB)
- `dashboards/performance-monitoring.xml` (5.0 KB)

### Small (<5 KB)
- `dashboards/threat-intelligence.xml` (4.7 KB)
- 모든 `.js` 파일 (<3 KB)

---

## 🔗 의존성 맵

```
index.js
├── domains/integration/fortianalyzer-direct-connector.js
│   └── domains/defense/circuit-breaker.js
├── domains/integration/splunk-api-connector.js
│   └── domains/defense/circuit-breaker.js
├── domains/integration/slack-connector.js
└── domains/security/security-event-processor.js
    ├── domains/integration/splunk-api-connector.js
    └── domains/integration/slack-connector.js

scripts/deploy-dashboards.js
└── domains/integration/splunk-rest-client.js

scripts/generate-mock-data.js
└── (독립적)

scripts/slack-alert-cli.js
└── domains/integration/slack-webhook-handler.js
```

---

## 🎯 빠른 참조

### 개발 시작
```bash
cp .env.example .env       # 환경변수 설정
npm start                  # 로컬 실행
```

### Cloudflare Workers 배포
```bash
npm run deploy:worker      # 배포
npm run tail:worker        # 로그 확인
```

### Splunk 대시보드 배포
```bash
node scripts/deploy-dashboards.js
```

### Slack 테스트
```bash
node scripts/slack-alert-cli.js --webhook="URL" --test
```

---

**작성일**: 2025-10-19
**버전**: 1.0.0
