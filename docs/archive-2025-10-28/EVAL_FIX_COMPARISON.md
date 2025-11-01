# eval 명령어 에러 수정 비교

## 🔴 문제 발생 코드 (BEFORE)

```spl
| eval details = if(isnotnull(cfgattr) AND len(cfgattr) < 100, cfgattr, "...")
| eval alert_message = "🔥 FortiGate Config Change\nDevice: " + device + "\nAdmin: " + admin + " (" + access_method + ")\nAction: " + action_type + "\nPath: " + config_path + "\nObject: " + object_name + "\nDetails: " + details
```

**에러 원인**:
1. `len(cfgattr)` - cfgattr 필드가 없으면 함수 실행 불가
2. `AND` 조건에서 좌측이 true여도 우측 `len()` 평가 시 에러
3. `\n` (줄바꿈) - Splunk/Slack에서 제대로 렌더링 안 될 수 있음

---

## ✅ 수정된 코드 (AFTER)

```spl
| eval details = case(isnull(cfgattr), "No details", 1=1, substr(cfgattr, 1, 100))
| eval alert_message = "🔥 FortiGate Config Change - Device: " + device + " | Admin: " + admin + " (" + access_method + ") | Action: " + action_type + " | Path: " + config_path + " | Object: " + object_name + " | Details: " + details
```

**변경 사항**:
1. ✅ `len()` 제거 → `substr()` 사용 (첫 100자만 추출)
2. ✅ `case()` 함수로 null 처리 명확화
3. ✅ `\n` → ` | ` (파이프 구분자)

---

## 🧪 테스트 쿼리

### 1. 기본 필드 확인 (에러 없이 실행되는지 확인)

```spl
index=fw earliest=-1h type=event subtype=system
    (logid=0100044546 OR logid=0100044547)
| head 10
| table _time, devname, user, logid, cfgpath, cfgobj, cfgattr, action, ui
```

**확인 사항**:
- `cfgattr` 필드가 있는지?
- 값이 100자 이상인 경우가 있는지?
- null 값이 있는지?

### 2. 수정된 eval 명령어 테스트

```spl
index=fw earliest=-1h type=event subtype=system
    (logid=0100044546 OR logid=0100044547)
| head 5
| eval details = case(isnull(cfgattr), "No details", 1=1, substr(cfgattr, 1, 100))
| eval test_message = "Device: " + devname + " | Details: " + details
| table devname, cfgattr, details, test_message
```

**기대 결과**:
- cfgattr 있음 → details에 첫 100자
- cfgattr 없음 → details = "No details"
- 에러 없이 실행

### 3. 전체 쿼리 테스트 (Alert 쿼리 그대로)

```spl
index=fw earliest=-1h type=event subtype=system \
    (logid=0100044546 OR logid=0100044547) \
| dedup devname, user, cfgpath \
| eval device = devname \
| eval admin = coalesce(user, "system") \
| eval access_method = case(logid="0100044546", "CLI", logid="0100044547", "GUI", 1=1, coalesce(ui, "N/A")) \
| eval config_path = cfgpath \
| eval action_type = coalesce(action, "Modified") \
| eval object_name = coalesce(cfgobj, "-") \
| eval details = case(isnull(cfgattr), "No details", 1=1, substr(cfgattr, 1, 100)) \
| eval alert_message = "🔥 FortiGate Config Change - Device: " + device + " | Admin: " + admin + " (" + access_method + ") | Action: " + action_type + " | Path: " + config_path + " | Object: " + object_name + " | Details: " + details \
| table alert_message, device, admin, config_path
```

---

## 📝 배포 방법

### 1. Splunk Web UI 배포 (권장)

```bash
# 1. 파일 복사
cp configs/savedsearches-fortigate-alerts-fixed.conf \
   /opt/splunk/etc/apps/search/local/savedsearches.conf

# 2. Splunk 재시작
sudo systemctl restart splunk
```

**또는 Web UI에서**:
1. Settings → Searches, reports, and alerts
2. FortiGate_Config_Change_Alert 찾기
3. Edit → Search 수정
4. 위 쿼리 붙여넣기 → Save

### 2. 설정 파일 직접 수정

```bash
# 기존 파일 백업
cp configs/savedsearches-fortigate-alerts.conf \
   configs/savedsearches-fortigate-alerts.conf.backup

# 수정된 파일로 교체
cp configs/savedsearches-fortigate-alerts-fixed.conf \
   configs/savedsearches-fortigate-alerts.conf
```

---

## 🔍 에러 메시지별 해결 방법

### 에러 1: `The function 'len' is invalid`

**원인**: Splunk 버전이 `len()` 함수를 지원하지 않음

**해결**: `substr()` 사용
```spl
# ❌ len(cfgattr) < 100
# ✅ substr(cfgattr, 1, 100)
```

### 에러 2: `Field 'cfgattr' does not exist`

**원인**: 실제 로그에 cfgattr 필드가 없음

**해결**: `case()` 또는 `coalesce()`로 null 처리
```spl
| eval details = coalesce(cfgattr, "No details")
```

### 에러 3: `Error in 'eval' command: The expression is malformed`

**원인**: 문자열 연결에서 null 값

**해결**: 모든 필드를 `coalesce()`로 감싸기
```spl
| eval msg = coalesce(field1, "") + " | " + coalesce(field2, "")
```

---

## ✅ 검증 체크리스트

- [ ] 테스트 쿼리 1번 실행 → cfgattr 필드 존재 확인
- [ ] 테스트 쿼리 2번 실행 → eval 에러 없이 실행
- [ ] 테스트 쿼리 3번 실행 → alert_message 정상 생성
- [ ] Alert 저장 후 15분 대기 → Slack 알림 수신 확인
- [ ] Alert 상태 확인: `Settings → Searches, reports, and alerts → FortiGate_Config_Change_Alert → View recent alerts`

---

## 📊 예상 출력 (Slack)

**Before (줄바꿈 포함)**:
```
🔥 FortiGate Config Change
Device: FGT-01
Admin: admin (CLI)
Action: Modified
Path: firewall.policy[10]
Object: policy_10
Details: srcaddr=all dstaddr=all service=HTTP
```

**After (파이프 구분)**:
```
🔥 FortiGate Config Change - Device: FGT-01 | Admin: admin (CLI) | Action: Modified | Path: firewall.policy[10] | Object: policy_10 | Details: srcaddr=all dstaddr=all service=HTTP
```

**참고**: Slack에서는 파이프 구분자가 더 깔끔하게 보입니다.
