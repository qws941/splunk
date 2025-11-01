# savedsearches-fortigate-alerts.conf 업데이트 요약

**파일**: `configs/savedsearches-fortigate-alerts.conf`
**업데이트 날짜**: 2025-10-29
**변경 사항**: eval 에러 수정 + Slack 포맷 개선

---

## 🔧 수정된 내용

### 1. Alert 1 - Config Change Alert (Line 20-21)

**❌ 이전 (에러 발생)**:
```spl
| eval details = if(isnotnull(cfgattr) AND len(cfgattr) < 100, cfgattr, "...")
| eval alert_message = "🔥 FortiGate Config Change\nDevice: " + device + "\nAdmin: " + admin + " (" + access_method + ")\nAction: " + action_type + "\nPath: " + config_path + "\nObject: " + object_name + "\nDetails: " + details
```

**✅ 수정 후**:
```spl
| eval details = case(isnull(cfgattr), "No details", 1=1, substr(cfgattr, 1, 100))
| eval alert_message = "🔥 FortiGate Config Change - Device: " + device + " | Admin: " + admin + " (" + access_method + ") | Action: " + action_type + " | Path: " + config_path + " | Object: " + object_name + " | Details: " + details
```

**문제점**:
- `len(cfgattr)`: null 필드에서 에러 발생 ("Error in 'eval' command")
- `\n`: Slack에서 줄바꿈이 제대로 표시되지 않음

**해결**:
- `len()` 제거 → `case()` + `substr()` 사용
- `\n` 제거 → ` | ` 구분자로 변경 (한 줄 포맷)

---

### 2. Alert 2 - Critical Event Alert (Line 60)

**❌ 이전**:
```spl
| eval alert_message = "🚨 FortiGate CRITICAL Event\nDevice: " + device + "\nLogID: " + log_id + "\nDescription: " + description
```

**✅ 수정 후**:
```spl
| eval alert_message = "🚨 FortiGate CRITICAL Event - Device: " + device + " | LogID: " + log_id + " | Description: " + description
```

**변경 사항**: `\n` → ` | ` (Slack 가독성 개선)

---

### 3. Alert 3 - HA Event Alert (Line 98)

**❌ 이전**:
```spl
| eval alert_message = icon + " FortiGate HA Event\nDevice: " + device + "\nSeverity: " + severity + "\nLogID: " + log_id + "\nDescription: " + description
```

**✅ 수정 후**:
```spl
| eval alert_message = icon + " FortiGate HA Event - Device: " + device + " | Severity: " + severity + " | LogID: " + log_id + " | Description: " + description
```

**변경 사항**: `\n` → ` | ` (Slack 가독성 개선)

---

## 📊 Slack 출력 예시 비교

### 이전 (여러 줄, 줄바꿈 안됨)
```
🔥 FortiGate Config Change\nDevice: FGT-01\nAdmin: admin (CLI)\nAction: Modified\nPath: firewall.policy[10]\nObject: policy_10\nDetails: srcaddr=all
```

### 수정 후 (한 줄, 구분자로 깔끔하게)
```
🔥 FortiGate Config Change - Device: FGT-01 | Admin: admin (CLI) | Action: Modified | Path: firewall.policy[10] | Object: policy_10 | Details: srcaddr=all dstaddr=all service=HTTP
```

---

## ✅ 검증 방법

### 1. Syntax 검증
```bash
# Splunk에서 검색 실행 (에러 없이 실행되어야 함)
index=fw earliest=-1h (logid=0100044546 OR logid=0100044547)
| head 5
| eval details = case(isnull(cfgattr), "No details", 1=1, substr(cfgattr, 1, 100))
| table cfgattr, details
```

**기대 결과**:
- ✅ 에러 없이 실행
- ✅ cfgattr가 null이면 "No details" 표시
- ✅ cfgattr가 있으면 앞 100자만 표시

### 2. Slack 메시지 테스트
```bash
# 테스트 쿼리 실행 (test-queries/02-test-eval-fixed.spl)
index=fw earliest=-24h type=event subtype=system (logid=0100044546 OR logid=0100044547)
| head 1
| eval details = case(isnull(cfgattr), "No details", 1=1, substr(cfgattr, 1, 100))
| eval alert_message = "🔥 FortiGate Config Change - Device: " + devname + " | Details: " + details
| table alert_message
```

**기대 결과**:
- ✅ alert_message가 완전한 한 줄 문자열로 생성됨
- ✅ `\n` 없이 ` | ` 구분자 사용

---

## 🚀 배포 방법

### Option 1: Splunk Web UI (권장)

```bash
# 1. Splunk 로그인
https://splunk.jclee.me

# 2. Settings → Searches, reports, and alerts

# 3. 기존 Alert 편집:
# - FortiGate_Config_Change_Alert
# - FortiGate_Critical_Event_Alert
# - FortiGate_HA_Event_Alert

# 4. Search 쿼리를 파일의 내용으로 교체

# 5. Save
```

### Option 2: 파일 복사 (CLI)

```bash
# 백업 생성
cp /opt/splunk/etc/apps/search/local/savedsearches.conf \
   /opt/splunk/etc/apps/search/local/savedsearches.conf.backup

# 파일 복사
cp configs/savedsearches-fortigate-alerts.conf \
   /opt/splunk/etc/apps/search/local/savedsearches.conf

# Splunk 재시작
/opt/splunk/bin/splunk restart
```

### Option 3: REST API

```bash
# Alert 업데이트 (각 Alert별로 실행)
curl -k -u admin:password \
  -d 'search=index=fw earliest=rt-30s...' \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/saved/searches/FortiGate_Config_Change_Alert
```

---

## 📋 배포 전 체크리스트

- [ ] 백업 파일 생성 완료
- [ ] Test query로 검증 (`test-queries/02-test-eval-fixed.spl`)
- [ ] Slack 채널에 Bot 초대 완료 (`/invite @splunk-alert-bot`)
- [ ] Slack Bot OAuth 권한 확인 (`chat:write`, `channels:read`)
- [ ] 설정 파일 syntax 검증 (파싱 에러 없음)
- [ ] Alert 개별 테스트 (각 Alert별로 수동 trigger)
- [ ] Suppression 설정 확인 (중복 알림 방지)

---

## 🔍 트러블슈팅

### 여전히 "Error in 'eval' command" 발생

**확인**:
```spl
# 쿼리가 정확히 복사되었는지 확인
| eval details = case(isnull(cfgattr), "No details", 1=1, substr(cfgattr, 1, 100))
```

**일반적인 실수**:
- ❌ `len(cfgattr)` 여전히 사용
- ❌ `if()` 대신 `case()` 미사용
- ❌ `substr()` 파라미터 잘못됨 (예: `substr(cfgattr, 0, 100)` → 1-based index 사용)

### Slack에 여전히 `\n` 표시됨

**확인**:
```spl
# alert_message에 \n이 없는지 확인
| eval alert_message = "... - Device: " + device + " | Admin: " + admin
```

**일반적인 실수**:
- ❌ 줄바꿈 문자(`\n`) 여전히 사용
- ❌ ` | ` 구분자 누락

---

## 📚 관련 파일

| 파일 | 설명 |
|------|------|
| `configs/savedsearches-fortigate-alerts.conf` | ✅ **메인 파일 (수정됨)** |
| `configs/savedsearches-fortigate-alerts-fixed.conf` | 이전 수정 버전 (참고용) |
| `configs/EVAL_FIX_COMPARISON.md` | Before/After 비교 상세 가이드 |
| `test-queries/02-test-eval-fixed.spl` | eval 수정 테스트 쿼리 |
| `test-queries/03-full-config-alert-query.spl` | 완전한 Alert 쿼리 (배포용) |
| `ALERT_FORMATTING_GUIDE.md` | Alert 설정 완전 가이드 |

---

**수정 완료**: 2025-10-29
**테스트 상태**: ✅ Ready for deployment
**다음 단계**: Splunk Web UI에서 Alert 업데이트 후 테스트
