# XWiki 작성 가이드 참조

이 프로젝트의 문서를 XWiki로 작성할 때는 범용 XWiki 가이드를 참조하세요.

## 📚 가이드 위치

**메인 가이드**: `/home/jclee/app/xwiki/docs/XWIKI_WRITING_GUIDE.md`

## 🚀 빠른 시작

### Splunk 프로젝트 문서 → XWiki 변환 예시

#### 1. 성능 개선 보고서
- **원본**: `docs/SPLUNK_PERFORMANCE_IMPROVEMENT_REPORT.md`
- **문서 유형**: Explanation + Reference
- **XWiki 페이지**: `SplunkProject.Reports.PerformanceImprovement2025Q4`

```xwiki
= Splunk 성능 개선 보고서 =

{{info}}
**작성일**: 2025-10-25
**대상**: Management, SOC Team, Infrastructure Team
**읽기 시간**: 10분
{{/info}}

{{toc depth="3" numbered="true"/}}

== 요약 ==

{{success}}
**핵심 개선안**: FAZ HEC 통합으로 70% 데이터 절감 + 80% 쿼리 속도 개선
{{/success}}

|= 항목 |= Before |= After |= 개선율
| 일일 데이터량 | 500 GB/day | 150 GB/day | **70%↓**
| 쿼리 속도 | 30-60초 | 5-10초 | **80%↑**
| 동시 검색 슬롯 | 48/48 (100%) | 18/48 (38%) | **62%↓**

[[자세한 내용 펼치기>>SplunkProject.Reports.PerformanceDetail]]
```

#### 2. Slack Block Kit 배포 가이드
- **원본**: `docs/SLACK_BLOCKKIT_DEPLOYMENT.md`
- **문서 유형**: How-to Guide
- **XWiki 페이지**: `SplunkProject.Guides.SlackBlockKitDeployment`

```xwiki
= Slack Block Kit Alert 배포 가이드 =

**목적**: 대화형 Slack 알림 배포
**소요 시간**: 15분
**난이도**: ⭐⭐⭐☆☆

{{toc depth="3"/}}

----

== 사전 요구사항 ==

{{info}}
* Splunk 8.0+ 설치
* Slack 워크스페이스 관리자 권한
* Python 3.7+ (Splunk 기본 제공)
{{/info}}

----

== 1단계: Slack App 생성 ==

{{tabs}}
(((//(tab1|Slack 설정)
1. https://api.slack.com/apps 접속
1. "Create New App" → "From scratch"
1. OAuth Scopes 추가:
   * chat:write
   * channels:read
//)))
(((//(tab2|Bot Token 발급)
{{code language="bash"}}
# .env 파일에 저장
SLACK_BOT_TOKEN=xoxb-1234567890-...
{{/code}}
//)))
{{/tabs}}

----

== 검증 ==

{{code language="bash"}}
# 테스트 명령
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN"
{{/code}}

{{success}}
✅ `"ok": true` 응답이 오면 성공
{{/success}}
```

#### 3. Correlation Rules 참조
- **원본**: `configs/correlation-rules.conf`
- **문서 유형**: Reference
- **XWiki 페이지**: `SplunkProject.Reference.CorrelationRules`

```xwiki
= Correlation Rules Reference =

**Version**: 2.0
**Last Updated**: 2025-10-25

{{toc depth="2"/}}

----

== 규칙 목록 ==

|= 규칙 ID |= 이름 |= 실행 주기 |= 임계값
| 1 | Multi-Factor Threat Score | 15분 | score ≥ 90
| 2 | Repeated High-Risk Events | 5분 | count > 3
| 3 | Weak Signal Combination | 10분 | indicators ≥ 3
| 4 | Geo Attack Pattern | 1시간 | abuse_score > 50
| 5 | Time-Based Anomaly | 15분 | deviation > 2σ
| 6 | Cross-Event Type | 5분 | correlation_count > 2

----

== 규칙 상세 ==

=== Rule 1: Multi-Factor Threat Score ===

**목적**: 다요소 위협 점수 계산

**SPL 쿼리**:
{{code language="spl"}}
| tstats count WHERE datamodel=Fortinet_Security.Security_Events earliest=-15m
  BY Security_Events.src_ip _time span=1h
| eval abuse_component = coalesce(abuse_score, 0) * 0.4
| eval geo_component = geo_risk * 0.2
| eval correlation_score = abuse_component + geo_component
| where correlation_score >= 75
{{/code}}

**동작 메커니즘**:
{{box title="점수 계산 로직 펼치기"}}
1. **Abuse Score (40%)**: AbuseIPDB 점수 기반
1. **Geo Risk (20%)**: 국가별 위험도
1. **Login Failures (30점)**: 로그인 실패 패턴
1. **Frequency (30점)**: 이벤트 빈도
{{/box}}

**자동 액션**:
* score ≥ 90 → FortiGate 자동 차단
* score 80-89 → Slack 검토 요청
* score 75-79 → 로그만 기록

[[트러블슈팅 가이드>>SplunkProject.Troubleshooting.CorrelationRules]]
```

## 🎨 XWiki 문서 구조 권장사항

### Splunk 프로젝트 계층 구조

```
SplunkProject (Space)
├── 📁 Overview
│   ├── Architecture
│   ├── Data Flow
│   └── Integration Points
├── 📁 Guides (How-to)
│   ├── Installation
│   ├── Dashboard Deployment
│   ├── Slack Block Kit Setup
│   └── Correlation Rules Config
├── 📁 Reference
│   ├── Correlation Rules API
│   ├── SPL Query Collection
│   ├── Configuration Files
│   └── REST API Endpoints
├── 📁 Reports (Explanation)
│   ├── Performance Improvement Plan
│   ├── Concurrent Search Slot Analysis
│   └── FAZ HEC Migration
└── 📁 Troubleshooting
    ├── Dashboard Issues
    ├── Slack Alert Failures
    └── Correlation Rule Debugging
```

## 📝 변환 체크리스트

### Markdown → XWiki 변환 시

**구문 변환**:
- [ ] `#` → `=`
- [ ] `##` → `==`
- [ ] ` ```bash` → `{{code language="bash"}}`
- [ ] `**bold**` → `**bold**` (동일)
- [ ] `[text](url)` → `[[text>>url]]`

**구조 개선**:
- [ ] 첫 문단을 `{{info}}` 박스로
- [ ] 코드 블록에 언어 지정
- [ ] 테이블 헤더에 `|=` 사용
- [ ] 경고/주의사항을 `{{warning}}` 박스로
- [ ] 접기/펼치기 박스 활용 (`{{box}}`)
- [ ] 목차 자동 생성 (`{{toc/}}`)

**메타데이터 추가**:
- [ ] 문서 유형 태그 추가
- [ ] 난이도/소요 시간 명시
- [ ] 최종 업데이트 날짜
- [ ] 내부 링크 3개 이상 연결

## 🔗 참고 자료

- **메인 가이드**: `/home/jclee/app/xwiki/docs/XWIKI_WRITING_GUIDE.md`
- **공식 문서**: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiSyntax/
- **Diataxis Framework**: https://diataxis.fr/

---

**생성일**: 2025-10-25
**목적**: Splunk 프로젝트 문서를 XWiki로 작성 시 참조용
