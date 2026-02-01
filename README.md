# Security Alert System v2.0.4

FortiGate 보안 이벤트 모니터링 및 Slack 알림 시스템

## 📦 배포 패키지

**파일명**: `security_alert.tar.gz` (26KB, 38개 파일)

```bash
# Splunk 설치
cd /opt/splunk/etc/apps/
tar -xzf security_alert.tar.gz
chown -R splunk:splunk security_alert
/opt/splunk/bin/splunk restart
```

## 🚨 알림 목록 (15개)

### 활성 알림 (12개) ✅

**바이너리 상태 (4개)**:
- `002_VPN_Tunnel` - VPN DOWN/UP 감지
- `007_Hardware` - 하드웨어 FAIL/OK
- `012_Interface` - 인터페이스 DOWN/UP
- `008_HA_State` - HA 역할 변경

**임계값 상태 (3개)**:
- `006_CPU_Memory` - 20% 이상 편차 → ABNORMAL
- `010_Resource` - 75% 사용 → EXCEEDED
- `015_Traffic_Spike` - 3배 급증 → SPIKE

**기타 (5개)**:
- `001_Config_Change` - 설정 변경
- `016_System_Reboot` - 재시작

### 비활성 알림 (3개) - 상태 추적만 수행 ⏸️

- `011_Admin_Login` - 어드민 로그인 실패 (상태 추적만)
- `013_VPN_Brute_Force` - VPN 브루트포스 (상태 추적만)
- `017_License` - 라이센스 만료 (상태 추적만)

**참고**: 비활성 알림은 `enableSched = 0`으로 설정되어 있어 Slack 알림은 발송되지 않지만, CSV 상태 파일에는 계속 기록됩니다.

## 💡 EMS 상태 추적

```spl
| eval current_state = if(condition, "ABNORMAL", "NORMAL")
| join device [inputlookup state_tracker]
| eval changed = if(prev != current, 1, 0)
| where changed=1 AND current_state="ABNORMAL"
| outputlookup append=t state_tracker
```

**장점**:
- ✅ 중복 알림 제거
- ✅ 복구 알림 (DOWN→UP)
- ✅ Suppression 불필요
- ✅ CSV 상태 저장

## 📁 프로젝트 구조

```
/home/jclee/app/splunk/
├── security_alert.tar.gz        # 🎯 배포 패키지 (16KB)
├── security_alert/               # 소스 디렉토리
│   ├── bin/                      # Python 스크립트
│   │   ├── slack_blockkit_alert.py
│   │   └── fortigate_auto_response.py
│   ├── default/                  # 기본 설정
│   │   ├── app.conf
│   │   ├── alert_actions.conf
│   │   ├── props.conf
│   │   ├── transforms.conf
│   │   ├── macros.conf
│   │   ├── savedsearches.conf
│   │   └── setup.xml
│   ├── lookups/                  # 13개 CSV
│   │   ├── fortigate_logid_notification_map.csv
│   │   ├── severity_priority.csv
│   │   ├── auto_response_actions.csv
│   │   └── *_state_tracker.csv (10개)
│   ├── local/                    # 사용자 수정
│   └── metadata/
│       └── default.meta
├── INSTALLATION_GUIDE.md         # 설치 가이드
├── nextrade/                     # ⚠️ 레거시 (참고용)
├── configs/                      # 설정 참조
├── lookups/                      # 공통 CSV
└── archive-dev/                  # 개발 아카이브
```

## ⚙️ Slack 설정

**방법 1: Bot Token (권장)**
```bash
# Splunk Web → Apps → Security Alert System → Setup
Slack Bot Token: xoxb-YOUR-BOT-TOKEN
Channel: #security-firewall-alert
```
**필요 권한**: `chat:write`, `chat:write.public`, `channels:read`

**방법 2: Webhook URL (대안)**
```bash
# Splunk Web → Apps → Security Alert System → Setup
Slack Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
Channel: #security-firewall-alert
```
**필요 권한**: Incoming Webhooks (Slack App)

## 🔍 트러블슈팅

```spl
# 알림 실행 로그
index=_internal source=*scheduler.log savedsearch_name="*Alert*"

# Slack 전송 로그
index=_internal source=*alert_actions.log action_name="slack"

# 상태 확인
| inputlookup vpn_state_tracker
| inputlookup hardware_state_tracker
```

## 📊 상태 파일 (10개)

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

## 🗂️ 디렉토리 설명

| 디렉토리 | 용도 | 사용자 필요 여부 |
|---------|------|------------------|
| `security_alert.tar.gz` | 🎯 **배포 패키지** | ✅ 필수 (Splunk 설치) |
| `security_alert/` | 소스 코드 | ⚠️ 수정 시만 |
| `INSTALLATION_GUIDE.md` | 설치 가이드 | 📖 참고 (필독) |
| `configs/` | 설정 참조 | 📖 참고용 |
| `lookups/` | 공통 CSV | 📖 참고용 |
| `nextrade/` | 레거시 (v2.0.3) | ❌ 무시 |
| `archive-dev/` | 개발 아카이브 | ❌ 무시 |

## 🚀 빠른 시작

1. **Splunk 서버에 업로드**
   ```bash
   scp security_alert.tar.gz splunk-server:/tmp/
   ```

2. **설치**
   ```bash
   ssh splunk-server
   cd /opt/splunk/etc/apps/
   sudo tar -xzf /tmp/security_alert.tar.gz
   sudo chown -R splunk:splunk security_alert
   sudo /opt/splunk/bin/splunk restart
   ```

3. **Slack Webhook 설정**
   - Splunk Web → Apps → Security Alert System → Setup
   - Webhook URL 입력 → Save

4. **검증**
   ```spl
   # 데이터 확인
   index=fw earliest=-1h | stats count

   # 알림 로그 확인
   index=_internal source=*scheduler.log savedsearch_name="*Alert*"
   ```

끝!

## 📌 버전

**v2.0.4** (2025-11-04)
- EMS 상태 추적 적용
- Slack Block Kit 알림
- Lookup 테이블 수정 (transforms.conf 정리)
- 15개 알림 활성화

**Repository**: https://github.com/jclee-homelab/splunk.git
