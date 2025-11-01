# FortiGate 샘플 이벤트 가이드

Splunk에서 FortiGate 알림을 테스트하기 위한 샘플 데이터입니다.

## 📋 포함된 샘플 이벤트 (20개)

| 알림 유형 | LogID | 이벤트 개수 | 설명 |
|----------|-------|-----------|------|
| **Config Change** | 0100044546, 0100044547 | 3개 | CLI/GUI 설정 변경 (정책, VPN) |
| **Interface Status** | 0100032001, 0100020007 | 2개 | 인터페이스 다운, 링크 모니터 실패 |
| **HA Status** | 0100020010, 0104043544, 0104043545 | 3개 | HA 상태 변경, 멤버 변경, 설정 동기화 |
| **Device Events** | 0103040001-0103040003 | 3개 | 팬 고장, 전원, 온도 경고 |
| **System Resource** | 0104043001-0104043004 | 4개 | CPU, 메모리, 디스크, 세션 경고 |
| **Admin Activity** | 0105032003-0105043002 | 5개 | 로그인, 로그아웃, 권한 거부, 백업 |

## 🚀 빠른 시작

### 방법 1: 자동 스크립트 (권장)

```bash
cd /home/jclee/app/splunk
./scripts/load-sample-events.sh
```

### 방법 2: Splunk CLI 직접 사용

```bash
sudo /opt/splunk/bin/splunk add oneshot \
  /home/jclee/app/splunk/sample-events.txt \
  -index fw \
  -sourcetype "fortigate:syslog" \
  -auth admin:changeme
```

### 방법 3: Splunk Web UI

1. **Settings → Add Data → Monitor → Files & Directories**
2. **File or Directory**: `/home/jclee/app/splunk/sample-events.txt`
3. **Source Type**: `fortigate:syslog`
4. **Index**: `fw`
5. **Review → Submit**

## ✅ 데이터 확인

### 1. 총 이벤트 수 확인
```spl
index=fw | stats count
```
**예상 결과**: `20 events`

### 2. LogID 별 분포
```spl
index=fw | stats count by logid | sort -count
```

### 3. 디바이스 별 이벤트
```spl
index=fw | stats count by devname
```
**예상 결과**:
- FGT-HQ-01: 11개
- FGT-Branch-02: 5개
- FGT-Branch-03: 2개
- FGT-HQ-02: 1개

### 4. 시간대별 이벤트
```spl
index=fw | timechart count by devname
```

## 🧪 알림 테스트

### 각 알림 개별 테스트

```spl
# 1. Config Change (3개 예상)
| savedsearch FortiGate_Config_Change

# 2. Interface Status (2개 예상)
| savedsearch FortiGate_Interface_Status

# 3. HA Status (3개 예상)
| savedsearch FortiGate_HA_Status

# 4. Device Events (3개 예상)
| savedsearch FortiGate_Device_Events

# 5. System Resource (4개 예상)
| savedsearch FortiGate_System_Resource

# 6. Admin Activity (5개 예상)
| savedsearch FortiGate_Admin_Activity
```

### 한 번에 모든 알림 테스트

```bash
# Splunk Search에서 실행:
| savedsearch FortiGate_Config_Change
| append [| savedsearch FortiGate_Interface_Status]
| append [| savedsearch FortiGate_HA_Status]
| append [| savedsearch FortiGate_Device_Events]
| append [| savedsearch FortiGate_System_Resource]
| append [| savedsearch FortiGate_Admin_Activity]
| stats count by savedsearch_name
```

## 📊 예상 Slack 알림

샘플 데이터 로드 후 각 알림이 실행되면:

| 알림 | Slack 채널 | 예상 메시지 수 | 설명 |
|-----|----------|------------|------|
| Config Change | #security-firewall-alert | 3개 | 정책/VPN 변경 알림 |
| Interface Status | #security-firewall-alert | 2개 | 인터페이스 다운 알림 |
| HA Status | #security-firewall-alert | 3개 | HA 상태 변경 알림 |
| Device Events | #security-firewall-alert | 3개 | 하드웨어 이슈 알림 |
| System Resource | #security-firewall-alert | 4개 | 리소스 경고 알림 |
| Admin Activity | #security-firewall-alert | 5개 | 관리자 활동 알림 |

**총 20개 Slack 메시지** (suppression 설정에 따라 다를 수 있음)

## 🔧 문제 해결

### 이벤트가 보이지 않는 경우

```spl
# 1. 원본 데이터 확인
index=fw sourcetype="fortigate:syslog" | head 20

# 2. 타임스탬프 확인 (샘플은 2025-11-02 날짜)
index=fw earliest=2025-11-02:00:00:00 latest=2025-11-03:00:00:00

# 3. 파싱 문제 확인
index=fw | table _raw, _time, logid, devname
```

### 알림이 실행되지 않는 경우

```spl
# 스케줄러 로그 확인
index=_internal source=*scheduler.log savedsearch_name="FortiGate_*"
| stats count, latest(_time) as last_run by savedsearch_name, status
```

### Slack 알림이 오지 않는 경우

1. **Slack 봇이 채널에 초대되었는지 확인**
   ```
   /invite @your-bot-name
   ```

2. **alert_actions.conf 확인**
   ```bash
   grep -A 5 "\[slack\]" /opt/splunk/etc/apps/*/local/alert_actions.conf
   ```

3. **Slack 알림 실행 로그 확인**
   ```spl
   index=_internal source=*alert_actions.log action=slack
   | table _time, savedsearch_name, result
   ```

## 🗑️ 샘플 데이터 삭제

테스트 완료 후 샘플 데이터 삭제:

```spl
# Splunk Search에서 실행:
index=fw sourcetype="fortigate:syslog" 
| delete
```

**주의**: 이 명령은 index=fw의 모든 `fortigate:syslog` 데이터를 삭제합니다. 실제 데이터와 섞여있다면 날짜로 필터링하세요:

```spl
index=fw sourcetype="fortigate:syslog" 
    earliest=2025-11-02:14:00:00 
    latest=2025-11-02:15:00:00
| delete
```

## 📝 샘플 데이터 커스터마이징

`sample-events.txt` 파일을 직접 수정하여:
- 디바이스 이름 변경 (`devname=`)
- 타임스탬프 조정 (`date=`, `time=`)
- 필드 값 수정 (cfgpath, user, interface 등)
- 추가 이벤트 생성 (같은 포맷 사용)

수정 후 다시 로드:
```bash
./scripts/load-sample-events.sh
```

## 🎯 다음 단계

1. ✅ 샘플 데이터 로드 완료
2. ✅ 각 알림 개별 테스트
3. ✅ Slack 알림 수신 확인
4. ⏭️ 실제 FortiGate syslog 연결
5. ⏭️ 알림 임계값/suppression 조정
6. ⏭️ 프로덕션 배포

---

**파일 위치**:
- 샘플 데이터: `/home/jclee/app/splunk/sample-events.txt`
- 로드 스크립트: `/home/jclee/app/splunk/scripts/load-sample-events.sh`
- 알림 설정: `/home/jclee/app/splunk/configs/savedsearches-fortigate-alerts-logid-based.conf`
