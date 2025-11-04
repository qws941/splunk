# Troubleshooting: "설정되지 않음" 문제 해결

## 증상별 해결 방법

### 1. "Slack 설정이 안 됨" 에러

**원인**: Setup 페이지에서 Slack 토큰 미입력

**해결**:
```bash
# Splunk Web 접속
https://your-splunk:8000

# Apps → Security Alert System → Setup 클릭
# 또는 직접 URL:
https://your-splunk:8000/en-US/manager/security_alert/apps/local/security_alert/setup

# 입력 필요:
# - Slack App OAuth Token (xoxb-...) 또는
# - Slack Webhook URL (https://hooks.slack.com/...)

# 저장 후 확인:
cat /opt/splunk/etc/apps/security_alert/local/alert_actions.conf
```

### 2. "Alert Action을 찾을 수 없음"

**원인**: alert_actions.conf가 로드되지 않음

**진단**:
```bash
/opt/splunk/bin/splunk btool alert_actions list | grep -A 20 "^\[slack\]"
```

**해결**:
```bash
# 파일 존재 확인
ls -la /opt/splunk/etc/apps/security_alert/default/alert_actions.conf

# spec 파일 확인
ls -la /opt/splunk/etc/apps/security_alert/README/alert_actions.conf.spec

# Splunk 재시작
sudo /opt/splunk/bin/splunk restart

# 다시 확인
/opt/splunk/bin/splunk btool alert_actions list slack
```

### 3. "파라미터가 유효하지 않음" (Invalid key)

**원인**: alert_actions.conf.spec 누락

**확인**:
```bash
# spec 파일이 있는지 확인
ls -la /opt/splunk/etc/apps/security_alert/README/alert_actions.conf.spec

# 없으면 다시 배포 필요
cd /tmp
tar -xzf security_alert.tar.gz security_alert/README/alert_actions.conf.spec
sudo cp security_alert/README/alert_actions.conf.spec \
  /opt/splunk/etc/apps/security_alert/README/
sudo chown splunk:splunk /opt/splunk/etc/apps/security_alert/README/alert_actions.conf.spec
sudo /opt/splunk/bin/splunk restart
```

### 4. "Python 스크립트 실행 실패"

**원인**: 실행 권한 없음

**확인**:
```bash
ls -la /opt/splunk/etc/apps/security_alert/bin/*.py
# 모두 -rwxr-xr-x (755) 권한이어야 함
```

**해결**:
```bash
sudo chmod 755 /opt/splunk/etc/apps/security_alert/bin/*.py
sudo chown splunk:splunk /opt/splunk/etc/apps/security_alert/bin/*.py
```

### 5. "Alert가 실행되지 않음"

**원인**: Alert가 비활성화됨

**확인**:
```bash
grep -n "enableSched" /opt/splunk/etc/apps/security_alert/default/savedsearches.conf | head -5
```

**해결**:
```bash
# Splunk Web에서:
# Settings → Searches, reports, and alerts
# "Security Alert System" 앱 필터
# 각 Alert의 "Enable" 체크박스 활성화

# 또는 CLI로:
/opt/splunk/bin/splunk edit saved-search "001_Config_Change" \
  -app security_alert -action enableSched -value 1
```

### 6. "Slack 메시지가 안 옴"

**원인 A**: Bot이 채널에 초대되지 않음

**해결**:
```bash
# Slack 채널에서:
/invite @YourBotName

# 또는 Bot Token이 chat:write.public 권한 있으면 초대 불필요
```

**원인 B**: Webhook URL 잘못됨

**확인**:
```bash
# Webhook 테스트
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from CLI"}'

# 응답: "ok" 또는 에러 메시지
```

**원인 C**: Bot Token 잘못됨

**확인**:
```bash
# Bot Token 테스트
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer xoxb-YOUR-TOKEN"

# 응답: {"ok":true,...} 또는 {"ok":false,"error":"invalid_auth"}
```

### 7. "Alert 창에 Slack 액션이 안 보임"

**원인**: Alert Action 등록 안 됨

**진단**:
```bash
# REST API로 확인
curl -k -u admin:password \
  "https://localhost:8089/services/admin/alert_actions?output_mode=json" \
  | jq '.entry[] | select(.name == "slack")'

# 결과 없으면 등록 안 된 것
```

**해결**:
```bash
# 1. 앱 재시작
sudo /opt/splunk/bin/splunk restart

# 2. 권한 확인
sudo chown -R splunk:splunk /opt/splunk/etc/apps/security_alert

# 3. 앱 활성화 상태 확인
/opt/splunk/bin/splunk display app security_alert
# enabled=true 인지 확인

# 4. 비활성화되어 있으면 활성화
/opt/splunk/bin/splunk enable app security_alert
```

## 완전 재배포 (마지막 수단)

```bash
# 1. 백업
cd /opt/splunk/etc/apps/
sudo tar -czf ~/security_alert.backup-$(date +%Y%m%d-%H%M%S).tar.gz security_alert/

# 2. 완전 삭제
sudo /opt/splunk/bin/splunk remove app security_alert -auth admin:password

# 3. 새로 배포
sudo tar -xzf /tmp/security_alert.tar.gz -C /opt/splunk/etc/apps/

# 4. 권한 설정
sudo chown -R splunk:splunk /opt/splunk/etc/apps/security_alert
sudo chmod 755 /opt/splunk/etc/apps/security_alert/bin/*.py

# 5. Splunk 재시작
sudo /opt/splunk/bin/splunk restart

# 6. Setup 다시 실행
# https://your-splunk:8000/en-US/manager/security_alert/apps/local/security_alert/setup
```

## 로그 확인 방법

```bash
# 일반 로그
tail -100 /opt/splunk/var/log/splunk/splunkd.log | grep security_alert

# Alert 실행 로그
tail -100 /opt/splunk/var/log/splunk/alert_actions.log | grep slack

# Python stderr 출력 확인
tail -100 /opt/splunk/var/log/splunk/python.log 2>/dev/null

# Splunk UI에서 로그 검색:
index=_internal source=*splunkd.log "security_alert"
index=_internal source=*alert_actions.log "slack"
```

## 체크리스트

배포 후 반드시 확인:

- [ ] 앱이 활성화됨: `/opt/splunk/bin/splunk display app security_alert`
- [ ] Alert Action 등록됨: `/opt/splunk/bin/splunk btool alert_actions list slack`
- [ ] spec 파일 존재: `ls README/alert_actions.conf.spec`
- [ ] Python 권한: `ls -la bin/*.py` (모두 755)
- [ ] Setup 완료: `ls local/alert_actions.conf`
- [ ] Slack 토큰 입력됨: `grep "param.slack_app_oauth_token\|param.webhook_url" local/alert_actions.conf`
- [ ] Alert 활성화됨: `grep "enableSched = 1" default/savedsearches.conf | wc -l`

## 문의 시 필요한 정보

문제 발생 시 다음 정보를 제공해주세요:

1. **에러 메시지** (정확한 문구)
2. **Splunk 로그**:
   ```bash
   tail -50 /opt/splunk/var/log/splunk/splunkd.log | grep -i security_alert
   ```
3. **btool 출력**:
   ```bash
   /opt/splunk/bin/splunk btool alert_actions list slack
   ```
4. **파일 존재 여부**:
   ```bash
   ls -la /opt/splunk/etc/apps/security_alert/{default,local,README}/
   ```
