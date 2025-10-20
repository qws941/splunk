# Splunk Dashboards

## 🎯 프로덕션 대시보드

### fortinet-dashboard.xml ⭐ **권장**
**통합 대시보드 - 모든 기능 포함**

```bash
파일: fortinet-dashboard.xml
크기: 27KB
패널: 29개 (8 sections)
인덱스: index=fw
```

**주요 기능**:
- ✅ 보안 이벤트 분석 (Critical, 차단, 공격 소스)
- ✅ 위협 인텔리전스 (멀웨어, Botnet, WebFilter)
- ✅ 트래픽 분석 (대역폭, 프로토콜, 애플리케이션)
- ✅ 성능 모니터링 (CPU, 메모리, 세션)
- ✅ 설정 관리 + Slack 드릴다운 알림
- ✅ Slack 설정 UI (Webhook URL 입력)
- ✅ 실시간 이벤트 스트림

**특징**:
- WCAG Level AA 색상 준수
- Global filters (장비, 시간, 심각도)
- 설정 변경 행 클릭 → Slack 자동 알림
- 세션 기반 Webhook URL 저장

---

## 📦 레거시 대시보드 (개별)

### fortinet-config-management-final.xml
**설정 관리 + Slack 통합 (구버전)**
- 25KB, Slack 알림 기능
- ⚠️ `fortinet-dashboard.xml`에 통합됨

### splunk-advanced-dashboard.xml
**고급 분석 대시보드**
- 24KB, 복잡한 SPL 쿼리
- ⚠️ `fortinet-dashboard.xml`에 통합됨

### fortigate-security-overview.xml
**보안 개요**
- 6.5KB, 기본 보안 지표
- ⚠️ `fortinet-dashboard.xml`에 통합됨

### threat-intelligence.xml
**위협 인텔**
- 4.7KB, 멀웨어/Botnet
- ⚠️ `fortinet-dashboard.xml`에 통합됨

### traffic-analysis.xml
**트래픽 분석**
- 5.0KB, 대역폭/프로토콜
- ⚠️ `fortinet-dashboard.xml`에 통합됨

### performance-monitoring.xml
**성능 모니터링**
- 5.0KB, CPU/메모리
- ⚠️ `fortinet-dashboard.xml`에 통합됨

---

## 🚀 배포

```bash
# 통합 대시보드 배포
cd /home/jclee/app/splunk
node scripts/deploy-dashboards.js

# 또는 Splunk Web UI
Settings → Dashboards → Import from XML
→ fortinet-dashboard.xml 선택
```

---

## 🔔 Slack 설정

### 1단계: Webhook URL 생성
```
https://api.slack.com/apps
→ Create New App
→ Incoming Webhooks → Activate
→ Add New Webhook → 채널 선택
```

### 2단계: 대시보드에서 설정
```
1. fortinet-dashboard.xml 열기
2. "🔧 Slack Webhook 설정" 패널에서 URL 입력
3. 채널 선택 (#splunk-alerts)
4. 최소 심각도 선택 (high 권장)
```

### 3단계: 백그라운드 프록시 실행
```bash
cd /home/jclee/app/splunk
echo "SLACK_WEBHOOK_URL=YOUR_URL" >> .env
pm2 start index.js --name slack-proxy
pm2 save
```

### 4단계: 테스트
```bash
# CLI 테스트
node scripts/slack-alert-cli.js --webhook="URL" --test

# 대시보드 테스트
"📢 설정 변경 이력" 테이블에서 행 클릭 → Slack 알림
```

---

## 📊 인덱스 정보

- **프로덕션**: `index=fw`
- **테스트**: `index=fortigate_security`

---

**권장**: `fortinet-dashboard.xml` 사용
**상태**: 프로덕션 준비 완료
**업데이트**: 2025-10-20
