# Splunk Dashboards

## 🎯 프로덕션 대시보드 (권장)

### fortinet-dashboard.xml ⭐
**통합 대시보드 - 모든 기능 포함**

```
파일: fortinet-dashboard.xml
크기: 18KB
패널: 17개 (7 sections)
인덱스: index=fw
상태: ✅ 프로덕션 준비 완료
```

**주요 기능**:
- ✅ **트래픽 데이터** - 대역폭, 프로토콜, 애플리케이션, 서비스 사용량
- ✅ **성능 데이터** - CPU, 메모리, 세션, HA 상태
- ✅ **설정 변경 추적** - 정책 변경 이력
- ✅ **보안 로그** - FortiGate 방화벽 로그 실시간 수집
- ✅ **Slack 알림** - Splunk Alert Action 지원

**특징**:
- 🎨 WCAG Level AA 색상 준수 (접근성)
- 🔍 Global filters (장비, 시간, 심각도)
- 🔔 Slack 알림 (Splunk Alert Actions 사용)

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

## 🔔 Slack 알림 설정 (Splunk Alert Action)

### 1단계: Slack 앱 설치

```bash
# 자동 설치 스크립트 실행
sudo /home/jclee/app/splunk/scripts/install-slack-alert.sh

# 설치 과정:
# 1. plugins/slack-notification-alert_232.tgz 압축 해제
# 2. $SPLUNK_HOME/etc/apps/slack_alerts/ 설치
# 3. Webhook URL 및 채널 설정
# 4. Slack 연결 테스트
```

**Webhook URL 생성 (필요 시)**:
```
https://api.slack.com/apps
→ Create New App
→ Incoming Webhooks → Activate
→ Add New Webhook → 채널 선택 (#splunk-alerts)
→ Webhook URL 복사
```

### 2단계: Splunk 재시작

```bash
sudo /opt/splunk/bin/splunk restart
```

### 3단계: Alert 생성

```
1. Splunk 대시보드에서 "📢 설정 변경 이력" 테이블 찾기
2. 검색 쿼리 옆 "Save As" → "Alert" 클릭
3. Alert 이름: "FortiGate 설정 변경 알림"
4. Trigger Conditions 설정:
   - Real-time 또는 Schedule (예: Every 5 minutes)
   - Trigger alert when: Number of Results > 0
5. Trigger Actions:
   - "Slack" 선택
   - Channel: #splunk-alerts
   - Message: 설정 변경 감지
6. Save
```

### 4단계: 테스트

```bash
# Slack 연결 테스트
curl -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  -H "Content-Type: application/json" \
  -d '{"text":"✅ Splunk Slack Alert 테스트"}'

# Alert 수동 트리거 (Splunk UI)
Settings → Searches, reports, and alerts → "FortiGate 설정 변경 알림" → Run
```

**참고**: 상세 가이드는 `docs/SLACK_ALERT_INSTALLATION.md` 참고

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

**원인 1**: slack_alerts 앱 미설치
```bash
# Splunk Web UI 확인
Settings → Alert Actions → "Slack" 존재 확인

# 설치
sudo /home/jclee/app/splunk/scripts/install-slack-alert.sh
sudo /opt/splunk/bin/splunk restart
```

**원인 2**: Alert 설정 오류
```bash
# Alert 확인
Settings → Searches, reports, and alerts → Alert 이름 클릭

# Trigger Actions에서 "Slack" 선택 여부 확인
# Webhook URL 설정 확인: Settings → Alert Actions → Slack
```

**원인 3**: Webhook URL 잘못됨
```bash
# 테스트
curl -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'
```

**원인 4**: 방화벽 차단
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

- **Slack 알림 설정**: `../docs/SLACK_ALERT_INSTALLATION.md`
- **프로젝트 구조**: `../PROJECT_STRUCTURE.md`

---

## ✨ Quick Start

```bash
# 1. 대시보드 배포
node scripts/deploy-dashboards.js

# 2. Slack 알림 설치 (선택사항)
sudo scripts/install-slack-alert.sh
sudo /opt/splunk/bin/splunk restart

# 3. Splunk Web UI에서 확인
open http://YOUR_SPLUNK:8000/app/search/fortinet_dashboard

# 4. Alert 생성 (선택사항)
# Settings → Searches, reports, and alerts → New Alert
# Trigger Actions → Slack 선택
```

---

**권장 대시보드**: `fortinet-dashboard.xml`
**상태**: ✅ 프로덕션 준비 완료
**마지막 업데이트**: 2025-10-21
**버전**: 1.0.0
