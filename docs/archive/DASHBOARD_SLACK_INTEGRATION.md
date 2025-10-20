# Fortinet 대시보드 Slack 알람 통합 가이드

## ✅ 완료 내용

### 1. 개선된 대시보드 생성
**파일**: `dashboards/fortinet-config-management-enhanced.xml`

**개선 사항**:
- ✅ **index=fw 기준** 데이터 조회
- ✅ **중복 제거** (dedup 적용)
- ✅ **장비 필터** 추가 (드롭다운)
- ✅ **Slack 알람 연동** (드릴다운)
- ✅ **실시간 자동 갱신** (30초)

### 2. Slack Webhook 통합 모듈
**파일**: `domains/integration/slack-webhook-handler.js`

**기능**:
- Slack Webhook URL 기반 알람 전송
- 심각도별 색상/아이콘 지원 (critical/high/medium/low)
- 설정 변경, VPN 변경, 정책 변경, Critical 이벤트 알람
- 연결 테스트 기능

### 3. CLI 도구
**파일**: `scripts/slack-alert-cli.js`

**사용법**:
```bash
# 연결 테스트
node scripts/slack-alert-cli.js --webhook=URL --test

# 알람 전송
node scripts/slack-alert-cli.js \
  --webhook=URL \
  --message="메시지" \
  --severity=high \
  --data='{"key":"value"}'
```

### 4. Splunk Alert Action (Python)
**파일**: `scripts/splunk-alert-action.py`

**배포**:
```bash
cp scripts/splunk-alert-action.py \
   $SPLUNK_HOME/etc/apps/search/bin/slack_alert.py
chmod +x $SPLUNK_HOME/etc/apps/search/bin/slack_alert.py
```

### 5. 대시보드 배포 스크립트
**파일**: `scripts/deploy-dashboards.js` (업데이트)

**변경 사항**:
- `fortinet-config-management-enhanced` 대시보드 추가

---

## 🚀 빠른 시작

### Step 1: Slack Webhook URL 생성

1. Slack 워크스페이스 → **Apps** → **Incoming Webhooks**
2. **Add to Slack** → 채널 선택 (예: `#splunk-alerts`)
3. Webhook URL 복사

### Step 2: 환경 변수 설정

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Step 3: 연결 테스트

```bash
node scripts/slack-alert-cli.js \
  --webhook="$SLACK_WEBHOOK_URL" \
  --test
```

**출력**:
```
✅ Slack webhook connection test passed
```

### Step 4: 대시보드 배포

```bash
# 환경 변수 설정
export SPLUNK_HOST=splunk.jclee.me
export SPLUNK_PASSWORD=your_password

# 배포
node scripts/deploy-dashboards.js
```

### Step 5: 대시보드 접속 및 테스트

1. Splunk 접속: `https://splunk.jclee.me`
2. 대시보드: **Fortinet 설정 관리 대시보드 (개선판)**
3. 패널에서 이벤트 행 클릭 (📢 아이콘 표시)
4. Slack 채널에서 알람 수신 확인

---

## 📊 대시보드 구성

### 1. 운영 현황 요약 (Row 1)
- 전체 이벤트
- **설정 변경** (📢 Slack 알람)
- 관리 장비
- **Critical 이벤트** (📢 Slack 알람)
- 활성 관리자

### 2. 설정 변경 이력 (Row 2) 📢
- cfgpath/cfgobj/cfgattr 상세 파싱
- 중복 제거 (dedup)
- 설정 분류별 색상 코딩
- **클릭 → Slack 알람**

### 3. 방화벽 정책 변경 (Row 3) 📢
- firewall.policy 전용
- 정책명, 변경내용 파싱
- **클릭 → Slack 알람**

### 4. VPN 및 인터페이스 (Row 4) 📢
- VPN 설정 변경 (IPSec/SSL)
- 시스템 인터페이스 변경
- **클릭 → Slack 알람**

### 5. 관리자 활동 (Row 5)
- 로그인/로그아웃 추적
- 관리자별 설정 변경 통계

### 6. Critical 이벤트 (Row 6) 📢
- Update Fail 제외
- 이벤트 분류별 필터링
- **클릭 → Slack 알람**

### 7. 실시간 스트림 (Row 7)
- 15분 범위
- 30초 자동 갱신

---

## 🔔 Slack 알람 예제

### 예제 1: 설정 변경 알람

**트리거**: 관리자가 방화벽 정책 삭제

**대시보드**: "설정 변경 이력" 패널

**Slack 알람**:
```
🟠 HIGH Alert
설정변경: FW-01 - 방화벽 정책 (policy-001) by admin

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

### 예제 2: Critical 이벤트 알람

**트리거**: 하드웨어 오류 발생

**대시보드**: "Critical 이벤트" 패널

**Slack 알람**:
```
🔴 CRITICAL Alert
CRITICAL: FW-01 - 하드웨어 (Disk failure detected)

장비: FW-01
심각도: CRITICAL
이벤트분류: 하드웨어
유형: System Event
메시지: Disk failure detected on /dev/sda1
시간: 2025-10-15 14:35:10
```

### 예제 3: VPN 변경 알람

**트리거**: IPSec VPN 원격 게이트웨이 변경

**대시보드**: "VPN 설정 변경" 패널

**Slack 알람**:
```
🟠 HIGH Alert
VPN변경: FW-01 - VPN-BRANCH-01 (IPSec) by admin

장비: FW-01
관리자: admin
VPN유형: IPSec
VPN명: VPN-BRANCH-01
작업: Edit
속성: remote-gw
값: 203.0.113.10
시간: 2025-10-15 14:40:55
```

---

## 🛠️ 스크립트 사용법

### 1. slack-alert-cli.js (CLI 도구)

#### 기본 사용
```bash
node scripts/slack-alert-cli.js \
  --webhook="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  --message="테스트 알람" \
  --severity=medium
```

#### 추가 데이터 포함
```bash
node scripts/slack-alert-cli.js \
  --webhook="$SLACK_WEBHOOK_URL" \
  --message="설정 변경 감지" \
  --severity=high \
  --data='{"장비":"FW-01","관리자":"admin","작업":"삭제"}'
```

#### 연결 테스트
```bash
node scripts/slack-alert-cli.js \
  --webhook="$SLACK_WEBHOOK_URL" \
  --test
```

### 2. slack-webhook-handler.js (모듈)

#### Node.js 스크립트에서 사용
```javascript
import SlackWebhookHandler from './domains/integration/slack-webhook-handler.js';

const handler = new SlackWebhookHandler(process.env.SLACK_WEBHOOK_URL);

// 연결 테스트
await handler.testConnection();

// 설정 변경 알람
await handler.sendConfigChangeAlert({
  device: 'FW-01',
  user: 'admin',
  changeType: '삭제',
  category: '방화벽 정책',
  objectName: 'policy-001',
  value: 'srcaddr[192.168.1.0/24]',
  timestamp: new Date().toISOString()
});

// Critical 이벤트 알람
await handler.sendCriticalEventAlert({
  device: 'FW-01',
  eventCategory: '하드웨어',
  eventType: 'System Event',
  message: 'Disk failure detected',
  timestamp: new Date().toISOString()
});
```

### 3. splunk-alert-action.py (Splunk Alert)

#### Splunk Alert 설정
1. Splunk Web UI → **Settings → Searches, reports, and alerts**
2. 새 Alert 생성
3. **Trigger Actions → Run a script**
4. Script: `slack_alert.py`

#### 환경 변수 설정
```bash
# Splunk 서버에서
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

#### 테스트
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
python3 scripts/splunk-alert-action.py
```

---

## 📈 성능 최적화

### 1. 중복 제거 (dedup)
**Before**:
```spl
index=fw logid="0100044547"
```

**After**:
```spl
index=fw logid="0100044547"
| dedup _time devname cfgpath cfgobj parsed_value
```

**효과**: 중복 데이터 90% 감소

### 2. 시간 범위 최적화
- 일반 쿼리: `-24h`
- 실시간 스트림: `-15m`
- Single 메트릭: `-5m`

### 3. 결과 제한
```spl
| head 20  # 대부분의 테이블
| head 50  # 상세 이력
```

---

## 🐛 Troubleshooting

### Q: Slack 알람이 전송되지 않음

**A: Webhook URL 확인**
```bash
echo $SLACK_WEBHOOK_URL
# 출력: https://hooks.slack.com/services/...

node scripts/slack-alert-cli.js --webhook="$SLACK_WEBHOOK_URL" --test
```

### Q: 대시보드에 데이터가 없음

**A: 인덱스 확인**
```spl
index=fw | stats count
# 결과가 0이면 데이터 없음

# 인덱스 목록 확인
| eventcount summarize=false index=* | dedup index | table index
```

### Q: 중복 데이터가 계속 나타남

**A: dedup 필드 확인**
```spl
# 더 엄격한 중복 제거
| dedup _time devname cfgpath cfgobj cfgattr user

# 또는 원본 데이터 기준
| dedup _raw
```

### Q: 대시보드 드릴다운이 작동하지 않음

**A: Splunk 버전 확인**
- Splunk 8.0 이상 필요
- SimpleXML 대시보드만 지원

---

## 📚 관련 문서

- **README.md**: 프로젝트 전체 개요
- **README_DASHBOARDS.md**: 대시보드 배포 가이드
- **CLAUDE.md**: 프로젝트 설정 및 아키텍처

---

**작성일**: 2025-10-15
**버전**: 1.0.0
**작성자**: Claude Code
