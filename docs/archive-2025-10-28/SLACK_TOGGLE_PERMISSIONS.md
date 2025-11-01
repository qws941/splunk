# Slack Toggle 버튼 필수 권한 가이드

**대상 기능**: FortiGate Alert Control 대시보드의 ON/OFF 토글 버튼

**Splunk 버전**: 9.x (9.3.1 확인됨)

---

## 🔑 필수 권한 (Capabilities)

Slack toggle 버튼이 작동하려면 **최소 2개의 capability**가 필요합니다:

### 1. `list_saved_searches` ⭐ 필수
```
설명: Saved search 목록을 조회할 수 있는 권한
용도:
  - REST API GET /services/saved/searches 호출
  - Alert 존재 여부 확인
  - 현재 상태(enabled/disabled) 조회
```

### 2. `edit_search` ⭐ 필수
```
설명: Saved search를 수정할 수 있는 권한
용도:
  - REST API POST /services/saved/searches/{name} 호출
  - disabled 속성 변경 (0=ON, 1=OFF)
  - 토글 버튼의 핵심 기능
```

### 3. `schedule_search` (권장)
```
설명: Search 스케줄을 관리할 수 있는 권한
용도:
  - realtime_schedule 속성 변경
  - cron_schedule 수정
  - 토글 버튼 외 추가 기능 사용 시 필요
```

---

## 📊 권한 확인 방법

### 방법 1: Splunk Web UI (간편) ⭐ 추천

```
1. Splunk Web 로그인
2. Settings → Access controls → Roles
3. 현재 사용자의 Role 클릭 (예: user, power, admin)
4. Capabilities 섹션 확인:

   ✅ 필수 확인:
   - [ ] list_saved_searches
   - [ ] edit_search

   ✅ 권장 확인:
   - [ ] schedule_search
```

### 방법 2: SPL 쿼리 (자동 진단) ⭐ 추천

**복사해서 Splunk Search에 붙여넣기**:

```spl
| rest /services/authentication/current-context
| eval current_user=username
| eval current_roles=roles
| fields current_user, current_roles
| mvexpand current_roles
| join type=left current_roles
    [| rest /services/authorization/roles
     | eval current_roles=title
     | fields current_roles, capabilities, imported_capabilities]
| eval all_caps=mvappend(capabilities, imported_capabilities)
| eval has_list_saved_searches=if(mvfind(all_caps, "list_saved_searches")>=0, "✅ 있음", "❌ 없음")
| eval has_edit_search=if(mvfind(all_caps, "edit_search")>=0, "✅ 있음", "❌ 없음")
| eval has_schedule_search=if(mvfind(all_caps, "schedule_search")>=0, "✅ 있음", "❌ 없음")
| stats
    values(current_user) as "사용자",
    values(current_roles) as "Role",
    first(has_list_saved_searches) as "list_saved_searches (필수)",
    first(has_edit_search) as "edit_search (필수)",
    first(has_schedule_search) as "schedule_search (권장)"
```

**예상 결과**:
```
사용자          Role      list_saved_searches  edit_search  schedule_search
secmon         power     ✅ 있음              ✅ 있음       ✅ 있음
test_user      user      ❌ 없음              ❌ 없음       ❌ 없음
admin          admin     ✅ 있음              ✅ 있음       ✅ 있음
```

### 방법 3: REST API (터미널)

```bash
# 1. 현재 사용자 확인
curl -k -u admin:password \
  "http://172.28.32.67:8089/services/authentication/current-context" \
  | grep -oP '<s:key name="username">.*?</s:key>'

# 2. Role의 capabilities 확인
curl -k -u admin:password \
  "http://172.28.32.67:8089/services/authorization/roles/power" \
  | grep -oP '<s:key name="capabilities">.*?</s:key>'

# 3. 필수 권한 체크 (grep으로 필터)
curl -k -u admin:password \
  "http://172.28.32.67:8089/services/authorization/roles/power" \
  | grep -E "list_saved_searches|edit_search|schedule_search"
```

---

## 🛠️ 권한 부족 시 해결 방법

### 상황 1: 일반 사용자 (user role)

**증상**: `❌ 없음` × 2개 이상

**해결**:
```
1. Splunk 관리자에게 요청:
   "Slack alert 제어를 위해 power role로 변경 요청합니다"

2. 또는 capabilities 추가 요청:
   - list_saved_searches
   - edit_search
```

**관리자 작업** (Settings → Access controls → Roles → user):
```
Capabilities 섹션에서 추가:
✅ list_saved_searches
✅ edit_search
✅ schedule_search (선택)

저장 → 사용자 재로그인
```

### 상황 2: Power 사용자 (power role)

**일반적으로 power role은 모든 필수 권한을 가지고 있습니다.**

확인:
```spl
| rest /services/authorization/roles
| search title="power"
| table title, capabilities, imported_capabilities
| eval has_required=if(
    like(capabilities, "%list_saved_searches%") AND
    like(capabilities, "%edit_search%"),
    "✅ 정상", "❌ 권한 부족")
```

### 상황 3: 관리자 (admin role)

**admin role은 모든 권한을 가지고 있습니다.**

만약 문제가 발생하면:
- Splunk 재시작 필요
- Role 설정 corruption 가능성
- `btool` 명령으로 확인:
  ```bash
  /opt/splunk/bin/splunk btool authorize list --debug
  ```

---

## 🎯 Role별 권한 매트릭스

| Role | list_saved_searches | edit_search | schedule_search | Toggle 가능? |
|------|---------------------|-------------|-----------------|--------------|
| **admin** | ✅ | ✅ | ✅ | ✅ 완전 가능 |
| **power** | ✅ | ✅ | ✅ | ✅ 완전 가능 |
| **user** | ❌ (기본값) | ❌ (기본값) | ❌ | ❌ 불가능 |
| **can_delete** | ✅ | ✅ | ✅ | ✅ 완전 가능 |

**참고**: 기본 Splunk roles 기준이며, 커스텀 role은 다를 수 있습니다.

---

## 🔍 권한 테스트 (실제 API 호출)

### 테스트 1: Saved Search 조회 권한

```bash
# list_saved_searches 권한 테스트
curl -k -u secmon:password \
  "http://172.28.32.67:8089/services/saved/searches/FortiGate_Critical_Event_Alert"

# 성공: <entry> XML 반환
# 실패: 403 Forbidden 또는 404 Not Found
```

### 테스트 2: Saved Search 수정 권한

```bash
# edit_search 권한 테스트 (disabled 변경)
curl -k -u secmon:password \
  -d "disabled=0" \
  "http://172.28.32.67:8089/servicesNS/nobody/search/saved/searches/FortiGate_Critical_Event_Alert"

# 성공: <entry> XML 반환 + disabled=0
# 실패: 403 Forbidden
```

### 테스트 3: 브라우저 콘솔에서 직접 테스트

```javascript
// F12 → Console
var service = mvc.createService();

// 1. 조회 테스트 (list_saved_searches)
service.get('/services/saved/searches/FortiGate_Critical_Event_Alert', {}, function(err, response) {
  if (err) {
    console.error('❌ 조회 권한 없음:', err.status, err.data);
  } else {
    console.log('✅ 조회 권한 있음');
  }
});

// 2. 수정 테스트 (edit_search)
service.post('/services/saved/searches/FortiGate_Critical_Event_Alert',
  { disabled: 0 },
  function(err, response) {
    if (err) {
      console.error('❌ 수정 권한 없음:', err.status, err.data);
    } else {
      console.log('✅ 수정 권한 있음');
    }
  }
);
```

---

## 📋 권한 문제 진단 플로우차트

```
권한 확인 시작
    ↓
[SPL 쿼리 실행]
    ↓
┌────────────────────────────────┐
│ list_saved_searches 있음?      │
└────────────────────────────────┘
         │ NO                YES │
         ↓                       ↓
    ❌ user role          ┌──────────────────┐
    → power로 변경 요청   │ edit_search 있음?│
                          └──────────────────┘
                               │ NO    YES │
                               ↓           ↓
                          권한 추가 요청   ✅ Toggle 가능!
                          (관리자)
```

---

## 🚀 빠른 권한 체크 (30초)

**복사해서 Splunk Search에 붙여넣기**:

```spl
| rest /services/authentication/current-context
| eval user=username, role=mvindex(roles,0)
| append [| rest /services/authorization/roles | search title="*" | eval role=title]
| stats first(user) as user by role
| join role [| rest /services/authorization/roles
    | eval role=title
    | eval has_list=if(like(capabilities, "%list_saved_searches%"), 1, 0)
    | eval has_edit=if(like(capabilities, "%edit_search%"), 1, 0)
    | eval can_toggle=if(has_list=1 AND has_edit=1, "✅ 가능", "❌ 불가능")
    | table role, can_toggle]
| where isnotnull(user)
| table user, role, can_toggle
```

**예상 결과**:
```
user      role     can_toggle
secmon    power    ✅ 가능
admin     admin    ✅ 가능
guest     user     ❌ 불가능
```

---

## 📞 관리자에게 권한 요청 시 메시지 템플릿

```
제목: Splunk Slack Alert Toggle 기능을 위한 권한 요청

안녕하세요,

FortiGate Alert Control 대시보드에서 Slack alert를 ON/OFF 제어하기 위해
다음 권한이 필요합니다:

현재 사용자: [사용자명]
현재 Role: [user/power/custom]

필요 Capabilities:
1. list_saved_searches - Saved search 조회
2. edit_search - Saved search 수정 (ON/OFF 토글)

요청 사항:
- Power role로 변경
- 또는 위 2개 capabilities를 현재 role에 추가

감사합니다.
```

---

## 🔐 보안 고려사항

### 최소 권한 원칙 (Principle of Least Privilege)

**권장 방식**:
```
일반 사용자 → Custom Role 생성:
- list_saved_searches (읽기 전용)
- edit_search (특정 saved search만)

관리자 → admin role 유지
```

**Custom Role 생성 예시**:
```
Settings → Access controls → Roles → New Role

Name: alert_operator
Inherits from: user
Additional capabilities:
  ✅ list_saved_searches
  ✅ edit_search

Restrictions:
  - Can only edit searches in "security" app
  - Cannot delete searches
```

---

**작성일**: 2025-10-28
**Splunk 버전**: 9.x (9.3.1 테스트됨)
**필수 Capabilities**: `list_saved_searches`, `edit_search`
**권장 Role**: power 이상
