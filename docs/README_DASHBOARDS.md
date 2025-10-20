# Splunk Dashboard Deployment Guide

## 📊 대시보드 개요

5개의 프로덕션 Splunk 대시보드가 준비되어 있습니다:

1. **Fortinet 설정 관리 대시보드 (개선판)** ✨ NEW
   - **index=fw 기준**, 중복 제거 (dedup)
   - **📢 Slack 알람 연동** (드릴다운 클릭 시)
   - 설정 변경 이력 (cfgpath/cfgobj/cfgattr 파싱)
   - 방화벽 정책, VPN, 인터페이스 변경 추적
   - 관리자 활동, Critical 이벤트
   - 실시간 이벤트 스트림 (15분, 30초 자동 갱신)

2. **FortiGate Security Overview** (6.4 KB)
   - 총 보안 이벤트, Critical 이벤트, 차단 공격, 위협 출발지
   - 보안 이벤트 타임라인 (4시간)
   - 공격 출발지 TOP 10, IPS 시그니처
   - FortiGate 디바이스 상태
   - 지리적 공격 분포 (World Map)

3. **Threat Intelligence Dashboard** (4.7 KB)
   - 멀웨어 탐지, Botnet 통신, 악성 DNS, WebFilter 차단
   - Top 멀웨어 패밀리, 감염된 호스트
   - Botnet C&C 서버, Botnet 타임라인
   - 차단된 웹사이트 (카테고리별), Top 차단 URL

4. **Network Traffic Analysis** (4.9 KB)
   - 총 트래픽 (GB), 활성 세션, Connections/Sec, 고유 출발지
   - 대역폭 사용 타임라인
   - Top 대역폭 소비자, Top 애플리케이션
   - 프로토콜별/서비스 포트별 트래픽
   - 24시간 트래픽 패턴

5. **FortiGate Performance Monitoring** (4.9 KB)
   - CPU, 메모리, 지연시간, 활성 세션
   - 디바이스별 CPU/메모리 사용률 타임라인
   - 활성 세션 타임라인, 네트워크 처리량
   - 디바이스 건강 상태

---

## 🚀 배포 방법

### 방법 1: 자동 배포 (Splunk REST API) ✅ 추천

**사전 요구사항:**
- Splunk 관리자 계정 (username/password)
- Splunk Management Port 접근 (기본: 8089)

**1. 환경변수 설정**

`.env` 파일에 추가:
```bash
# Splunk REST API (대시보드 배포용)
SPLUNK_HOST=splunk.jclee.me
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your_admin_password
SPLUNK_APP=search
```

**2. 배포 실행**

```bash
# 대시보드 XML 생성 (이미 완료됨)
node scripts/export-dashboards.js

# Splunk에 배포
node scripts/deploy-dashboards.js
```

**3. 배포 결과 확인**

성공 시:
```
🚀 Deploying Splunk Dashboards via REST API...

📡 Target: https://splunk.jclee.me:8089
📦 App: search
👤 User: admin

📊 Deploying: FortiGate Security Overview...
✅ Dashboard deployed: FortiGate Security Overview

📊 Deploying: Threat Intelligence Dashboard...
✅ Dashboard deployed: Threat Intelligence Dashboard

📊 Deploying: Network Traffic Analysis...
✅ Dashboard deployed: Network Traffic Analysis

📊 Deploying: FortiGate Performance Monitoring...
✅ Dashboard deployed: FortiGate Performance Monitoring

📊 Deployment Summary:
   ✅ Deployed: 4
   ❌ Failed: 0
   📁 Total: 4

🌐 Access dashboards at:
   https://splunk.jclee.me/app/search/dashboards
```

---

### 방법 2: 수동 업로드 (Splunk Web UI)

**1. Splunk Web UI 접속**
```
https://splunk.jclee.me
```

**2. 대시보드 생성**

각 XML 파일에 대해:

1. **Settings → User Interface → Dashboards**
2. **Create New Dashboard** 클릭
3. Dashboard ID 입력:
   - `fortigate-security-overview`
   - `threat-intelligence`
   - `traffic-analysis`
   - `performance-monitoring`
4. **Edit → Source** 모드로 전환
5. `dashboards/{dashboard-id}.xml` 파일 내용 복사/붙여넣기
6. **Save** 클릭

**3. 권한 설정**

- Settings → Dashboards → {Dashboard Name} → Permissions
- **Read**: Everyone
- **Write**: Admin

---

## 🔔 Slack 알람 설정

### 1. Slack Webhook URL 생성

1. Slack 워크스페이스 → **Apps** → **Incoming Webhooks**
2. **Add to Slack** 클릭
3. 채널 선택 (예: `#splunk-alerts`)
4. Webhook URL 복사
   ```
   https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
   ```

### 2. 환경 변수 설정

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### 3. Slack 알람 테스트

```bash
# 연결 테스트
node scripts/slack-alert-cli.js \
  --webhook="$SLACK_WEBHOOK_URL" \
  --test

# 알람 전송
node scripts/slack-alert-cli.js \
  --webhook="$SLACK_WEBHOOK_URL" \
  --message="설정 변경 감지: FW-01" \
  --severity=high \
  --data='{"장비":"FW-01","관리자":"admin","작업":"삭제"}'
```

### 4. 대시보드에서 Slack 알람 사용

**Fortinet 설정 관리 대시보드**에서:

1. 패널에서 이벤트 행 클릭 (📢 아이콘 표시된 패널)
2. 자동으로 Slack으로 알람 전송
3. Slack 채널에서 실시간 알림 수신

**알람 예시**:
```
🟠 HIGH Alert
설정변경: FW-01 - 방화벽 정책 (policy-001) by admin

장비: FW-01
관리자: admin
작업유형: 삭제
설정분류: 방화벽 정책
객체명: policy-001
시간: 2025-10-15 14:30:22
```

---

## 📁 대시보드 파일 위치

```
/home/jclee/app/splunk/dashboards/
├── fortinet-config-management-enhanced.xml  # 설정 관리 (Slack 연동) ✨ NEW
├── fortigate-security-overview.xml          # Security Overview
├── threat-intelligence.xml                  # Threat Intelligence
├── traffic-analysis.xml                     # Traffic Analysis
└── performance-monitoring.xml               # Performance Monitoring
```

---

## 🔍 대시보드 접근 URL

배포 후 다음 URL로 접근:

1. **Security Overview**
   ```
   https://splunk.jclee.me/app/search/fortigate-security-overview
   ```

2. **Threat Intelligence**
   ```
   https://splunk.jclee.me/app/search/threat-intelligence
   ```

3. **Traffic Analysis**
   ```
   https://splunk.jclee.me/app/search/traffic-analysis
   ```

4. **Performance Monitoring**
   ```
   https://splunk.jclee.me/app/search/performance-monitoring
   ```

**대시보드 목록:**
```
https://splunk.jclee.me/app/search/dashboards
```

---

## 🛠️ Troubleshooting

### 배포 실패: 인증 오류
```bash
❌ Error: 401 Unauthorized
```

**해결:**
- `.env`의 `SPLUNK_USERNAME`, `SPLUNK_PASSWORD` 확인
- Splunk 관리자 계정 권한 확인

### 배포 실패: 연결 오류
```bash
❌ Error: ECONNREFUSED
```

**해결:**
- Splunk 서버 실행 상태 확인
- `SPLUNK_HOST`, `SPLUNK_PORT` (기본: 8089) 확인
- 방화벽 설정 확인

### 대시보드가 비어있음

**원인:**
- Splunk 인덱스에 데이터가 없음
- 인덱스 이름 불일치

**해결:**
```spl
# Splunk에서 인덱스 확인
index=fortigate_security | head 10

# 인덱스가 없으면 생성
Settings → Indexes → New Index
Name: fortigate_security
```

### 쿼리가 작동하지 않음

**원인:**
- FAZ 이벤트가 아직 전송되지 않음
- 인덱스 이름이 다름

**해결:**
1. FAZ → Splunk HEC integration 실행:
   ```bash
   cd /home/jclee/app/splunk
   npm start
   ```

2. 데이터 유입 확인:
   ```spl
   index=fortigate_security earliest=-1h | stats count
   ```

---

## 📊 대시보드 커스터마이징

### 인덱스 이름 변경

대시보드 XML에서 인덱스 이름 수정:

```xml
<!-- Before -->
<query>index=fortigate_security ...</query>

<!-- After (예: main 인덱스 사용) -->
<query>index=main sourcetype=fortigate:security ...</query>
```

### 시간 범위 변경

```xml
<!-- Before: 1시간 -->
<query>index=fortigate_security earliest=-1h ...</query>

<!-- After: 24시간 -->
<query>index=fortigate_security earliest=-24h ...</query>
```

### 패널 추가/제거

각 `<panel>` 블록을 추가/삭제하여 커스터마이징

---

## 🎯 권장 설정

### Splunk Index 생성

```bash
# Splunk CLI 또는 Web UI
splunk add index fortigate_security

# Settings
- Max Size: 500GB
- Retention: 90 days
- Searchable Retention: 30 days
```

### HEC Token 설정

```bash
# Settings → Data Inputs → HTTP Event Collector

Name: fortianalyzer-hec
Source Type: fortigate:security
Index: fortigate_security
Enable Indexer Acknowledgement: Yes
```

### Scheduled Searches (선택사항)

Critical 이벤트 알림:
```spl
index=fortigate_security severity=critical earliest=-5m
| table _time, src_ip, dst_ip, attack_name, action
| sendemail to="security@example.com"
```

---

## 📝 스크립트 파일

### export-dashboards.js
- **위치**: `scripts/export-dashboards.js`
- **기능**: Splunk 대시보드를 개별 XML 파일로 추출
- **실행**: `node scripts/export-dashboards.js`

### deploy-dashboards.js
- **위치**: `scripts/deploy-dashboards.js`
- **기능**: Splunk REST API로 대시보드 자동 배포
- **실행**: `node scripts/deploy-dashboards.js`
- **환경변수**: SPLUNK_HOST, SPLUNK_PORT, SPLUNK_USERNAME, SPLUNK_PASSWORD

---

**작성일**: 2025-10-14
**버전**: 1.0.0
