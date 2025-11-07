# Deployment Guide - Security Alert System v2.0.4

## Overview

**Security Alert System**은 FortiGate 보안 이벤트를 모니터링하고 Slack으로 알림을 전송하는 독립 Splunk 앱입니다.

## Architecture

```
security_alert/
├── app.manifest                       # Splunk 앱 매니페스트
├── README.md                          # 사용자 문서
├── default/                           # 기본 설정
│   ├── app.conf                       # 앱 메타데이터
│   ├── savedsearches.conf             # 15개 알림 정의
│   ├── macros.conf                    # LogID 그룹, 임계값
│   ├── transforms.conf                # 11개 상태 추적 + 3개 참조 lookup
│   ├── alert_actions.conf             # Slack webhook 설정
│   └── data/ui/
│       ├── views/*.xml                # 대시보드 (4개)
│       └── nav/default.xml            # 네비게이션
├── local/                             # 사용자 재정의 (gitignored)
│   ├── alert_actions.conf             # Slack webhook (필수)
│   └── savedsearches.conf             # 알림 enable/disable
├── bin/                               # Python 스크립트
│   ├── slack.py                       # Slack 메시지 포매터
│   ├── safe_fmt.py                    # 안전 문자열 포맷
│   └── six.py                         # Python 2/3 호환
├── lib/python3/                       # 번들 의존성 (pip 불필요)
│   ├── requests/                      # HTTP 클라이언트
│   ├── urllib3/                       # 연결 풀링
│   ├── charset_normalizer/            # 문자 인코딩
│   ├── certifi/                       # SSL 인증서
│   └── idna/                          # 도메인 인코딩
├── lookups/                           # CSV 상태 추적 + 참조 데이터
│   ├── *_state_tracker.csv            # 11개 상태 추적 파일
│   └── fortigate_logid_notification_map.csv  # LogID 참조
└── metadata/
    └── default.meta                   # 권한 설정
```

## Prerequisites

- **Splunk Enterprise** 8.x 또는 9.x
- **FortiGate 로그** Splunk에 인덱싱됨 (기본: `index=fw`)
- **Slack Workspace** Incoming Webhook 생성됨
- **파일 시스템 권한** splunk 사용자 읽기/쓰기 권한

## Deployment Steps

### 1. 패키지 다운로드

```bash
# GitLab에서 다운로드
cd /tmp
curl -O https://gitlab.jclee.me/jclee/splunk/-/archive/main/splunk-main.tar.gz
tar -xzf splunk-main.tar.gz
```

### 2. Splunk 서버에 배포

```bash
# Splunk 앱 디렉토리로 복사
cd /opt/splunk/etc/apps/
cp -r /tmp/splunk-main/security_alert .

# 권한 설정
chown -R splunk:splunk security_alert
chmod 755 security_alert/bin/*.py
chmod 755 security_alert/lib/python3

# 번들 라이브러리 권한 확인
ls -la security_alert/lib/python3/
```

### 3. Slack Webhook 설정

**방법 1: local 설정 파일** (권장)

```bash
# local 디렉토리 생성
mkdir -p /opt/splunk/etc/apps/security_alert/local

# Slack webhook 설정
cat > /opt/splunk/etc/apps/security_alert/local/alert_actions.conf <<EOF
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF

# 권한 설정
chown splunk:splunk /opt/splunk/etc/apps/security_alert/local/alert_actions.conf
```

**방법 2: 환경 변수**

```bash
# Splunk 환경 변수 설정
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# systemd에 추가 (선택)
echo "Environment=SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  >> /etc/systemd/system/splunk.service
```

### 4. FortiGate 인덱스 설정 (선택)

기본값 `index=fw`가 아닌 경우:

```bash
# local/macros.conf 생성
cat > /opt/splunk/etc/apps/security_alert/local/macros.conf <<EOF
[fortigate_index]
definition = index=your_fortigate_index
EOF
```

### 5. Splunk 재시작

```bash
# Splunk 재시작
/opt/splunk/bin/splunk restart

# 로그 확인 (2-3분 소요)
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep security_alert
```

### 6. 배포 검증

#### 6.1. 앱 로드 확인

```spl
# Splunk 내부 로그 확인
index=_internal source=*splunkd.log security_alert
| stats count by log_level
```

#### 6.2. 알림 활성화 확인

```spl
# 저장된 검색 확인
| rest /services/saved/searches
| search title="*Alert*"
| table title, disabled, cron_schedule, actions
| where disabled=0
```

**예상 결과**: 15개 알림 모두 `disabled=0`, `actions=slack`

#### 6.3. 번들 라이브러리 테스트

```bash
# Python 환경 테스트
cd /opt/splunk/etc/apps/security_alert
python3 -c "
import sys
sys.path.insert(0, 'lib/python3')
import requests
print('✓ Bundled libraries working')
"
```

#### 6.4. 상태 추적 파일 확인

```spl
# 상태 추적 CSV 확인
| inputlookup vpn_state_tracker
| stats count

# 모든 상태 추적 파일 확인
| rest /services/data/lookup-table-files
| search title="*state_tracker*"
| table title, eai:acl.app
```

**예상 결과**: 11개 state_tracker CSV 파일

#### 6.5. Slack 통합 테스트

```bash
# 수동 알림 테스트
cat > /tmp/test_alert.json <<EOF
{
  "search_name": "Test Alert",
  "results_link": "http://localhost:8000",
  "configuration": {
    "webhook_url": "$(cat /opt/splunk/etc/apps/security_alert/local/alert_actions.conf | grep webhook_url | cut -d'=' -f2 | tr -d ' ')"
  },
  "result": {
    "formatted_message": "🧪 Test Alert | This is a test message from Security Alert System v2.0.4"
  }
}
EOF

cd /opt/splunk/etc/apps/security_alert/bin
python3 slack.py < /tmp/test_alert.json
```

#### 6.6. 실시간 로그 모니터링

```spl
# 알림 실행 로그 (실시간)
index=_internal source=*scheduler.log savedsearch_name="*Alert*"
| stats count by savedsearch_name, status, result_count
| sort - count

# Slack 전송 로그 (실시간)
index=_internal source=*alert_actions.log action_name="slack"
| table _time, savedsearch_name, action_status, stderr
| sort - _time
```

## Customization

### 알림 비활성화

```bash
# local/savedsearches.conf에 추가
cat > /opt/splunk/etc/apps/security_alert/local/savedsearches.conf <<EOF
[002_VPN_Tunnel_Down]
enableSched = 0

[011_Admin_Login_Failed]
enableSched = 0
EOF

# Splunk 재시작
/opt/splunk/bin/splunk restart
```

### 임계값 변경

```bash
# CPU 임계값 변경 (80% → 90%)
cat > /opt/splunk/etc/apps/security_alert/local/macros.conf <<EOF
[cpu_high_threshold]
definition = 90

[memory_high_threshold]
definition = 90
EOF
```

### Slack 채널 변경

```bash
# 특정 알림의 Slack 채널 변경
cat >> /opt/splunk/etc/apps/security_alert/local/savedsearches.conf <<EOF
[001_Config_Change]
action.slack.param.channel = #your-custom-channel

[007_Hardware_Failure]
action.slack.param.channel = #critical-alerts
EOF
```

## Monitoring

### 알림 실행 통계

```spl
# 최근 24시간 알림 실행 통계
index=_internal source=*scheduler.log savedsearch_name="*Alert*" earliest=-24h
| stats count by savedsearch_name, status
| eval alert_name = replace(savedsearch_name, "^[0-9]+_", "")
| table alert_name, status, count
| sort - count
```

### Slack 전송 성공률

```spl
# Slack 전송 성공률 (최근 7일)
index=_internal source=*alert_actions.log action_name="slack" earliest=-7d
| stats count by action_status
| eval success_rate = round(count / sum(count) * 100, 2)
| table action_status, count, success_rate
```

### 상태 추적 파일 크기

```bash
# 상태 추적 CSV 크기 확인
ls -lh /opt/splunk/etc/apps/security_alert/lookups/*_state_tracker.csv
```

**권장**: 각 파일 < 1MB (약 10,000 행)

### 성능 모니터링

```spl
# 알림 실행 시간 (최근 24시간)
index=_internal source=*scheduler.log savedsearch_name="*Alert*" earliest=-24h
| stats avg(run_time) as avg_runtime, max(run_time) as max_runtime by savedsearch_name
| eval avg_runtime = round(avg_runtime, 2)
| eval max_runtime = round(max_runtime, 2)
| table savedsearch_name, avg_runtime, max_runtime
| sort - max_runtime
```

## Troubleshooting

### 문제 1: 알림이 실행되지 않음

**증상**: 알림이 예약되었지만 실행되지 않음

**원인**:
- FortiGate 인덱스에 데이터 없음
- 알림이 비활성화됨
- 스케줄러 문제

**해결**:
```spl
# 1. FortiGate 데이터 확인
index=fw earliest=-1h
| stats count by logid, devname
| head 10

# 2. 알림 활성화 상태 확인
| rest /services/saved/searches
| search title="002_VPN_Tunnel_Down"
| table title, disabled, cron_schedule

# 3. 스케줄러 로그 확인
index=_internal source=*scheduler.log savedsearch_name="002_VPN_Tunnel_Down"
| table _time, status, result_count, run_time
```

### 문제 2: Slack으로 알림이 전송되지 않음

**증상**: 알림은 실행되지만 Slack 메시지 없음

**원인**:
- Webhook URL 미설정
- Webhook URL 잘못됨
- Slack API 오류

**해결**:
```bash
# 1. Webhook URL 확인
cat /opt/splunk/etc/apps/security_alert/local/alert_actions.conf | grep webhook_url

# 2. Slack 전송 로그 확인
index=_internal source=*alert_actions.log action_name="slack" earliest=-1h
| table _time, savedsearch_name, action_status, stderr
| head 20

# 3. 수동 테스트
curl -X POST YOUR_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message from Security Alert System"}'
```

### 문제 3: 중복 알림 발생

**증상**: 동일한 상태에 대해 반복 알림

**원인**:
- 상태 추적 CSV 파일 권한 문제
- `outputlookup` 실패
- CSV 잠금 오류

**해결**:
```bash
# 1. CSV 권한 확인
ls -la /opt/splunk/etc/apps/security_alert/lookups/*.csv
chown splunk:splunk /opt/splunk/etc/apps/security_alert/lookups/*.csv

# 2. 상태 추적 로그 확인
index=_internal source=*splunkd.log outputlookup error
| table _time, message

# 3. 상태 추적 데이터 확인
| inputlookup vpn_state_tracker
| stats count by device, state
```

### 문제 4: 번들 라이브러리 로드 실패

**증상**: `ModuleNotFoundError: No module named 'requests'`

**원인**:
- lib/ 디렉토리 권한 문제
- sys.path 설정 오류

**해결**:
```bash
# 1. lib/ 권한 수정
chmod -R 755 /opt/splunk/etc/apps/security_alert/lib/
chown -R splunk:splunk /opt/splunk/etc/apps/security_alert/lib/

# 2. Python 경로 테스트
cd /opt/splunk/etc/apps/security_alert
python3 -c "
import sys
sys.path.insert(0, 'lib/python3')
import requests
print('OK')
"

# 3. 스크립트 실행 테스트
cd bin
python3 -c "
import sys, os
sys.path.insert(0, '../lib/python3')
import requests
print('Bundled libraries OK')
"
```

### 문제 5: 상태 추적 CSV 크기 증가

**증상**: CSV 파일이 10MB 이상으로 증가

**원인**: 오래된 상태 데이터 누적

**해결**:
```spl
# 월별 정리 스케줄 (30일 이상 데이터 삭제)
| inputlookup vpn_state_tracker
| where last_seen > relative_time(now(), "-30d")
| outputlookup vpn_state_tracker

# 모든 상태 추적 파일 정리 스크립트
| rest /services/data/lookup-table-files
| search title="*state_tracker*"
| fields title
| map search="| inputlookup $title$ | where last_seen > relative_time(now(), \"-30d\") | outputlookup $title$"
```

## Maintenance

### 월별 유지보수 체크리스트

```bash
# 1. 상태 추적 파일 크기 확인
du -sh /opt/splunk/etc/apps/security_alert/lookups/*.csv

# 2. 오래된 상태 정리 (SPL 참조 - 위 참조)

# 3. 알림 성능 모니터링 (SPL 참조 - Monitoring 섹션)

# 4. 로그 분석
index=_internal source=*splunkd.log security_alert error OR warning earliest=-7d
| stats count by log_level, message

# 5. Slack 전송 실패 확인
index=_internal source=*alert_actions.log action_status=failure earliest=-7d
| table _time, savedsearch_name, stderr
```

### 백업 권장사항

```bash
# 상태 추적 파일 백업 (일별)
tar -czf /backup/security_alert_state_$(date +%Y%m%d).tar.gz \
  /opt/splunk/etc/apps/security_alert/lookups/*_state_tracker.csv

# 설정 파일 백업 (변경 시)
tar -czf /backup/security_alert_config_$(date +%Y%m%d).tar.gz \
  /opt/splunk/etc/apps/security_alert/local/
```

## Rollback

배포를 롤백하려면:

```bash
# 1. 앱 비활성화
/opt/splunk/bin/splunk disable app security_alert

# 2. Splunk 재시작
/opt/splunk/bin/splunk restart

# 또는 앱 완전 제거
rm -rf /opt/splunk/etc/apps/security_alert
/opt/splunk/bin/splunk restart
```

## Version History

**v2.0.4** (2025-11-07)
- 독립 Splunk 앱으로 재구성
- EMS 상태 추적 (11개 CSV 파일)
- Slack 공식 Alert Action 통합
- Python 의존성 번들 포함
- Alert 018 (FMG Out of Sync) 추가

**v2.0.3** (2025-11-04)
- FMG 동기화 SPL 수정
- EMS 상태 추적 구현
- Slack 메시지 포맷 개선

## Support

**Repository**: https://github.com/qws941/splunk.git
**Maintainer**: NextTrade Security Team
**Documentation**: See `CLAUDE.md` for development details
