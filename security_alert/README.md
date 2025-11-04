# Security Alert System v2.0.4

FortiGate 보안 이벤트 모니터링 및 Slack 알림 시스템

## 핵심 기능

- **EMS 방식 상태 추적**: 중복 알림 제거, 상태 변화만 감지
- **15개 알림**: VPN, HA, 하드웨어, 리소스, 로그인, 트래픽 등
- **Slack Block Kit**: 포맷된 알림 메시지
- **CSV 상태 저장**: 10개 상태 추적 테이블

## 빠른 설치

```bash
# 1. Splunk 서버에 업로드
cd /opt/splunk/etc/apps/
tar -xzf security_alert.tar.gz

# 2. 권한 설정
chown -R splunk:splunk security_alert

# 3. Splunk 재시작
/opt/splunk/bin/splunk restart
```

## 설정

### Slack Webhook URL 설정

`security_alert/default/alert_actions.conf` 파일 수정:

```ini
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
param.channel = #security-firewall-alert
```

또는 환경변수 설정:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

## 알림 목록

### 바이너리 상태 알림 (4개)

| 알림 | 감지 대상 | 심각도 |
|-----|----------|--------|
| 002_VPN_Tunnel_Down/Up | VPN 터널 상태 변화 | Critical |
| 007_Hardware_Failure/Restored | 하드웨어 장애/복구 | Critical |
| 012_Interface_Down/Up | 네트워크 인터페이스 상태 | Medium-High |
| 008_HA_State_Change | HA 역할 변경 | Medium-High |

### 임계값 기반 알림 (6개)

| 알림 | 임계값 | 상태 |
|-----|-------|------|
| 006_CPU_Memory_Anomaly | 평균 대비 20% 편차 | ABNORMAL |
| 010_Resource_Limit | 75% 사용량 | EXCEEDED |
| 011_Admin_Login_Failed | 3회 이상 실패 | ATTACK |
| 013_SSL_VPN_Brute_Force | 5회 이상 실패 | ATTACK |
| 015_Abnormal_Traffic_Spike | 3배 급증 | SPIKE |
| 017_License_Expiry_Warning | 30일 이내 만료 | WARNING |

### 기타 알림 (5개)

- 001_Config_Change - 설정 변경 감지
- 016_System_Reboot - 시스템 재시작

## 상태 추적 로직

```spl
| eval current_state = if(condition, "ABNORMAL", "NORMAL")
| join device [inputlookup state_tracker]
| eval state_changed = if(prev_state != current_state, 1, 0)
| where state_changed=1
| outputlookup append=t state_tracker
```

**장점**:
- ✅ 중복 알림 제거 (상태 변화만)
- ✅ 복구 알림 지원 (DOWN→UP)
- ✅ Suppression 불필요 (즉시 감지)

## 상태 파일

```
security_alert/lookups/
├── vpn_state_tracker.csv
├── hardware_state_tracker.csv
├── ha_state_tracker.csv
├── interface_state_tracker.csv
├── cpu_memory_state_tracker.csv
├── resource_state_tracker.csv
├── admin_login_state_tracker.csv
├── vpn_brute_force_state_tracker.csv
├── traffic_spike_state_tracker.csv
└── license_state_tracker.csv
```

## 트러블슈팅

```spl
# 알림 실행 로그
index=_internal source=*scheduler.log savedsearch_name="*Alert*"

# Slack 전송 로그
index=_internal source=*alert_actions.log action_name="slack"

# 상태 확인
| inputlookup vpn_state_tracker
| inputlookup hardware_state_tracker
```

## 버전

**v2.0.4** (2025-11-04)
- EMS 상태 추적 적용
- Slack Block Kit 알림
- 15개 알림 활성화

**Repository**: https://github.com/qws941/splunk.git
