# 즉시 해결 가이드 - FortiGate Slack Alerts

**문제**: Slack 앱 미설치, Alert 미생성, 데이터 없음

---

## ✅ Step 1: Splunk Web 접속 (1분)

```bash
# 브라우저 열기
http://localhost:8000
# 또는
http://YOUR_SERVER_IP:8000

# 기본 로그인 (변경했으면 그거 사용)
Username: admin
Password: changeme
```

---

## ✅ Step 2: Slack 앱 설치 (2분)

```
Splunk Web 접속 후:

1. 좌측 상단 [Apps] 클릭
2. [Find More Apps] 클릭
3. 검색창에 "Slack" 입력
4. "Slack Notification Alert" 앱 찾기
5. [Install] 버튼 클릭
6. Splunk.com 계정으로 로그인 (무료 가입)
7. Install 완료 후 [Restart Splunk Now] 클릭

⚠️ 재시작 후 다시 로그인
```

**Alternative (CLI 설치)**:
```bash
# Slack 앱 다운로드
cd /tmp
wget https://splunkbase.splunk.com/app/2878/release/3.2.1/download -O slack-notification-alert.tgz

# 설치
sudo tar -xzvf slack-notification-alert.tgz -C /opt/splunk/etc/apps/

# Splunk 재시작
sudo systemctl restart splunk
# 또는 docker라면:
docker restart splunk
```

---

## ✅ Step 3: Slack Bot Token 설정 (3분)

### 3-1. Slack Bot 생성 (https://api.slack.com/apps)

```
1. [Create New App] 클릭
2. "From scratch" 선택
3. App Name: FortiGate Alerts
4. Workspace 선택
5. [Create App] 클릭
```

### 3-2. Bot Token Scopes 추가

```
좌측 [OAuth & Permissions] 클릭

Scopes 섹션에서 다음 권한 추가:
- chat:write
- chat:write.public
- channels:read

[Save Changes] 클릭
```

### 3-3. Bot Token 복사

```
상단 [Install to Workspace] 클릭
→ 권한 허용
→ Bot User OAuth Token 복사 (xoxb-로 시작)
```

### 3-4. Splunk에 Token 설정

```
Splunk Web:

1. Settings → Alert actions → Slack
2. Enable: Yes
3. Slack API Token: (복사한 xoxb- 토큰 입력)
4. [Save] 클릭
```

---

## ✅ Step 4: Slack 채널 초대 (1분)

```
Slack 앱에서:

1. #security-firewall-alert 채널 열기 (없으면 생성)
2. 채널에서 다음 명령 입력:
   /invite @FortiGate Alerts

✅ "FortiGate Alerts가 채널에 추가되었습니다" 메시지 확인
```

---

## ✅ Step 5: Alert 생성 (5분)

**파일 열기**:
```bash
cat /home/jclee/app/splunk/configs/savedsearches-fortigate-alerts.conf
```

### Alert 1: Config Change Alert

```
Splunk Web:

1. Settings → Searches, reports, and alerts
2. [New Alert] 버튼 클릭
3. 다음 입력:

Title: FortiGate_Config_Change_Alert
Description: FortiGate configuration change notifications

Search (conf 파일의 lines 10-22 복사):
index=fw earliest=rt-30s latest=rt type=event subtype=system \
    (logid=0100044546 OR logid=0100044547) \
    (cfgpath="firewall.policy*" OR cfgpath="firewall.address*" OR cfgpath="firewall.service*" OR cfgpath="system.interface*" OR cfgpath="router.*" OR cfgpath="vpn.*") \
| dedup devname, user, cfgpath \
| eval device = devname \
| eval admin = coalesce(user, "system") \
| eval access_method = case(logid="0100044546", "CLI", logid="0100044547", "GUI", 1=1, coalesce(ui, "N/A")) \
| eval config_path = cfgpath \
| eval action_type = coalesce(action, "Modified") \
| eval object_name = coalesce(cfgobj, "-") \
| eval details = if(isnotnull(cfgattr) AND len(cfgattr) < 100, cfgattr, "...") \
| eval alert_message = "🔥 FortiGate Config Change\nDevice: " + device + "\nAdmin: " + admin + " (" + access_method + ")\nAction: " + action_type + "\nPath: " + config_path + "\nObject: " + object_name + "\nDetails: " + details \
| table alert_message, device, admin, config_path

4. Alert type: Real-time
5. Trigger Conditions:
   - Number of Results
   - is greater than: 0

6. Trigger Actions:
   - Add Actions → Slack
   - Channel: #security-firewall-alert
   - Message: $result.alert_message$

7. Throttle:
   - [✓] Suppress results containing field values
   - Fields: user, cfgpath
   - Suppress for: 15 seconds

8. [Save] 클릭
```

### Alert 2: Critical Event Alert

```
동일한 방법으로 생성:

Title: FortiGate_Critical_Event_Alert

Search (lines 52-61):
index=fw earliest=rt-30s latest=rt type=event subtype=system level=critical \
    logid!=0100044546 logid!=0100044547 logid!=010032021 \
| search NOT msg="*Update Fail*" NOT msg="*Login Fail*" \
| dedup devname, logid \
| eval device = devname \
| eval log_id = logid \
| eval severity = level \
| eval description = coalesce(logdesc, msg, "No details available") \
| eval alert_message = "🚨 FortiGate CRITICAL Event\nDevice: " + device + "\nLogID: " + log_id + "\nDescription: " + description \
| table alert_message, device, log_id, severity

Trigger: Real-time, Number of Results > 0
Action: Slack (#security-firewall-alert, $result.alert_message$)
Throttle: devname, logid, 15 seconds
```

### Alert 3: HA Event Alert

```
Title: FortiGate_HA_Event_Alert

Search (lines 91-99):
index=fw earliest=rt-30s latest=rt type=event subtype=system logid=0103* \
| dedup devname, logid, level \
| eval device = devname \
| eval log_id = logid \
| eval severity = level \
| eval description = coalesce(logdesc, msg, "HA event occurred") \
| eval icon = case(level="critical", "🔴", level="error", "🟠", level="warning", "🟡", 1=1, "🔵") \
| eval alert_message = icon + " FortiGate HA Event\nDevice: " + device + "\nSeverity: " + severity + "\nLogID: " + log_id + "\nDescription: " + description \
| table alert_message, device, log_id, severity

Trigger: Real-time, Number of Results > 0
Action: Slack (#security-firewall-alert, $result.alert_message$)
Throttle: devname, logid, 15 seconds
```

---

## ✅ Step 6: UDP Input 설정 (2분)

```
Splunk Web:

1. Settings → Data inputs → UDP
2. [New Local UDP] 클릭
3. 입력:
   - Port: 6514
   - Source name override: fortigate
   - Source type: fgt_log (없으면 Manual 입력)
   - Index: fw (없으면 먼저 생성: Settings → Indexes → New Index)
4. [Save] 클릭
```

**Index 생성 (fw 인덱스가 없을 경우)**:
```
Settings → Indexes → New Index

Index Name: fw
Index Data Type: Events
[Save] 클릭
```

---

## ✅ Step 7: FortiGate Syslog 설정 (2분)

```bash
# FortiGate CLI 접속 (SSH)
config log syslogd setting
  set status enable
  set server "YOUR_SPLUNK_SERVER_IP"
  set port 6514
  set format default
  set facility local7
end
```

**또는 GUI 설정**:
```
FortiGate Web:

1. Log & Report → Log Settings
2. Syslog 탭
3. [Create New] 클릭
4. 입력:
   - Name: Splunk
   - IP Address: YOUR_SPLUNK_SERVER_IP
   - Port: 6514
   - Facility: local7
   - Format: Default
5. [OK] 클릭
```

---

## ✅ Step 8: 검증 (2분)

### 8-1. 데이터 확인

```spl
# Splunk Search:
index=fw earliest=-5m | stats count

# 결과: count > 0 확인 (데이터 들어오는 중)
```

### 8-2. Alert 활성화 확인

```spl
| rest /services/saved/searches
| search title="FortiGate_*"
| table title, disabled, actions

# 결과:
# title                              disabled  actions
# FortiGate_Config_Change_Alert      0         slack
# FortiGate_Critical_Event_Alert     0         slack
# FortiGate_HA_Event_Alert           0         slack
```

### 8-3. 테스트 알림 발송

```
FortiGate에서 테스트 설정 변경:
1. Firewall Policy 생성/수정
2. 30초 후 Slack #security-firewall-alert 채널 확인

예상 메시지:
🔥 FortiGate Config Change
Device: FGT-1
Admin: admin (GUI)
Action: Modified
Path: firewall.policy[5]
Object: TestPolicy
Details: ...
```

---

## ❌ 문제 해결

### 문제 1: Slack 메시지 안 옴

**원인**: Bot이 채널에 없음

**해결**:
```
Slack 채널에서:
/invite @FortiGate Alerts
```

### 문제 2: "index=fw" 데이터 없음

**원인**: UDP 포트 막혔거나 FortiGate 설정 오류

**해결**:
```bash
# 방화벽 확인 (Rocky Linux)
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=6514/udp --permanent
sudo firewall-cmd --reload

# 포트 리스닝 확인
ss -ulnp | grep 6514

# FortiGate 연결 확인 (tcpdump)
sudo tcpdump -i any udp port 6514 -n
```

### 문제 3: Alert 실행 안 됨

**원인**: Real-time search 제한

**해결**:
```
# limits.conf 수정
sudo vi /opt/splunk/etc/system/local/limits.conf

[search]
max_rt_search_multiplier = 10

# Splunk 재시작
sudo systemctl restart splunk
```

---

## 📊 모니터링

```spl
# Alert 실행 기록
index=_audit action=alert_fired
| stats count by savedsearch_name

# 최근 Alert 결과
| rest /services/saved/searches
| search title="FortiGate_*"
| table title, triggered_alert_count, next_scheduled_time

# Slack 발송 실패
index=_internal source=*slack*
| search ERROR OR WARN
```

---

**총 소요 시간**: ~20분
**전제 조건**: Splunk 실행 중, FortiGate CLI/GUI 접근 가능, Slack Workspace admin 권한
