# 📊 FMG 대시보드 배포 가이드

## 최종 파일 (Splunk 9 + FortiGate 7.4.5)

### 1. 통합 대시보드 (권장)
**파일**: `configs/dashboards/fmg-all-changes-simple.xml`
**용도**: Policy + Address + Service 모든 변경사항 한 화면에 표시

**배포**:
```bash
# Splunk 서버에 복사
scp /home/jclee/app/splunk/configs/dashboards/fmg-all-changes-simple.xml \
  splunk:/opt/splunk/etc/apps/search/local/data/ui/views/

# Splunk 재시작 (필요시)
/opt/splunk/bin/splunk restart splunkweb

# 접속
https://your-splunk:8000/app/search/fmg_all_changes_simple
```

**또는 Splunk Web UI**:
1. Settings → User Interface → Views → New from XML
2. `fmg-all-changes-simple.xml` 내용 붙여넣기
3. View Name: `fmg_all_changes_simple`
4. Save

---

## 2. 데이터 확인 (문제 발생 시)

**파일**: `test-data-exists.spl`

**실행 순서**:
```spl
# 1단계: fw 인덱스에 데이터 있는지
index=fortianalyzer earliest=-24h | head 1 | table _time, _raw

# 2단계: cfgpath 필드 존재 확인
index=fortianalyzer earliest=-24h cfgpath=* | head 10 | table _time, devname, cfgpath, _raw

# 3단계: 설정 변경 로그 넓게 검색
index=fortianalyzer earliest=-24h (config OR policy OR address OR service)
| head 20 | table _time, devname, logdesc, msg, type, subtype, _raw

# 5단계: 모든 필드 목록
index=fortianalyzer earliest=-1h | head 100 | fieldsummary
| where count > 0 | table field, count, distinct_count | sort -count
```

**데이터가 안 나오면**:
1. 5단계 쿼리 실행 → 실제 존재하는 필드 확인
2. 로그 샘플 (_raw) 공유 → 쿼리 수정

---

## 3. 주요 변경사항

### ❌ 이전 (작동 안 함)
- Dashboard Studio JSON 형식
- 복잡한 정규식 파싱
- 분리된 대시보드 (Policy/Object 따로)
- 좁은 검색 조건: `cfgpath="firewall.policy"`

### ✅ 현재 (간단하게 수정)
- Classic XML 형식 (Splunk 7-9 호환)
- 기본 필드만 사용 (coalesce로 null 처리)
- **통합 대시보드** (모든 변경사항 한 곳에)
- **넓은 검색**: `(cfgpath=* OR config OR policy OR address OR service)`

---

## 4. 대시보드 구성

### Row 1: 요약 지표
- 📝 전체 변경사항 수
- 👤 관리자 수
- 🖥️ 장비 수

### Row 2: 통합 테이블 (핵심)
- **한 테이블**에 Policy + Address + Service 모두 표시
- 변경유형 자동 분류: 정책/주소객체/서비스객체/기타설정
- 색상 코딩으로 시각화
- 최근 100개 이벤트

### Row 3: 차트
- 📊 시간별 변경 추이 (막대 차트)
- 📊 유형별 변경 통계 (파이 차트)

---

## 5. 문제 해결

### 데이터가 안 나올 때
1. `test-data-exists.spl` 1-3단계 실행
2. FortiGate 7.4.5 로그가 `index=fw`에 실제 들어오는지 확인
3. 필드 이름 확인 (cfgpath, logid, msg, logdesc 등)

### 쿼리 에러 날 때
- XML 인코딩 확인: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`
- 검증: `python3 -c "import xml.etree.ElementTree as ET; ET.parse('file.xml')"`

### 이상한 데이터 나올 때
- 실제 로그 샘플 확인
- `| table _raw` 추가해서 원본 로그 보기
- 필드 추출 로직 조정

---

**버전**: Splunk 9 + FortiGate 7.4.5
**작성일**: 2025-10-28
**통합 대시보드 파일**: `fmg-all-changes-simple.xml`
**진단 쿼리**: `test-data-exists.spl`
