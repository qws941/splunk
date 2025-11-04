# Security Alert System - 설치 가이드

## 📦 패키지 정보

- **파일명**: `security_alert.tar.gz`
- **크기**: 16KB
- **파일 개수**: 24개
- **버전**: v2.0.4

## 🚀 설치 방법

### 방법 1: Web UI 설치 (권장)

1. Splunk Web 로그인
2. **Apps** → **Manage Apps** → **Install app from file**
3. `security_alert.tar.gz` 업로드
4. **Restart Splunk** 클릭

### 방법 2: CLI 설치

```bash
# 1. 파일 복사
scp security_alert.tar.gz splunk-server:/tmp/

# 2. Splunk 서버 접속
ssh splunk-server

# 3. 압축 해제
cd /opt/splunk/etc/apps/
sudo tar -xzf /tmp/security_alert.tar.gz

# 4. 권한 설정
sudo chown -R splunk:splunk security_alert

# 5. Splunk 재시작
sudo /opt/splunk/bin/splunk restart
```

## ⚙️ 초기 설정

### 1. Slack Webhook URL 설정

**방법 A: Setup UI 사용 (권장)**

1. Splunk Web → **Apps** → **Security Alert System**
2. **Set up** 클릭
3. Slack Webhook URL 입력: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
4. Default Channel 입력: `#security-firewall-alert`
5. **Save** 클릭

**방법 B: 파일 직접 수정**

```bash
sudo vi /opt/splunk/etc/apps/security_alert/local/alert_actions.conf
```

```ini
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
param.channel = #security-firewall-alert
```

### 2. Slack Webhook URL 생성 방법

1. https://api.slack.com/apps 접속
2. **Create New App** → **From scratch**
3. App 이름: `FortiGate Security Alerts`
4. Workspace 선택 → **Create App**
5. **Incoming Webhooks** → **Activate Incoming Webhooks** (On)
6. **Add New Webhook to Workspace**
7. 채널 선택 (`#security-firewall-alert`) → **Allow**
8. Webhook URL 복사 (예: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`)

## ✅ 설치 확인

### 1. 앱 설치 확인

```bash
ls -la /opt/splunk/etc/apps/security_alert/
```

**예상 출력**:
```
drwxr-xr-x 7 splunk splunk   93 Nov  4 11:22 .
drwxr-xr-x 9 splunk splunk 4096 Nov  4 11:22 ..
-rw-r--r-- 1 splunk splunk 3199 Nov  4 11:22 README.md
drwxr-xr-x 2 splunk splunk   71 Nov  4 11:22 bin
drwxr-xr-x 2 splunk splunk  150 Nov  4 11:22 default
drwxr-xr-x 2 splunk splunk    6 Nov  4 11:22 local
drwxr-xr-x 2 splunk splunk 4096 Nov  4 11:22 lookups
drwxr-xr-x 2 splunk splunk   26 Nov  4 11:22 metadata
```

### 2. 알림 설정 확인

```bash
/opt/splunk/bin/splunk btool savedsearches list | grep -E "^\[0[0-9]{2}_"
```

**예상 출력**: 15개 알림 stanza
```
[001_Config_Change]
[002_VPN_Tunnel_Down]
[002_VPN_Tunnel_Up]
[006_CPU_Memory_Anomaly]
[007_Hardware_Failure]
[007_Hardware_Restored]
[008_HA_State_Change]
[010_Resource_Limit]
[011_Admin_Login_Failed]
[012_Interface_Down]
[012_Interface_Up]
[013_SSL_VPN_Brute_Force]
[015_Abnormal_Traffic_Spike]
[016_System_Reboot]
[017_License_Expiry_Warning]
```

### 3. Lookup 테이블 확인

```bash
/opt/splunk/bin/splunk btool transforms list | grep -E "state_tracker|fortigate_logid"
```

**예상 출력**: 10개 state tracker + 1개 logid lookup
```
[fortigate_logid_lookup]
[vpn_state_tracker]
[hardware_state_tracker]
[ha_state_tracker]
[interface_state_tracker]
[cpu_memory_state_tracker]
[resource_state_tracker]
[admin_login_state_tracker]
[vpn_brute_force_state_tracker]
[traffic_spike_state_tracker]
[license_state_tracker]
```

### 4. 데이터 확인

```spl
index=fw earliest=-1h | stats count
```

**예상**: `count > 0` (FortiGate 로그 수신 중)

### 5. 알림 실행 확인

```spl
index=_internal source=*scheduler.log savedsearch_name="*Alert*" earliest=-15m
| stats count by savedsearch_name, status
```

**예상**: 각 알림별로 `status="success"` 또는 `status="skipped"`

### 6. Slack 전송 확인

```spl
index=_internal source=*alert_actions.log action_name="slack" earliest=-15m
| table _time, sid, search_name, action_mode, result
```

## 🔧 트러블슈팅

### 문제 1: 알림이 실행되지 않음

**진단**:
```spl
index=_internal source=*scheduler.log savedsearch_name="001_Config_Change" earliest=-1h
| table _time, status, run_time, result_count, message
```

**해결**:
```bash
# 알림 활성화 확인
/opt/splunk/bin/splunk btool savedsearches list 001_Config_Change | grep enableSched
# 예상: enableSched = 1

# Scheduler 재시작
sudo /opt/splunk/bin/splunk restart splunkd
```

### 문제 2: Slack 알림이 전송되지 않음

**진단**:
```bash
# Webhook URL 확인
grep "webhook_url" /opt/splunk/etc/apps/security_alert/local/alert_actions.conf

# Python 스크립트 권한 확인
ls -la /opt/splunk/etc/apps/security_alert/bin/*.py
# 예상: -rwxr-xr-x (실행 권한 있어야 함)
```

**해결**:
```bash
# 권한 설정
sudo chmod +x /opt/splunk/etc/apps/security_alert/bin/*.py

# Webhook URL 테스트
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message from Splunk"}'
# 예상: ok
```

### 문제 3: Lookup 테이블 오류

**진단**:
```bash
# Lookup 파일 존재 확인
ls -la /opt/splunk/etc/apps/security_alert/lookups/*.csv

# transforms.conf 검증
/opt/splunk/bin/splunk btool transforms list --debug | grep security_alert
```

**해결**:
```bash
# 권한 설정
sudo chown -R splunk:splunk /opt/splunk/etc/apps/security_alert/lookups/
sudo chmod 644 /opt/splunk/etc/apps/security_alert/lookups/*.csv
```

### 문제 4: 상태 추적 CSV 초기화

**증상**: 중복 알림 발생

**해결**:
```bash
# 상태 파일 초기화
cd /opt/splunk/etc/apps/security_alert/lookups/

# 각 state tracker 초기화
echo "device,vpn_name,state,last_seen" > vpn_state_tracker.csv
echo "device,component,state,last_seen" > hardware_state_tracker.csv
echo "device,ha_role,state,last_seen" > ha_state_tracker.csv
echo "device,interface,state,last_seen" > interface_state_tracker.csv
echo "device,resource,state,last_seen" > cpu_memory_state_tracker.csv
echo "device,resource_type,state,last_seen" > resource_state_tracker.csv
echo "device,source_ip,state,last_seen" > admin_login_state_tracker.csv
echo "device,source_ip,state,last_seen" > vpn_brute_force_state_tracker.csv
echo "device,source_ip,state,last_seen" > traffic_spike_state_tracker.csv
echo "device,license_category,state,last_seen" > license_state_tracker.csv

# 권한 재설정
sudo chown splunk:splunk *.csv
sudo chmod 644 *.csv
```

## 📊 모니터링

### 알림 실행 통계

```spl
index=_internal source=*scheduler.log savedsearch_name="*Alert*" earliest=-24h
| stats count by savedsearch_name, status
| sort -count
```

### Slack 전송 성공률

```spl
index=_internal source=*alert_actions.log action_name="slack" earliest=-24h
| stats count by result
| eval success_rate = round(count / sum(count) * 100, 2) . "%"
```

### 상태 변화 빈도

```spl
| inputlookup vpn_state_tracker
| stats count by device, state
| sort -count
```

## 🔐 보안 권장사항

1. **Webhook URL 보호**: `local/alert_actions.conf` 파일을 Git에 커밋하지 마세요
2. **권한 제한**: Splunk 관리자만 앱 수정 가능하도록 설정
3. **채널 접근 제한**: Slack 채널을 보안팀만 접근 가능하도록 설정
4. **토큰 교체**: 주기적으로 Webhook URL 재생성

## 📞 지원

**Repository**: https://github.com/qws941/splunk.git
**버전**: v2.0.4 (2025-11-04)
**문의**: NextTrade Security Team
