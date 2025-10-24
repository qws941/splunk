# Splunk Dashboard Studio Research: Capabilities & Limitations

**Research Date**: 2025-10-24
**Focus**: Slack Alert Control Implementation in Dashboard Studio vs Simple XML
**Verdict**: **Simple XML is the only viable option for REST API-based Slack alert control**

---

## Executive Summary

Dashboard Studio **CANNOT** make REST API calls to modify saved searches or trigger custom actions via HTTP POST requests. The framework is designed for **visualization and token-based interactivity only**, not external API integrations or system modifications.

**For Slack alert ON/OFF controls that modify saved search configurations, you MUST use Simple XML with custom JavaScript.**

---

## 1. Dashboard Studio JSON Structure

### Core Components (5 Sections)

```json
{
  "visualizations": {},  // UI components (charts, tables, single values)
  "dataSources": {},     // SPL searches and data queries
  "inputs": {},          // User input controls (dropdown, text, time range)
  "defaults": {},        // Default values and settings
  "layout": {}           // Positioning and layout (grid or absolute)
}
```

**Key Characteristics**:
- JSON-formatted stanzas (not XML)
- Version 2 framework (`<dashboard version="2">` in XML wrapper)
- Two layout modes: **Grid** (classic) and **Absolute** (pixel-precise positioning)
- Source editor available for direct JSON editing
- No custom JavaScript/CSS support (major limitation)

### Visualization Types

```json
"visualizations": {
  "viz_example": {
    "type": "splunk.singlevalue",  // Built-in types only
    "dataSources": { "primary": "ds_search" },
    "options": {
      "majorValue": "> primary | seriesByName('count')",
      "majorColor": "> majorValue | rangeValue(colorConfig)"
    },
    "context": { /* color thresholds, etc */ }
  }
}
```

**Available Types**: `splunk.table`, `splunk.singlevalue`, `splunk.column`, `splunk.line`, `splunk.markdown`, `splunk.area`, `splunk.pie`, etc.

### Data Sources

```json
"dataSources": {
  "ds_example": {
    "type": "ds.search",  // or ds.savedSearch, ds.chain
    "options": {
      "query": "index=fw | stats count",
      "queryParameters": {
        "earliest": "$global_time.earliest$",  // Token usage
        "latest": "$global_time.latest$"
      },
      "refresh": "1m",
      "refreshType": "delay"  // or "interval"
    }
  }
}
```

**Types**:
- `ds.search` - Ad-hoc SPL query
- `ds.savedSearch` - Call existing saved search
- `ds.chain` - Chain multiple searches

---

## 2. Input Controls & Token System

### Available Input Types

| Type | Purpose | Example |
|------|---------|---------|
| `input.dropdown` | Select from predefined options | Alert ON/OFF toggle |
| `input.text` | Free text input | Threshold values |
| `input.timerange` | Time picker | Global time range |
| `input.radio` | Radio button selection | Mode selection |
| `input.multiselect` | Multiple selections | Multi-filter |

### Token-Based Interaction

```json
"inputs": {
  "input_slack_toggle": {
    "type": "input.dropdown",
    "options": {
      "items": [
        { "label": "🟢 ON", "value": "enabled" },
        { "label": "🔴 OFF", "value": "disabled" }
      ],
      "defaultValue": "enabled",
      "token": "slack_status"  // ✅ Sets $slack_status$ token
    },
    "title": "Slack Alerts"
  }
}
```

**Token Usage in Searches**:
```spl
index=fw status=$slack_status$  /* Token substitution */
| where enabled="$slack_status$"
```

**Predefined Tokens** (Splunk 9.3+):
- `$click.value$` - Clicked cell value
- `$click.name$` - Column name
- `$row.<fieldname>$` - Row field values

### Token Limitations

❌ **What Tokens CANNOT Do**:
- Trigger REST API calls
- Execute Python scripts
- Modify saved search configurations
- Send HTTP POST requests
- Run external commands
- Update KV Store directly (must use SPL `outputlookup`)

✅ **What Tokens CAN Do**:
- Filter search results
- Control visualization display
- Update other inputs
- Set search parameters
- Write to KV Store via SPL commands

---

## 3. Drilldown Actions (Splunk 9.0.2305+)

Dashboard Studio supports **5 drilldown types** (added in 2023):

### 1. Set Token
```json
"eventHandlers": [
  {
    "type": "drilldown.setToken",
    "options": {
      "tokens": [
        { "token": "selection_tok", "key": "click.value" }
      ]
    }
  }
]
```

### 2. Link to Custom URL
```json
{
  "type": "drilldown.customUrl",
  "options": {
    "url": "/app/search/search?q=index=fw ip=$row.src_ip$",
    "newTab": true
  }
}
```

### 3. Link to Dashboard
```json
{
  "type": "drilldown.linkToDashboard",
  "options": {
    "app": "search",
    "dashboard": "details_dashboard",
    "newTab": false
  }
}
```

### 4. Link to Report
```json
{
  "type": "drilldown.linkToReport",
  "options": {
    "reportId": "my_saved_report"
  }
}
```

### 5. Link to Search
```json
{
  "type": "drilldown.openInSearch",
  "options": {
    "q": "index=fw src_ip=$click.value$",
    "earliest": "-1h",
    "latest": "now"
  }
}
```

### Critical Limitation

❌ **NO "Execute Custom Action" Drilldown Type**
There is **NO** drilldown type for:
- Triggering REST API calls
- Running custom Python/JavaScript
- Modifying system configurations
- Sending webhook notifications

---

## 4. REST API Interaction - THE CRITICAL LIMITATION

### What Dashboard Studio CAN Do with REST API

✅ **Via SPL `rest` Command** (Read-only queries):
```spl
| rest /services/saved/searches
| search title="Correlation_*"
| table title, disabled, cron_schedule
```

✅ **Read saved search status**:
```json
"dataSources": {
  "ds_savedsearch_status": {
    "type": "ds.search",
    "options": {
      "query": "| rest /services/saved/searches | search title=\"Slack_Alert_Rule_1\" | table disabled"
    }
  }
}
```

### What Dashboard Studio CANNOT Do

❌ **Modify saved searches via REST API**:
```javascript
// ❌ NOT POSSIBLE in Dashboard Studio
POST /services/saved/searches/Slack_Alert_Rule_1
{
  "disabled": "1"  // Cannot execute this
}
```

❌ **Execute custom JavaScript**:
```javascript
// ❌ NOT SUPPORTED
require(['splunkjs/mvc', 'jquery'], function(mvc, $) {
  $.ajax({
    url: '/services/saved/searches/MySearch',
    type: 'POST',
    data: { disabled: 1 }
  });
});
```

❌ **Custom action handlers**:
- No `<script>` tag support
- No external JavaScript file loading
- No custom event handlers
- No jQuery/AJAX calls

---

## 5. Limitations Summary

### Dashboard Studio vs Simple XML Feature Comparison

| Feature | Dashboard Studio | Simple XML |
|---------|-----------------|------------|
| **Custom JavaScript** | ❌ Not supported | ✅ Full support |
| **Custom CSS** | ❌ Not supported | ✅ Full support |
| **REST API POST** | ❌ Not possible | ✅ Via JavaScript |
| **External HTTP Calls** | ❌ Not possible | ✅ Via JavaScript |
| **Token System** | ✅ Advanced (9.0+) | ✅ Basic (`$form.token$`) |
| **Drilldown Actions** | ✅ 5 types (9.0.2305+) | ✅ Unlimited (custom JS) |
| **Layout Control** | ✅ Grid + Absolute | ⚠️ Grid only |
| **Visual Customization** | ✅ No code needed | ⚠️ Requires CSS |
| **Background Images** | ✅ Native support | ⚠️ Requires CSS |
| **Conditional Show/Hide** | ✅ Token eval | ✅ `depends` attribute |
| **KV Store Updates** | ✅ Via SPL only | ✅ SPL + REST API |
| **Saved Search Modification** | ❌ Not possible | ✅ Via REST API |
| **Python Script Execution** | ❌ Not possible | ✅ Via alert actions |
| **Webhook Triggers** | ❌ Not possible | ✅ Via JavaScript |

### Key Architectural Differences

**Dashboard Studio Philosophy**:
- **Declarative** UI framework (JSON configuration)
- **Sandboxed** environment (no custom code execution)
- **Token-driven** interactions (data filtering only)
- **SPL-centric** data manipulation
- **Security-first** design (prevents arbitrary code execution)

**Simple XML Philosophy**:
- **Hybrid** framework (XML + JavaScript + CSS)
- **Extensible** via custom code
- **Event-driven** interactions (full DOM access)
- **REST API** access for system modifications
- **Flexibility-first** design (full control over behavior)

---

## 6. Slack Alert Control Implementation Analysis

### Requirement
Toggle Slack notifications ON/OFF for correlation rules by modifying saved search `disabled` attribute via dashboard controls.

### Option 1: Dashboard Studio Approach ❌ NOT VIABLE

**Attempt 1: Drilldown to Custom URL (Workaround)**
```json
{
  "type": "drilldown.customUrl",
  "options": {
    "url": "/en-US/manager/search/saved/searches/Correlation_Rule_1?action=disable",
    "newTab": false
  }
}
```

**Problems**:
- Opens Splunk Web UI manager page (not an API call)
- Requires manual user interaction (not automated)
- No direct REST API execution
- Cannot pass authentication headers

**Attempt 2: SPL `rest` Command (Read-only)**
```spl
| rest /services/saved/searches/Correlation_Rule_1
| eval disabled=1
| outputlookup slack_toggle_state
```

**Problems**:
- `rest` command is **read-only** (cannot POST/modify)
- `outputlookup` only writes to KV Store (not saved search configs)
- Saved search reads toggle state, but manual reconfiguration needed

**Attempt 3: Markdown Panel with Hardcoded Links** (Current Implementation)
```json
{
  "type": "splunk.markdown",
  "options": {
    "markdown": "[Enable](/app/search/search?q=| makeresults | outputlookup...)"
  }
}
```

**Problems**:
- Links open new search window (not inline action)
- No visual feedback (button doesn't update)
- Poor UX (user must click → wait → return to dashboard)
- No REST API modification (just KV Store state tracking)

### Option 2: Simple XML + JavaScript ✅ VIABLE

**Implementation**:
```xml
<dashboard>
  <row>
    <panel>
      <input type="dropdown" token="slack_toggle">
        <label>Slack Alerts</label>
        <choice value="enabled">ON</choice>
        <choice value="disabled">OFF</choice>
        <change>
          <eval token="form.slack_toggle">$value$</eval>
        </change>
      </input>
    </panel>
  </row>

  <row depends="$alwaysHiddenCondition$">
    <panel>
      <html>
        <script>
          require(['splunkjs/mvc', 'jquery', 'splunkjs/mvc/simplexml/ready!'],
          function(mvc, $) {
            var tokens = mvc.Components.get('default');

            tokens.on('change:slack_toggle', function(model, value) {
              var service = mvc.createService();
              var savedSearches = service.savedSearches();

              savedSearches.fetch(function(err, searches) {
                var search = searches.item('Correlation_Multi_Factor_Threat_Score');
                search.update({
                  'disabled': (value === 'disabled') ? '1' : '0'
                }, function(err) {
                  if (!err) {
                    console.log('✅ Saved search updated');
                    alert('Slack alerts ' + value);
                  }
                });
              });
            });
          });
        </script>
      </html>
    </panel>
  </row>
</dashboard>
```

**Why This Works**:
- ✅ JavaScript has full REST API access (`splunkjs.Service`)
- ✅ `savedSearches().update()` modifies saved search configs
- ✅ Inline execution (no page navigation)
- ✅ Immediate feedback (alert confirmation)
- ✅ Token-driven (reactive updates)

---

## 7. Best Practices & Recommendations

### When to Use Dashboard Studio

✅ **Use Dashboard Studio if**:
- Dashboard is **visualization-only** (charts, tables, metrics)
- Interactions are **token-based filtering** (no system modifications)
- Requires **advanced layouts** (absolute positioning, backgrounds)
- Team lacks JavaScript/CSS expertise
- Security requires **sandboxed environment**

### When to Use Simple XML

✅ **Use Simple XML if**:
- Dashboard needs **REST API calls** (modify configs, trigger webhooks)
- Requires **custom JavaScript** (AJAX, DOM manipulation)
- Needs **external integrations** (third-party APIs)
- Advanced **form validation** or **multi-step workflows**
- **System administration** functions (enable/disable objects)

### Hybrid Approach (Not Recommended)

⚠️ **Mixing frameworks**:
- Dashboard Studio for main monitoring dashboard
- Simple XML for control panel (Slack toggle)
- **Problem**: Inconsistent UX, double maintenance

**Better**: Pick one framework and stick with it for related dashboards.

---

## 8. Token Usage Best Practices

### Setting Default Values

```json
"defaults": {
  "tokens": {
    "global_time.earliest": "-24h@h",
    "global_time.latest": "now",
    "slack_status": "enabled"
  }
}
```

### Token Eval (Conditional Logic)

```json
"options": {
  "majorColor": "> majorValue | rangeValue(colorConfig)"
}
```

**`rangeValue()` function**:
```json
"context": {
  "colorConfig": [
    { "value": "#65A637", "to": 70 },
    { "value": "#F7BC38", "from": 70, "to": 85 },
    { "value": "#D93F3C", "from": 85 }
  ]
}
```

### Search Result Tokens (Advanced)

```json
"options": {
  "queryParameters": {
    "enableSearchResultsToken": true
  }
}
```

**Access via**:
```
$ds_example.results.count$
$ds_example.job.sid$
```

---

## 9. Conversion from Simple XML

**Splunk Conversion Tool**: Settings → Dashboards → Convert to Dashboard Studio

**What Converts Successfully**:
- ✅ Basic visualizations (tables, charts, single values)
- ✅ Simple tokens (`$form.token$` → `$token$`)
- ✅ Drilldowns (limited)
- ✅ Time ranges

**What FAILS Conversion**:
- ❌ Custom JavaScript (`<script>` tags)
- ❌ Custom CSS (`<style>` tags)
- ❌ iframes (converted to Markdown with source code)
- ❌ HTML panels with dynamic content
- ❌ Complex event handlers

**Recommendation**: For Slack alert control dashboard, **DO NOT convert** from Simple XML.

---

## 10. Official Documentation References

1. **Dashboard Studio Overview**
   https://docs.splunk.com/Documentation/Splunk/latest/DashStudio/CreateDash

2. **Dashboard Definition (JSON Schema)**
   https://docs.splunk.com/Documentation/Splunk/9.4.0/DashStudio/dashDef

3. **Token System**
   https://docs.splunk.com/Documentation/Splunk/9.3.1/DashStudio/tokens

4. **Drilldown Actions**
   https://www.splunk.com/en_us/blog/tips-and-tricks/dashboard-studio-drilldown-to-new-features-in-splunk-cloud-platform-9-0-2305.html

5. **REST API Endpoints**
   https://docs.splunk.com/Documentation/Splunk/9.4.2/DashStudio/RESTusage

6. **Conversion Guide**
   https://docs.splunk.com/Documentation/Splunk/9.4.2/DashStudio/ConvertSXML

---

## 11. Conclusion & Decision

### For Slack Alert ON/OFF Control Dashboard

**Verdict**: **Use Simple XML with Custom JavaScript**

**Reasoning**:
1. ❌ Dashboard Studio **cannot modify saved searches** via REST API
2. ❌ Dashboard Studio **cannot execute custom HTTP POST** requests
3. ❌ Dashboard Studio **drilldowns are limited** to navigation/tokens
4. ✅ Simple XML **has full REST API access** via JavaScript SDK
5. ✅ Simple XML **can update saved search configs** directly
6. ✅ Simple XML **provides immediate feedback** without page navigation

### Implementation Path

```
Current State:
  - configs/dashboards/slack-alert-control.xml (Simple XML)
  - Uses custom JavaScript for REST API calls
  - Modifies saved search 'disabled' attribute directly

Recommendation:
  ✅ KEEP Simple XML implementation
  ❌ DO NOT migrate to Dashboard Studio
  ⚠️ Dashboard Studio version can display status only (read-only)
```

### Alternative: Hybrid Read/Write Pattern

**Dashboard Studio** (Read-only monitoring):
- Display current Slack alert status
- Show toggle history from KV Store
- Visualize alert statistics

**Simple XML** (Control panel):
- Toggle buttons with REST API calls
- Modify saved search configurations
- Update KV Store state

**Trade-off**: UX inconsistency, double maintenance burden.

---

## 12. Code Examples Reference

See existing implementations:
- **Simple XML**: `/home/jclee/app/splunk/configs/dashboards/slack-alert-control.xml`
- **Dashboard Studio (read-only)**: `/home/jclee/app/splunk/configs/dashboards/studio/correlation-analysis-studio.json`
- **Markdown workaround**: `/home/jclee/app/splunk/configs/dashboards/archive-legacy/slack-toggle-control.json`

**Key Insight**: All Dashboard Studio attempts rely on **workarounds** (Markdown links, KV Store state tracking) because the framework fundamentally **cannot execute REST API modifications**.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-24
**Research Status**: Complete
**Recommendation**: Use Simple XML for Slack alert control (REST API requirement)
