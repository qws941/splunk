# Splunk Alert Manager 설치 가이드

**생성일**: 2025-10-30
**상태**: ⚠️ DEPRECATED → Enterprise 버전 사용 권장

---

## 🚨 중요 공지

### ❌ Alert Manager (v2.x) - DEPRECATED
- **Splunkbase**: https://splunkbase.splunk.com/app/2665
- **상태**: ⚠️ **더 이상 지원 안 됨**
- **공식 안내**: "This app is deprecated. Please plan to switch to Alert Manager Enterprise"

### ✅ Alert Manager Enterprise (v3.x) - 권장
- **Splunkbase**: https://splunkbase.splunk.com/app/6730
- **GitHub**: https://github.com/alertmanager/alert_manager
- **상태**: ✅ **현재 지원 중**
- **마이그레이션 도구**: 제공됨

---

## 📦 1. Alert Manager Enterprise

### 📊 기본 정보

| 항목 | 내용 |
|------|------|
| **앱 이름** | Alert Manager Enterprise |
| **Splunkbase ID** | 6730 |
| **최신 버전** | v3.6.0 (2025-10-10 릴리스) ⭐ |
| **호환성** | Splunk 10.0, 9.4, 9.3, 9.2 (Enterprise & Cloud) |
| **GitHub** | https://github.com/alertmanager/alert_manager |
| **공식 문서** | https://docs.datapunctum.com/ame/ame-setup |
| **라이선스** | CC BY-NC-SA 4.0 (비상업용) |
| **상업 지원** | https://alertmanager.app |
| **지원 상태** | ✅ Active (개발자 지원 + 커뮤니티) |

### 🎯 주요 기능

1. **알림 이력 관리**
   - 모든 알림 중앙 집중화
   - 이력 추적 및 검색
   - 대시보드로 시각화

2. **워크플로우 관리**
   - 상태 추적: New → In Progress → Resolved
   - 담당자 할당 (reassign)
   - 자동 할당 (auto-assign)
   - 우선순위 설정

3. **알림 조작**
   - 상태 변경 (New, In Progress, Resolved)
   - 심각도 수정 (Low, Medium, High, Critical)
   - 벌크 편집 (여러 알림 동시 처리)
   - 수동 인시던트 생성

4. **통합 기능** ⭐ v3.6.0 신규
   - **다채널 알림**: Mail, Slack, Webhooks, Custom Alert Actions
   - **티켓 시스템**: Jira, ServiceNow (원격 티켓 삭제 지원)
   - **보안 프레임워크**: Cyber Kill Chain, MITRE ATT&CK, NIST, CVE
   - **워크플로우 자동화**: Rule Engine으로 이벤트 자동 업데이트
   - **알림 집계**: 중복 알림 자동 그룹핑
   - KVStore 기반 저장

5. **고급 기능** (유료 구독)
   - **멀티 테넌시**: 조직별 격리
   - **SLA 관리**: 서비스 레벨 추적
   - **리스크 스코어링**: 위험도 자동 계산
   - **취약점 인텔리전스**: CVE 드릴다운
   - **Role-Based Access Control**: 역할별 권한 제어

6. **대시보드**
   - Incident Posture Dashboard (운영 현황)
   - 알림 통계 및 트렌드
   - 담당자별 작업량
   - 보안 프레임워크 매핑 (MITRE ATT&CK 등)

### 💻 요구사항

- **Splunk Enterprise**: 8.0 이상
- **Splunk Cloud**: v3.2.3 (별도 버전)
- **저장소**: KVStore 사용 (인덱스 불필요)
- **권한**: Admin 권한 필요

---

## 📥 2. 설치 방법

### 방법 1: Splunkbase에서 다운로드 (권장)

#### Step 1: 다운로드
1. **Splunkbase 접속**: https://splunkbase.splunk.com/app/6730
2. **로그인** (Splunk 계정 필요)
3. **Download** 클릭 → `alert_manager_enterprise-3.0.8.tgz` 다운로드

#### Step 2: Splunk에 설치 (Web UI)
```bash
# 1. 다운로드한 파일을 plugins/ 디렉토리에 복사
cp ~/Downloads/alert_manager_enterprise-3.0.8.tgz /home/jclee/app/splunk/plugins/

# 2. Splunk Web UI 접속
# http://localhost:8800

# 3. Apps → Manage Apps → Install app from file

# 4. Browse 클릭 → alert_manager_enterprise-3.0.8.tgz 선택

# 5. Upload 클릭

# 6. Restart Splunk
```

#### Step 3: Docker 설치 (자동)
```bash
# 플러그인 파일이 있다면
docker cp /home/jclee/app/splunk/plugins/alert_manager_enterprise-3.0.8.tgz \
  splunk-test:/opt/splunk/etc/apps/

docker exec splunk-test tar -xzf \
  /opt/splunk/etc/apps/alert_manager_enterprise-3.0.8.tgz \
  -C /opt/splunk/etc/apps/

docker restart splunk-test
```

---

### 방법 2: GitHub에서 빌드

#### Step 1: GitHub 클론
```bash
cd /tmp
git clone https://github.com/alertmanager/alert_manager.git
cd alert_manager
```

#### Step 2: Gradle 빌드
```bash
# Gradle 필요 (Java 8+)
./gradlew splunkAppPackage

# 또는
gradle build
```

#### Step 3: 빌드된 파일 설치
```bash
# 빌드 결과: build/alert_manager-<version>.spl (또는 .tgz)
cp build/alert_manager-*.spl /home/jclee/app/splunk/plugins/

# Splunk Web UI에서 설치
```

⚠️ **참고**: GitHub 릴리스가 없어서 직접 빌드 필요

---

## ⚙️ 3. 설정

### 초기 설정

#### Step 1: Custom Alert Action 활성화
```bash
# Settings → Searches, reports, and alerts → 알림 선택 → Edit Alert

# Trigger Actions 섹션:
☑ Add to Triggered Alerts (Alert Manager)
```

#### Step 2: Alert Manager 설정
```bash
# Apps → Alert Manager → Settings

# 필수 설정:
- Email Server (SMTP)
- Default Assignee
- Notification Scheme
```

#### Step 3: 알림 등록 (기존 알림에 추가)
```spl
# savedsearches.conf에 추가:
action.alert_manager = 1
action.alert_manager.param.severity = critical
action.alert_manager.param.category = hardware
```

---

### PowerShell 스크립트 통합

기존 `register-alerts-interactive.ps1`에 Alert Manager 액션 추가:

```powershell
# Alert Manager 액션 추가
$body["action.alert_manager"] = "1"
$body["action.alert_manager.param.severity"] = "critical"  # low, medium, high, critical
$body["action.alert_manager.param.category"] = "hardware"  # 카테고리 지정
$body["action.alert_manager.param.subcategory"] = "fan_failure"
```

---

## 📊 4. 사용 방법

### 알림 확인 (Web UI)
```bash
# Apps → Alert Manager → Incident Posture

# 또는 직접 URL:
http://localhost:8800/en-US/app/alert_manager/incident_posture
```

### 알림 상태 변경
1. **Incident Posture** 대시보드 열기
2. 알림 클릭
3. **Edit** 버튼:
   - Status: New → In Progress → Resolved
   - Owner: 담당자 할당
   - Priority: Low/Medium/High/Critical

### SPL로 알림 조회
```spl
# Alert Manager 인시던트 검색
| `incident_details`
| search status="new" severity="critical"
| table _time, title, severity, status, owner
```

### 대시보드 모니터링
```spl
# 담당자별 미해결 알림
| `incident_details`
| search status!="resolved"
| stats count by owner, severity
| sort -count
```

---

## 🔄 5. 마이그레이션 (v2.x → v3.x)

### 자동 마이그레이션 도구

Alert Manager Enterprise에 **마이그레이션 도구 내장**:

```bash
# Apps → Alert Manager → Settings → Migration Tool

# 기존 데이터 자동 이전:
- Incident history
- Settings
- Notification schemes
- Email templates
```

### 수동 마이그레이션 체크리스트

- [ ] 기존 Alert Manager v2.x 비활성화
- [ ] Alert Manager Enterprise v3.x 설치
- [ ] Migration Tool 실행
- [ ] 설정 확인 (SMTP, Assignee, Schemes)
- [ ] 알림 재등록 (Custom Alert Action 추가)
- [ ] 테스트 알림 생성 및 워크플로우 확인

---

## 🎯 6. 통합 예제 (FortiGate 알림)

### Critical Events 알림에 Alert Manager 추가

**SPL 쿼리** (`001-critical-events.spl`):
```spl
index=fw type=event
  (logid=0103040* OR msg=*fan*fail* OR msg=*power*fail*)
| search NOT (msg=*update*fail*)
| stats count as event_count,
        latest(_time) as last_event,
        values(msg) as messages
  by devname
| where event_count>0
```

**API 파일** (`001-critical-events-api.txt`):
```ini
name=Critical_Events
search=<SPL 쿼리>
is_scheduled=1
realtime_schedule=1
cron_schedule=*/5 * * * *

# Slack 알림
actions=slack,alert_manager
action.slack=1
action.slack.param.channel=#security-firewall-alert

# Alert Manager 통합
action.alert_manager=1
action.alert_manager.param.severity=critical
action.alert_manager.param.category=hardware
action.alert_manager.param.subcategory=fan_failure
action.alert_manager.param.tags=fortigate,hardware,critical
```

---

## 🔧 7. 문제 해결

### ❌ Alert Manager에 알림이 안 뜸

**체크포인트**:
```spl
# 1. Custom Alert Action 활성화 확인
| rest /services/saved/searches
| search title="Critical_Events"
| table action.alert_manager, action.alert_manager.param.*

# 2. Alert Manager 로그 확인
index=_internal source=*alert_manager*
| tail 50
```

### ❌ 마이그레이션 실패

**해결 방법**:
1. 기존 Alert Manager v2.x 완전 제거
2. Splunk 재시작
3. Alert Manager Enterprise 재설치
4. Migration Tool 재실행

### ❌ 이메일 알림이 안 옴

**설정 확인**:
```bash
# Apps → Alert Manager → Settings → Email Settings
# - SMTP Server
# - SMTP Port (587 for TLS, 465 for SSL)
# - Username/Password
# - From Address

# 테스트 전송:
Apps → Alert Manager → Settings → Test Email
```

---

## 📚 8. 추가 리소스

| 리소스 | URL |
|--------|-----|
| **공식 문서** | http://docs.alertmanager.info/ |
| **Splunkbase** | https://splunkbase.splunk.com/app/6730 |
| **GitHub** | https://github.com/alertmanager/alert_manager |
| **Migration Guide** | http://docs.alertmanager.info/en/latest/migration/ |
| **Release Notes** | https://github.com/alertmanager/alert_manager/blob/develop/CHANGELOG.md |

---

## ✅ 체크리스트

### 설치 전
- [ ] Splunk 8.0 이상 확인
- [ ] Admin 권한 확인
- [ ] 기존 Alert Manager v2.x 비활성화 (있다면)

### 설치
- [ ] Splunkbase에서 다운로드 또는 GitHub 빌드
- [ ] Splunk에 설치 (Web UI 또는 Docker)
- [ ] Splunk 재시작

### 설정
- [ ] Email SMTP 설정
- [ ] Default Assignee 설정
- [ ] Notification Scheme 설정
- [ ] 기존 알림에 Custom Alert Action 추가

### 테스트
- [ ] 수동 인시던트 생성
- [ ] 상태 변경 테스트 (New → In Progress → Resolved)
- [ ] 이메일 알림 수신 확인
- [ ] Incident Posture 대시보드 확인

---

**버전**: 1.0
**상태**: ✅ Production Ready (Enterprise v3.x)
**다음 단계**: Splunkbase에서 다운로드 → 설치 → SMTP 설정 → 알림 통합
