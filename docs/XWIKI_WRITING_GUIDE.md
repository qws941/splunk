# XWiki 효율적 작성 가이드

**목적**: Splunk 프로젝트 문서를 XWiki로 빠르게 작성하고 관리하기 위한 실용 가이드

**Version**: 1.0
**Last Updated**: 2025-10-25

---

## 🎯 Quick Start (30초 요약)

```xwiki
= 제목 =
== 소제목 ==

**굵게** //이탤릭// __밑줄__

* 목록 항목 1
* 목록 항목 2

1. 번호 목록 1
1. 번호 목록 2

[[링크 텍스트>>https://example.com]]
[[내부 페이지>>Space.Page]]

{{code language="bash"}}
echo "코드 블록"
{{/code}}

{{warning}}
경고 메시지
{{/warning}}
```

---

## 📚 Diataxis Framework (2025 XWiki 표준)

XWiki는 2025년부터 문서를 4가지 유형으로 구분합니다:

| 유형 | 목적 | 예시 |
|------|------|------|
| **Tutorial** | 학습 (Learning-oriented) | "Splunk 첫 대시보드 만들기" |
| **How-to Guide** | 작업 (Problem-oriented) | "Slack Block Kit 배포하는 법" |
| **Reference** | 참조 (Information-oriented) | "Correlation Rules API 명세" |
| **Explanation** | 이해 (Understanding-oriented) | "Concurrent Search Slot이란?" |

**우리 문서 분류 예시**:
- `SLACK_BLOCKKIT_DEPLOYMENT.md` → **How-to Guide**
- `SPLUNK_PERFORMANCE_IMPROVEMENT_REPORT.md` → **Explanation** (+ Reference)
- `correlation-rules.conf` → **Reference**

---

## ✍️ XWiki Syntax 2.1 (핵심만)

### 1. 제목 (Headings)

```xwiki
= 제목 1 (H1) =
== 제목 2 (H2) ==
=== 제목 3 (H3) ===
==== 제목 4 (H4) ====
```

### 2. 텍스트 서식

```xwiki
**굵게 (Bold)**
//이탤릭 (Italic)//
__밑줄 (Underline)__
--취소선 (Strikethrough)--
{{monospace}}단일 공백 텍스트{{/monospace}}
^^위 첨자^^ ,,아래 첨자,,
```

### 3. 링크

```xwiki
# 외부 링크
[[Splunk 공식 문서>>https://docs.splunk.com]]

# 내부 페이지 링크 (같은 스페이스)
[[대시보드 가이드>>DashboardGuide]]

# 다른 스페이스의 페이지
[[참조>>AnotherSpace.PageName]]

# 앵커 링크
[[성능 개선 섹션>>#performance-improvement]]

# 이미지와 함께
[[image:logo.png>>https://example.com]]
```

### 4. 목록

```xwiki
# 순서 없는 목록
* 항목 1
* 항목 2
** 중첩 항목 2.1
** 중첩 항목 2.2
* 항목 3

# 순서 있는 목록
1. 첫 번째
1. 두 번째
11. 중첩 2.1
11. 중첩 2.2
1. 세 번째

# 혼합
* 항목 1
*1. 번호 1.1
*1. 번호 1.2
* 항목 2
```

### 5. 테이블

```xwiki
|= 헤더 1 |= 헤더 2 |= 헤더 3
| 데이터 1 | 데이터 2 | 데이터 3
| 데이터 4 | 데이터 5 | 데이터 6

# 셀 병합 (colspan)
|= 헤더 1 |= 헤더 2
|(((데이터 1 (2열 병합))))
| 데이터 2 | 데이터 3
```

### 6. 코드 블록

```xwiki
{{code language="bash"}}
#!/bin/bash
curl -k -u admin:password https://splunk.jclee.me:8089/health
{{/code}}

{{code language="python"}}
def send_slack_alert(message):
    return requests.post(SLACK_WEBHOOK_URL, json={"text": message})
{{/code}}

{{code language="spl"}}
index=fortianalyzer earliest=-1h severity=critical
| stats count by src_ip, dst_ip
| sort -count
{{/code}}
```

### 7. 인용구

```xwiki
> 단일 인용
> 여러 줄
> 인용

>> 중첩 인용
>> 2단계
```

---

## 🎨 유용한 매크로 (Macros)

### 1. Info/Warning/Error 박스

```xwiki
{{info}}
ℹ️ 정보: Splunk 8.0 이상에서 테스트되었습니다.
{{/info}}

{{warning}}
⚠️ 경고: 프로덕션 환경에서는 반드시 백업 후 진행하세요.
{{/warning}}

{{error}}
🚨 오류: SLACK_BOT_TOKEN 환경 변수가 설정되지 않았습니다.
{{/error}}

{{success}}
✅ 성공: Block Kit 배포가 완료되었습니다.
{{/success}}
```

### 2. 목차 (Table of Contents)

```xwiki
{{toc depth="3" numbered="true"/}}
```

### 3. 코드 블록 (번호 있는 줄)

```xwiki
{{code language="bash" lines="true"}}
npm install
npm start
curl http://localhost:3001/health
{{/code}}
```

### 4. 접기/펼치기 (Collapsible)

```xwiki
{{box title="설정 예시 펼치기"}}
{{code language="ini"}}
[fw_security]
homePath = $SPLUNK_DB/fw_security/db
coldPath = $SPLUNK_DB/fw_security/colddb
maxTotalDataSizeMB = 500000
{{/code}}
{{/box}}
```

### 5. 포함 (Include) - 재사용

```xwiki
{{include reference="Space.CommonFooter"/}}
```

---

## 🏗️ 문서 구조 템플릿

### Template 1: How-to Guide (작업 가이드)

```xwiki
= [작업명] 가이드 =

**목적**: [한 문장으로 목적 설명]
**소요 시간**: [예상 시간]
**난이도**: ⭐⭐⭐☆☆ (5점 만점)

{{toc/}}

----

== 사전 요구사항 ==

{{info}}
이 가이드를 따르기 전에 다음을 준비하세요:
* 항목 1
* 항목 2
* 항목 3
{{/info}}

----

== 1단계: [단계 이름] ==

[단계 설명]

{{code language="bash"}}
# 실행 명령
command here
{{/code}}

**예상 결과**:
{{code}}
Expected output
{{/code}}

{{warning}}
⚠️ 주의사항: [중요 경고]
{{/warning}}

----

== 2단계: [다음 단계] ==

...

----

== 검증 ==

다음 명령으로 정상 동작을 확인하세요:

{{code language="bash"}}
# 검증 명령
curl http://localhost:3001/health | jq
{{/code}}

----

== 트러블슈팅 ==

=== 문제 1: [증상] ===

**원인**: [원인 설명]

**해결방법**:
{{code language="bash"}}
# 해결 명령
fix command
{{/code}}

----

== 참고 자료 ==

* [[내부 문서>>Space.RelatedPage]]
* [[외부 링크>>https://example.com]]
```

### Template 2: Reference (참조 문서)

```xwiki
= [항목명] Reference =

**Version**: 1.0
**Last Updated**: 2025-10-25

{{toc depth="2"/}}

----

== 개요 ==

[한 문단으로 개요 설명]

----

== API 명세 ==

|= 메서드 |= 엔드포인트 |= 설명
| GET | /api/stats | 통계 조회
| POST | /api/events | 이벤트 생성
| DELETE | /api/alerts/:id | 알림 삭제

----

== 파라미터 ==

=== Request ===

{{code language="json"}}
{
  "channel": "#splunk-alerts",
  "severity": "critical",
  "message": "Alert message"
}
{{/code}}

=== Response ===

{{code language="json"}}
{
  "success": true,
  "message_id": "12345"
}
{{/code}}

----

== 예시 ==

{{code language="bash"}}
curl -X POST http://localhost:3001/api/events \
  -H "Content-Type: application/json" \
  -d '{"type":"security","severity":"high"}'
{{/code}}
```

### Template 3: Explanation (설명 문서)

```xwiki
= [개념/메커니즘] 이해하기 =

{{info}}
**읽기 시간**: 5분
**대상**: Splunk 관리자, SOC 팀
{{/info}}

{{toc/}}

----

== 무엇인가? (What) ==

[개념 정의 - 1-2 문단]

----

== 왜 중요한가? (Why) ==

[중요성 설명 - 실무 예시 포함]

**실제 사례**:
{{warning}}
현재 환경에서는 Concurrent Search Slot이 48/48로 포화 상태입니다.
이로 인해 알림이 124회/24시간 Skip되고 있습니다.
{{/warning}}

----

== 어떻게 작동하는가? (How) ==

=== 동작 원리 ===

[다이어그램 또는 단계별 설명]

{{code}}
Step 1: [설명]
   ↓
Step 2: [설명]
   ↓
Step 3: [결과]
{{/code}}

----

== 실무 적용 ==

[구체적인 적용 방법]

----

== 더 읽을거리 ==

* [[관련 How-to 가이드>>Space.HowToPage]]
* [[API Reference>>Space.APIReference]]
```

---

## 🚀 효율적 작성 전략

### 1. 페이지 계층 구조 (Nested Pages)

```
Splunk Project (Space)
├── 📁 Overview
│   ├── Architecture
│   └── Getting Started
├── 📁 Deployment
│   ├── Dashboard Deployment
│   ├── Slack Block Kit Setup
│   └── Cloudflare Workers
├── 📁 Operations
│   ├── Performance Monitoring
│   ├── Troubleshooting
│   └── Alert Management
├── 📁 Reference
│   ├── API Specification
│   ├── Configuration Files
│   └── Correlation Rules
└── 📁 Reports
    ├── Performance Improvement Plan
    └── Q4 2025 Review
```

**장점**:
- URL 자동 생성: `Space.Deployment.SlackBlockKitSetup`
- 네비게이션 자동화
- 권한 관리 계층별 적용 가능

### 2. 템플릿 활용 (Template Pages)

```xwiki
# 1. 템플릿 페이지 생성: Space.Templates.HowToTemplate
# 2. 새 페이지 생성 시:
[[Create new How-to>>Space.NewPage?template=Space.Templates.HowToTemplate]]

# 3. 또는 URL 직접:
https://wiki.example.com/create/Space/NewPage?template=Space.Templates.HowToTemplate
```

### 3. 공통 요소 재사용 (Include)

**공통 푸터** (`Space.Common.Footer`):
```xwiki
----

== 도움이 필요하신가요? ==

* [[FAQ>>Space.FAQ]]
* [[문의하기>>Space.Contact]]
* Slack: #splunk-support

{{info}}
**문서 버전**: {{velocity}}$doc.version{{/velocity}}
**최종 수정**: {{velocity}}$doc.date{{/velocity}}
**작성자**: {{velocity}}$doc.author{{/velocity}}
{{/info}}
```

**사용**:
```xwiki
= 내 문서 =

[문서 내용...]

{{include reference="Space.Common.Footer"/}}
```

### 4. 자동 태깅 및 메타데이터

```xwiki
{{velocity}}
## 자동 태그 추가
$doc.addTag("splunk")
$doc.addTag("deployment")
$doc.addTag("production")

## 커스텀 속성
$doc.set("difficulty", "intermediate")
$doc.set("estimated_time", "30min")
{{/velocity}}
```

### 5. 검색 최적화 (Solr)

**검색 잘 되는 문서 작성**:
- ✅ 제목에 핵심 키워드 포함: "Splunk Performance Improvement"
- ✅ 첫 문단에 요약 포함 (검색 결과 스니펫으로 표시)
- ✅ 태그 활용: `splunk`, `performance`, `hec`, `faz`
- ✅ 내부 링크 많이 연결 (관련성 점수 상승)

---

## 📊 실전: 성능 개선 보고서를 XWiki로 옮기기

### Before (Markdown)

```markdown
# Splunk Performance Improvement Report

## Current Architecture

70 FortiGate → Syslog → Splunk (500 GB/day)
```

### After (XWiki)

```xwiki
= Splunk 성능 개선 보고서 =

{{info}}
**작성일**: 2025-10-25
**대상**: SOC Team, Infrastructure Team, Management
**읽기 시간**: 10분
{{/info}}

{{toc depth="3"/}}

----

== 요약 ==

{{success}}
**핵심 개선안**: FortiAnalyzer HEC 통합으로 70% 데이터 절감 + 80% 쿼리 속도 개선
{{/success}}

|= 항목 |= Before |= After |= 개선율
| 일일 데이터량 | 500 GB/day | 150 GB/day | **70%↓**
| 쿼리 속도 | 30-60초 | 5-10초 | **80%↑**
| 동시 검색 슬롯 | 48/48 (100%) | 18/48 (38%) | **62%↓**

----

== 현재 아키텍처 ==

{{code}}
┌────────────────────────┐
│ FortiGate (70대)       │
└───────────┬────────────┘
            │ Syslog UDP 514
            ↓
┌────────────────────────┐
│ Splunk (index=fw)      │
│ - 500 GB/day           │
│ - 슬롯 포화: 48/48     │
└────────────────────────┘
{{/code}}

{{warning}}
⚠️ **문제점**: Concurrent Search Slot 포화로 인해 실시간 알림이 124회/24시간 Skip되고 있습니다.
{{/warning}}

[[자세한 슬롯 메커니즘 설명>>Space.Explanation.ConcurrentSearchSlot]]

----

== 개선 방안 ==

{{box title="Phase 1: 환경 준비 (1주)"}}
* FAZ 메인 장비 선정
* Splunk HEC 토큰 생성
* 네트워크 방화벽 규칙 설정

{{code language="bash"}}
# HEC 토큰 생성
curl -k -u admin:password -X POST \
  https://splunk.jclee.me:8089/servicesNS/nobody/splunk_httpinput/data/inputs/http \
  -d name=faz_hec_token \
  -d indexes=fw_security,fw_threat
{{/code}}
{{/box}}

{{box title="Phase 2: FAZ HEC 설정 (2주)"}}
...
{{/box}}

----

== 예상 효과 ==

=== 비용 절감 ===

{{success}}
**연간 절감액**: ₩80,000,000
* 스토리지 비용: ₩30,000,000
* 라이선스 비용: ₩50,000,000
{{/success}}

=== 성능 개선 ===

[[성능 벤치마크 상세>>Space.Reference.PerformanceBenchmark]]

----

== 검증 쿼리 ==

=== HEC 데이터 유입 확인 ===

{{code language="spl"}}
index=fw_security OR index=fw_threat earliest=-1h
| stats count, sum(eval(len(_raw))) as total_bytes by index, sourcetype
| eval total_mb=round(total_bytes/1024/1024, 2)
{{/code}}

[[전체 검증 쿼리 모음>>Space.Reference.VerificationQueries]]

----

{{include reference="Space.Common.Footer"/}}
```

---

## 🎯 빠른 체크리스트

**XWiki 문서 작성 전**:
- [ ] 문서 유형 결정 (Tutorial / How-to / Reference / Explanation)
- [ ] 적절한 템플릿 선택
- [ ] 페이지 위치 결정 (계층 구조)
- [ ] 태그 준비 (3-5개)

**작성 중**:
- [ ] 제목에 핵심 키워드 포함
- [ ] 첫 문단에 요약 포함 (info 박스 활용)
- [ ] 목차 자동 생성 (`{{toc/}}`)
- [ ] 코드 블록에 언어 지정 (`language="bash"`)
- [ ] 경고/정보 박스 적절히 배치

**작성 후**:
- [ ] 내부 링크 연결 (최소 3개)
- [ ] 메타데이터 입력 (작성자, 날짜, 버전)
- [ ] 공통 푸터 포함 (`{{include}}`)
- [ ] 검색 테스트 (Solr)

---

## 🔗 참고 자료

**공식 문서**:
- XWiki Syntax 2.1: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiSyntax/
- Macro Reference: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiSyntax/Macros
- Diataxis Framework: https://diataxis.fr/

**실무 예시**:
- 이 프로젝트의 모든 Markdown 문서는 위 템플릿으로 변환 가능
- `docs/SPLUNK_PERFORMANCE_IMPROVEMENT_REPORT.md` → "Explanation" 유형
- `docs/SLACK_BLOCKKIT_DEPLOYMENT.md` → "How-to Guide" 유형

---

**Version**: 1.0
**작성자**: Claude Code
**업데이트 주기**: 분기별 검토
