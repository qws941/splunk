# Deployment Checklist

배포 후 반드시 확인해야 할 체크리스트입니다.

## 📦 배포 단계

### 1. 파일 복사
```bash
scp release/security_alert.tar.gz splunk-server:/tmp/
```

### 2. Splunk 서버 접속
```bash
ssh splunk-server
cd /opt/splunk/etc/apps/
```

### 3. 기존 버전 백업 (선택)
```bash
sudo tar -czf ~/security_alert.backup-$(date +%Y%m%d-%H%M%S).tar.gz security_alert/
```

### 4. 새 버전 배포
```bash
# 기존 삭제
sudo rm -rf security_alert/

# 압축 해제
sudo tar -xzf /tmp/security_alert.tar.gz
sudo mv security_alert security_alert_temp
sudo mkdir security_alert
sudo mv security_alert_temp/* security_alert/
sudo rmdir security_alert_temp
```

### 5. 권한 설정
```bash
sudo chown -R splunk:splunk security_alert
sudo chmod 755 security_alert/bin/*.py
```

### 6. Splunk 재시작
```bash
sudo /opt/splunk/bin/splunk restart
```

---

## ✅ 배포 후 검증

### Step 1: 앱 활성화 확인
```bash
/opt/splunk/bin/splunk display app security_alert
```
**Expected**: `enabled=true`

**❌ If disabled**:
```bash
/opt/splunk/bin/splunk enable app security_alert
sudo /opt/splunk/bin/splunk restart
```

---

### Step 2: Alert Action 등록 확인
```bash
/opt/splunk/bin/splunk btool alert_actions list slack
```

**Expected**: `[slack]` 섹션과 7개 파라미터 표시:
```
[slack]
command = slack_blockkit_alert.py
is_custom = 1
label = Send to Slack (Block Kit)
param.slack_app_oauth_token =
param.webhook_url =
param.proxy_enabled = 0
param.proxy_url =
param.proxy_port =
param.proxy_username =
param.proxy_password =
python.version = python3
```

**❌ If empty or missing**:
```bash
# spec 파일 확인
ls -la /opt/splunk/etc/apps/security_alert/README/alert_actions.conf.spec

# 없으면 파일 누락, 재배포 필요
```

---

### Step 3: spec 파일 확인
```bash
ls -la /opt/splunk/etc/apps/security_alert/README/alert_actions.conf.spec
```

**Expected**: 파일 존재, readable 권한

**❌ If missing**:
```bash
# 재배포 또는 수동 복사
cat > /opt/splunk/etc/apps/security_alert/README/alert_actions.conf.spec << 'EOF'
# alert_actions.conf.spec
[slack]
param.slack_app_oauth_token = <string>
param.webhook_url = <string>
param.proxy_enabled = <boolean>
param.proxy_url = <string>
param.proxy_port = <string>
param.proxy_username = <string>
param.proxy_password = <string>
EOF

sudo chown splunk:splunk /opt/splunk/etc/apps/security_alert/README/alert_actions.conf.spec
sudo /opt/splunk/bin/splunk restart
```

---

### Step 4: Python 스크립트 권한 확인
```bash
ls -la /opt/splunk/etc/apps/security_alert/bin/*.py
```

**Expected**: 모두 `-rwxr-xr-x` (755) 권한, `splunk:splunk` 소유

**❌ If wrong permissions**:
```bash
sudo chmod 755 /opt/splunk/etc/apps/security_alert/bin/*.py
sudo chown splunk:splunk /opt/splunk/etc/apps/security_alert/bin/*.py
```

---

### Step 5: Setup 페이지 접속
**URL**: `https://your-splunk:8000/en-US/manager/security_alert/apps/local/security_alert/setup`

**Expected 화면**:
- ✅ **Slack Configuration** 섹션
  - Slack App OAuth Token (password 입력란)
  - Slack Webhook URL (password 입력란)
- ✅ **Proxy Configuration (Optional)** 섹션 (같은 페이지 아래쪽)
  - Enable Proxy (checkbox)
  - Proxy Server (text 입력란)
  - Proxy Port (text 입력란)
  - Proxy Username (text 입력란)
  - Proxy Password (password 입력란)
- ✅ **Setup Instructions** 섹션

**❌ If proxy 설정 안 보임**:
```bash
# setup.xml 확인
cat /opt/splunk/etc/apps/security_alert/default/setup.xml | grep -A 5 "Proxy Configuration"

# 없으면 파일 문제, 재배포 필요
```

---

### Step 6: Slack 설정 입력

**Method 1 (권장)**: Bot Token
```
Slack App OAuth Token: xoxb-YOUR-TOKEN-HERE
```

**Method 2 (대안)**: Webhook URL
```
Slack Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**프록시 필요 시**:
```
Enable Proxy: ✓ (체크)
Proxy Server: proxy.company.com
Proxy Port: 8080
Proxy Username: (선택)
Proxy Password: (선택)
```

**저장 후** `local/alert_actions.conf` 파일 생성 확인:
```bash
cat /opt/splunk/etc/apps/security_alert/local/alert_actions.conf
```

---

### Step 7: 쿼리 문법 검증
```bash
# btool로 saved search 검증
/opt/splunk/bin/splunk btool savedsearches list --debug | grep -i error

# 또는 수동 검증
grep "search =" /opt/splunk/etc/apps/security_alert/default/savedsearches.conf | head -5
```

**Expected**: No syntax errors

**❌ If errors found**: 로그 확인
```bash
tail -50 /opt/splunk/var/log/splunk/splunkd.log | grep -i "security_alert\|savedsearches"
```

---

### Step 8: Alert 활성화 상태 확인
```bash
grep "enableSched = 1" /opt/splunk/etc/apps/security_alert/default/savedsearches.conf | wc -l
```

**Expected**: `12` (12개 active alerts)

---

### Step 9: 데이터 확인
```spl
index=fw earliest=-1h | head 10
```

**Expected**: FortiGate 로그 데이터 존재

**❌ If no data**: FortiGate syslog 설정 확인 필요

---

### Step 10: Alert 테스트
```spl
index=fw earliest=-1h | savedsearch 001_Config_Change
```

또는 Splunk Web:
- Search & Reporting → Alert 선택 → "Run"

**Expected**: Slack 채널에 메시지 수신

**❌ If no message**:
```bash
# Alert action 로그 확인
tail -50 /opt/splunk/var/log/splunk/alert_actions.log | grep slack
```

---

## 🚨 일반적인 문제 해결

### 문제 1: "Invalid key" 에러 (btool)
**원인**: `alert_actions.conf.spec` 누락
**해결**: Step 3 참조

### 문제 2: Setup 페이지에 프록시 설정 안 보임
**원인**:
- Splunk 재시작 안 함
- setup.xml 파일 문제

**해결**:
```bash
# 파일 확인
cat /opt/splunk/etc/apps/security_alert/default/setup.xml | grep "Proxy Configuration"

# 재시작
sudo /opt/splunk/bin/splunk restart
```

### 문제 3: Slack 메시지 안 옴
**원인**:
- Bot이 채널에 초대 안 됨
- Token/Webhook URL 잘못됨
- 프록시 설정 필요한데 안 함

**해결**:
1. Slack 채널에서 `/invite @BotName`
2. Token 테스트: `curl -X POST https://slack.com/api/auth.test -H "Authorization: Bearer TOKEN"`
3. 프록시 설정 활성화

### 문제 4: Alert가 실행 안 됨
**원인**: 데이터 없음 또는 Alert 비활성화

**해결**:
```spl
# 데이터 확인
index=fw earliest=-1h | stats count

# Alert 스케줄 확인
| rest /services/saved/searches
| search title="*Alert*"
| table title, disabled, cron_schedule
```

---

## 📊 배포 성공 확인

모든 체크 항목이 ✅이면 배포 성공:

- [ ] 앱 활성화 (`enabled=true`)
- [ ] Alert Action 등록 (`btool` 출력 정상)
- [ ] spec 파일 존재
- [ ] Python 스크립트 권한 (755)
- [ ] Setup 페이지 접속 가능
- [ ] Slack 토큰 또는 Webhook URL 입력
- [ ] 프록시 설정 (필요 시) 입력
- [ ] 쿼리 검증 통과
- [ ] 12개 Alert 활성화 확인
- [ ] 데이터 존재 확인
- [ ] Alert 테스트 성공 (Slack 메시지 수신)

---

**배포 완료 시각 기록**: ___________
**배포자**: ___________
**검증자**: ___________
