# Splunk App 배포 체크리스트

## ⚠️ 배포 전 필수 조치 사항

### 🔴 CRITICAL - 반드시 수정 필요

#### 1. 민감 정보 하드코딩 제거

**파일: `bin/fortigate_auto_response.py`** (Line 16-18)
```python
# ❌ 현재 (배포 불가)
FORTIMANAGER_URL = "https://fmg.example.com"
FORTIMANAGER_TOKEN = "YOUR_FMG_API_TOKEN"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# ✅ 수정 필요
FORTIMANAGER_URL = os.environ.get('FORTIMANAGER_URL', 'https://fmg.example.com')
FORTIMANAGER_TOKEN = os.environ.get('FORTIMANAGER_TOKEN')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
```

**해결 방법:**
```bash
# Option 1: Splunk 환경변수 설정 (권장)
# $SPLUNK_HOME/etc/apps/security_alert/local/app.conf
[install]
state = enabled

[package]
check_for_updates = 1

# Option 2: 시스템 환경변수
export FORTIMANAGER_URL="https://your-fmg-server.com"
export FORTIMANAGER_TOKEN="your-actual-token"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK"

# Option 3: Splunk Credential Storage 사용 (가장 안전)
/opt/splunk/bin/splunk add credential -name fortimanager_token -password 'your-token'
```

---

#### 2. Slack Webhook URL 설정

**파일: `default/alert_actions.conf`** (Line 10)
```ini
# ❌ 현재 (빈 값)
param.webhook_url =

# ✅ 수정 방법
# Option 1: Web UI에서 설정
# Settings > Alert actions > Slack > Configure

# Option 2: local/alert_actions.conf 생성
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**생성 방법:**
```bash
mkdir -p /opt/splunk/etc/apps/security_alert/local
cat > /opt/splunk/etc/apps/security_alert/local/alert_actions.conf <<EOF
[slack]
param.webhook_url = YOUR_ACTUAL_WEBHOOK_URL
EOF
```

---

#### 3. Python 캐시 파일 제거

**발견된 파일:**
```
bin/__pycache__/*.pyc
```

**제거 명령:**
```bash
cd /home/jclee/app/alert/security_alert
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
```

**배포 전 확인:**
```bash
tar -czf security_alert.tar.gz security_alert/ --exclude='__pycache__' --exclude='*.pyc'
```

---

### 🟡 WARNING - 설정 검토 권장

#### 4. App 설치 상태 확인

**파일: `default/app.conf`** (Line 2)
```ini
is_configured = 0  # ⚠️ 첫 설치 시 Setup 화면 표시
```

**변경 옵션:**
- `is_configured = 0`: 설치 후 Setup 화면 표시 (현재 설정 - OK)
- `is_configured = 1`: Setup 화면 건너뛰기

---

#### 5. Index 존재 여부 확인

**모든 Alert가 사용하는 Index:**
```spl
`fortigate_index` → index=fw
```

**배포 전 확인:**
```bash
# Splunk에서 확인
/opt/splunk/bin/splunk list index | grep "fw"

# 없으면 생성 필요
/opt/splunk/bin/splunk add index fw -maxTotalDataSizeMB 500000
```

---

#### 6. CSV Lookup 파일 권한

**확인 필요:**
```bash
cd /opt/splunk/etc/apps/security_alert/lookups
ls -l *.csv

# 권한 설정 (Splunk 사용자가 읽기/쓰기 가능해야 함)
chown -R splunk:splunk /opt/splunk/etc/apps/security_alert/lookups/
chmod 644 /opt/splunk/etc/apps/security_alert/lookups/*.csv
```

---

### 🟢 INFO - 선택 사항

#### 7. FortiManager 자동 응답 활성화 여부

**기본 상태:** 비활성화 (하드코딩된 example URL)

**활성화 방법:**
1. FortiManager API 토큰 발급
2. 환경변수 설정 (위 1번 참조)
3. `auto_response_actions.csv` 수정하여 자동 응답 규칙 정의

**테스트 모드 실행:**
```python
# fortigate_auto_response.py에 dry-run 모드 추가 권장
DRY_RUN = os.environ.get('AUTO_RESPONSE_DRY_RUN', 'true').lower() == 'true'
```

---

## 📋 배포 절차

### 1. 배포 전 준비

```bash
# 1) 민감 정보 제거 확인
grep -r "YOUR_" security_alert/bin/
grep -r "example.com" security_alert/bin/

# 2) 캐시 파일 제거
find security_alert/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find security_alert/ -type f -name "*.pyc" -delete

# 3) 아카이브 생성
tar -czf security_alert-$(date +%Y%m%d).tar.gz security_alert/ \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='*.log'

# 4) 파일 크기 확인
ls -lh security_alert-*.tar.gz
```

### 2. Splunk 서버 배포

```bash
# 1) 서버로 전송
scp security_alert-*.tar.gz splunk-server:/tmp/

# 2) 서버에서 압축 해제
ssh splunk-server
cd /opt/splunk/etc/apps/
tar -xzf /tmp/security_alert-*.tar.gz

# 3) 권한 설정
chown -R splunk:splunk security_alert
chmod -R 755 security_alert/bin/
chmod 644 security_alert/lookups/*.csv

# 4) Local 설정 파일 생성
mkdir -p security_alert/local
cat > security_alert/local/alert_actions.conf <<EOF
[slack]
param.webhook_url = YOUR_ACTUAL_WEBHOOK_URL
EOF

# 5) 환경변수 설정 (선택)
cat >> /opt/splunk/etc/splunk-launch.conf <<EOF
FORTIMANAGER_URL=https://your-fmg-server.com
FORTIMANAGER_TOKEN=your-actual-token
EOF

# 6) Splunk 재시작
/opt/splunk/bin/splunk restart
```

### 3. 배포 후 검증

```bash
# 1) App 로딩 확인
/opt/splunk/bin/splunk display app security_alert

# 2) Alert 상태 확인
/opt/splunk/bin/splunk list saved-search -app security_alert | grep "Alert"

# 3) Python 스크립트 실행 가능 확인
cd /opt/splunk/etc/apps/security_alert/bin
python3 -c "import slack; print('OK')"
python3 -c "import fortigate_auto_response; print('OK')"

# 4) 로그 확인
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep "security_alert"
tail -f /opt/splunk/var/log/splunk/auto_response.log

# 5) Web UI에서 확인
# - Apps > Security Alert System
# - Settings > Searches, reports, and alerts > security_alert
# - Settings > Alert actions > Slack
```

### 4. 테스트 Alert 실행

```spl
# 간단한 테스트 (실제 데이터 없이)
| makeresults
| eval device="test-fw01", tunnel="test_vpn", state="DOWN"
| collect index=fw sourcetype=fortigate:utm

# Alert 즉시 실행 테스트
# Settings > Searches, reports, and alerts > 002_VPN_Tunnel_Down
# "Run" 버튼 클릭
```

---

## 🚨 배포 후 모니터링

### Alert 실행 로그
```spl
index=_internal source=*scheduler.log savedsearch_name="*Alert*"
| table _time, savedsearch_name, status, result_count
```

### Slack 전송 로그
```spl
index=_internal source=*alert_actions.log action_name="slack"
| table _time, sid, result
```

### Python 스크립트 에러
```bash
tail -f /opt/splunk/var/log/splunk/python.log | grep "security_alert"
tail -f /opt/splunk/var/log/splunk/auto_response.log
```

---

## 📝 배포 완료 체크리스트

- [ ] `bin/fortigate_auto_response.py` 하드코딩 제거
- [ ] `local/alert_actions.conf`에 Slack Webhook URL 설정
- [ ] Python 캐시 파일 (\_\_pycache\_\_) 제거
- [ ] `index=fw` 존재 확인
- [ ] CSV 파일 권한 설정 (splunk:splunk, 644)
- [ ] 아카이브 생성 시 임시 파일 제외
- [ ] 서버 배포 및 권한 설정
- [ ] Splunk 재시작
- [ ] Web UI에서 App 확인
- [ ] 테스트 Alert 실행
- [ ] Slack 알림 수신 확인
- [ ] 로그 모니터링 설정

---

## 🔧 트러블슈팅

### Issue: "No module named 'requests'"
```bash
/opt/splunk/bin/splunk cmd python3 -m pip install requests
```

### Issue: "Permission denied: lookups/*.csv"
```bash
chown -R splunk:splunk /opt/splunk/etc/apps/security_alert/lookups/
chmod 664 /opt/splunk/etc/apps/security_alert/lookups/*.csv
```

### Issue: Slack 알림 안 옴
```bash
# 1) Webhook URL 테스트
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from Splunk"}'

# 2) Alert action 로그 확인
tail -f /opt/splunk/var/log/splunk/alert_actions.log
```

---

**Last Updated:** 2025-11-06
**Version:** 1.0.0
