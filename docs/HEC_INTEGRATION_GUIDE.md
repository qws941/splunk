# Splunk HTTP Event Collector (HEC) 완전 통합 가이드

> **FortiAnalyzer → Splunk HEC 통합의 모든 것**
> 설정 절차, 통신 프로토콜, 데이터 포맷, 보안, 트러블슈팅을 포함한 완전한 가이드

---

## 📋 목차

1. [HEC 개념 및 아키텍처](#1-hec-개념-및-아키텍처)
2. [Splunk 서버 측 HEC 설정](#2-splunk-서버-측-hec-설정)
3. [클라이언트 설정 (이 프로젝트)](#3-클라이언트-설정-이-프로젝트)
4. [통신 프로토콜](#4-통신-프로토콜)
5. [데이터 포맷](#5-데이터-포맷)
6. [인증 및 보안](#6-인증-및-보안)
7. [에러 핸들링](#7-에러-핸들링)
8. [테스트 및 검증](#8-테스트-및-검증)
9. [트러블슈팅](#9-트러블슈팅)
10. [실전 예제](#10-실전-예제)

---

## 1. HEC 개념 및 아키텍처

### 1.1 HEC란?

**HTTP Event Collector (HEC)**는 Splunk의 데이터 수집 메커니즘으로, HTTP(S) 프로토콜을 통해 JSON 형식의 이벤트를 Splunk 인덱스에 직접 전송합니다.

**주요 특징**:
- ✅ **Zero Agent**: 별도의 Forwarder 설치 불필요
- ✅ **HTTP/HTTPS**: 표준 프로토콜 사용 (방화벽 친화적)
- ✅ **JSON 포맷**: 구조화된 데이터 전송
- ✅ **토큰 기반 인증**: API Key 방식의 간단한 인증
- ✅ **확장성**: 대용량 이벤트 처리 가능 (초당 수천 건)

### 1.2 아키텍처

```
┌──────────────────┐
│  FortiAnalyzer   │
│  (이벤트 소스)     │
└────────┬─────────┘
         │ JSON-RPC API
         ▼
┌──────────────────┐
│  Node.js Client  │ ◄─── index.js / worker.js
│  (이 프로젝트)     │
└────────┬─────────┘
         │ HTTPS POST
         │ Authorization: Splunk <TOKEN>
         ▼
┌──────────────────┐
│   Splunk HEC     │ ◄─── :8088/services/collector/event
│  (Endpoint)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Splunk Index    │ ◄─── fortigate_security
│  (데이터 저장)     │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│  Dashboard       │ ◄─── correlation-analysis.xml
│  (시각화)         │
└──────────────────┘
```

### 1.3 이 프로젝트에서의 HEC 사용

**경로**: `FortiAnalyzer → Node.js Client → HEC → Splunk Index`

| 컴포넌트 | 역할 | 파일 |
|---------|------|------|
| **FAZ Connector** | FortiAnalyzer REST API로 이벤트 수집 | `domains/integration/fortianalyzer-direct-connector.js` |
| **Security Processor** | 이벤트 분석 및 enrichment | `domains/security/security-event-processor.js` |
| **HEC Connector** | Splunk HEC로 전송 | `src/worker.js:291-325` |
| **Circuit Breaker** | 장애 대응 | `domains/defense/circuit-breaker.js` |

---

## 2. Splunk 서버 측 HEC 설정

### 2.1 HEC 엔드포인트 활성화

**방법 1: Splunk Web UI**

1. **Settings → Data Inputs → HTTP Event Collector**
2. **Global Settings 클릭**
3. 다음 설정:
   - ✅ **All Tokens**: Enabled
   - ✅ **Enable SSL**: Yes (프로덕션 필수)
   - ✅ **HTTP Port Number**: `8088` (기본값)
   - ✅ **Default Index**: `fortigate_security`
   - ❌ **indexer acknowledgement**: Disabled (대부분의 경우)

4. **Save** 클릭

**방법 2: CLI (inputs.conf)**

```ini
# /opt/splunk/etc/apps/fortigate/local/inputs.conf

[http]
disabled = 0
port = 8088
enableSSL = 1
dedicatedIoThreads = 2

[http://fortigate-hec]
disabled = 0
token = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
index = fortigate_security
sourcetype = fortigate:security
```

### 2.2 HEC Token 생성

**Splunk Web UI**:

1. **Settings → Data Inputs → HTTP Event Collector → New Token**
2. 설정:
   ```
   Token Name: fortigate-hec-token
   Source name override: fortianalyzer
   Source type: fortigate:security
   Index: fortigate_security
   ```
3. **Review → Submit**
4. **Token 값 복사** (한 번만 표시됨):
   ```
   Token: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

**CLI 방식**:

```bash
# Splunk REST API로 토큰 생성
curl -k -u admin:changeme \
  https://localhost:8089/servicesNS/admin/splunk_httpinput/data/inputs/http \
  -d name=fortigate-hec \
  -d index=fortigate_security \
  -d sourcetype=fortigate:security

# 응답에서 token 값 확인
{
  "entry": [{
    "content": {
      "token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
  }]
}
```

### 2.3 인덱스 생성

```bash
# fortigate_security 인덱스 생성
curl -k -u admin:changeme \
  https://localhost:8089/services/data/indexes \
  -d name=fortigate_security \
  -d datatype=event \
  -d maxDataSizeMB=10000 \
  -d maxHotBuckets=10
```

**indexes.conf 방식**:

```ini
# /opt/splunk/etc/apps/fortigate/local/indexes.conf

[fortigate_security]
homePath = $SPLUNK_DB/fortigate_security/db
coldPath = $SPLUNK_DB/fortigate_security/colddb
thawedPath = $SPLUNK_DB/fortigate_security/thaweddb
maxDataSize = 10000
maxHotBuckets = 10
maxWarmDBCount = 300
frozenTimePeriodInSecs = 2592000
```

### 2.4 Health Check 엔드포인트

HEC가 정상 작동하는지 확인:

```bash
# Health Check
curl -k https://splunk.jclee.me:8088/services/collector/health

# 기대 응답
{"text":"HEC is healthy","code":17}
```

---

## 3. 클라이언트 설정 (이 프로젝트)

### 3.1 환경 변수 설정

**Local/Docker 배포 (.env)**:

```bash
# Splunk HEC Configuration
SPLUNK_HEC_HOST=splunk.jclee.me
SPLUNK_HEC_PORT=8088
SPLUNK_HEC_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SPLUNK_HEC_SCHEME=https

# Index
SPLUNK_INDEX_FORTIGATE=fortigate_security
```

**Cloudflare Workers 배포 (Secrets)**:

```bash
# Secrets 설정 (한 번만 실행)
npm run secret:splunk-host      # splunk.jclee.me 입력
npm run secret:splunk-token     # HEC token 입력

# wrangler.toml (Public variables)
[vars]
SPLUNK_INDEX_FORTIGATE = "fortigate_security"
```

### 3.2 코드 구현 (Zero Dependencies)

**핵심 파일**: `src/worker.js:291-325`

```javascript
class SplunkHECConnector {
  constructor(env) {
    this.host = env.SPLUNK_HEC_HOST;
    this.port = env.SPLUNK_HEC_PORT || '8088';
    this.token = env.SPLUNK_HEC_TOKEN;
    this.scheme = env.SPLUNK_HEC_SCHEME || 'https';
    this.index = env.SPLUNK_INDEX_FORTIGATE || 'fortigate_security';
  }

  async sendEvents(events) {
    // 1. Splunk HEC 포맷으로 변환
    const hecEvents = events.map(event => ({
      time: event.timestamp || Math.floor(Date.now() / 1000),
      source: 'fortianalyzer',
      sourcetype: 'fortigate:security',
      index: this.index,
      event: event
    }));

    // 2. HEC Endpoint로 POST 요청
    const response = await fetch(
      `${this.scheme}://${this.host}:${this.port}/services/collector/event/1.0`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Splunk ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: hecEvents.map(e => JSON.stringify(e)).join('\n')
      }
    );

    // 3. 응답 처리
    const result = await response.json();

    return {
      success: result.code === 0 ? events.length : 0,
      failed: result.code === 0 ? 0 : events.length
    };
  }
}
```

**사용 예시**:

```javascript
// 1. Connector 초기화
const hecConnector = new SplunkHECConnector(env);

// 2. 이벤트 전송
const events = [
  {
    timestamp: 1704067200,
    severity: 'high',
    src_ip: '192.168.1.100',
    dst_ip: '10.0.1.50',
    attack: 'SQL.Injection.Attempt'
  }
];

const result = await hecConnector.sendEvents(events);
console.log(`Success: ${result.success}, Failed: ${result.failed}`);
```

---

## 4. 통신 프로토콜

### 4.1 HTTP 메서드 및 엔드포인트

**기본 엔드포인트**:
```
POST https://<SPLUNK_HOST>:8088/services/collector/event/1.0
```

**Batch 엔드포인트** (여러 이벤트 한 번에):
```
POST https://<SPLUNK_HOST>:8088/services/collector/event
```

**Raw 엔드포인트** (JSON 파싱 없이):
```
POST https://<SPLUNK_HOST>:8088/services/collector/raw
```

### 4.2 Request Headers

```http
POST /services/collector/event/1.0 HTTP/1.1
Host: splunk.jclee.me:8088
Authorization: Splunk xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Content-Type: application/json
Content-Length: 1234
```

**필수 헤더**:
- ✅ `Authorization: Splunk <TOKEN>` - 인증
- ✅ `Content-Type: application/json` - 데이터 포맷

**선택적 헤더**:
- `X-Splunk-Request-Channel: <UUID>` - Channel 기반 전송 (고급)

### 4.3 Response Codes

| HTTP Code | HEC Code | Meaning | Action |
|-----------|----------|---------|--------|
| **200** | 0 | Success | ✅ 이벤트 수신 성공 |
| **400** | 5 | Invalid data format | ❌ JSON 포맷 확인 |
| **401** | 2 | Invalid token | ❌ Token 확인 |
| **403** | 4 | Token disabled | ❌ Token 활성화 |
| **503** | 9 | Server busy | 🔄 Retry with backoff |

**성공 응답**:
```json
{
  "text": "Success",
  "code": 0
}
```

**실패 응답**:
```json
{
  "text": "Invalid data format",
  "code": 5,
  "invalid-event-number": 2
}
```

### 4.4 Connection 관리

**Keep-Alive** (권장):
```javascript
const response = await fetch(url, {
  headers: {
    'Connection': 'keep-alive'
  }
});
```

**Timeout 설정**:
```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000); // 30초

const response = await fetch(url, {
  signal: controller.signal
});

clearTimeout(timeoutId);
```

---

## 5. 데이터 포맷

### 5.1 HEC Event Format

**기본 구조**:

```json
{
  "time": 1704067200,
  "host": "fortigate-fw01",
  "source": "fortianalyzer",
  "sourcetype": "fortigate:security",
  "index": "fortigate_security",
  "event": {
    "severity": "high",
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.1.50",
    "attack": "SQL.Injection.Attempt"
  }
}
```

**필드 설명**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `time` | Number | ❌ | Unix epoch (초 단위). 생략 시 현재 시각 |
| `host` | String | ❌ | 호스트명. 기본값: HEC 설정 |
| `source` | String | ❌ | 소스 식별자. 기본값: HEC 설정 |
| `sourcetype` | String | ❌ | Splunk sourcetype. 기본값: HEC 설정 |
| `index` | String | ❌ | 타겟 인덱스. 기본값: HEC 설정 |
| `event` | Object/String | ✅ | 실제 이벤트 데이터 (필수!) |

### 5.2 Batch Events (여러 이벤트)

**개행 문자(`\n`)로 구분**:

```json
{"time": 1704067200, "event": {"severity": "high", "src_ip": "192.168.1.100"}}
{"time": 1704067201, "event": {"severity": "medium", "src_ip": "192.168.1.101"}}
{"time": 1704067202, "event": {"severity": "low", "src_ip": "192.168.1.102"}}
```

**구현 예시**:

```javascript
const hecEvents = events.map(e => JSON.stringify({
  time: e.timestamp,
  source: 'fortianalyzer',
  sourcetype: 'fortigate:security',
  index: 'fortigate_security',
  event: e
}));

const body = hecEvents.join('\n'); // 개행 문자로 연결
```

### 5.3 FortiAnalyzer Event Mapping

**원본 이벤트** (FortiAnalyzer):
```json
{
  "devname": "FortiGate-FW01",
  "logid": "0419016384",
  "type": "utm",
  "subtype": "ips",
  "level": "alert",
  "srcip": "192.168.1.100",
  "dstip": "10.0.1.50",
  "attack": "SQL.Injection.Attempt",
  "attackid": 12345,
  "action": "blocked"
}
```

**변환 후** (HEC 전송):
```json
{
  "time": 1704067200,
  "source": "fortianalyzer",
  "sourcetype": "fortigate:security",
  "index": "fortigate_security",
  "event": {
    "timestamp": 1704067200,
    "device": "FortiGate-FW01",
    "severity": "high",
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.1.50",
    "attack_name": "SQL.Injection.Attempt",
    "event_type": "intrusion_attempt",
    "risk_score": 80
  }
}
```

**변환 로직** (`domains/security/security-event-processor.js:156`):

```javascript
class SecurityEventProcessor {
  processEvent(rawEvent) {
    return {
      timestamp: rawEvent.time || Math.floor(Date.now() / 1000),
      device: rawEvent.devname,
      severity: this.calculateSeverity(rawEvent),
      src_ip: rawEvent.srcip,
      dst_ip: rawEvent.dstip,
      attack_name: rawEvent.attack,
      event_type: this.classifyEventType(rawEvent),
      risk_score: this.calculateRiskScore(rawEvent)
    };
  }
}
```

### 5.4 Field Naming Conventions

**Splunk 권장 사항**:
- ✅ **소문자 + 언더스코어**: `src_ip`, `event_type`, `risk_score`
- ❌ **CamelCase 피하기**: `srcIP` (X), `eventType` (X)
- ✅ **일관성 유지**: 모든 이벤트에서 동일한 필드명 사용
- ✅ **예약어 피하기**: `_time`, `_raw`, `index`, `host`, `source`, `sourcetype`

---

## 6. 인증 및 보안

### 6.1 Token 기반 인증

**Authorization Header**:
```http
Authorization: Splunk xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Token 형식**:
- UUID v4 형식 (36자)
- 예시: `12345678-1234-1234-1234-123456789abc`

**Token 저장 (보안)**:

❌ **잘못된 방법**:
```javascript
// 하드코딩 (절대 금지!)
const token = '12345678-1234-1234-1234-123456789abc';
```

✅ **올바른 방법**:
```javascript
// 환경 변수
const token = process.env.SPLUNK_HEC_TOKEN;

// Cloudflare Workers Secrets
const token = env.SPLUNK_HEC_TOKEN;
```

### 6.2 HTTPS/TLS

**프로덕션 필수 설정**:

```javascript
const response = await fetch(
  `https://splunk.jclee.me:8088/services/collector/event`,
  {
    headers: {
      'Authorization': `Splunk ${token}`
    }
    // TLS 인증서 검증 (기본값: true)
  }
);
```

**개발 환경에서만** (self-signed 인증서):

```javascript
// Node.js
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // ⚠️ 개발 환경만!

// cURL
curl -k https://... # -k: insecure
```

### 6.3 IP Whitelist (선택 사항)

Splunk에서 HEC Token별로 IP 제한 가능:

**limits.conf**:
```ini
[http_input]
# 허용할 IP 대역
acceptFrom = 192.168.1.0/24, 10.0.0.0/8
```

### 6.4 Token 교체 전략

**정기 교체 (권장: 90일)**:

1. **새 Token 생성**
   ```bash
   # Splunk에서 새 HEC Token 생성
   Token: new-token-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

2. **클라이언트에 새 Token 배포**
   ```bash
   # Cloudflare Workers
   npm run secret:splunk-token
   # 입력: new-token-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

3. **정상 작동 확인** (24시간 모니터링)

4. **기존 Token 비활성화**
   ```bash
   # Splunk Web UI
   Settings → Data Inputs → HTTP Event Collector
   → 기존 token → Disable
   ```

---

## 7. 에러 핸들링

### 7.1 Retry 로직

**Exponential Backoff** 구현:

```javascript
async function sendEventsWithRetry(events, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const result = await hecConnector.sendEvents(events);

      if (result.success > 0) {
        return result;
      }

    } catch (error) {
      const isLastAttempt = attempt === maxRetries - 1;

      // 503 (Server Busy) → Retry
      if (error.response?.status === 503 && !isLastAttempt) {
        const backoffMs = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
        console.log(`Retry in ${backoffMs}ms...`);
        await sleep(backoffMs);
        continue;
      }

      // 401/403 (Auth Error) → No Retry
      if ([401, 403].includes(error.response?.status)) {
        throw new Error('Authentication failed. Check HEC token.');
      }

      // 마지막 시도 실패
      if (isLastAttempt) {
        throw error;
      }
    }
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### 7.2 Circuit Breaker 패턴

**구현** (`domains/defense/circuit-breaker.js`):

```javascript
import CircuitBreaker from './domains/defense/circuit-breaker.js';

const breaker = new CircuitBreaker({
  failureThreshold: 5,    // 5번 실패 시 OPEN
  resetTimeout: 60000     // 60초 후 HALF_OPEN
});

// Circuit Breaker로 보호
const result = await breaker.call(
  () => hecConnector.sendEvents(events),  // 실제 호출
  () => ({ success: 0, failed: events.length }) // Fallback
);

if (result.success === 0) {
  // Fallback 처리 (예: 로컬 파일 저장)
  await saveToLocalFile(events);
}
```

**Circuit Breaker 상태 전이**:
```
CLOSED (정상)
  → 5번 연속 실패
OPEN (차단)
  → 60초 경과
HALF_OPEN (테스트)
  → 1번 성공 시 CLOSED
  → 1번 실패 시 OPEN
```

### 7.3 에러 로그 수집

**Splunk 자체로 에러 기록**:

```javascript
async function sendEvents(events) {
  try {
    const result = await hecConnector.sendEvents(events);
    return result;

  } catch (error) {
    // 에러를 별도 인덱스로 전송
    await hecConnector.sendEvents([{
      timestamp: Math.floor(Date.now() / 1000),
      event_type: 'integration_error',
      error_message: error.message,
      error_stack: error.stack,
      failed_events_count: events.length
    }]);

    throw error;
  }
}
```

---

## 8. 테스트 및 검증

### 8.1 HEC Health Check

```bash
# 1. Health 엔드포인트 확인
curl -k https://splunk.jclee.me:8088/services/collector/health

# 기대 응답
{"text":"HEC is healthy","code":17}
```

### 8.2 단일 이벤트 전송 테스트

```bash
# 2. 테스트 이벤트 전송
curl -k https://splunk.jclee.me:8088/services/collector/event/1.0 \
  -H "Authorization: Splunk xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "time": 1704067200,
    "source": "test",
    "sourcetype": "fortigate:security",
    "index": "fortigate_security",
    "event": {
      "severity": "high",
      "src_ip": "192.168.1.100",
      "message": "Test event from cURL"
    }
  }'

# 기대 응답
{"text":"Success","code":0}
```

### 8.3 Batch 이벤트 테스트

```bash
# 3. 여러 이벤트 한 번에 전송
curl -k https://splunk.jclee.me:8088/services/collector/event \
  -H "Authorization: Splunk xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"event": {"severity": "high", "src_ip": "192.168.1.100"}}
{"event": {"severity": "medium", "src_ip": "192.168.1.101"}}
{"event": {"severity": "low", "src_ip": "192.168.1.102"}}'

# 기대 응답
{"text":"Success","code":0}
```

### 8.4 Mock 데이터 생성 및 전송

```bash
# 4. Node.js 스크립트로 100개 이벤트 생성 및 전송
node scripts/generate-mock-data.js --count=100 --send

# 출력
📊 Generating 100 events...
📈 Event Statistics:
   Security Events: 40
   Malware Events: 10
   Botnet Events: 10
🚀 Sending events to Splunk HEC...
✅ All events sent successfully!
```

### 8.5 Splunk에서 확인

```spl
# 5. 최근 수신된 이벤트 확인
index=fortigate_security earliest=-5m
| head 10
| table _time, severity, src_ip, dst_ip, event_type

# 6. HEC 통계 확인
index=_internal source=*metrics.log component=Metrics group=per_index_thruput series=fortigate_security
| timechart sum(kb) as KB
```

---

## 9. 트러블슈팅

### 9.1 "Connection Refused" (연결 거부)

**증상**:
```
Error: connect ECONNREFUSED 192.168.1.10:8088
```

**원인 및 해결**:

1. **HEC 비활성화**
   ```bash
   # Splunk에서 확인
   splunk show http-event-collector

   # 활성화
   splunk enable http-event-collector
   ```

2. **방화벽 차단**
   ```bash
   # 포트 8088 열기
   sudo firewall-cmd --add-port=8088/tcp --permanent
   sudo firewall-cmd --reload
   ```

3. **Splunk 서비스 중지**
   ```bash
   # Splunk 재시작
   sudo /opt/splunk/bin/splunk restart
   ```

### 9.2 "401 Unauthorized" (인증 실패)

**증상**:
```json
{"text":"Invalid token","code":2}
```

**해결**:

1. **Token 확인**
   ```bash
   # .env 파일
   cat .env | grep SPLUNK_HEC_TOKEN

   # Cloudflare Workers Secrets
   wrangler secret list
   ```

2. **Splunk에서 Token 상태 확인**
   ```bash
   # REST API
   curl -k -u admin:changeme \
     https://localhost:8089/services/data/inputs/http/fortigate-hec

   # 응답에서 "disabled": 0 확인
   ```

3. **Token 재생성**
   - Splunk Web UI → Settings → Data Inputs → HTTP Event Collector
   - 기존 token 삭제 후 신규 생성

### 9.3 "403 Forbidden" (Token 비활성화)

**증상**:
```json
{"text":"Token is disabled","code":4}
```

**해결**:
```bash
# Splunk Web UI
Settings → Data Inputs → HTTP Event Collector
→ fortigate-hec-token → Enable
```

### 9.4 "400 Bad Request" (잘못된 데이터 포맷)

**증상**:
```json
{"text":"Invalid data format","code":5,"invalid-event-number":2}
```

**해결**:

1. **JSON 유효성 검사**
   ```javascript
   // 전송 전 검증
   const validateEvent = (event) => {
     try {
       JSON.stringify(event);
       return true;
     } catch (error) {
       console.error('Invalid JSON:', error);
       return false;
     }
   };
   ```

2. **필수 필드 확인**
   ```javascript
   // event 필드 필수!
   const hecEvent = {
     event: { /* 데이터 */ }  // ← 필수
   };
   ```

3. **시간 포맷 확인**
   ```javascript
   // Unix epoch (초 단위)
   const time = Math.floor(Date.now() / 1000); // ✅
   const time = Date.now(); // ❌ (밀리초)
   ```

### 9.5 "503 Service Unavailable" (서버 과부하)

**증상**:
```json
{"text":"Server is busy","code":9}
```

**해결**:

1. **Indexer 큐 확인**
   ```spl
   index=_internal source=*metrics.log group=queue
   | stats max(current_size) as max_size, avg(current_size) as avg_size by name
   ```

2. **Batch 크기 줄이기**
   ```javascript
   // 100개씩 → 50개씩
   const BATCH_SIZE = 50;
   ```

3. **Retry with Backoff**
   ```javascript
   if (response.status === 503) {
     await sleep(2000); // 2초 대기
     return sendEvents(events); // 재시도
   }
   ```

### 9.6 이벤트가 Splunk에 안 보임

**확인 절차**:

1. **인덱스 존재 여부**
   ```spl
   | eventcount summarize=false index=fortigate_security
   ```

2. **시간 범위 확장**
   ```spl
   # 지난 24시간으로 확대
   index=fortigate_security earliest=-24h
   ```

3. **_internal 로그 확인**
   ```spl
   index=_internal source=*http_event_collector.log*
   | search ERROR OR WARN
   ```

4. **HEC Metrics 확인**
   ```spl
   index=_internal source=*metrics.log component=Metrics group=http_event_collector
   | stats sum(kb) as total_kb, sum(ev) as total_events
   ```

---

## 10. 실전 예제

### 10.1 완전한 Node.js 구현

**파일**: `examples/complete-hec-client.js`

```javascript
import https from 'https';

class SplunkHECClient {
  constructor(config) {
    this.host = config.host;
    this.port = config.port || 8088;
    this.token = config.token;
    this.index = config.index;
  }

  async sendEvents(events) {
    const hecEvents = events.map(e => ({
      time: e.timestamp || Math.floor(Date.now() / 1000),
      source: 'fortianalyzer',
      sourcetype: 'fortigate:security',
      index: this.index,
      event: e
    }));

    const body = hecEvents.map(e => JSON.stringify(e)).join('\n');

    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.host,
        port: this.port,
        path: '/services/collector/event',
        method: 'POST',
        headers: {
          'Authorization': `Splunk ${this.token}`,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body)
        },
        rejectUnauthorized: false // ⚠️ 프로덕션에서는 true
      };

      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const result = JSON.parse(data);

            if (res.statusCode === 200 && result.code === 0) {
              resolve({
                success: events.length,
                failed: 0,
                response: result
              });
            } else {
              reject(new Error(`HEC Error: ${result.text} (code: ${result.code})`));
            }
          } catch (error) {
            reject(new Error(`Failed to parse response: ${data}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      req.write(body);
      req.end();
    });
  }
}

// 사용 예시
const client = new SplunkHECClient({
  host: 'splunk.jclee.me',
  port: 8088,
  token: process.env.SPLUNK_HEC_TOKEN,
  index: 'fortigate_security'
});

const events = [
  {
    timestamp: Math.floor(Date.now() / 1000),
    severity: 'high',
    src_ip: '192.168.1.100',
    dst_ip: '10.0.1.50',
    attack: 'SQL.Injection.Attempt',
    risk_score: 85
  }
];

const result = await client.sendEvents(events);
console.log(`✅ Sent ${result.success} events to Splunk`);
```

### 10.2 Batch Processing with Queue

```javascript
class BatchedHECClient {
  constructor(config) {
    this.hecClient = new SplunkHECClient(config);
    this.queue = [];
    this.batchSize = 100;
    this.flushInterval = 5000; // 5초

    // 주기적 Flush
    setInterval(() => this.flush(), this.flushInterval);
  }

  addEvent(event) {
    this.queue.push(event);

    // 배치 크기 초과 시 즉시 전송
    if (this.queue.length >= this.batchSize) {
      this.flush();
    }
  }

  async flush() {
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, this.batchSize);

    try {
      const result = await this.hecClient.sendEvents(batch);
      console.log(`✅ Flushed ${result.success} events`);
    } catch (error) {
      console.error(`❌ Flush failed:`, error);
      // 실패한 이벤트를 다시 큐에 추가 (선택 사항)
      this.queue.unshift(...batch);
    }
  }
}
```

### 10.3 Cloudflare Workers 예제

**파일**: `src/worker.js` (이미 구현됨)

```javascript
export default {
  async scheduled(event, env, ctx) {
    // 1. FortiAnalyzer에서 이벤트 수집
    const fazConnector = new FortiAnalyzerConnector(env);
    const events = await fazConnector.getEvents();

    // 2. 보안 이벤트 처리
    const processor = new SecurityEventProcessor();
    const processedEvents = events.map(e => processor.processEvent(e));

    // 3. Splunk HEC로 전송
    const hecConnector = new SplunkHECConnector(env);
    const result = await hecConnector.sendEvents(processedEvents);

    console.log(`✅ Sent ${result.success} events to Splunk HEC`);
  }
};
```

---

## 📊 성능 튜닝

### Batch Size 최적화

| Batch Size | Latency | Throughput | 권장 시나리오 |
|-----------|---------|------------|-------------|
| **1-10** | 낮음 | 낮음 | 실시간 알림 |
| **50-100** | 중간 | 높음 | ⭐ **일반 사용** |
| **500-1000** | 높음 | 매우 높음 | 대용량 배치 |

### Connection Pooling

```javascript
import http from 'http';
import https from 'https';

const agent = new https.Agent({
  keepAlive: true,
  maxSockets: 10
});

const req = https.request({
  agent: agent,
  // ...
});
```

---

## 🔒 보안 체크리스트

- ✅ HTTPS 사용 (TLS 1.2+)
- ✅ Token을 환경 변수로 저장
- ✅ IP Whitelist 설정 (선택)
- ✅ Token 정기 교체 (90일)
- ✅ 최소 권한 원칙 (HEC Token은 쓰기 전용)
- ✅ 민감 정보 마스킹 (PII, 비밀번호)

---

## 📚 참고 자료

- [Splunk HEC 공식 문서](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)
- [HEC Specification](https://docs.splunk.com/Documentation/Splunk/latest/Data/FormateventsforHTTPEventCollector)
- [FortiAnalyzer REST API Guide](https://docs.fortinet.com/document/fortianalyzer/latest/rest-api-reference)
- [이 프로젝트 CLAUDE.md](../CLAUDE.md)

---

**작성일**: 2025-10-22
**버전**: 1.0
**작성자**: Claude Code (Anthropic)
