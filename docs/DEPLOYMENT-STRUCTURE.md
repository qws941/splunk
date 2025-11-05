# Splunk 배포 구조

## 🏗️ 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     개발/테스트 환경 (접근 가능)                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Synology NAS (192.168.50.215)                           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Docker Container: splunk                          │  │   │
│  │  │  - Image: splunk/splunk:latest                     │  │   │
│  │  │  - Ports: 8000 (Web), 8088 (HEC), 9997 (TCP)      │  │   │
│  │  │  - Volume: /volume1/docker/splunk-apps/           │  │   │
│  │  │            security_alert (mounted)                │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  Storage: /volume1/docker/splunk-apps/security_alert/   │   │
│  │  - bin/                (Python scripts)                  │   │
│  │  - default/            (Configuration)                   │   │
│  │  - lookups/            (CSV files)                       │   │
│  │  - metadata/           (Permissions)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  개발 서버 (192.168.50.100)                                       │
│  - Git Repository: /home/jclee/app/splunk                       │
│  - rsync로 Synology에 파일 복사                                  │
│  - Docker Compose 관리                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 테스트 완료 후 배포
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              운영 환경 (Air-gap, 접근 불가)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  OPS Splunk Server                                       │   │
│  │  - 외부 네트워크 차단 (Air-gap)                            │   │
│  │  - 수동 배포만 가능 (tarball)                              │   │
│  │  - security_alert.tar.gz 업로드                           │   │
│  │  - 사용자가 직접 설치/설정                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  배포 방법:                                                       │
│  1. 개발서버에서 tarball 생성                                     │
│  2. 사용자가 OPS 서버로 파일 전송                                │
│  3. Splunk Web UI 또는 CLI로 설치                               │
│  4. Setup UI에서 Slack 설정                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 현재 환경 상태

### Synology Docker (개발/테스트)

**컨테이너 정보**:
```yaml
Name: splunk
Status: Starting (Ansible provisioning 중)
Image: splunk/splunk:latest
Network: splunk-demo
Context: synology (remote Docker)
```

**포트 매핑**:
- 8000 → Splunk Web UI
- 8088 → HTTP Event Collector (HEC)
- 9997 → TCP Data Input

**볼륨 마운트**:
```
Host: /volume1/docker/splunk-apps/security_alert
Container: /opt/splunk/etc/apps/security_alert (read-only)
```

**파일 구조** (Synology):
```
/volume1/docker/splunk-apps/security_alert/
├── bin/                              # Python backend
│   ├── slack.py                      # Slack 메시지 전송
│   ├── auto_validator.py             # 설정 검증
│   ├── deployment_health_check.py    # 상태 확인
│   └── ...
├── default/                          # 기본 설정
│   ├── savedsearches.conf            # 15개 Alert 정의
│   ├── macros.conf                   # 매크로 (LogID, 임계값)
│   ├── transforms.conf               # Lookup 정의
│   ├── props.conf                    # 필드 추출
│   └── alert_actions.conf            # Slack 액션
├── lookups/                          # CSV 데이터
│   ├── fortigate_logid_notification_map.csv
│   ├── *_state_tracker.csv (10개)
│   └── ...
└── metadata/
    └── default.meta                  # 권한 설정
```

---

## 🔄 개발 워크플로우

### 1. 개발/수정 (개발 서버)

```bash
# 소스 수정
cd /home/jclee/app/splunk/security_alert
vim default/savedsearches.conf

# Git 커밋
git add .
git commit -m "feat: Add new alert"
git push origin master
```

### 2. Synology 배포 (테스트)

```bash
# Synology로 파일 동기화
rsync -avz -e "ssh -p 1111" \
  /home/jclee/app/splunk/security_alert/ \
  jclee@192.168.50.215:/volume1/docker/splunk-apps/security_alert/

# Splunk 재시작 (설정 반영)
docker exec splunk /opt/splunk/bin/splunk restart
```

### 3. 테스트 (Synology)

```bash
# 1. Web UI 접속
http://192.168.50.215:8000
Username: admin
Password: changeme123

# 2. Alert 확인
Settings → Searches, reports, and alerts

# 3. 수동 Alert 실행
Search → Alert 이름 → Run

# 4. Slack 메시지 확인
#security-firewall-alert 채널
```

### 4. 운영 배포 (사용자 수동)

```bash
# 개발 서버에서 tarball 생성
cd /home/jclee/app/splunk
tar -czf security_alert.tar.gz security_alert/

# 사용자가 OPS 서버로 전송 (Air-gap 환경)
# - USB 드라이브
# - 내부 파일 전송 시스템
# - 기타 승인된 방법

# OPS Splunk에 설치 (사용자가 직접)
# Web UI: Apps → Manage Apps → Install app from file
# 또는 CLI: tar -xzf security_alert.tar.gz -C /opt/splunk/etc/apps/
```

---

## 🧪 Synology 테스트 시나리오

### 필수 테스트 항목

#### 1. 기본 동작 확인
```bash
# Splunk 서비스 상태
docker exec splunk /opt/splunk/bin/splunk status

# 앱 인식 확인
docker exec splunk /opt/splunk/bin/splunk display app security_alert

# 설정 파일 검증
docker exec splunk /opt/splunk/bin/splunk btool check --app=security_alert
```

#### 2. Alert 동작 테스트
```spl
# Alert 001: Config Change (수동 실행)
index=fw logid=0100044546 OR logid=0100044547
| table _time, devname, user, cfgpath, msg

# Alert 002: VPN Tunnel (수동 실행)
index=fw logid=0101037124 OR logid=0101037131 OR logid=0101037134
| eval current_state = if(match(msg, "down"), "DOWN", "UP")
| table _time, devname, vpn_name, current_state, msg
```

#### 3. Slack 통합 테스트
```bash
# 1. Setup UI에서 Slack 설정
http://192.168.50.215:8000/app/security_alert/setup

# 2. Bot Token 또는 Webhook URL 입력
# 3. Test 버튼 클릭

# 4. 로그 확인
docker exec splunk tail -f /opt/splunk/var/log/splunk/splunkd.log | grep slack
```

#### 4. 데이터 수집 테스트
```bash
# FortiGate syslog → Splunk (port 9997)
# FortiGate CLI:
config log syslogd setting
  set status enable
  set server "192.168.50.215"
  set port 9997
end

# Splunk에서 확인
index=fw earliest=-5m | stats count by sourcetype, host
```

#### 5. Lookup 파일 동작 확인
```spl
# State tracker 확인
| inputlookup vpn_state_tracker
| table device, prev_state, current_state, last_change

# LogID 매핑 확인
| inputlookup fortigate_logid_notification_map
| search logid=0100044546
| table logid, category, severity, description
```

---

## 📊 테스트 체크리스트

### 설치 확인
- [ ] Splunk 컨테이너 정상 실행 (healthy)
- [ ] security_alert 앱 인식
- [ ] Web UI 접속 가능
- [ ] 모든 설정 파일 로드 (btool check)

### Alert 확인
- [ ] 15개 Alert 존재 (savedsearches.conf)
- [ ] 12개 Active, 3개 Inactive 상태
- [ ] Cron schedule 정상
- [ ] Macro 확장 정상

### Slack 통합
- [ ] Bot Token 설정 완료
- [ ] 채널 접근 가능 (#security-firewall-alert)
- [ ] 메시지 전송 성공
- [ ] Block Kit 포맷 정상

### 데이터 처리
- [ ] FortiGate syslog 수신
- [ ] index=fw에 데이터 저장
- [ ] 필드 자동 추출 (props.conf)
- [ ] Lookup 조인 정상

### State Tracking
- [ ] CSV 파일 자동 생성
- [ ] State 변경 감지
- [ ] outputlookup 정상 동작
- [ ] 중복 알림 방지

---

## 🚀 배포 준비 사항

### OPS 서버 요구사항

**Splunk 환경**:
- Splunk Enterprise 8.0 이상
- Python 3 지원
- 최소 2GB RAM, 10GB 디스크

**네트워크 설정**:
- FortiGate → Splunk (port 9997 TCP)
- 관리자 → Splunk Web UI (port 8000)

**Slack 설정**:
- Bot Token 또는 Webhook URL
- #security-firewall-alert 채널 생성
- Bot 초대

**데이터 인덱스**:
- index=fw 생성
- 적절한 retention 설정
- 충분한 storage 할당

---

## 📝 Notes

**테스트 환경 특징**:
- ✅ 실제 운영과 동일한 Docker 구조
- ✅ 동일한 앱 구조 및 설정
- ✅ Synology 스토리지 사용 (영구 데이터)
- ⚠️ FortiGate 연동은 별도 설정 필요

**주의사항**:
1. **Read-only 마운트**: 컨테이너 내부에서 앱 파일 수정 불가
2. **설정 변경 후**: Splunk 재시작 필요 (`docker exec splunk /opt/splunk/bin/splunk restart`)
3. **Lookup CSV**: 컨테이너에서 쓰기 가능하도록 권한 확인
4. **로그 확인**: `docker logs splunk -f` 또는 Splunk UI

**다음 단계**:
1. Ansible 프로비저닝 완료 대기 (~3분)
2. Web UI 접속 확인 (http://192.168.50.215:8000)
3. security_alert 앱 Setup 실행
4. 테스트 Alert 실행 및 Slack 확인
5. 문제 없으면 tarball 생성 → OPS 배포

---

**작성일**: 2025-11-05
**환경**: Synology Docker (192.168.50.215)
**대상**: OPS Air-gap 환경 배포 준비
