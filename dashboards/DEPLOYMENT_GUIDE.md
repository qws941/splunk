# FortiGate 보안 대시보드 배포 가이드

## 📊 대시보드 개요

**파일**: `fortinet-dashboard.xml`
**크기**: 31KB (755 lines)
**패널**: 32개 (8 sections + 1 hidden section)
**인덱스**: `index=fw`
**버전**: v2.0 (Unified + Slack Integration)

---

## 🎯 주요 기능

### 1. 보안 모니터링 (8 Sections)

```
✅ Row 1: 핵심 KPI (5 panels)
   - Critical 이벤트, 차단 공격, 위협 소스, 전체 이벤트, 설정 변경

✅ Row 2: 보안 이벤트 분석 (3 panels)
   - 타임라인 차트, 공격 유형 분포, Top 10 공격 IP

✅ Row 3: 위협 인텔리전스 (4 panels)
   - 멀웨어, Botnet, WebFilter, SSL 검사

✅ Row 4: 트래픽 분석 (3 panels)
   - 대역폭, 프로토콜, Top 10 애플리케이션

✅ Row 5: 성능 모니터링 (4 panels)
   - CPU, 메모리, 활성 세션, 디바이스 상태

✅ Row 6: 설정 관리 (1 panel)
   - 설정 변경 이력 (Drilldown → Slack 알림)

✅ Row 7: Slack 설정 UI (2 panels)
   - Webhook URL 입력, 채널 선택, 심각도 필터
   - 설정 가이드 (Step-by-step)

✅ Row 8: 실시간 이벤트 스트림 (1 panel)
   - 30초 자동 새로고침
```

### 2. Slack 알림 통합 ⭐

**대시보드에서 설정 가능**:
```
✅ Slack Webhook URL 입력 (text input)
✅ 알림 채널 선택 (#splunk-alerts, #security, #fortigate, #operations)
✅ 최소 심각도 필터 (critical, high, medium, low)
✅ URL 유효성 검증 (정규식 기반)
```

**자동 알림 생성 (Drilldown 기반)**:
```
1. "📢 설정 변경 이력" 테이블에서 행 클릭
2. Hidden Row가 나타남 (depends="$trigger_config_alert$")
3. 3개 패널 자동 생성:
   - 📩 알림 준비 메시지
   - 💬 Slack 메시지 미리보기
   - 📋 curl 명령어 자동 생성 (복사-붙여넣기)
4. 닫기 버튼 클릭 → Hidden Row 숨김
```

**Slack 메시지 포맷**:
```markdown
🟠 *Fortinet Dashboard Alert*

*[설정변경]* 방화벽 정책
━━━━━━━━━
🖥️ 장비: `FW-01`
🔄 변경유형: *삭제*
📋 대상: `policy-100`
👤 관리자: admin
🌐 접속IP: 192.168.1.100
🕒 시간: 2025-10-20 14:30:00
⚠️ 심각도: *high*
```

---

## 🚀 배포 방법

### Option 1: Splunk Web UI (권장)

```bash
1. Splunk Web 로그인 (http://splunk:8000)
2. Settings → User Interface → Dashboards
3. "Create New Dashboard" → "Import from XML"
4. fortinet-dashboard.xml 파일 선택
5. Dashboard ID: "fortinet_dashboard"
6. App: Search & Reporting (또는 커스텀 앱)
7. Permissions: Shared in App
8. Save
```

### Option 2: 자동 배포 스크립트

```bash
cd /home/jclee/app/splunk
node scripts/deploy-dashboards.js
```

**스크립트 기능**:
- Splunk REST API 사용
- 기존 대시보드 자동 업데이트
- 권한 자동 설정 (Shared in App)
- 배포 결과 로깅

### Option 3: Splunk CLI

```bash
# Splunk 서버에서 직접 실행
$SPLUNK_HOME/bin/splunk add dashboard fortinet_dashboard \
  -description "FortiGate 보안 대시보드" \
  -eai:data @/home/jclee/app/splunk/dashboards/fortinet-dashboard.xml \
  -auth admin:changeme
```

---

## 🔧 Slack 설정 (Step-by-Step)

### Step 1: Slack Webhook URL 생성

```
1. https://api.slack.com/apps → "Create New App"
2. "From scratch" → App Name: "Splunk Alerts"
3. Workspace 선택
4. "Incoming Webhooks" → Toggle On
5. "Add New Webhook to Workspace"
6. 채널 선택 (#splunk-alerts 권장)
7. "Allow" 클릭
8. Webhook URL 복사 (https://hooks.slack.com/services/...)
```

### Step 2: 대시보드에서 설정

```
1. Splunk에서 "FortiGate 보안 대시보드" 열기
2. "🔧 Slack Webhook 설정" 섹션 찾기
3. Webhook URL 붙여넣기
4. 채널 선택 (#splunk-alerts)
5. 최소 심각도 선택 (High 이상 권장)
6. "📌 현재 설정 값" 테이블에서 ✅ Valid URL 확인
```

### Step 3: 알림 테스트

**방법 1: 대시보드에서 직접**
```
1. "📢 설정 변경 이력" 테이블에서 아무 행이나 클릭
2. Hidden Row가 나타남 (3개 패널)
3. "📋 터미널 실행 명령어" 패널에서 curl 명령어 복사
4. 터미널에 붙여넣기 → Enter
5. Slack 채널에서 알림 확인
```

**방법 2: CLI 스크립트**
```bash
cd /home/jclee/app/splunk
export SLACK_WEBHOOK_URL="대시보드에 입력한 URL"
node scripts/slack-alert-cli.js \
  --webhook="$SLACK_WEBHOOK_URL" \
  --message="방화벽 정책 변경 감지" \
  --severity=high \
  --test
```

### Step 4: 자동화 (선택사항)

**백그라운드 프록시 서버 실행** (권장):
```bash
cd /home/jclee/app/splunk

# .env 파일에 Webhook URL 저장
echo "SLACK_WEBHOOK_URL=YOUR_URL" >> .env
echo "SLACK_CHANNEL=#splunk-alerts" >> .env
echo "SLACK_ENABLED=true" >> .env

# PM2로 백그라운드 실행
pm2 start index.js --name slack-proxy

# 시스템 재시작 시 자동 시작
pm2 save
pm2 startup

# 상태 확인
pm2 status
pm2 logs slack-proxy
```

---

## 🎨 디자인 사양

### 색상 팔레트 (WCAG Level AA 준수)

```
Critical: #D93F3C 🔴 (빨강)
High:     #F8BE34 🟠 (주황)
Medium:   #87CEEB 🟡 (하늘색)
Low:      #53A051 🟢 (초록)
Info:     #6C757D 🔵 (회색)
```

### Global Filters

```xml
✅ device_filter    - 장비 선택 (devname 기반)
✅ time_picker      - 시간 범위 (-24h@h ~ now)
✅ severity_filter  - 심각도 필터 (critical/high/medium/low)
```

### Chart Types

```
Single Value:    14개 (KPI, 위협 인텔, 성능)
Timeline Chart:  2개 (보안 이벤트, 대역폭)
Pie Chart:       1개 (공격 유형)
Bar Chart:       1개 (프로토콜)
Table:           4개 (공격 IP, 애플리케이션, 설정 변경, curl 명령어)
Event Stream:    1개 (실시간 이벤트)
HTML Panel:      5개 (섹션 헤더, 가이드, 알림)
```

---

## 📋 SPL 쿼리 샘플

### Critical 이벤트 카운트
```spl
index=fw devname=$device_filter$
(level=critical OR level=alert OR level=emergency)
earliest=$time_picker.earliest$ latest=$time_picker.latest$
| search NOT msg="*Update Fail*"
| stats count
```

### 공격 소스 IP Top 10
```spl
index=fw devname=$device_filter$
(action=deny OR action=block)
earliest=$time_picker.earliest$ latest=$time_picker.latest$
| stats count as attack_count by srcip, srccountry
| sort - attack_count
| head 10
```

### 설정 변경 이력
```spl
index=fw devname=$device_filter$
(logid="0100044547" OR logid="0100044546" OR logid="0100044545")
earliest=$time_picker.earliest$ latest=$time_picker.latest$
| rex field=_raw "cfgpath=\"?(?<cfg_path>[^\"]+)\"?"
| rex field=_raw "cfgobj=\"?(?<cfg_object>[^\"]+)\"?"
| eval change_type = case(
    logid="0100044547", "삭제",
    logid="0100044546", "수정",
    logid="0100044545", "추가",
    1=1, "기타"
  )
| table _time, devname, user, change_type, cfg_path, cfg_object
| sort - _time
```

---

## 🔍 트러블슈팅

### 문제 1: 대시보드가 로드되지 않음

**증상**: "Dashboard not found" 오류

**해결**:
```bash
# 1. 대시보드 존재 확인
curl -k -u admin:password https://splunk:8089/servicesNS/-/-/data/ui/views/fortinet_dashboard

# 2. 권한 확인
Settings → Dashboards → fortinet_dashboard → Permissions → "Everyone (Read, Write)"

# 3. 재배포
node scripts/deploy-dashboards.js
```

### 문제 2: 데이터가 표시되지 않음

**증상**: "No results found" 또는 빈 패널

**해결**:
```bash
# 1. 인덱스 확인
index=fw | head 10

# 2. 시간 범위 확장
Time Picker: Last 7 days

# 3. 장비 필터 확인
device_filter: * (전체)

# 4. Splunk에 데이터가 있는지 확인
| metadata type=sourcetypes index=fw
```

### 문제 3: Slack 알림이 전송되지 않음

**증상**: curl 명령어 실행 시 오류

**해결**:
```bash
# 1. Webhook URL 유효성 검증
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text":"Test message"}'

# 예상 응답: "ok"

# 2. 네트워크 연결 확인
ping hooks.slack.com

# 3. JSON 이스케이프 확인
# \" 대신 ' 사용 또는 heredoc 사용

# 4. 프록시 서버 상태 확인
pm2 status slack-proxy
pm2 logs slack-proxy --lines 50
```

### 문제 4: Hidden Row가 나타나지 않음

**증상**: 설정 변경 행 클릭 시 아무 반응 없음

**해결**:
```bash
# 1. 브라우저 콘솔 확인
F12 → Console → JavaScript 오류 확인

# 2. Token 확인
Dashboard → Edit → 우측 상단 "Show Token Values"
→ trigger_config_alert 토큰이 설정되는지 확인

# 3. Drilldown 옵션 확인
<option name="drilldown">row</option>  # "none"이 아닌지 확인

# 4. 브라우저 캐시 클리어
Ctrl + Shift + R (강제 새로고침)
```

---

## 📈 성능 최적화

### 쿼리 최적화 팁

```spl
# ❌ 느림: 전체 이벤트 스캔
index=fw | where level="critical"

# ✅ 빠름: 인덱스 시간에 필터링
index=fw level=critical

# ❌ 느림: eval 후 stats
index=fw | eval severity=... | stats count by severity

# ✅ 빠름: stats 후 eval
index=fw | stats count by level | eval severity=...

# ❌ 느림: 정규식 남용
index=fw | rex ... | rex ... | rex ...

# ✅ 빠름: tstats 사용 (가능한 경우)
| tstats count where index=fw by sourcetype
```

### 대시보드 로딩 속도 개선

```
✅ 시간 범위 제한 (기본: 24시간)
✅ 패널당 결과 제한 (head 10, head 20)
✅ 불필요한 필드 제거 (fields 명령어)
✅ 캐시 활용 (base search 사용)
✅ Auto-refresh 비활성화 (정적 대시보드)
```

---

## 🎯 다음 단계

### Phase 1: 기본 배포 ✅
- [x] XML 파일 생성
- [x] Splunk 배포
- [x] Slack 설정 UI 추가
- [x] 기본 알림 테스트

### Phase 2: 고급 기능 (선택)
- [ ] Splunk Alert Action 구현 (Python)
- [ ] JavaScript 기반 실시간 Webhook 호출
- [ ] Slack App Manifest 생성 (자동 설치)
- [ ] 대시보드 PDF 내보내기 자동화

### Phase 3: 확장 (선택)
- [ ] MS Teams 알림 통합
- [ ] Email 알림 추가
- [ ] PagerDuty 통합
- [ ] ServiceNow 티켓 생성

---

## 📞 지원

**문서**:
- `/home/jclee/app/splunk/dashboards/README.md` - 대시보드 목록
- `/home/jclee/app/splunk/CLAUDE.md` - 프로젝트 전체 가이드
- `/home/jclee/app/splunk/README_DASHBOARDS.md` - SPL 쿼리 가이드

**스크립트**:
- `scripts/deploy-dashboards.js` - 자동 배포
- `scripts/slack-alert-cli.js` - CLI 알림 테스트
- `scripts/generate-mock-data.js` - 테스트 데이터 생성

**문의**: GitHub Issues 또는 Slack #splunk-alerts

---

**버전**: 2.0
**작성일**: 2025-10-20
**상태**: ✅ 프로덕션 준비 완료
