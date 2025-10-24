# Figma to Splunk Dashboard Automation

**자동화 워크플로우: Figma 디자인 → Dashboard Studio JSON → Splunk 배포**

## 🎯 개요

Figma에서 디자인한 대시보드 레이아웃을 자동으로 Splunk Dashboard Studio JSON으로 변환합니다.

**처리 흐름**:
```
Figma Design (Frames)
    ↓
Figma API (GET /v1/files/:key)
    ↓
figma-to-dashboard.js (변환 엔진)
    ↓
Dashboard Studio JSON
    ↓
Splunk REST API (POST /data/ui/views/studio)
    ↓
Deployed Dashboard
```

---

## 🚀 Quick Start

### 1. Figma 디자인 준비

**Figma 파일 구조**:
```
📄 Splunk Dashboard Design (File)
├── 📄 Dashboard Design (Page)
│   ├── 🖼️ Device Status Table (Frame)
│   ├── 🖼️ Admin Activity Line Chart (Frame)
│   ├── 🖼️ Log Volume Single Value (Frame)
│   └── 🖼️ Config Changes Bar Chart (Frame)
```

**Frame 명명 규칙**:
- `[Name] Table` → `splunk.table` 시각화
- `[Name] Line Chart` → `splunk.line` 시각화
- `[Name] Bar` → `splunk.bar` 시각화
- `[Name] Pie` → `splunk.pie` 시각화
- `[Name] Single Value` → `splunk.singlevalue` 시각화

**Frame Description에 SPL 쿼리 추가** (선택사항):
```
SPL: index=fw | stats count by devname | sort -count
```

### 2. Figma File Key 찾기

1. Figma에서 파일 열기
2. URL 확인: `https://www.figma.com/file/[FILE_KEY]/...`
3. FILE_KEY 복사 (예: `abc123xyz`)

### 3. 스크립트 실행

```bash
# 기본 사용법
node scripts/figma-to-dashboard.js <FILE_KEY> <PAGE_NAME>

# 예제
node scripts/figma-to-dashboard.js abc123xyz "Dashboard Design"
```

**출력**:
```
🔍 Fetching Figma file...
✅ Loaded: Splunk Dashboard Design
🔄 Converting to Dashboard Studio JSON...
📊 Found 4 frames in page "Dashboard Design"
✅ Dashboard created: /home/jclee/app/splunk/configs/dashboards/studio/dashboard-design.json

📊 Summary:
   - Visualizations: 4
   - Data Sources: 4
   - Canvas Size: 1440x1200

🚀 Next steps:
   1. Review generated JSON and adjust SPL queries
   2. Deploy to Splunk via REST API
```

### 4. 생성된 JSON 검토

```bash
cat configs/dashboards/studio/dashboard-design.json | jq .
```

**확인 사항**:
- ✅ 레이아웃 위치 정확한지 확인
- ✅ SPL 쿼리 수정 필요 시 편집
- ✅ 시각화 타입 적절한지 확인

### 5. Splunk에 배포

```bash
# 방법 1: node scripts/deploy-dashboards.js 사용
node scripts/deploy-dashboards.js

# 방법 2: curl 직접 사용
curl -k -u admin:password \
  -d "eai:data=$(cat configs/dashboards/studio/dashboard-design.json)" \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/studio/dashboard_design

# 방법 3: Splunk Web UI
# Settings → User Interface → Dashboards → Create New Dashboard → Import JSON
```

---

## 📐 Figma 디자인 가이드

### 레이아웃 권장사항

**Canvas Size**: 1440px width (Dashboard Studio 기본)

**Grid System**:
- 12-column grid
- Gutter: 20px
- Margin: 40px

**Frame Sizes** (예제):
```
Single Value Metric: 288x120 (small), 360x120 (medium)
Table: 720x300 (half width), 1440x400 (full width)
Chart: 720x300 (half width), 1440x300 (full width)
```

**Spacing**:
- Vertical gap between rows: 20px
- Horizontal gap between columns: 20px

### 색상 코드 (Splunk 기본)

```
Primary:   #007BFF (파랑)
Success:   #65A637 (초록)
Warning:   #F7BC38 (노랑)
Danger:    #D93F3C (빨강)
Info:      #17A2B8 (청록)
Dark:      #2D2D2D (어두운 배경)
Light:     #F5F5F5 (밝은 배경)
```

### Typography

```
Title:       Splunk Platform Sans, 18px, Bold
Subtitle:    Splunk Platform Sans, 14px, Medium
Body:        Splunk Platform Sans, 12px, Regular
Label:       Splunk Platform Sans, 11px, Regular
```

---

## 🔧 고급 사용법

### 1. SPL 쿼리 자동 추출

**Figma Frame Description 작성**:
```
SPL: index=fw devname=*
| stats latest(_time) as last_seen, count by devname
| eval status=if((now()-last_seen)<300, "Connected", "Disconnected")
| table devname, status, count
```

**변환 결과**:
```json
{
  "dataSources": {
    "ds_device_status_table": {
      "type": "ds.search",
      "options": {
        "query": "index=fw devname=* | stats latest(_time) as last_seen, count by devname | eval status=if((now()-last_seen)<300, \"Connected\", \"Disconnected\") | table devname, status, count"
      }
    }
  }
}
```

### 2. 시각화 옵션 커스터마이징

**스크립트 수정** (`scripts/figma-to-dashboard.js`):
```javascript
// Line 105-125: frameToVisualization() 함수

if (vizType === 'splunk.table') {
  visualization.options = {
    count: 50,                    // 행 개수
    dataOverlayMode: 'heatmap',   // 히트맵 오버레이
    drilldown: 'row',             // 드릴다운 활성화
    rowNumbers: true,
    wrap: true
  };
}
```

### 3. 배치 변환 (여러 페이지)

```bash
# 모든 페이지를 순회하며 변환
for page in "Overview" "Security" "Performance"; do
  node scripts/figma-to-dashboard.js abc123xyz "$page"
done
```

### 4. CI/CD 파이프라인 통합

```yaml
# .github/workflows/figma-sync.yml
name: Figma to Dashboard

on:
  schedule:
    - cron: '0 2 * * *'  # 매일 새벽 2시
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Convert Figma to Dashboard
        env:
          FIGMA_API_KEY: ${{ secrets.FIGMA_API_KEY }}
        run: |
          echo "{\"apiKey\":\"$FIGMA_API_KEY\"}" > ~/.mcp-figma/config.json
          node scripts/figma-to-dashboard.js ${{ secrets.FIGMA_FILE_KEY }} "Production Dashboard"

      - name: Deploy to Splunk
        run: node scripts/deploy-dashboards.js
```

---

## 📊 변환 매핑 테이블

| Figma Frame Name Pattern | Dashboard Studio Type | 비고 |
|--------------------------|----------------------|------|
| `*Table` | `splunk.table` | 테이블 시각화 |
| `*Line Chart`, `*Line` | `splunk.line` | 라인 차트 |
| `*Bar Chart`, `*Bar` | `splunk.bar` | 바 차트 |
| `*Column Chart`, `*Column` | `splunk.column` | 컬럼 차트 |
| `*Pie Chart`, `*Pie` | `splunk.pie` | 파이 차트 |
| `*Area Chart`, `*Area` | `splunk.area` | 영역 차트 |
| `*Single Value`, `*Metric` | `splunk.singlevalue` | 단일 값 메트릭 |
| 기타 | `splunk.table` (기본값) | 매칭 실패 시 테이블로 |

---

## 🐛 Troubleshooting

### 1. "Figma API key not found"

**원인**: `~/.mcp-figma/config.json` 파일 없음

**해결**:
```bash
# Figma Personal Access Token 생성
# 1. Figma → Settings → Personal Access Tokens
# 2. Generate new token

# API 키 설정
mkdir -p ~/.mcp-figma
echo '{"apiKey":"figd_YOUR_TOKEN_HERE"}' > ~/.mcp-figma/config.json
```

### 2. "HTTP 403: Forbidden"

**원인**: Figma 파일 접근 권한 없음

**해결**:
- Figma 파일을 "Anyone with the link can view"로 설정
- 또는 Personal Access Token에 해당 팀 접근 권한 부여

### 3. "Page not found"

**원인**: 페이지 이름 오타 또는 대소문자 불일치

**해결**:
```bash
# 사용 가능한 페이지 목록 확인
node scripts/figma-to-dashboard.js abc123xyz "Any"
# Error 메시지에서 "Available pages: ..." 확인
```

### 4. 레이아웃이 겹침

**원인**: Figma에서 Frame이 겹쳐있음

**해결**:
- Figma에서 Frame 위치 조정 (겹치지 않도록)
- 또는 JSON 파일 수정 (`layout.structure[].position`)

### 5. SPL 쿼리 작동 안 함

**원인**: Figma Description에서 SPL 쿼리를 올바르게 추출하지 못함

**해결**:
```bash
# 생성된 JSON 파일 수정
vim configs/dashboards/studio/dashboard-design.json

# dataSources.<ds_id>.options.query 섹션 수정
{
  "dataSources": {
    "ds_example": {
      "options": {
        "query": "index=fw | stats count"  // 여기 수정
      }
    }
  }
}
```

---

## 🎨 예제: Slack Control Dashboard

### Figma 디자인 구조

```
📄 Slack Alert Control (Page)
├── 🖼️ Alert Status Single Value (288x120)
│   └── Description: SPL: | makeresults | eval enabled=6
│
├── 🖼️ Rules Table (1440x400)
│   └── Description: SPL: | makeresults count=6
│       | eval rule=mvindex(split("Correlation_Multi_Factor_Threat_Score,Correlation_Repeated_High_Risk_Events,Correlation_Weak_Signal_Combination,Correlation_Geo_Attack_Pattern,Correlation_Time_Based_Anomaly,Correlation_Cross_Event_Type", ","), 0, $count$-1)
│       | eval status="Enabled"
│       | table rule, status
│
└── 🖼️ Control Buttons (1440x100)
    └── [Markdown 또는 HTML 컴포넌트로 구현]
```

### 변환 실행

```bash
node scripts/figma-to-dashboard.js abc123xyz "Slack Alert Control"
```

### 생성된 JSON

```json
{
  "visualizations": {
    "viz_alert_status_single_value": {
      "type": "splunk.singlevalue",
      "options": {
        "majorValue": "> primary | seriesByName('enabled')",
        "unit": "rules enabled"
      },
      "dataSources": {"primary": "ds_alert_status_single_value"},
      "title": "Alert Status Single Value"
    },
    "viz_rules_table": {
      "type": "splunk.table",
      "options": {
        "count": 20,
        "drilldown": "none",
        "rowNumbers": true
      },
      "dataSources": {"primary": "ds_rules_table"},
      "title": "Rules Table"
    }
  },
  "layout": {
    "structure": [
      {
        "item": "viz_alert_status_single_value",
        "position": {"x": 0, "y": 0, "w": 288, "h": 120}
      },
      {
        "item": "viz_rules_table",
        "position": {"x": 0, "y": 140, "w": 1440, "h": 400}
      }
    ]
  }
}
```

---

## 📚 참고 자료

- **Figma API 문서**: https://www.figma.com/developers/api
- **Dashboard Studio JSON 스키마**: https://docs.splunk.com/Documentation/Splunk/latest/DashStudio/
- **Splunk 색상 팔레트**: https://splunkui.splunk.com/Packages/react-ui/Color
- **Figma Personal Access Token 생성**: https://www.figma.com/developers/api#access-tokens

---

**Version**: 1.0.0
**Last Updated**: 2025-10-24
**Script Location**: `/home/jclee/app/splunk/scripts/figma-to-dashboard.js`
