# Security Alert System v2.0.4

FortiGate 보안 이벤트 모니터링 및 Slack 알림 시스템

## 핵심 기능

- **EMS 방식 상태 추적**: 중복 알림 제거, 상태 변화만 감지
- **15개 알림**: VPN, HA, 하드웨어, 리소스, 로그인, 트래픽, FMG 동기화 등
- **Slack 통합**: 공식 Slack Alert Action 사용, Plain Text 포맷
- **CSV 상태 저장**: 11개 상태 추적 테이블
- **번들 라이브러리**: Python 의존성 포함, 격리 환경 지원

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

### Slack 알림 설정

이 앱은 **공식 Slack Add-on과 동일한 구조**로 설계되었습니다.

**설정 방법:**

1. Slack Workspace에서 Incoming Webhook 생성
2. Webhook URL 복사
3. Splunk에서 설정:
   ```bash
   # local/alert_actions.conf 생성
   mkdir -p security_alert/local
   cat > security_alert/local/alert_actions.conf <<EOF
   [slack]
   param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   EOF
   ```

**메시지 형식:**
- `attachment = none`: Plain Text 전송 (첨부 형식 없음)
- `formatted_message` 필드: 정리된 단일 메시지
- 이모지 포함
- UUID 패턴 자동 제거
- 긴 값 자동 truncate (40자)

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
- 018_FMG_Out_Of_Sync - FortiManager 동기화 실패

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

**11개 CSV 파일** (EMS 상태 추적):

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
├── license_state_tracker.csv
└── fmg_sync_state_tracker.csv        # FortiManager 동기화 추적
```

**추가 참조 파일**:
- `fortigate_logid_notification_map.csv` - LogID 참조 테이블

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

## 번들 라이브러리

**격리 환경 지원** - 모든 Python 의존성 포함, pip 불필요:

```
lib/python3/
├── requests/          # 2.32.5 - HTTP 클라이언트
├── urllib3/           # 2.5.0 - 연결 풀링
├── charset_normalizer/ # 3.4.4 - 문자 인코딩
├── certifi/           # 2025.10.5 - SSL 인증서
└── idna/              # 3.11 - 도메인 이름 인코딩
```

**장점**:
- ✅ 격리 환경 (air-gapped) 배포 가능
- ✅ 인터넷 접속 불필요
- ✅ pip install 권한 불필요
- ✅ 버전 충돌 방지

## 버전

**v2.0.4** (2025-11-07)
- EMS 상태 추적 적용 (11개 상태 추적 파일)
- Slack 공식 Alert Action 통합 (Plain Text 포맷)
- 15개 알림 활성화 (Alert 018 포함)
- Python 의존성 번들 포함 (격리 환경 지원)

**Repository**: https://github.com/qws941/splunk.git
