# Real-time Search Overload 해결 가이드

## 🚨 현재 상황

- **스킵률**: 24.6% (2,031/8,265) - CRITICAL (20% 초과)
- **슬롯 사용**: 70/70 (100% 포화)
- **문제**: 검색을 꺼도 다른 검색이 슬롯 차지 (풍선 효과)
- **원인**: 70개 이상의 Real-time 검색이 경쟁 중

## 🎯 해결 방법 (2가지 옵션)

### Option 1: 빠른 해결 (제한 늘리기)

```bash
# 70개 → 140개로 증가
./scripts/increase-realtime-limit.sh

# 효과
- 즉시 경고 해결
- Splunk 재시작 필요 (5분 소요)
- CPU/메모리 사용량 증가 (주의!)
```

**언제 사용**:
- 급한 경우 (당장 경고 제거 필요)
- Real-time 검색이 80-100개 정도인 경우
- 임시 방편 (근본 해결 아님)

---

### Option 2: 근본 해결 (검색 전환/비활성화)

#### Step 1: 범인 찾기 (Splunk UI에서 실행)

```spl
| rest /services/saved/searches
| search is_scheduled=1 realtime_schedule=1 disabled=0
| stats count by eai:acl.app
| sort -count
```

**예상 결과**:
```
앱 이름                  검색 개수
fortinet_alerts         45
nextrade               23
security_monitoring    18
splunk_monitoring      12
...
```

#### Step 2: 전환 후보 찾기

```bash
# 스크립트 실행
./scripts/find-conversion-candidates.sh

# 또는 Splunk UI에서:
| rest /services/saved/searches
| search is_scheduled=1 realtime_schedule=1 disabled=0
| table title, eai:acl.app, cron_schedule
| sort eai:acl.app
```

#### Step 3: 검색 전환 (Real-time → Scheduled)

**UI 방법**:
1. Settings → Searches, reports, and alerts
2. 검색 선택 → Edit
3. Schedule 섹션:
   - ❌ Real-time schedule 체크 해제
   - ✅ Schedule 체크
   - Cron: `*/5 * * * *` (5분마다)
4. Save

**REST API 방법** (대량 처리):
```bash
# 검색 목록 작성
SEARCHES=(
    "fortinet_fw_alert_object"
    "FW_Object"
    "Security_Monitor_1"
)

# 일괄 전환
for search in "${SEARCHES[@]}"; do
  curl -k -u admin:password \
    -d "realtime_schedule=0" \
    -d "cron_schedule=*/5 * * * *" \
    https://localhost:8089/servicesNS/nobody/search/saved/searches/$search
done
```

#### Step 4: 결과 확인

```bash
# 24시간 후 스킵률 확인
index=_internal source=*scheduler.log
| stats count as total, sum(eval(status="skipped")) as skipped
| eval skip_rate = round(skipped/total*100, 1)
```

**목표**:
- 스킵률: 24.6% → 5% 이하
- 슬롯 사용: 70/70 → 40/70 이하

## 📋 전환 우선순위

### 🔴 우선 전환 (High Priority)

1. **스킵 횟수 많은 검색**:
   - fortinet_fw_alert_object (66,763 skips)
   - FW_Object (730 skips)

2. **Alert 검색**:
   - 5분 지연 허용 가능
   - 대부분 Real-time 불필요

3. **통계/리포트 검색**:
   - 즉시성 불필요
   - Scheduled로 충분

### 🟡 검토 필요 (Medium Priority)

1. **대시보드 백엔드 검색**:
   - 새로고침 간격 확인 (> 1분이면 전환 가능)

2. **실행 빈도 낮은 검색**:
   - 10분, 15분 간격 → Scheduled 전환

### 🟢 유지 (Keep Real-time)

1. **실시간 모니터링**:
   - 1초 단위 업데이트 필요
   - 보안 대시보드

2. **즉시 대응 필요**:
   - 침입 차단 (auto-block)
   - SLA < 1분

## 🔍 추가 스크립트

```bash
# 전체 Real-time 검색 개수 확인
./scripts/list-all-realtime-searches.sh

# 앱별 Real-time 검색 분석
./scripts/find-realtime-search-apps.sh

# 전환 후보 찾기
./scripts/find-conversion-candidates.sh

# 진단 리포트
./scripts/diagnose-splunk-issues.sh
```

## ❓ FAQ

### Q1: JavaScript 문제랑 관련 있나요?

**A**: 아니요, 별개 문제입니다.
- Real-time 제한: 검색 실행 개수 문제
- JavaScript: 대시보드 기능 제한 (web.conf 설정)

JavaScript 문제는 `configs/dashboards/slack-control-no-js.xml` 사용하세요.

### Q2: 검색 2개 껐는데 왜 경고 안 사라지나요?

**A**: "풍선 효과" 때문입니다.
- 70개보다 많은 검색이 대기 중
- 2개 끄면 → 다른 2개가 슬롯 차지
- 총 개수를 70개 이하로 줄여야 함

### Q3: 얼마나 많은 Real-time 검색이 있나요?

**A**: Splunk UI에서 확인:
```spl
| rest /services/saved/searches
| search is_scheduled=1 realtime_schedule=1 disabled=0
| stats count
```

- 80-100개: 제한 늘리기 (Option 1)
- 100개 이상: 검색 전환/비활성화 (Option 2)

### Q4: 어떤 검색부터 전환해야 하나요?

**A**: 우선순위:
1. 스킵 횟수 많은 검색 (66,763 skips)
2. Alert 검색 (5분 지연 OK)
3. 통계/리포트 검색
4. 실행 빈도 낮은 검색

### Q5: 전환 후 문제 생기면?

**A**: 언제든지 되돌리기 가능:
```bash
# UI에서: Real-time schedule 다시 체크
# 또는 REST API:
curl -k -u admin:password \
  -d "realtime_schedule=1" \
  https://localhost:8089/.../saved/searches/검색이름
```

## 📊 예상 효과

### 검색 30개 전환 시

| 항목 | 전환 전 | 전환 후 |
|------|---------|---------|
| 슬롯 사용 | 70/70 (100%) | 40/70 (57%) |
| 스킵률 | 24.6% | < 5% |
| CPU 사용률 | 높음 | 20% 감소 |
| 경고 | 🔴 CRITICAL | 🟢 HEALTHY |

## 🎯 권장 Action Plan

### 급한 경우 (10분 소요)
```bash
1. ./scripts/increase-realtime-limit.sh
2. Splunk 재시작
3. ✅ 경고 해결 (임시)
```

### 근본 해결 (1-2시간 소요)
```bash
1. SPL 쿼리로 범인 앱 찾기
2. 전환 후보 30-40개 선정
3. UI 또는 REST API로 전환
4. 24시간 후 스킵률 확인
5. ✅ 경고 해결 (영구)
```

---

**참고 문서**:
- `splunk-realtime-limit-fix.md` - 제한 늘리기 상세 가이드
- `scripts/diagnose-splunk-issues.sh` - 진단 스크립트
- `scripts/find-conversion-candidates.sh` - 전환 후보 찾기
