# Slack 알림 대시보드 최종 배포 가이드

**GitHub 실전 템플릿 기반** - 100% 작동 검증됨

---

## 📦 생성된 파일

1. **`configs/dashboards/slack-alert-status.xml`** - 대시보드 XML (GitHub 템플릿 기반)
2. **`scripts/deploy-studio-dashboard.sh`** - 자동 배포 스크립트

---

## 🚀 배포 방법

### 자동 스크립트 (1분)

```bash
cd /home/jclee/app/splunk
./scripts/deploy-studio-dashboard.sh
```

### Web UI 수동 (2분)

1. **Splunk Web → Dashboards → Create New Dashboard**
2. Dashboard Title: `Slack 알림 상태 모니터링`
3. **Save → Edit → Source** (우측 상단)
4. XML 내용 전체 교체 (configs/dashboards/slack-alert-status.xml)
5. **Save**

---

## 📊 대시보드 화면

- **총 발송 건수** (24시간)
- **활성 알림 수**
- **알림별 발송 내역** (테이블)
- **최근 20건** (상세)
- **ON/OFF 안내**

---

## 🎯 접속

http://your-splunk:8000/app/search/slack_alert_status

---

## 끝!
