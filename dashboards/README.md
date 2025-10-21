# Splunk Dashboards

## 🎯 프로덕션 대시보드 (권장)

### fortinet-dashboard.xml ⭐
**통합 대시보드 - 모든 기능 포함**

```
파일: fortinet-dashboard.xml
크기: 31KB
패널: 29개 (8 sections)
인덱스: index=fw
상태: ✅ 프로덕션 준비 완료
```

**주요 기능**:
- ✅ **트래픽 분석** - 대역폭, 프로토콜, 애플리케이션, 서비스 사용량
- ✅ **성능 모니터링** - CPU, 메모리, 세션, HA 상태
- ✅ **설정 변경 추적** - 정책 변경 이력, Slack 알림 통합
- ✅ **보안 로그** - FortiGate 방화벽 로그 실시간 수집

**특징**:
- 🎨 WCAG Level AA 색상 준수 (접근성)
- 🔍 Global filters (장비, 시간, 심각도)
- 🔔 Slack 자동 알림 (설정 변경 행 클릭)
- 💾 세션 기반 Webhook URL 저장

---

## 🚀 배포 방법

### Option 1: 자동 배포 (권장)
```bash
cd /home/jclee/app/splunk
node scripts/deploy-dashboards.js
```

**스크립트가 자동으로**:
1. Splunk REST API 인증
2. `fortinet-dashboard.xml` 읽기
3. Dashboard 생성/업데이트
4. 권한 설정 (모든 사용자 읽기 가능)

### Option 2: Splunk Web UI
```
1. Splunk Web → Settings → Dashboards
2. "Create New Dashboard" → "Create from XML"
3. dashboards/fortinet-dashboard.xml 내용 복사
4. Save
```

### Option 3: Splunk CLI
```bash
# Splunk CLI 사용
splunk add dashboard fortinet-dashboard \
  -auth admin:password \
  -definition dashboards/fortinet-dashboard.xml
```

---

## 🔔 Slack 통합 설정

### 1단계: Slack Webhook URL 생성

```
https://api.slack.com/apps
→ Create New App
→ Incoming Webhooks → Activate
→ Add New Webhook → 채널 선택 (#splunk-alerts)
→ Webhook URL 복사
```

### 2단계: 대시보드에서 설정

```
1. Splunk에서 fortinet-dashboard 열기
2. "🔧 Slack Webhook 설정" 패널 찾기
3. Webhook URL 입력
4. 채널 선택 (#splunk-alerts)
5. 최소 심각도 선택 (high 권장)
6. "설정 저장" 클릭
```

### 3단계: 백그라운드 프록시 실행 (선택사항)

```bash
# .env 파일 설정
cd /home/jclee/app/splunk
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/..." >> .env

# PM2로 프록시 실행
pm2 start index.js --name slack-proxy
pm2 save

# 또는 Docker
docker-compose up -d
```

### 4단계: 테스트

```bash
# CLI 테스트
node scripts/slack-alert-cli.js \
  --webhook="https://hooks.slack.com/..." \
  --test

# 대시보드 테스트
1. "📢 설정 변경 이력" 테이블에서 행 클릭
2. Slack 채널에서 알림 확인
```

---

## 📊 Splunk Index 정보

| 환경 | Index | 용도 |
|------|-------|------|
| **프로덕션** | `index=fw` | 실제 FortiGate 로그 |
| **테스트** | `index=fortigate_security` | 개발/테스트 데이터 |

**대시보드 기본 인덱스**: `index=fw`
**변경 방법**: XML 파일에서 `index=fw`를 원하는 인덱스로 수정

---

## 🔧 Troubleshooting

### 대시보드가 "No results found" 표시

**원인**: 인덱스에 데이터가 없거나 잘못된 인덱스 사용

**해결**:
```spl
# Splunk Search에서 데이터 확인
index=fw earliest=-1h | head 10

# 다른 인덱스 확인
| eventcount summarize=false index=* | search count>0
```

### Slack 알림이 작동하지 않음

**원인 1**: Webhook URL 잘못됨
```bash
# 테스트
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'
```

**원인 2**: 프록시 서버 미실행
```bash
# 프록시 상태 확인
pm2 status slack-proxy

# 로그 확인
pm2 logs slack-proxy
```

**원인 3**: 방화벽 차단
```bash
# Splunk 서버에서 Slack 연결 테스트
curl -I https://hooks.slack.com
```

### 대시보드 로딩 느림

**원인**: 너무 긴 시간 범위

**해결**:
- Time range를 "Last 1 hour"로 변경
- 또는 대시보드 XML에서 `earliest=-1h` 사용

---

## 📚 추가 문서

- **Slack 프록시 설정**: `../PROXY_SLACK_SETUP_GUIDE.md`
- **프로젝트 구조**: `../PROJECT_STRUCTURE.md`

---

## ✨ Quick Start

```bash
# 1. 대시보드 배포
node scripts/deploy-dashboards.js

# 2. Slack Webhook 설정 (선택사항)
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/..." >> .env

# 3. 프록시 실행 (선택사항)
pm2 start index.js --name slack-proxy

# 4. Splunk Web UI에서 확인
open http://YOUR_SPLUNK:8000/app/search/fortinet_dashboard
```

---

**권장 대시보드**: `fortinet-dashboard.xml`
**상태**: ✅ 프로덕션 준비 완료
**마지막 업데이트**: 2025-10-21
**버전**: 1.0.0
