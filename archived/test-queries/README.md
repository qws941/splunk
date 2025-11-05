# Splunk 테스트 쿼리 모음

**FortiGate 운영 모니터링 쿼리 (FMG 7.4.7 / FAZ 7.4.4 기반)**

## 📁 파일 목록 (총 13개)

### 🔧 기본 테스트 및 Alert 쿼리 (01-05)

| 파일 | 목적 | 실행 시간 |
|------|------|----------|
| `01-check-config-fields.spl` | 설정 변경 필드 확인 | ~5초 |
| `02-test-eval-fixed.spl` | eval 명령어 에러 수정 테스트 | ~10초 |
| `03-full-config-alert-query.spl` | 완전한 Alert 쿼리 (배포용) | ~15초 |
| `04-critical-events.spl` | Critical 이벤트 확인 | ~10초 |
| `05-ha-events.spl` | HA 이벤트 확인 | ~5초 |

### 👥 관리자 및 접근 모니터링 (06)

| 파일 | 목적 | 주요 LogID |
|------|------|-----------|
| `06-admin-activity.spl` | 관리자 로그인/로그아웃, 계정 변경 추적 | 0105*, 0100044546, 0100044547 |

### 🌐 네트워크 및 인프라 (07-08)

| 파일 | 목적 | 주요 LogID |
|------|------|-----------|
| `07-interface-status.spl` | 인터페이스 Up/Down 상태 변경 | 0104043521, 0104043522 |
| `08-vpn-status.spl` | VPN 터널 상태 (IPsec, SSL VPN) | 0101039*, 0101040*, 0102104* |

### 📊 리소스 및 시스템 (09-10)

| 파일 | 목적 | 주요 LogID |
|------|------|-----------|
| `09-resource-usage.spl` | CPU/Memory/Disk/Session 사용률 | 0104032* |
| `10-firmware-system-updates.spl` | 펌웨어 업그레이드, 재시작, 크래시 | 0104033*, 0104010* |

### 🛡️ 정책 및 라우팅 (11-12)

| 파일 | 목적 | 주요 LogID |
|------|------|-----------|
| `11-policy-changes-detail.spl` | 방화벽 정책 변경 상세 (Field Extraction) | 0100044546, 0100044547 |
| `12-routing-changes.spl` | Static Route, BGP, OSPF 라우팅 변경 | router.* cfgpath |

### 🖥️ 하드웨어 모니터링 (13)

| 파일 | 목적 | 포함 내용 |
|------|------|----------|
| `13-hardware-monitoring.spl` | Fan, Power, Temperature, Disk 하드웨어 이벤트 | Hardware failure detection |

## 🚀 사용 방법

### 1. Splunk Web UI에서 검색

```bash
# 1. Splunk 로그인
https://splunk.jclee.me

# 2. Search & Reporting 앱
# 3. 검색창에 쿼리 붙여넣기
# 4. 시간 범위 선택: Last 24 hours
# 5. 검색 버튼 클릭
```

### 2. 쿼리 저장 (Saved Search)

```bash
# 검색 실행 후:
# 1. Save As → Alert
# 2. Title: FortiGate_Config_Change_Alert
# 3. Schedule: Real-time (Every minute)
# 4. Trigger: number of events > 0
# 5. Actions: Slack (#security-firewall-alert)
# 6. Suppress: 15 seconds, fields: user, cfgpath
# 7. Save
```

### 3. CLI로 검색 (선택사항)

```bash
# splunk 명령어 사용
splunk search "index=fw earliest=-1h ..." -auth admin:password
```

## 🧪 테스트 순서

### Step 1: 필드 확인
```bash
# 01-check-config-fields.spl 실행
# 확인: cfgattr, cfgobj, cfgpath 필드가 있는지
```

**기대 결과**:
- ✅ 설정 변경 로그가 20개 이상 보임
- ✅ cfgpath, cfgobj 필드에 값이 있음
- ✅ cfgattr 필드에 설정 세부사항이 있음

### Step 2: eval 에러 수정 테스트
```bash
# 02-test-eval-fixed.spl 실행
# 확인: 에러 없이 실행되는지
```

**기대 결과**:
- ✅ "Error in 'eval' command" 메시지 없음
- ✅ alert_message 필드에 완전한 메시지 생성
- ✅ details 필드에 "No details" 또는 실제 값

### Step 3: 전체 Alert 쿼리 테스트
```bash
# 03-full-config-alert-query.spl 실행
# 확인: Alert 저장 가능 여부
```

**기대 결과**:
- ✅ dedup으로 중복 제거됨
- ✅ 정책/주소/인터페이스/라우팅/VPN 변경만 표시
- ✅ alert_message 형식 완벽

### Step 4: Critical 이벤트 확인
```bash
# 04-critical-events.spl 실행
# 확인: 실제 Critical 이벤트가 있는지
```

**기대 결과**:
- ✅ "Update Fail" 메시지가 제외됨
- ✅ 하드웨어/HA/시스템 Critical만 표시

### Step 5: HA 이벤트 확인
```bash
# 05-ha-events.spl 실행
# 확인: HA 관련 이벤트
```

**기대 결과**:
- ✅ HA sync/failover 이벤트 표시
- ✅ Severity별 아이콘 표시 (🔴🟠🟡🔵)

## 🎯 쿼리 분류별 사용 가이드 (06-13)

### 👥 관리자 활동 감사 (Audit)

**06-admin-activity.spl** - 관리자 행위 추적
```spl
# 언제 사용?
- 누가 언제 로그인했는지 확인
- 계정 생성/삭제 추적
- 의심스러운 로그인 실패 탐지
- CLI vs GUI 접근 비교

# Alert 조건 제안
- 로그인 실패 > 5회 (1시간 이내)
- 새 계정 생성 (즉시 알림)
- 야간 시간 로그인 (00:00-06:00)
```

### 🌐 네트워크 상태 모니터링

**07-interface-status.spl** - 인터페이스 장애 탐지
```spl
# 언제 사용?
- WAN 링크 다운 확인
- 인터페이스 플래핑 (반복 up/down) 탐지
- 네트워크 장애 원인 분석

# Alert 조건 제안
- WAN 인터페이스 down (즉시)
- 인터페이스 플래핑 > 3회 (10분 이내)
```

**08-vpn-status.spl** - VPN 연결 상태
```spl
# 언제 사용?
- IPsec 터널 다운 확인
- SSL VPN 접속 실패 원인
- VPN 연결 빈도 통계

# Alert 조건 제안
- 중요 IPsec 터널 down (즉시)
- SSL VPN 로그인 실패 > 10회
```

### 📊 성능 및 용량 관리

**09-resource-usage.spl** - 리소스 과부하 탐지
```spl
# 언제 사용?
- CPU/메모리 고갈 확인
- 디스크 Full 예측
- 세션 테이블 포화 상태

# Alert 조건 제안
- CPU > 90% (5분 지속)
- Memory > 90%
- Disk > 95%
- Session table > 90%
```

**10-firmware-system-updates.spl** - 시스템 안정성
```spl
# 언제 사용?
- 펌웨어 업그레이드 성공 여부
- 비정상 재시작 탐지 (crash, panic)
- 서비스 재시작 빈도 확인

# Alert 조건 제안
- 펌웨어 업그레이드 실패
- 비정상 재시작 (crash, panic)
- 서비스 재시작 > 3회 (1시간 이내)
```

### 🛡️ 보안 정책 변경 감시

**11-policy-changes-detail.spl** - 정책 변경 상세 분석
```spl
# 언제 사용?
- 누가 어떤 정책을 변경했는지
- 과도한 허용 정책 탐지 (srcaddr=any, dstaddr=any)
- 정책 삭제 추적
- CLI vs GUI 변경 비교

# Alert 조건 제안
- 정책 삭제 (즉시)
- srcaddr=any AND dstaddr=any (위험한 변경)
- 정책 action=accept 변경
```

**12-routing-changes.spl** - 라우팅 변경 추적
```spl
# 언제 사용?
- Default route 변경 확인
- BGP neighbor down 탐지
- Static route 추가/삭제 추적

# Alert 조건 제안
- Default route 변경 (즉시)
- BGP neighbor down
- 중요 Static route 삭제
```

### 🖥️ 하드웨어 건강도 체크

**13-hardware-monitoring.spl** - 하드웨어 장애 예측
```spl
# 언제 사용?
- Fan 고장 탐지
- 전원 공급 장치 이상
- 온도 초과 경고
- 디스크 에러 추적

# Alert 조건 제안
- Fan failure (즉시)
- Power supply redundancy lost (즉시)
- Temperature > threshold
- Disk failure, RAID degraded
```

## ❌ 문제 해결

### 문제 1: "No results found"

**원인**: 데이터가 없거나 시간 범위가 잘못됨

**해결**:
```spl
# 시간 범위를 늘려보세요
earliest=-7d latest=now

# 또는 모든 데이터 확인
index=fw | head 100
```

### 문제 2: "Error in 'eval' command"

**원인**: 필드가 없거나 함수 사용 오류

**해결**:
```spl
# 필드 존재 확인
index=fw | table cfgattr, cfgobj, cfgpath

# eval 단계별 테스트
| eval test1 = devname
| eval test2 = coalesce(user, "system")
```

### 문제 3: "Field 'cfgattr' does not exist"

**원인**: 실제 로그에 cfgattr 필드가 없음

**해결**:
```spl
# 실제 필드 이름 확인
index=fw logid=0100044546 | fieldsummary

# 또는
index=fw logid=0100044546 | head 1 | transpose
```

## 📊 예상 결과 (샘플)

### 설정 변경 (01-check-config-fields.spl)
```
_time                devname  user   logid       cfgpath              cfgobj      cfgattr
2025-10-29 10:30:00  FGT-01   admin  0100044546  firewall.policy[10]  policy_10   srcaddr=all dstaddr=all service=HTTP
2025-10-29 10:25:00  FGT-02   admin  0100044547  system.interface     port1       ip=10.0.1.1 allowaccess=ping ssh
```

### Critical 이벤트 (04-critical-events.spl)
```
_time                alert_message                                                      device  log_id    severity
2025-10-29 09:00:00  🚨 FortiGate CRITICAL Event - Device: FGT-01 | LogID: 0104001... FGT-01  0104001   critical
2025-10-29 08:30:00  🚨 FortiGate CRITICAL Event - Device: FGT-02 | LogID: 0103008... FGT-02  0103008   critical
```

### HA 이벤트 (05-ha-events.spl)
```
_time                alert_message                                                severity  description
2025-10-29 07:00:00  🔴 FortiGate HA Event - Device: FGT-01 | Severity: critical  critical  HA member down
2025-10-29 06:30:00  🟡 FortiGate HA Event - Device: FGT-01 | Severity: warning   warning   HA sync delay
```

## 💾 저장된 검색 관리

### 저장된 검색 확인
```bash
# Splunk Web UI
Settings → Searches, reports, and alerts

# CLI
splunk list saved-search
```

### Alert 상태 확인
```bash
# Web UI
Settings → Searches, reports, and alerts → FortiGate_Config_Change_Alert → View recent alerts

# CLI
splunk list fired-alerts
```

### Alert 비활성화/활성화
```bash
# Web UI
Alert 클릭 → Edit → Disable checkbox

# CLI
splunk edit saved-search FortiGate_Config_Change_Alert -disabled 1
splunk edit saved-search FortiGate_Config_Change_Alert -disabled 0
```

## 📖 LogID 빠른 참조 (FortiGate 7.4+)

### 시스템 및 관리 LogID

| LogID Pattern | 설명 | 관련 쿼리 |
|--------------|------|---------|
| `0100044546` | 설정 변경 (CLI) | 01, 03, 06, 11, 12 |
| `0100044547` | 설정 변경 (GUI) | 01, 03, 06, 11, 12 |
| `0103008*` | HA 이벤트 (Failover, Sync) | 04, 05 |
| `0104010*` | 시스템 재시작/Startup/Shutdown | 10 |
| `0104032*` | 리소스 사용률 (CPU/Memory/Disk/Session) | 09 |
| `0104033*` | 펌웨어 업그레이드 | 10 |
| `0104043521` | 인터페이스 Link Up | 07 |
| `0104043522` | 인터페이스 Link Down | 07 |
| `0105*` | 관리자 활동 (Login/Logout/Account) | 06 |

### 네트워크 LogID

| LogID Pattern | 설명 | 관련 쿼리 |
|--------------|------|---------|
| `0101039*` | IPsec Phase 1 | 08 |
| `0101040*` | IPsec Phase 2 | 08 |
| `0101045*` | IPsec Tunnel | 08 |
| `010210*` | SSL VPN | 08 |

### 설정 경로 (cfgpath)

| cfgpath | 설명 | 관련 쿼리 |
|---------|------|---------|
| `firewall.policy*` | 방화벽 정책 | 03, 11 |
| `router.static` | Static Route | 12 |
| `router.bgp` | BGP 설정 | 12 |
| `router.ospf` | OSPF 설정 | 12 |
| `system.interface` | 인터페이스 설정 | 03 |
| `vpn.*` | VPN 설정 | 03 |
| `firewall.address*` | 주소 객체 | 03 |

## 🚀 빠른 시작 가이드 (처음 사용자)

### 1단계: 데이터 확인 (30초)
```spl
# Splunk에 FortiGate 로그가 들어오는지 확인
index=fw | head 10
```

### 2단계: 기본 쿼리 실행 (2분)
```spl
# 01-check-config-fields.spl 실행 (설정 변경 확인)
# 04-critical-events.spl 실행 (Critical 이벤트 확인)
# 05-ha-events.spl 실행 (HA 상태 확인)
```

### 3단계: 필요한 쿼리 선택 (용도별)
```
관리자 감사 필요 → 06-admin-activity.spl
네트워크 장애 추적 → 07-interface-status.spl, 08-vpn-status.spl
성능 모니터링 → 09-resource-usage.spl
정책 변경 추적 → 11-policy-changes-detail.spl
하드웨어 체크 → 13-hardware-monitoring.spl
```

### 4단계: Alert 설정 (5분)
```
중요 쿼리를 Saved Search로 저장 후:
- Schedule: Real-time
- Trigger: count > 0
- Action: Slack 알림
```

## 📋 체크리스트 (운영자용)

### 매일 확인 (Daily)
- [ ] `04-critical-events.spl` - Critical 이벤트 없는지
- [ ] `05-ha-events.spl` - HA 상태 정상인지
- [ ] `09-resource-usage.spl` - 리소스 사용률 정상인지

### 주간 확인 (Weekly)
- [ ] `06-admin-activity.spl` - 비정상 로그인 없는지
- [ ] `11-policy-changes-detail.spl` - 정책 변경 리뷰
- [ ] `13-hardware-monitoring.spl` - 하드웨어 경고 없는지

### 월간 확인 (Monthly)
- [ ] `10-firmware-system-updates.spl` - 펌웨어 업데이트 필요 여부
- [ ] `12-routing-changes.spl` - 라우팅 변경 이력 리뷰
- [ ] 전체 쿼리 실행 후 통계 분석

---

**버전**: 2.0 (13 queries)
**기반**: FortiManager 7.4.7 / FortiAnalyzer 7.4.4
**업데이트**: 2025-10-29
**참고**: 모든 쿼리는 `index=fw`를 사용합니다. 인덱스 이름이 다르면 수정하세요.
