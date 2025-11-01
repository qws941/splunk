# 📊 FortiGate 7.4.5 대시보드 수정 내역

> **실제 FortiGate 로그 구조 기반**으로 수정 완료

---

## ✅ 수정 완료 (v2)

**파일**: `configs/dashboards/fmg-all-changes-v2.xml`

### 🔍 실제 FortiGate 7.4 로그 구조 확인

FortiGate 7.4.5 실제 로그 예시:
```
logid=0100044546 type=event subtype=system level=information vd=root
logdesc="Attribute configured" user="admin" ui="ssh(192.168.82.80)"
action=Edit cfgtid=1911423018 cfgpath="log.memory.filter"
cfgattr="filter[logid(0103020301)->]filter-type[exclude->include]"
msg="Edit log.memory.filter"
```

**확인된 필드**:
- `type=event` - 이벤트 로그
- `subtype=system` - 시스템 서브타입
- `logid=0100044546` - 설정 속성 변경
- `logid=0100044547` - 설정 객체 변경
- `cfgpath` - 설정 경로 (firewall.policy, firewall.address 등)
- `user` - 관리자 사용자명
- `action` - 작업 (Add/Edit/Delete)
- `logdesc` - 로그 설명
- `msg` - 메시지

---

## 🔄 주요 변경사항

### 1. 검색 쿼리 수정 (가장 중요)

| 항목 | 이전 (v1) | 수정 (v2) |
|------|-----------|----------|
| **Base Search** | `(cfgpath=* OR config OR policy)` | `type=event subtype=system (logid=0100044546 OR logid=0100044547 OR cfgpath=*)` |
| **Log Type** | 지정 안 함 | ✅ `type=event subtype=system` 추가 |
| **Log ID** | 사용 안 함 | ✅ `logid=0100044546 OR logid=0100044547` 추가 |
| **Regex Escape** | `match(cfgpath, "firewall.policy")` | ✅ `match(cfgpath, "firewall\.policy")` (점 이스케이프) |

### 2. 필드 우선순위 수정

**설명 필드**:
```spl
# 이전 (v1)
eval 설명 = coalesce(msg, logdesc, cfgpath, "Configuration change")

# 수정 (v2)
eval 설명 = coalesce(logdesc, msg, cfgpath, "Configuration change")
```
→ FortiGate 7.4에서는 `logdesc="Attribute configured"` 형태로 나오므로 logdesc 우선

### 3. 새로운 카테고리 추가

```spl
| eval 변경유형 = case(
    match(cfgpath, "firewall\.policy"), "정책",
    match(cfgpath, "firewall\.address"), "주소객체",
    match(cfgpath, "firewall\.service"), "서비스객체",
    match(cfgpath, "system\.") OR match(cfgpath, "log\."), "시스템설정",  ⭐ 신규
    isnotnull(cfgpath), "기타설정",
    1=1, "설정변경")
```

**색상 추가**:
- 시스템설정: 보라색 (#A569BD)

### 4. 새로운 패널 추가 (Row 4)

**작업 유형별 분석**:
- ⚙️ 작업 유형 (Add/Edit/Delete) - 막대 차트
- 👥 관리자별 변경 현황 - 파이 차트 (상위 10명)

### 5. 테이블 컬럼 추가

```
시간, 장비, 관리자, 변경유형, 작업, 설명, cfgpath, logid, _raw
```
→ `logid` 컬럼 추가 (어떤 로그 타입인지 확인용)

---

## 📊 대시보드 구성 (v2)

### Row 1: 요약 통계 (3개 패널)
- 📝 전체 설정 변경 (count)
- 👤 관리자 수 (distinct users)
- 🖥️ 장비 수 (distinct devices)

### Row 2: 통합 테이블 (1개 패널)
- 📋 전체 변경 내역
  - Policy + Address + Service + System 모두 통합
  - 최근 100개 이벤트
  - 색상 코딩 (유형별, 작업별)

### Row 3: 타임라인 (2개 패널)
- 📊 시간별 변경 추이 (막대 차트, 1시간 단위)
- 📊 유형별 변경 통계 (파이 차트)

### Row 4: 작업 분석 (2개 패널) ⭐ 신규
- ⚙️ 작업 유형 (Add/Edit/Delete 막대 차트)
- 👥 관리자별 변경 현황 (파이 차트, Top 10)

---

## 🔧 FortiGate 7.4 특화 수정사항

### 1. Event System 로그 필터링
```spl
type=event subtype=system
```
→ FortiGate 설정 변경 로그는 모두 `type=event subtype=system`

### 2. LogID 기반 검색
```spl
logid=0100044546  # 설정 속성 변경
logid=0100044547  # 설정 객체 변경
```
→ 더 정확한 설정 변경 로그 캡처

### 3. 정규식 점(.) 이스케이프
```spl
# ❌ 이전 (잘못된 정규식)
match(cfgpath, "firewall.policy")  # .은 모든 문자 매칭

# ✅ 수정 (올바른 정규식)
match(cfgpath, "firewall\.policy")  # 리터럴 점만 매칭
```
→ `firewall.policy`는 매칭, `firewallXpolicy`는 제외

---

## 📁 파일 비교

| 파일 | 용도 | 상태 |
|------|------|------|
| `fmg-all-changes-simple.xml` | v1 - 추정 기반 | 참고용 |
| `fmg-all-changes-v2.xml` | **v2 - 실제 로그 구조 기반** | ✅ **배포 권장** |

---

## 🚀 배포 방법

### Splunk Web UI에서 배포

1. Splunk 접속: `https://splunk.jclee.me:8000`
2. **Settings** → **User Interface** → **Views** → **New from XML**
3. `configs/dashboards/fmg-all-changes-v2.xml` 내용 붙여넣기
4. **View Name**: `fmg_all_changes_v2`
5. **Save** 클릭
6. 접속: `https://splunk.jclee.me:8000/app/search/fmg_all_changes_v2`

---

## ✅ 검증 완료

```bash
✅ XML 문법 검증 완료
✅ FortiGate 7.4 실제 로그 구조 반영
✅ type=event subtype=system 필터 추가
✅ logid=0100044546/0100044547 사용
✅ 정규식 이스케이프 수정
✅ 새로운 분석 패널 추가 (작업 유형, 관리자별)
```

---

## 🔍 테스트 쿼리 (배포 전 확인)

```spl
# 1. Event System 로그 확인
index=fw earliest=-1h type=event subtype=system
| head 10
| table _time, devname, type, subtype, logid, cfgpath, user, action

# 2. 설정 변경 로그만 (LogID 사용)
index=fw earliest=-1h type=event subtype=system (logid=0100044546 OR logid=0100044547)
| head 20
| table _time, devname, logid, cfgpath, user, action, logdesc, msg

# 3. cfgpath 필드 확인
index=fw earliest=-1h type=event subtype=system cfgpath=*
| stats count by cfgpath
| sort -count
```

---

**버전**: v2.0
**날짜**: 2025-10-28
**기반**: FortiGate 7.4.5 실제 로그 구조
**메인 파일**: `fmg-all-changes-v2.xml`
**변경 사항**: LogID 기반 검색, Event System 필터, 정규식 수정, 새 패널 추가
