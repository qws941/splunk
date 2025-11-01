# 📊 FMG 통합 대시보드 (최종)

> **Splunk 9 + FortiGate 7.4.5** 환경용 단일 통합 대시보드

---

## ✅ 완료된 작업

1. ✅ **통합 대시보드 생성**: `configs/dashboards/fmg-all-changes-simple.xml`
   - Policy + Address + Service 모두 **한 화면**에 표시
   - 넓은 검색 패턴: `(cfgpath=* OR config OR policy OR address OR service)`
   - 간단한 필드 처리 (coalesce로 null 처리)

2. ✅ **진단 쿼리 작성**: `test-data-exists.spl`
   - 데이터 존재 확인
   - 필드 목록 확인
   - 로그 샘플 확인

3. ✅ **분리된 대시보드 삭제**
   - ~~fmg-policy-changes-only.xml~~ (삭제됨)
   - ~~fmg-object-changes-only.xml~~ (삭제됨)

4. ✅ **검증 완료**
   - XML 문법 정상
   - 통합 테이블 구조 확인
   - 넓은 검색 패턴 적용

---

## 📁 파일 구조

```
/home/jclee/app/splunk/
├── configs/dashboards/
│   └── fmg-all-changes-simple.xml        ⭐ 메인 대시보드 (146줄)
├── test-data-exists.spl                   🔍 진단 쿼리
├── DASHBOARD-DEPLOYMENT.md                📖 배포 가이드 (상세)
├── README-FMG-DASHBOARD.md                📋 이 파일
└── QUICK-TEST.sh                          ✅ 검증 스크립트
```

---

## 🚀 빠른 배포

### 방법 1: Splunk Web UI (권장)

1. Splunk 접속: `https://your-splunk:8000`
2. **Settings** → **User Interface** → **Views** → **New from XML**
3. 아래 파일 내용 복사 붙여넣기:
   ```bash
   cat configs/dashboards/fmg-all-changes-simple.xml
   ```
4. **View Name**: `fmg_all_changes_simple`
5. **Save** 클릭
6. 접속: `https://your-splunk:8000/app/search/fmg_all_changes_simple`

### 방법 2: 파일 복사

```bash
scp configs/dashboards/fmg-all-changes-simple.xml \
  splunk:/opt/splunk/etc/apps/search/local/data/ui/views/

ssh splunk "/opt/splunk/bin/splunk restart splunkweb"
```

---

## 🔍 데이터 확인 (중요!)

**대시보드 배포 후 데이터가 안 나오면**, 진단 쿼리 실행:

```bash
# Splunk Search에서 실행
cat test-data-exists.spl
```

**실행 순서**:
1. **1단계**: fw 인덱스에 데이터가 있는지 확인
2. **2단계**: cfgpath 필드가 있는지 확인
3. **5단계**: 실제 존재하는 모든 필드 목록 확인

**데이터가 없으면**:
- FortiGate 7.4.5 로그가 `index=fw`로 들어오는지 확인
- Syslog 설정 확인
- 필드 이름이 다를 수 있음 (5단계 쿼리로 확인)

---

## 📊 대시보드 구성

### 📌 Row 1: 요약 통계
- 📝 전체 변경사항 수
- 👤 관리자 수 (distinct users)
- 🖥️ 장비 수 (distinct devices)

### 📌 Row 2: 통합 테이블 (핵심)
**한 테이블**에 모든 변경사항 표시:
- ✅ Policy 변경 (firewall.policy, firewall.rule)
- ✅ Address 객체 변경 (firewall.address, firewall.addrgrp)
- ✅ Service 객체 변경 (firewall.service, firewall.servicegrp)

**컬럼**:
- 시간 (타임스탬프)
- 장비 (devname)
- 관리자 (user)
- 변경유형 (자동 분류: 정책/주소객체/서비스객체/기타설정)
- 작업 (action: Add/Delete/Edit/modify)
- 설명 (msg/logdesc)
- cfgpath (원본 경로)
- _raw (전체 로그)

**색상 코딩**:
- 정책: 노란색 (#F7BC38)
- 주소객체: 초록색 (#65A637)
- 서비스객체: 파란색 (#6DB7C6)
- 기타설정: 보라색 (#8B4789)

### 📌 Row 3: 차트
- 📊 **시간별 변경 추이** (막대 차트, 1시간 단위)
- 📊 **유형별 변경 통계** (파이 차트)

---

## 🔧 주요 변경사항 (이전 버전 대비)

| 항목 | 이전 | 현재 |
|------|------|------|
| **형식** | Dashboard Studio JSON | Classic XML |
| **대시보드 수** | 3개 분리 | **1개 통합** ⭐ |
| **검색 패턴** | `cfgpath="firewall.policy"` (좁음) | `(cfgpath=* OR config OR policy OR address OR service)` (넓음) |
| **필드 처리** | 복잡한 정규식 | `coalesce()` 간단 처리 |
| **테이블** | Policy/Object 분리 | **한 테이블에 통합** ⭐ |
| **호환성** | Splunk 9 전용 | Splunk 7-9 호환 |

---

## ⚠️ 문제 해결

### 1. 데이터가 안 나올 때
```spl
# 진단 쿼리 1-5단계 실행
index=fw earliest=-24h | head 1 | table _time, _raw
index=fw earliest=-1h | head 100 | fieldsummary | where count > 0 | table field, count
```

### 2. 쿼리 에러 날 때
- XML 인코딩 확인: `&` → `&amp;`, `<` → `&lt;`
- 검증: `python3 -c "import xml.etree.ElementTree as ET; ET.parse('file.xml')"`

### 3. 이상한 데이터 나올 때
- `| table _raw` 추가해서 원본 로그 확인
- 필드 이름이 다를 수 있음 (fieldsummary로 확인)

---

## 📞 지원

**파일**:
- 상세 가이드: `DASHBOARD-DEPLOYMENT.md`
- 검증 스크립트: `QUICK-TEST.sh` (실행: `./QUICK-TEST.sh`)
- 진단 쿼리: `test-data-exists.spl`

**검증**:
```bash
./QUICK-TEST.sh  # 모든 검증 자동 실행
```

---

**버전**: 1.0
**날짜**: 2025-10-28
**환경**: Splunk 9 + FortiGate 7.4.5
**메인 파일**: `configs/dashboards/fmg-all-changes-simple.xml`
**상태**: ✅ 테스트 완료, 배포 준비됨
