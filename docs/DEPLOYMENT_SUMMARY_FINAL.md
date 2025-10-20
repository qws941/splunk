# Fortinet Splunk Dashboard 배포 요약 (Proxy Slack 통합)

## 🎯 구현 완료 사항

### 1. 대시보드 생성
- **파일**: `dashboards/fortinet-config-management-final.xml`
- **특징**:
  - ✅ index=fw 기반 (FAZ/FMG 로그)
  - ✅ dedup 중복 제거
  - ✅ Hidden Panel + sendalert 패턴
  - ✅ Proxy 서버 지원
  - ✅ Splunk 재기동 불필요

### 2. Slack 알림 통합
- **방식**: Hidden Panel → sendalert → Webhook Alert Action → Proxy → Slack
- **알림 트리거**:
  - 📢 설정 변경 이력 (클릭)
  - 📢 방화벽 정책 변경 (클릭)
  - 📢 VPN 설정 변경 (클릭)
  - 📢 Critical 이벤트 (클릭)

### 3. 문서 생성
- **PRD_DEPLOYMENT_GUIDE.md** - 배포 가이드 (Proxy 지원)
- **PROXY_SLACK_SETUP_GUIDE.md** - Proxy 설정 상세 가이드
- **DEPLOYMENT_SUMMARY_FINAL.md** - 이 파일

---

## 🚀 Quick Start

### Step 1: Proxy 및 Webhook 설정

**방법 1: Web UI** (권장)
```
Splunk Web UI → Settings → Alert actions → Webhook
  - HTTP Proxy: http://your-proxy-server:3128
  - HTTPS Proxy: https://your-proxy-server:3128
  - Save (재시작 불필요)
```

**방법 2: 설정 파일**
```bash
# $SPLUNK_HOME/etc/apps/search/local/alert_actions.conf
cat <<EOF >> $SPLUNK_HOME/etc/apps/search/local/alert_actions.conf

[webhook]
disabled = 0
http_proxy = http://your-proxy-server:3128
https_proxy = https://your-proxy-server:3128

[fortinet_slack]
disabled = 0
is_custom = 1
label = Fortinet Slack Alert
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF
```

### Step 2: 대시보드 배포

```bash
# 환경 변수 설정
export SPLUNK_HOST=splunk.jclee.me
export SPLUNK_PORT=8089
export SPLUNK_USERNAME=admin
export SPLUNK_PASSWORD=your_password

# 배포
cd /home/jclee/app/splunk
node scripts/deploy-dashboards.js
```

**출력 예시:**
```
🚀 Deploying Splunk Dashboards via REST API...

📡 Target: https://splunk.jclee.me:8089
📦 App: search
👤 User: admin

📊 Deploying: Fortinet 설정 관리 (PRD - Proxy Slack 통합)...
✅ Dashboard deployed: Fortinet 설정 관리 (PRD - Proxy Slack 통합)

📊 Deployment Summary:
   ✅ Deployed: 5
   ❌ Failed: 0
   📁 Total: 5

🌐 Access dashboards at:
   https://splunk.jclee.me/app/search/dashboards
```

### Step 3: 알림 테스트

1. **대시보드 접속**:
   ```
   https://splunk.jclee.me/app/search/fortinet-config-management-final
   ```

2. **테이블 행 클릭** (📢 아이콘 표시):
   - 설정 변경 이력
   - 방화벽 정책 변경
   - VPN 설정 변경
   - Critical 이벤트

3. **Slack 채널 확인**:
   - `#splunk-alerts` 채널에서 알림 수신 확인

---

## 📊 대시보드 구성

### Row 1: 운영 현황 요약 (5개 메트릭)
- 전체 이벤트
- 설정 변경
- 관리 장비
- Critical 이벤트
- 활성 관리자

### Row 2: 📢 설정 변경 이력 (Slack 알림)
- cfgpath/cfgobj/cfgattr 상세 파싱
- 중복 제거 (dedup)
- 설정 분류별 색상 코딩
- **클릭 → Slack 알림**

**SPL 쿼리 핵심**:
```spl
index=fw devname=$device_filter$ (logid="0100044547" OR logid="0100044546" OR logid="0100044545")
| rex field=_raw "cfgpath=\"?(?<cfg_path>[^\"]+)\"?"
| rex field=_raw "cfgobj=\"?(?<cfg_object>[^\"]+)\"?"
| dedup _time devname config_path config_object parsed_value
| eval change_type = case(
    logid="0100044547", "삭제",
    logid="0100044546", "수정",
    logid="0100044545", "추가"
  )
| eval path_category = case(
    match(config_path, "firewall\.policy"), "방화벽 정책",
    match(config_path, "vpn\.ipsec"), "IPSec VPN",
    match(config_path, "vpn\.ssl"), "SSL VPN",
    ...
  )
```

### Row 3: 📢 방화벽 정책 변경 (Slack 알림)
- firewall.policy 전용
- 정책명, 변경내용 파싱
- **클릭 → Slack 알림**

### Row 4: 📢 VPN 및 인터페이스 (Slack 알림)
- VPN 설정 변경 (IPSec/SSL)
- 시스템 인터페이스 변경
- **클릭 → Slack 알림**

### Row 5: 관리자 활동
- 로그인/로그아웃 추적
- 관리자별 설정 변경 통계

### Row 6: 📢 Critical 이벤트 (Slack 알림)
- Update Fail 제외
- 이벤트 분류별 필터링
- **클릭 → Slack 알림**

### Row 7: 실시간 이벤트 스트림
- 15분 범위
- 30초 자동 갱신

---

## 🔔 Slack 알림 예시

### 설정 변경 알림
```
🟡 설정변경: FW-01 - 방화벽 정책 (policy-001) by admin

장비: FW-01
관리자: admin
작업유형: 삭제
설정분류: 방화벽 정책
객체명: policy-001
설정값: srcaddr[192.168.1.0/24]
접속방법: GUI
접속IP: 203.0.113.50
시간: 2025-10-15 14:30:22
```

### Critical 이벤트 알림
```
🔴 CRITICAL: FW-01 - 하드웨어 (Disk failure detected)

장비: FW-01
심각도: critical
이벤트분류: 하드웨어
유형: System Event
메시지: Disk failure detected on /dev/sda1
시간: 2025-10-15 14:35:10
```

### VPN 변경 알림
```
🟠 VPN변경: FW-01 - VPN-BRANCH-01 (IPSec) by admin

장비: FW-01
관리자: admin
VPN유형: IPSec
VPN명: VPN-BRANCH-01
작업: 수정
속성: remote-gw
값: 203.0.113.10
시간: 2025-10-15 14:40:55
```

---

## 🔧 기술 상세

### Hidden Panel + sendalert 패턴

**실행 흐름:**
```
1. 사용자 클릭 (테이블 행)
   ↓
2. Drilldown 이벤트
   ↓
3. 토큰 설정 (trigger_config_alert=1)
   ↓
4. Hidden Panel 활성화
   ↓
5. sendalert fortinet_slack 실행
   ↓
6. Splunk Webhook Alert Action
   ↓
7. Proxy 서버 경유
   ↓
8. Slack API POST
   ↓
9. <done> 핸들러 → 토큰 초기화
```

### Proxy 설정

**alert_actions.conf**:
```ini
[webhook]
http_proxy = http://your-proxy-server:3128
https_proxy = https://your-proxy-server:3128

[fortinet_slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**환경 변수** (선택):
```bash
export http_proxy=http://your-proxy-server:3128
export https_proxy=https://your-proxy-server:3128
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 🛠️ Troubleshooting

### Proxy 연결 테스트
```bash
curl -x http://your-proxy-server:3128 https://hooks.slack.com/services/TEST
```

### sendalert 수동 테스트
```spl
| makeresults
| eval message="Test Alert"
| eval severity="medium"
| sendalert fortinet_slack param.message="$result.message$"
```

### Splunk 로그 확인
```bash
tail -f $SPLUNK_HOME/var/log/splunk/splunkd.log | grep -i webhook
tail -f $SPLUNK_HOME/var/log/splunk/splunkd.log | grep -i fortinet_slack
```

### 데이터 확인
```spl
index=fw | stats count
index=fw logid="0100044547" | head 10
```

---

## 📚 파일 구조

```
/home/jclee/app/splunk/
├── dashboards/
│   ├── fortinet-config-management-final.xml  ← 메인 대시보드
│   ├── fortigate-security-overview.xml
│   ├── threat-intelligence.xml
│   ├── traffic-analysis.xml
│   └── performance-monitoring.xml
│
├── scripts/
│   ├── deploy-dashboards.js                  ← 배포 스크립트
│   └── ...
│
├── docs/ (또는 루트)
│   ├── PRD_DEPLOYMENT_GUIDE.md               ← 배포 가이드
│   ├── PROXY_SLACK_SETUP_GUIDE.md            ← Proxy 설정 가이드
│   ├── DEPLOYMENT_SUMMARY_FINAL.md           ← 이 파일
│   ├── DASHBOARD_SLACK_INTEGRATION.md        ← 이전 접근 (참고)
│   └── README_DASHBOARDS.md
│
└── domains/
    └── integration/
        ├── splunk-rest-client.js             ← REST API 클라이언트 (참고)
        └── ...
```

---

## ✅ Checklist

### 배포 전
- [ ] Slack Webhook URL 생성 완료
- [ ] Proxy 서버 주소 확인
- [ ] Splunk 접속 정보 준비 (host, port, username, password)
- [ ] index=fw 데이터 확인 (`index=fw | stats count`)

### 배포
- [ ] alert_actions.conf 설정 (Proxy + Webhook URL)
- [ ] 대시보드 배포 (`node scripts/deploy-dashboards.js`)
- [ ] 대시보드 접속 확인 (`https://splunk.jclee.me/app/search/dashboards`)

### 테스트
- [ ] 데이터 표시 확인 (중복 제거 확인)
- [ ] 테이블 클릭 → Slack 알림 수신 확인
- [ ] Proxy 로그에서 Slack 요청 확인
- [ ] 모든 알림 패널 (4개) 테스트 완료

---

## 🎯 Next Steps (선택 사항)

### 1. Python 스크립트로 고도화
- 더 정교한 Slack 메시지 포맷
- 심각도별 색상 자동 변경
- 추가 필드 매핑

**위치**: `$SPLUNK_HOME/etc/apps/search/bin/fortinet_slack.py`
**참고**: `PROXY_SLACK_SETUP_GUIDE.md`

### 2. n8n Workflow 연동
- Slack 알림을 n8n으로 전달
- 추가 자동화 (티켓 생성, 이메일 등)

### 3. Grafana 시각화
- Splunk → Prometheus → Grafana
- 장기 트렌드 분석

### 4. 알림 조건 커스터마이징
- 특정 관리자만 알림
- 특정 설정 객체만 알림
- Rate Limiting (알림 빈도 제한)

---

## 📊 Summary

| 항목 | 상태 |
|------|------|
| **Splunk 재기동** | ❌ 불필요 |
| **Proxy 지원** | ✅ HTTP/HTTPS |
| **index=fw 활용** | ✅ 완료 |
| **중복 제거** | ✅ dedup 적용 |
| **Slack 알림** | ✅ 클릭 → Proxy → Slack |
| **설정 방법** | ✅ Web UI 또는 alert_actions.conf |
| **Hidden Panel + sendalert** | ✅ 구현 완료 |
| **PRD 배포** | ✅ 즉시 가능 |

---

**작성일**: 2025-10-15
**버전**: 2.0.0 (Proxy Support)
**작성자**: Claude Code
**프로젝트**: FortiAnalyzer to Splunk HEC Integration
