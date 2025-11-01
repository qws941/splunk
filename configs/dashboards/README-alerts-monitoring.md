# FortiGate Alerts Monitoring Dashboard

**파일**: `fortigate-alerts-monitoring.xml`
**크기**: 17KB
**패널 수**: 13개 (통계 4개, 차트 6개, 테이블 3개)
**목적**: 프로덕션 알림 시스템 모니터링 및 최적화

---

## 📊 대시보드 구성

### Row 1: 전체 개요 (4개 통계 패널)
- **Total Alerts Fired**: 지난 24시간 총 알림 실행 수
- **Success Rate**: 알림 실행 성공률 (%)
- **Avg Execution Time**: 평균 실행 시간 (초)
- **Suppressed Alerts**: Suppression으로 차단된 중복 알림 수

### Row 2: 알림 유형별 빈도
- **Alert Execution Count by Type**: 알림 유형별 실행 횟수 (막대 차트)

### Row 3: 시계열 분석
- **Alert Execution Timeline**: 시간대별 알림 발생 추이 (1시간 단위)

### Row 4: 성능 분석
- **Alert Execution Time by Type**: 알림별 평균 실행 시간 (바 차트)
- **Alert Success vs Failure**: 성공/실패 비율 (스택 컬럼)

### Row 5: 최근 실행 내역
- **Recent Alert Executions**: 최근 50개 알림 실행 기록 (테이블)
  - 실행 시간, 알림 유형, 상태, 실행 시간, 결과 수, Suppression 여부

### Row 6: Suppression 효과 분석
- **Suppression Effectiveness**: 알림별 Suppression 효과 (스택 차트)
- **Suppression Rate Table**: Suppression 비율 및 평가 (테이블)
  - 🟢 Good (10-30%): 적정 수준
  - 🟡 Moderate (30-50%): 임계값 조정 고려
  - 🔴 Too High (50%+): 임계값 너무 높음, 수정 필요

### Row 7: Slack 알림 상태
- **Slack Notification Success Rate**: Slack 전송 성공률 (%)
- **Total Slack Messages Sent**: 총 전송 메시지 수
- **Slack Failures**: Slack 전송 실패 로그 (테이블)

### Row 8: 설정 요약
- **Alert Configuration Overview**: 10개 알림 설정 요약 (HTML 패널)
  - 실시간 알림 6개 (설정 상세)
  - 요약 전용 알림 3개
  - 비활성화 알림 1개
  - 배포 상태 및 명령어

---

## 🚀 배포 방법

### 방법 1: Splunk Web UI (권장)
```
1. Splunk Web → Settings → User Interface → Views
2. "New View" 클릭
3. "View Type" → Dashboard (XML)
4. fortigate-alerts-monitoring.xml 내용 붙여넣기
5. "Save As" → Dashboard ID: fortigate_alerts_monitoring
```

### 방법 2: REST API
```bash
curl -k -u admin:password \
  -d "eai:data=$(cat configs/dashboards/fortigate-alerts-monitoring.xml)" \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/fortigate_alerts_monitoring
```

### 방법 3: 파일 시스템 복사
```bash
sudo cp configs/dashboards/fortigate-alerts-monitoring.xml \
  /opt/splunk/etc/apps/search/local/data/ui/views/

sudo chown splunk:splunk /opt/splunk/etc/apps/search/local/data/ui/views/fortigate-alerts-monitoring.xml

/opt/splunk/bin/splunk reload display -auth admin:password
```

---

## 📈 주요 모니터링 지표

### 1. 알림 건강성
- **Success Rate > 95%**: 정상
- **Success Rate 85-95%**: 주의 (로그 확인 필요)
- **Success Rate < 85%**: 경고 (즉시 조치)

### 2. 실행 성능
- **Avg Time < 5초**: 우수
- **Avg Time 5-15초**: 양호
- **Avg Time 15-30초**: 개선 필요 (쿼리 최적화)
- **Avg Time > 30초**: 심각 (즉시 최적화)

### 3. Suppression 효과
- **10-30%**: 적정 (중복 방지 효과적)
- **30-50%**: 주의 (임계값 재검토)
- **50%+**: 위험 (임계값 너무 높음, 실제 알림 놓칠 수 있음)

### 4. Slack 전송
- **Success Rate > 95%**: 정상
- **Success Rate < 95%**: Slack API 또는 네트워크 문제

---

## 🔍 트러블슈팅

### 문제 1: 알림이 실행되지 않음
```spl
# 스케줄 로그 확인
index=_internal source=*scheduler.log savedsearch_name="*.[alert]*"
| stats count by savedsearch_name, status
```

**해결책**:
- `disabled = 0` 인지 확인
- `cron_schedule` 문법 검증
- `enableSched = 1` 설정 확인

### 문제 2: 알림 실행 시간이 느림 (>30초)
```spl
# 느린 알림 찾기
index=_internal source=*scheduler.log savedsearch_name="*.[alert]*"
| where run_time > 30
| stats avg(run_time) as avg_time, max(run_time) as max_time by savedsearch_name
| sort -avg_time
```

**해결책**:
- 쿼리에 `index=` 명시
- 불필요한 `stats`, `eval` 제거
- Data Model 가속화 사용
- 시간 범위 줄이기 (rt-1m → rt-30s)

### 문제 3: Suppression이 작동하지 않음
```spl
# Suppression 로그 확인
index=_internal source=*scheduler.log savedsearch_name="001.[alert]FortiGate_Config_Change" suppressed=1
| stats count by suppressed
```

**해결책**:
- `alert.suppress = 1` 설정 확인
- `alert.suppress.fields` 필드 존재 여부 확인
- `alert.suppress.period` 형식 검증 (30s, 5m, 1h, 24h)

### 문제 4: Slack 메시지가 전송되지 않음
```spl
# Slack 에러 확인
index=_internal source=*slack* error=*
| table _time, savedsearch_name, error, message
```

**해결책**:
- Slack bot이 채널에 초대되었는지 확인: `/invite @bot-name`
- OAuth Scopes 확인: `chat:write`, `channels:read`, `chat:write.public`
- Slack token 유효성 확인:
  ```bash
  curl -X POST https://slack.com/api/auth.test \
    -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"
  ```

---

## 📊 권장 대시보드 사용 패턴

### 일일 체크 (매일 오전)
1. **Success Rate** 확인 (95% 이상 유지)
2. **Recent Alert Executions** 테이블 스캔 (실패 건 확인)
3. **Slack Failures** 테이블 확인 (에러 메시지 분석)

### 주간 리뷰 (매주 월요일)
1. **Alert Execution Timeline** 차트 분석 (트렌드 확인)
2. **Suppression Effectiveness** 테이블 검토 (50% 이상 항목 조정)
3. **Alert Execution Time** 차트 확인 (30초 이상 항목 최적화)

### 월간 최적화 (매월 초)
1. **Alert Frequency** 차트 분석 (과도한 알림 유형 조정)
2. Suppression period 재조정 (너무 많이 차단되는 항목)
3. 임계값 튜닝 (Traffic: 10GB, Metrics: 2x baseline 등)

---

## 🎯 최적화 목표

| 지표 | 현재 목표 | 최적화 후 목표 |
|------|----------|---------------|
| Success Rate | > 95% | > 99% |
| Avg Execution Time | < 15초 | < 5초 |
| Suppression Rate | 10-30% | 15-25% |
| Slack Success Rate | > 95% | > 99% |
| 일일 알림 수 | < 100 | < 50 (smart detection) |

---

## 📝 연관 파일

- **설정 파일**: `configs/savedsearches-fortigate-production-alerts.conf`
- **배포 체크리스트**: `configs/DEPLOYMENT_CHECKLIST.md`
- **대시보드 디렉토리**: `configs/dashboards/`

---

**작성일**: 2025-11-02
**버전**: 1.0
**작성자**: jclee
**Git Commit**: `8989741` - Comprehensive alerts monitoring dashboard
