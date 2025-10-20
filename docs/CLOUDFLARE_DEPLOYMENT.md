# Cloudflare Workers 배포 가이드

FortiAnalyzer → Splunk HEC 통합 서비스를 Cloudflare Workers 서버리스 환경에 배포하는 가이드입니다.

---

## 📋 목차

1. [아키텍처 개요](#아키텍처-개요)
2. [사전 요구사항](#사전-요구사항)
3. [초기 설정](#초기-설정)
4. [Secrets 설정](#secrets-설정)
5. [배포](#배포)
6. [모니터링 및 로그](#모니터링-및-로그)
7. [커스텀 도메인 설정](#커스텀-도메인-설정)
8. [문제 해결](#문제-해결)

---

## 🏗️ 아키텍처 개요

### Serverless Architecture

```
Cloudflare Workers (Edge Network)
    ↓ Cron Trigger (Every 1 minute)
    ↓
FAZSplunkProcessor
    ↓
┌─────────────────────────────────────┐
│ 1. FortiAnalyzer REST API           │
│    - Login (JSON-RPC)               │
│    - Fetch logs (last 1 minute)     │
│    - Logout                         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. SecurityEventProcessor           │
│    - Calculate severity             │
│    - Calculate risk score           │
│    - Classify event type            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. Splunk HEC API                   │
│    - Batch send events              │
│    - Index: fortigate_security      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. Slack Bot API (if critical)      │
│    - Rich Attachments               │
│    - Color-coded alerts             │
└─────────────────────────────────────┘
```

### Key Benefits

✅ **Zero Server Management** - 서버 관리 불필요
✅ **Global Distribution** - 전 세계 Cloudflare Edge에서 실행
✅ **Auto-Scaling** - 자동 스케일링 (무제한)
✅ **Cost Efficient** - 무료 티어: 100,000 requests/day
✅ **High Availability** - 99.99% SLA
✅ **Built-in Monitoring** - Cloudflare Dashboard 통합

---

## 📦 사전 요구사항

### 1. Cloudflare Account

- **무료 계정 생성**: https://dash.cloudflare.com/sign-up
- **Workers 플랜**: Free (100,000 requests/day) 또는 Paid ($5/month for 10M requests)

### 2. Wrangler CLI 설치

```bash
# Node.js 18+ 필요
npm install -g wrangler

# 또는 프로젝트에 로컬 설치
npm install --save-dev wrangler
```

### 3. Cloudflare API 토큰

```bash
# Cloudflare 로그인
wrangler login

# 브라우저에서 인증 완료
```

### 4. 필수 정보

- **FortiAnalyzer**:
  - Host: `fortianalyzer.example.com`
  - Username: `admin`
  - Password: `your_password`

- **Splunk HEC**:
  - Host: `splunk.jclee.me`
  - Port: `8088`
  - Token: `your_hec_token`

- **Slack Bot** (선택):
  - Bot Token: `xoxb-...`
  - Channel: `splunk-alerts`

---

## ⚙️ 초기 설정

### 1. wrangler.toml 설정

`wrangler.toml` 파일에서 Account ID 설정:

```toml
name = "faz-splunk-hec-integration"
main = "src/worker.js"
compatibility_date = "2025-01-14"

# Cloudflare Dashboard에서 확인: Workers & Pages → Account ID
account_id = "your_account_id_here"

# Cron Triggers - 매 1분마다 실행
[triggers]
crons = ["* * * * *"]
```

**Account ID 확인 방법**:
1. https://dash.cloudflare.com 로그인
2. **Workers & Pages** 클릭
3. 오른쪽 사이드바에서 **Account ID** 복사

### 2. 커스텀 도메인 설정 (선택)

`wrangler.toml`에 추가:

```toml
# Route configuration (선택사항)
route = "https://faz-splunk.jclee.me/*"
zone_id = "your_zone_id_here"
```

**Zone ID 확인 방법**:
1. Cloudflare Dashboard → 도메인 선택 (예: jclee.me)
2. 오른쪽 사이드바에서 **Zone ID** 복사

---

## 🔐 Secrets 설정

Cloudflare Workers에서 환경 변수는 **Secrets**로 관리됩니다 (암호화 저장).

### 방법 1: npm scripts 사용 (권장)

```bash
# FortiAnalyzer
npm run secret:faz-host
# 입력: fortianalyzer.example.com

npm run secret:faz-username
# 입력: admin

npm run secret:faz-password
# 입력: your_secure_password

# Splunk HEC
npm run secret:splunk-host
# 입력: splunk.jclee.me

npm run secret:splunk-token
# 입력: your_hec_token_here

# Slack (선택)
npm run secret:slack-token
# 입력: xoxb-your-slack-bot-token

npm run secret:slack-channel
# 입력: splunk-alerts
```

### 방법 2: 수동으로 wrangler 사용

```bash
# FortiAnalyzer
wrangler secret put FAZ_HOST
wrangler secret put FAZ_PORT         # 443
wrangler secret put FAZ_USERNAME
wrangler secret put FAZ_PASSWORD

# Splunk HEC
wrangler secret put SPLUNK_HEC_HOST
wrangler secret put SPLUNK_HEC_PORT  # 8088
wrangler secret put SPLUNK_HEC_TOKEN
wrangler secret put SPLUNK_HEC_SCHEME # https

# Slack
wrangler secret put SLACK_BOT_TOKEN
wrangler secret put SLACK_CHANNEL
wrangler secret put SLACK_ENABLED    # true
```

### 모든 Secrets 확인

```bash
wrangler secret list
```

### Secret 삭제

```bash
wrangler secret delete SECRET_NAME
```

---

## 🚀 배포

### 1. 로컬 개발 (테스트)

```bash
# 로컬 개발 서버 실행
npm run dev:worker

# 또는
wrangler dev

# Output:
# ⛅️ wrangler 3.22.1
# ------------------
# ⎔ Starting local server...
# ✨ http://localhost:8787
```

**로컬 테스트**:

```bash
# Health check
curl http://localhost:8787/health

# Manual trigger
curl -X POST http://localhost:8787/trigger
```

### 2. Production 배포

```bash
# 배포
npm run deploy:worker

# 또는
wrangler publish

# Output:
# ✨ Built successfully!
# ✨ Successfully published faz-splunk-hec-integration
# 🌍 https://faz-splunk-hec-integration.your-subdomain.workers.dev
```

### 3. 배포 확인

```bash
# Health check
curl https://faz-splunk-hec-integration.your-subdomain.workers.dev/health

# Expected:
# {
#   "status": "healthy",
#   "service": "faz-splunk-hec-integration",
#   "timestamp": "2025-01-14T10:00:00Z",
#   "environment": "production"
# }
```

### 4. Cron Trigger 확인

Cloudflare Dashboard에서:

1. **Workers & Pages** → **faz-splunk-hec-integration** 클릭
2. **Triggers** 탭 → **Cron Triggers** 확인
3. `* * * * *` (매 1분) 설정 확인

---

## 📊 모니터링 및 로그

### 실시간 로그 스트리밍

```bash
# 실시간 로그 확인
npm run tail:worker

# 또는
wrangler tail

# Output:
# 🕐 Cron trigger fired at: 2025-01-14T10:00:00Z
# 🚀 Starting event processing...
# 📥 Collected 45 events from FortiAnalyzer
# ⚙️  Processed 45 events
# 🚨 Found 3 critical events
# 📤 Sent 45 events to Splunk (0 failed)
# 📢 Slack alerts: 3 sent, 0 failed
# ✅ Processing completed in 2345ms
```

### Cloudflare Dashboard

https://dash.cloudflare.com

**Workers & Pages** → **faz-splunk-hec-integration** → **Metrics**:

- ✅ **Requests**: 시간별 요청 수
- ✅ **Errors**: 에러율 (%)
- ✅ **CPU Time**: 평균 CPU 시간 (ms)
- ✅ **Duration**: 평균 응답 시간 (ms)

### Grafana 통합 (선택)

Cloudflare Workers 메트릭을 Grafana로 전송:

```bash
# Cloudflare Analytics API를 사용하여 메트릭 수집
# grafana.jclee.me에서 대시보드 생성
```

---

## 🌐 커스텀 도메인 설정

### 1. Cloudflare DNS에 도메인 추가

Cloudflare Dashboard:

1. **Websites** → **Add a site**
2. 도메인 입력 (예: `jclee.me`)
3. Nameserver를 Cloudflare로 변경

### 2. Workers Route 설정

**wrangler.toml**:

```toml
route = "https://faz-splunk.jclee.me/*"
zone_id = "your_zone_id_here"
```

**또는 Cloudflare Dashboard**:

1. **Workers & Pages** → **faz-splunk-hec-integration**
2. **Triggers** → **Routes** → **Add route**
3. Route: `faz-splunk.jclee.me/*`
4. Zone: `jclee.me`

### 3. 재배포

```bash
wrangler publish
```

### 4. 확인

```bash
curl https://faz-splunk.jclee.me/health
```

---

## 🛠️ 문제 해결

### 문제 1: Secrets가 인식되지 않음

**증상**:
```
Error: env.FAZ_HOST is undefined
```

**해결**:
```bash
# Secret 확인
wrangler secret list

# Secret 추가
wrangler secret put FAZ_HOST
```

### 문제 2: Cron Trigger가 실행되지 않음

**증상**: 로그에 아무것도 나타나지 않음

**해결**:
1. Cloudflare Dashboard → **Triggers** → **Cron Triggers** 확인
2. `wrangler.toml`에 `[triggers]` 섹션 확인
3. 재배포: `wrangler publish`

### 문제 3: FortiAnalyzer 연결 실패

**증상**:
```
Error: FortiAnalyzer login failed
```

**해결**:
1. FAZ_HOST, FAZ_USERNAME, FAZ_PASSWORD Secrets 확인
2. FortiAnalyzer 방화벽 규칙 확인 (Cloudflare IP 대역 허용)
3. FortiAnalyzer REST API 활성화 확인

**Cloudflare IP 대역**:
- https://www.cloudflare.com/ips/

### 문제 4: Splunk HEC 전송 실패

**증상**:
```
Sent 0 events to Splunk (45 failed)
```

**해결**:
1. SPLUNK_HEC_HOST, SPLUNK_HEC_TOKEN Secrets 확인
2. Splunk HEC 엔드포인트 확인:
   ```bash
   curl -k https://splunk.jclee.me:8088/services/collector/health
   ```
3. HEC Token 유효성 확인 (Splunk Web UI)

### 문제 5: CPU Time 초과 (Free Tier)

**증상**:
```
Error: CPU time limit exceeded
```

**해결**:
- **Free Tier**: CPU time 제한 50ms
- **해결책 1**: Workers Unbound로 업그레이드 ($5/month)
- **해결책 2**: 배치 크기 줄이기 (`EVENT_BATCH_SIZE=50` in wrangler.toml)

**Unbound 설정**:

```toml
# wrangler.toml
[limits]
cpu_ms = 30000  # 30 seconds
```

### 문제 6: 로그가 너무 많음

**해결**:

```toml
# wrangler.toml - 로그 레벨 조정
[vars]
LOG_LEVEL = "warn"  # info → warn 또는 error
```

---

## 📈 비용 계산

### Free Tier (무료)

- **요청**: 100,000 requests/day
- **CPU Time**: 50ms per request (최대)
- **현재 사용량**: 1,440 requests/day (매 1분 Cron)
- **비용**: **$0/month** ✅

### Workers Unbound (유료)

- **요청**: 최초 1M requests 포함, 이후 $0.50/M requests
- **CPU Time**: 30초까지 (최초 400,000 GB-s 포함)
- **월 기본료**: **$5/month**
- **추가 비용**: 거의 없음 (현재 사용량 기준)

### 권장 사항

✅ **무료 티어로 시작** (1,440 requests/day << 100,000)
✅ **필요 시 Unbound로 업그레이드** (대량 로그 처리 시)

---

## 🔗 추가 리소스

### Cloudflare Workers 문서

- **공식 문서**: https://developers.cloudflare.com/workers/
- **Cron Triggers**: https://developers.cloudflare.com/workers/configuration/cron-triggers/
- **Secrets**: https://developers.cloudflare.com/workers/configuration/secrets/
- **Wrangler CLI**: https://developers.cloudflare.com/workers/wrangler/

### 관련 프로젝트 문서

- **README.md**: 프로젝트 개요 및 로컬 실행 가이드
- **README_DASHBOARDS.md**: Splunk 대시보드 배포 가이드
- **DEPLOYMENT_SUMMARY.md**: 대시보드 배포 요약

---

## ✅ 배포 체크리스트

- [ ] Cloudflare 계정 생성 및 로그인
- [ ] `wrangler login` 실행
- [ ] `wrangler.toml`에 `account_id` 설정
- [ ] 모든 Secrets 설정 (FAZ, Splunk, Slack)
- [ ] 로컬 테스트 (`wrangler dev`)
- [ ] Production 배포 (`wrangler publish`)
- [ ] Health check 확인 (`curl /health`)
- [ ] Cron Trigger 실행 확인 (`wrangler tail`)
- [ ] Splunk에서 데이터 유입 확인 (`index=fortigate_security`)
- [ ] Slack 알림 수신 확인 (Critical 이벤트 발생 시)
- [ ] Cloudflare Dashboard에서 메트릭 확인
- [ ] 커스텀 도메인 설정 (선택)

---

**작성일**: 2025-01-14
**버전**: 1.0.0
**상태**: ✅ Production Ready
