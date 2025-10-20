# Fortinet Dashboard PRD 배포 가이드 (Proxy Slack 통합)

## 🎯 개요

**Splunk 재기동 없이** Proxy 서버를 통한 Slack 알림이 가능한 Fortinet 설정 관리 대시보드입니다.

### 핵심 특징
- ✅ **Splunk 재기동 불필요** - Web UI에서 Alert Action 설정
- ✅ **index=fw 기반** - FAZ/FMG 로그 직접 활용
- ✅ **중복 제거** - dedup으로 깔끔한 데이터
- ✅ **Proxy 지원** - HTTP/HTTPS Proxy 서버 경유
- ✅ **Hidden Panel + sendalert** - 클릭 → 즉시 Slack 전송

---

## 🚀 배포 방법

### 1. 환경 변수 설정

`.env` 파일 또는 환경 변수 설정:

```bash
export SPLUNK_HOST=splunk.jclee.me
export SPLUNK_PORT=8089
export SPLUNK_USERNAME=admin
export SPLUNK_PASSWORD=your_password
```

### 2. 대시보드 배포

```bash
# 배포
node scripts/deploy-dashboards.js
```

**출력 예시:**
```
🚀 Deploying Splunk Dashboards via REST API...

📡 Target: https://splunk.jclee.me:8089
📦 App: search
👤 User: admin

📊 Deploying: Fortinet 설정 관리 (PRD - Slack 통합)...
✅ Dashboard deployed: Fortinet 설정 관리 (PRD - Slack 통합)

📊 Deployment Summary:
   ✅ Deployed: 5
   ❌ Failed: 0
   📁 Total: 5

🌐 Access dashboards at:
   https://splunk.jclee.me/app/search/dashboards
```

### 3. Slack Webhook 설정 (Proxy 지원)

#### 3.1. Slack Webhook URL 생성

1. Slack 워크스페이스 → **Apps** → **Incoming Webhooks**
2. **Add to Slack** 클릭
3. 채널 선택 (예: `#splunk-alerts`)
4. Webhook URL 복사:
   ```
   https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
   ```

#### 3.2. Splunk Alert Action 설정 (Proxy 포함)

**방법 1: Web UI 설정**

1. Splunk Web UI 접속
2. **Settings** → **Alert actions**
3. **Webhook** 클릭
4. **Proxy Settings**:
   - HTTP Proxy: `http://your-proxy-server:3128`
   - HTTPS Proxy: `https://your-proxy-server:3128`
   - (인증 필요 시) `http://username:password@your-proxy-server:3128`
5. **Save**

**방법 2: 설정 파일 편집**

`$SPLUNK_HOME/etc/apps/search/local/alert_actions.conf`:
```ini
[webhook]
disabled = 0
http_proxy = http://your-proxy-server:3128
https_proxy = https://your-proxy-server:3128
```

#### 3.3. Fortinet Slack Alert Action 생성

`$SPLUNK_HOME/etc/apps/search/local/alert_actions.conf`:
```ini
[fortinet_slack]
disabled = 0
is_custom = 1
label = Fortinet Slack Alert
description = Send Fortinet events to Slack via Proxy

# Slack Webhook URL
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Proxy 설정 (webhook action 설정 상속)
# http_proxy = http://your-proxy-server:3128
# https_proxy = https://your-proxy-server:3128
```

**재시작 불필요** - Web UI 설정 변경은 즉시 반영됩니다.

#### 3.4. 알림 테스트

1. 대시보드에서 📢 표시된 패널 (예: "설정 변경 이력")
2. 테이블 행 클릭
3. Slack 채널에서 알림 수신 확인

**예시 알림:**
```
🟡 설정 변경 감지

장비: FW-01
관리자: admin
작업유형: 삭제
설정분류: 방화벽 정책
객체명: policy-001
시간: 2025-10-15 14:30:22
```

---

## 📊 대시보드 구성

### Row 1: 운영 현황 요약
- 전체 이벤트
- 설정 변경
- 관리 장비
- Critical 이벤트
- 활성 관리자

### Row 2: 📢 설정 변경 이력 (Slack 알림)
- cfgpath/cfgobj/cfgattr 파싱
- 중복 제거 (dedup)
- 설정 분류별 색상 코딩
- **클릭 → Slack 알림**

### Row 3: 📢 방화벽 정책 변경 (Slack 알림)
- firewall.policy 전용
- 정책명, 변경내용 파싱
- **클릭 → Slack 알림**

### Row 4: 📢 VPN 및 인터페이스 (Slack 알림)
- VPN 설정 변경 (IPSec/SSL)
- 시스템 인터페이스 변경
- **클릭 → Slack 알림**

### Row 5: 📢 Critical 이벤트 (Slack 알림)
- Update Fail 제외
- 이벤트 분류별 필터링
- **클릭 → Slack 알림**

### Row 6: 관리자 활동
- 로그인/로그아웃 추적
- 관리자별 설정 변경 통계

### Row 7: 실시간 이벤트 스트림
- 15분 범위
- 30초 자동 갱신

---

## 🔧 기술 상세

### Hidden Panel + sendalert 패턴

**대시보드 구조:**
```xml
<!-- 1. 클릭 가능한 테이블 -->
<table id="config_changes_table">
  <search>
    <query>index=fw | ... | dedup ...</query>
  </search>
  <drilldown>
    <set token="slack_device">$row.devname$</set>
    <set token="slack_user">$row.user$</set>
    <set token="trigger_config_alert">1</set>
  </drilldown>
</table>

<!-- 2. Hidden Panel (trigger_config_alert 토큰에 의존) -->
<row depends="$trigger_config_alert$">
  <panel>
    <search>
      <query>
| makeresults
| eval device="$slack_device$", user="$slack_user$"
| sendalert fortinet_slack param.device="$result.device$" param.user="$result.user$"
      </query>
      <done>
        <unset token="trigger_config_alert"></unset>
      </done>
    </search>
  </panel>
</row>
```

**실행 흐름:**
1. 사용자가 테이블 행 클릭
2. Drilldown 이벤트로 토큰 설정 (`trigger_config_alert=1`)
3. Hidden Panel이 토큰 감지 → 검색 실행
4. `sendalert fortinet_slack` 명령 실행
5. Splunk Alert Action → Proxy → Slack
6. `<done>` 핸들러로 토큰 초기화

**특징:**
- ✅ Splunk 서버 재기동 불필요
- ✅ Proxy 서버 지원
- ✅ Web UI에서 Webhook URL 설정
- ✅ 네이티브 Splunk 기능 사용
- ✅ PRD 즉시 배포 가능

### 자동 심각도 분류

| 패널 | 심각도 | 색상 | 이모지 |
|------|--------|------|--------|
| 설정 변경 (삭제) | high | 🟠 Orange | 🟠 |
| 설정 변경 (수정/추가) | medium | 🟡 Yellow | 🟡 |
| 방화벽 정책 | high | 🟠 Orange | 🟠 |
| VPN 변경 | high | 🟠 Orange | 🟠 |
| Critical 이벤트 | critical | 🔴 Red | 🔴 |

---

## 🛠️ Troubleshooting

### Q1: Slack 알림이 전송되지 않음

**A1-1: Alert Action 설정 확인**
```bash
# Splunk Web UI
Settings → Alert actions → fortinet_slack → Enable 확인
```

**A1-2: sendalert 수동 테스트**
```spl
| makeresults
| eval message="Test Alert"
| eval severity="medium"
| sendalert fortinet_slack param.message="$result.message$"
```

**A1-3: Splunk 로그 확인**
```bash
tail -f $SPLUNK_HOME/var/log/splunk/splunkd.log | grep -i webhook
tail -f $SPLUNK_HOME/var/log/splunk/splunkd.log | grep -i fortinet_slack
```

### Q2: 대시보드에 데이터가 없음

**A2: 인덱스 확인**
```spl
index=fw | stats count
```

결과가 0이면 데이터 없음. FAZ/FMG 로그 전송 확인.

### Q3: Proxy 연결 실패

**A3-1: Proxy 서버 확인**
```bash
# Proxy 연결 테스트
curl -x http://your-proxy-server:3128 https://hooks.slack.com/services/TEST

# Splunk에서 환경 변수 확인
$SPLUNK_HOME/bin/splunk show config | grep proxy
```

**A3-2: Proxy 인증 설정**
```ini
# alert_actions.conf
[webhook]
http_proxy = http://username:password@your-proxy-server:3128
https_proxy = https://username:password@your-proxy-server:3128
```

**A3-3: SSL 인증서 오류 (내부 Proxy 사용 시)**
```ini
# alert_actions.conf
[webhook]
ssl_verify = false
```

### Q4: 중복 데이터가 계속 나타남

**A4: dedup 필드 확인**

대시보드 쿼리에 다음이 포함되어 있는지 확인:
```spl
| dedup _time devname cfgpath cfgobj parsed_value
```

---

## 📝 Next Steps

### 선택적 고도화

1. **n8n Workflow 연동** (선택)
   - Slack 알림을 n8n으로 전달
   - 추가 자동화 (티켓 생성, 이메일 등)

2. **Grafana 시각화** (선택)
   - Splunk → Prometheus → Grafana
   - 장기 트렌드 분석

3. **알림 조건 커스터마이징**
   - JavaScript 코드 수정
   - 특정 패턴만 알림 (예: 특정 관리자, 특정 객체)

---

## 🎯 Summary

| 항목 | 상태 |
|------|------|
| Splunk 재기동 | ❌ 불필요 |
| Proxy 지원 | ✅ HTTP/HTTPS |
| index=fw 활용 | ✅ 완료 |
| 중복 제거 | ✅ dedup 적용 |
| Slack 알림 | ✅ 클릭 → Proxy → Slack |
| 설정 방법 | ✅ Web UI 또는 alert_actions.conf |
| Hidden Panel + sendalert | ✅ 구현 완료 |
| PRD 배포 | ✅ 즉시 가능 |

---

## 📚 관련 문서

- **PROXY_SLACK_SETUP_GUIDE.md** - Proxy 설정 상세 가이드
- **DASHBOARD_SLACK_INTEGRATION.md** - 이전 접근 방식 (참고용)
- **README_DASHBOARDS.md** - 대시보드 배포 가이드
- **CLAUDE.md** - 프로젝트 설정 및 아키텍처

---

**작성일**: 2025-10-15
**버전**: 2.0.0 (Proxy Support)
**작성자**: Claude Code
