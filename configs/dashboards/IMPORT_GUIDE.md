# Splunk Dashboard Studio JSON 임포트 가이드

## ⚠️ 중요: Dashboard Studio vs Classic Dashboard

- **Dashboard Studio** (JSON) ← 이걸 선택해야 함!
- **Classic Dashboard** (XML) ← 이건 JSON 안 됨

---

## 📝 단계별 임포트 방법

### 1. Splunk Web UI 접속
```
https://localhost:8000
```

### 2. 대시보드 생성 시작
```
좌측 메뉴 → Dashboards → "Create New Dashboard" 버튼 클릭
```

### 3. **Dashboard Studio 선택** ⚠️ 중요!
```
팝업에서 "Dashboard Studio" 선택
"Classic Dashboard" 절대 선택 금지!
```

### 4. 기본 정보 입력
```
Title: FortiGate Operations (예시)
Description: (선택사항)
Permissions: Private 또는 Shared
```

### 5. Source 편집 모드
```
우측 상단 "< >" (Source) 버튼 클릭
→ 빈 JSON 템플릿이 나타남
```

### 6. JSON 전체 교체
```
기존 JSON 전체 삭제 (Ctrl+A → Delete)
↓
파일 내용 붙여넣기 (Ctrl+V)
```

### 7. 저장
```
우측 상단 "Save" 버튼 클릭
```

---

## 🚫 자주 하는 실수

### 실수 1: Classic Dashboard 선택
```
❌ Classic Dashboard → Source 편집 → JSON 붙여넣기
→ 오류: "Invalid XML format"
```

### 실수 2: 기존 JSON에 추가
```
❌ 기존 JSON에 일부만 수정/추가
✅ 전체를 교체해야 함
```

### 실수 3: 데이터가 없음
```
대시보드는 생성됐지만 "No results found"
→ index=fw 에 데이터가 없음
→ 확인: Search → index=fw earliest=-1h | stats count
```

---

## 🔍 문제 해결

### 증상 1: "Invalid JSON" 오류
```bash
# 로컬에서 JSON 검증
jq empty 01-fortigate-operations.json
```

### 증상 2: 대시보드는 보이지만 데이터 없음
```spl
# Splunk Search 앱에서 실행
index=fw earliest=-1h | stats count

# 결과가 0이면 → Syslog 데이터 수신 안 됨
# inputs.conf 확인 필요
```

### 증상 3: "You don't have permission"
```
Settings → Access controls → Roles
→ 해당 대시보드 권한 확인
```

---

## 📋 3개 파일 위치

```
/home/jclee/app/splunk/configs/dashboards/studio-production/01-fortigate-operations.json
/home/jclee/app/splunk/configs/dashboards/studio-production/02-fmg-operations.json
/home/jclee/app/splunk/configs/dashboards/studio-production/03-slack-alert-control.json
```

---

## 🚀 REST API로 직접 생성 (대안)

```bash
# Dashboard 01
curl -k -u admin:password \
  -X POST \
  "https://localhost:8089/servicesNS/nobody/search/data/ui/views" \
  --data-urlencode "name=fortigate_operations" \
  --data-urlencode "eai:type=views" \
  --data-urlencode "eai:data=$(cat 01-fortigate-operations.json)"

# Dashboard 02
curl -k -u admin:password \
  -X POST \
  "https://localhost:8089/servicesNS/nobody/search/data/ui/views" \
  --data-urlencode "name=fmg_operations" \
  --data-urlencode "eai:type=views" \
  --data-urlencode "eai:data=$(cat 02-fmg-operations.json)"

# Dashboard 03
curl -k -u admin:password \
  -X POST \
  "https://localhost:8089/servicesNS/nobody/search/data/ui/views" \
  --data-urlencode "name=slack_control" \
  --data-urlencode "eai:type=views" \
  --data-urlencode "eai:data=$(cat 03-slack-alert-control.json)"
```

---

**Version**: 1.0
**Last Updated**: 2025-10-27
