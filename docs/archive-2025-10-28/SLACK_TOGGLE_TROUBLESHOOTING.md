# Slack Alert Toggle 버튼 트러블슈팅 가이드

**문제**: FortiGate Alert Control 대시보드의 ON/OFF 버튼이 작동하지 않음

**대시보드**: `configs/dashboards/fortigate-alert-control.xml`

---

## 🔍 진단 단계별 체크리스트

### 1단계: 대시보드 로딩 환경 확인 (가장 중요!) ⭐

**문제 증상**:
- 버튼 클릭 시 아무 반응 없음
- 브라우저 콘솔에 에러도 없음
- alert() 팝업도 뜨지 않음

**원인**: XML 파일을 직접 열거나 로컬 환경에서 보고 있음

**확인 방법**:
```
브라우저 주소창 확인:
✅ 정상: https://splunk.jclee.me:8000/ko-KR/app/nextrade/fortigate_alert_control
✅ 정상: http://172.28.32.67:8000/ko-KR/app/nextrade/fortigate_alert_control
❌ 오류: file:///home/jclee/app/splunk/configs/dashboards/fortigate-alert-control.xml
❌ 오류: http://localhost:3000/fortigate-alert-control.xml
```

**해결 방법**:
1. Splunk Web UI로 이동
2. Dashboards 메뉴 클릭
3. "FortiGate Alert Control" 선택
4. 주소창에 Splunk 서버 URL 확인

**중요**: JavaScript는 Splunk Web UI 컨텍스트에서만 작동합니다!

---

### 2단계: JavaScript 로딩 확인

**브라우저 콘솔 열기** (F12 키 또는 우클릭 → 검사):

```javascript
// 1. 대시보드 로딩 메시지 확인
// 콘솔에 다음 메시지가 보여야 함:
[Dashboard] FortiGate Alert Control loaded - toggleAlert() ready

// 2. 함수 존재 확인
typeof window.toggleAlert
// 예상 출력: "function"

// 3. 수동으로 함수 실행 테스트
window.toggleAlert('FortiGate_Critical_Event_Alert', 0)
// 예상: alert() 팝업 또는 에러 메시지
```

**결과별 진단**:

| 결과 | 원인 | 해결 방법 |
|------|------|-----------|
| `undefined` | JavaScript 로드 실패 | Splunk 9.x 버전 확인, 대시보드 재로드 |
| `function` | 함수는 정상 | 3단계로 이동 (권한 확인) |
| 에러 발생 | 코드 오류 | 콘솔 에러 메시지 확인 → 5단계 |

---

### 3단계: Splunk 권한 확인

**확인 SPL**:
```spl
| rest /services/authorization/roles
| search title="현재_사용자_role"
| table title, imported_capabilities, capabilities
| where like(capabilities, "%searches%")
```

**필요 권한**:
- `edit_search` - saved search 수정 권한
- `write` - REST API POST 권한
- `list_saved_searches` - saved search 목록 조회

**권한 테스트** (브라우저 콘솔):
```javascript
// 수동 REST API 호출 테스트
var service = mvc.createService();
service.get('/services/saved/searches/FortiGate_Critical_Event_Alert', {}, function(err, response) {
  if (err) {
    console.error('❌ 권한 에러:', err);
  } else {
    console.log('✅ 권한 정상:', response);
  }
});
```

**권한 부족 시 해결**:
```bash
# Splunk 관리자에게 요청:
# Settings → Access controls → Roles → [사용자 Role] → Capabilities
# - edit_search: 체크
# - list_saved_searches: 체크
```

---

### 4단계: Saved Search 존재 확인

**확인 SPL**:
```spl
| rest /services/saved/searches
| search title="FortiGate_*"
| table title, disabled, realtime_schedule, eai:acl.sharing
```

**예상 결과**:
```
title                              disabled  realtime_schedule  eai:acl.sharing
FortiGate_Critical_Event_Alert     0         1                  app
FortiGate_Config_Change_Alert      0         1                  app
FortiGate_HA_Event_Alert           0         1                  app
```

**Saved Search가 없는 경우**:
```bash
# 1. savedsearches-fortigate-alerts.conf 배포 확인
ls -l /opt/splunk/etc/apps/nextrade/local/savedsearches.conf

# 2. Splunk 재시작 (conf 적용)
sudo systemctl restart splunk

# 3. 다시 확인
| rest /services/saved/searches | search title="FortiGate_*" | stats count
# 예상: count = 3
```

---

### 5단계: 네트워크 요청 확인 (고급)

**브라우저 Network 탭 열기** (F12 → Network):

1. 버튼 클릭 (예: "🟢 ON" 버튼)
2. Network 탭에서 `saved/searches` 요청 확인

**정상적인 요청**:
```
POST /servicesNS/nobody/search/saved/searches/FortiGate_Critical_Event_Alert
Status: 200 OK
Response: <entry>...</entry>
```

**에러별 진단**:

| Status Code | 원인 | 해결 방법 |
|-------------|------|-----------|
| 404 Not Found | Saved search 없음 | 4단계 참조 (conf 배포) |
| 403 Forbidden | 권한 부족 | 3단계 참조 (권한 확인) |
| 500 Internal Server Error | Splunk 서버 에러 | Splunk 로그 확인 (`splunkd.log`) |
| No request sent | JavaScript 실행 안 됨 | 2단계 참조 (함수 확인) |

---

## 🛠️ 원인별 해결 방법

### 원인 1: 로컬 XML 파일을 직접 열었음 (50% 확률)

**증상**:
- 주소창에 `file:///` 또는 `localhost:3000`
- 아무 에러 없이 버튼만 클릭되지 않음

**해결**:
```bash
# 대시보드 Splunk Web에 배포
cd /home/jclee/app/splunk/configs

# PowerShell 배포 (Windows)
.\Deploy-SplunkDashboards.ps1 -SplunkHost "172.28.32.67" -SplunkPass "password"

# 또는 Splunk Web UI로 수동 배포:
# 1. Splunk → Dashboards → Create New Dashboard → Classic
# 2. Source 탭 → XML 붙여넣기 → Save
```

---

### 원인 2: Splunk 구버전 (mvc.createService() 미지원) (30% 확률)

**확인**:
```spl
| rest /services/server/info
| table version
```

**해결**:
- Splunk 9.x 이상 필요
- 구버전(8.x)인 경우 REST API 스크립트 사용:

```bash
# 대체 방법: REST API 직접 호출
cd /home/jclee/app/splunk/scripts
chmod +x slack-alert-api-control.sh

# Alert ON
./slack-alert-api-control.sh enable FortiGate_Critical_Event_Alert

# Alert OFF
./slack-alert-api-control.sh disable FortiGate_Critical_Event_Alert
```

---

### 원인 3: 사용자 권한 부족 (15% 확률)

**확인**:
```spl
| rest /services/authentication/current-context
| table username, roles
```

**해결**:
```
Splunk 관리자에게 요청:
Settings → Access controls → Roles → [User Role] → Edit
Capabilities 섹션:
- ✅ edit_search
- ✅ list_saved_searches
```

---

### 원인 4: Saved Search가 다른 App에 배포됨 (5% 확률)

**확인**:
```spl
| rest /services/saved/searches
| search title="FortiGate_Critical_Event_Alert"
| table title, eai:acl.app, eai:acl.owner, eai:acl.sharing
```

**해결**:
```javascript
// 대시보드 JavaScript 수정 (LINE 21)
// 변경 전:
'/servicesNS/nobody/search/saved/searches/' + encodeURIComponent(alertName)

// 변경 후 (app 명시):
'/servicesNS/nobody/nextrade/saved/searches/' + encodeURIComponent(alertName)
```

---

## 🔬 고급 진단 (에러 없이 작동 안 함)

### Splunk REST API 직접 테스트

```bash
# 1. Saved search 조회 (권한 확인)
curl -k -u admin:password \
  "https://172.28.32.67:8089/servicesNS/nobody/search/saved/searches/FortiGate_Critical_Event_Alert"

# 2. Saved search 수정 (토글 시뮬레이션)
curl -k -u admin:password \
  -d "disabled=0" \
  "https://172.28.32.67:8089/servicesNS/nobody/search/saved/searches/FortiGate_Critical_Event_Alert"

# 3. 상태 확인
curl -k -u admin:password \
  "https://172.28.32.67:8089/servicesNS/nobody/search/saved/searches/FortiGate_Critical_Event_Alert" \
  | grep -oP '(?<=<s:key name="disabled">)[01](?=</s:key>)'
```

**성공 시**: 대시보드 문제 (JavaScript)
**실패 시**: Splunk 서버 문제 (권한 또는 saved search)

---

## 📋 빠른 체크리스트 (5분 진단)

```
[ ] 1. Splunk Web UI에서 대시보드 열림 (file:/// 아님)
[ ] 2. F12 콘솔: "toggleAlert() ready" 메시지 보임
[ ] 3. typeof window.toggleAlert = "function"
[ ] 4. | rest /services/saved/searches | search title="FortiGate_*" | stats count = 3
[ ] 5. 현재 사용자 role에 edit_search 권한 있음
```

**5개 모두 체크**: 5단계 Network 탭 확인
**1번 체크 안 됨**: Splunk Web에 대시보드 배포 필요
**2-3번 체크 안 됨**: Splunk 버전 확인 (9.x 필요)
**4번 체크 안 됨**: savedsearches.conf 배포 필요
**5번 체크 안 됨**: 관리자에게 권한 요청

---

## 🚀 추천 해결 순서

### 대부분의 경우 (80%):

```bash
# 1. Splunk Web에 대시보드 배포 확인
# URL이 file:/// 또는 localhost가 아닌지 확인

# 2. 브라우저 콘솔 확인 (F12)
# typeof window.toggleAlert = "function" 확인

# 3. 문제 지속 시 REST API 대체 사용
cd /home/jclee/app/splunk/scripts
./slack-alert-api-control.sh enable FortiGate_Critical_Event_Alert
```

---

## 📞 지원 요청 시 포함할 정보

```
1. Splunk 버전: | rest /services/server/info | table version
2. 현재 URL: (브라우저 주소창 전체 복사)
3. 브라우저 콘솔 출력: (F12 → Console 탭 스크린샷)
4. Network 탭: (F12 → Network → 버튼 클릭 후 스크린샷)
5. Saved search 확인: | rest /services/saved/searches | search title="FortiGate_*"
```

---

**작성일**: 2025-10-28
**대상 대시보드**: `fortigate-alert-control.xml`
**Splunk 버전**: 9.x 권장
**JavaScript 패턴**: `mvc.createService()` (Splunk 9.x+ 전용)
