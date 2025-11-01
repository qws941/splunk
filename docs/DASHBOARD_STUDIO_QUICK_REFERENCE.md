# Dashboard Studio Quick Reference Guide

**Version**: Splunk 9.0+ (Dashboard Studio v2)
**Last Updated**: 2025-10-24

---

## When to Use What

```
Need to MODIFY system configs? ──────────► Simple XML + JavaScript
Need ONLY visualization/filtering? ──────► Dashboard Studio
Need custom actions/webhooks? ───────────► Simple XML + JavaScript
Need beautiful UI, no code? ─────────────► Dashboard Studio
```

---

## 5-Second Decision Tree

```
┌─ Need REST API POST calls?
│  ├─ YES ──► Simple XML
│  └─ NO ──► Continue
│
├─ Need custom JavaScript?
│  ├─ YES ──► Simple XML
│  └─ NO ──► Continue
│
├─ Need to modify saved searches/alerts?
│  ├─ YES ──► Simple XML
│  └─ NO ──► Continue
│
├─ Need advanced visual layout?
│  ├─ YES ──► Dashboard Studio
│  └─ NO ──► Either works
│
└─ Team has JS expertise?
   ├─ YES ──► Simple XML (more flexibility)
   └─ NO ──► Dashboard Studio (easier)
```

---

## Dashboard Studio JSON Structure (30-Second Cheat Sheet)

```json
{
  "visualizations": {
    "viz_id": {
      "type": "splunk.TYPE",           // table, singlevalue, column, line, etc.
      "dataSources": { "primary": "ds_id" },
      "options": { /* styling */ },
      "title": "Panel Title"
    }
  },
  "dataSources": {
    "ds_id": {
      "type": "ds.search",             // or ds.savedSearch, ds.chain
      "options": {
        "query": "index=fortianalyzer | stats count",
        "queryParameters": {
          "earliest": "$time.earliest$",
          "latest": "$time.latest$"
        },
        "refresh": "1m"
      }
    }
  },
  "inputs": {
    "input_id": {
      "type": "input.dropdown",        // or input.text, input.timerange
      "options": {
        "items": [
          { "label": "Option 1", "value": "val1" }
        ],
        "token": "my_token",           // Sets $my_token$
        "defaultValue": "val1"
      }
    }
  },
  "layout": {
    "type": "grid",                    // or "absolute"
    "structure": [ /* positioning */ ]
  }
}
```

---

## Token System (Most Common Patterns)

### Set Token from Input
```json
"inputs": {
  "input_time": {
    "type": "input.timerange",
    "options": {
      "token": "global_time",          // ✅ Sets $global_time.earliest$ and $global_time.latest$
      "defaultValue": "-24h@h,now"
    }
  }
}
```

### Use Token in Search
```json
"options": {
  "query": "index=fortianalyzer earliest=$global_time.earliest$ latest=$global_time.latest$ | stats count",
  "queryParameters": {
    "earliest": "$global_time.earliest$",  // ✅ Proper token substitution
    "latest": "$global_time.latest$"
  }
}
```

### Set Token from Click
```json
"eventHandlers": [
  {
    "type": "drilldown.setToken",
    "options": {
      "tokens": [
        { "token": "selected_ip", "key": "click.value" }  // ✅ $selected_ip$ = clicked value
      ]
    }
  }
]
```

### Predefined Tokens
```
$click.value$       - Clicked cell value
$click.name$        - Column name
$row.fieldname$     - Specific field from clicked row
$env:user$          - Current username
```

---

## Drilldown Actions (5 Types)

### 1. Set Token (Most Common)
```json
"eventHandlers": [
  {
    "type": "drilldown.setToken",
    "options": {
      "tokens": [
        { "token": "selected_value", "key": "click.value" }
      ]
    }
  }
]
```

### 2. Link to Search
```json
{
  "type": "drilldown.openInSearch",
  "options": {
    "q": "index=fortianalyzer src_ip=$click.value$",
    "earliest": "-1h",
    "latest": "now"
  }
}
```

### 3. Link to Custom URL
```json
{
  "type": "drilldown.customUrl",
  "options": {
    "url": "/app/search/details?ip=$row.src_ip$",
    "newTab": true
  }
}
```

### 4. Link to Dashboard
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

### 5. Link to Report
```json
{
  "type": "drilldown.linkToReport",
  "options": {
    "reportId": "my_saved_report"
  }
}
```

---

## Color Coding with `rangeValue()`

```json
"viz_threat_score": {
  "type": "splunk.singlevalue",
  "options": {
    "majorColor": "> majorValue | rangeValue(threatColors)"  // ✅ Dynamic color
  },
  "context": {
    "threatColors": [
      { "value": "#65A637", "to": 50 },              // Green: 0-49
      { "value": "#F7BC38", "from": 50, "to": 80 },  // Yellow: 50-79
      { "value": "#D93F3C", "from": 80 }             // Red: 80+
    ]
  }
}
```

---

## Common Visualization Types

| Type | Use Case | Example |
|------|----------|---------|
| `splunk.singlevalue` | KPIs, metrics | Device count, threat score |
| `splunk.table` | Data lists | Event logs, IP addresses |
| `splunk.column` | Bar charts | Count by category |
| `splunk.line` | Time series | Events over time |
| `splunk.area` | Stacked time series | Multiple metrics trend |
| `splunk.pie` | Proportions | Traffic by protocol |
| `splunk.markdown` | Text/instructions | Dashboard title, help text |

---

## Layout Modes

### Grid Layout (Classic)
```json
"layout": {
  "type": "grid",
  "options": {
    "width": 1440,
    "display": "auto-scale"
  },
  "structure": [
    {
      "item": "viz_id",
      "position": { "x": 0, "y": 0, "w": 720, "h": 300 }
    }
  ]
}
```

### Absolute Layout (Pixel-Perfect)
```json
"layout": {
  "type": "absolute",
  "options": {
    "width": 1440,
    "height": 1200,
    "display": "auto-scale",
    "backgroundImage": { "sizeType": "cover" }
  }
}
```

---

## Data Source Options

### Basic Search
```json
"ds_example": {
  "type": "ds.search",
  "options": {
    "query": "index=fortianalyzer | stats count",
    "refresh": "1m",              // Auto-refresh interval
    "refreshType": "delay"        // "delay" or "interval"
  }
}
```

### Saved Search
```json
"ds_saved": {
  "type": "ds.savedSearch",
  "options": {
    "name": "Correlation_Multi_Factor_Threat_Score",
    "app": "search"               // ✅ Required if saved search in different app
  }
}
```

### Chained Search
```json
"ds_chained": {
  "type": "ds.chain",
  "options": {
    "query": "| stats count by src_ip | sort -count | head 10",
    "extend": "ds_parent_search"  // Builds on another data source
  }
}
```

---

## What Dashboard Studio CAN'T Do ❌

1. ❌ **Custom JavaScript** - No `<script>` tags, no external JS files
2. ❌ **REST API POST** - Cannot modify saved searches, alerts, or configs
3. ❌ **External HTTP calls** - No AJAX, no webhooks, no third-party APIs
4. ❌ **Custom CSS** - No `<style>` tags (use built-in options only)
5. ❌ **iframes** - Not supported (converts to Markdown on import)
6. ❌ **Python scripts** - Cannot trigger alert actions or custom scripts
7. ❌ **KV Store writes via API** - Must use SPL `outputlookup` command
8. ❌ **System modifications** - Cannot enable/disable objects, change configs

---

## What Dashboard Studio CAN Do ✅

1. ✅ **Advanced layouts** - Grid + Absolute positioning, background images
2. ✅ **Token-based filtering** - Dynamic searches based on user input
3. ✅ **Drilldown navigation** - Link to dashboards, searches, reports, URLs
4. ✅ **Color coding** - `rangeValue()` for conditional formatting
5. ✅ **SPL data manipulation** - Full SPL support including `outputlookup`
6. ✅ **Visual customization** - Colors, fonts, spacing (no code needed)
7. ✅ **Conditional visibility** - Show/hide panels based on tokens
8. ✅ **Auto-refresh** - Configurable refresh intervals per data source

---

## SPL Commands Available in Dashboard Studio

### Read Data
```spl
| rest /services/saved/searches           ✅ Read-only REST API
| inputlookup slack_alert_toggle          ✅ Read KV Store
| tstats count WHERE index=fortianalyzer             ✅ Fast stats
```

### Write Data
```spl
| outputlookup slack_alert_toggle         ✅ Write to KV Store
| collect index=summary_fw                ✅ Write to summary index
```

### NOT Available
```spl
| rest /services/saved/searches POST      ❌ Cannot POST via SPL
| sendalert slack                         ❌ Cannot trigger alert actions
| script python my_script.py              ❌ No custom scripts
```

---

## Performance Tips

### 1. Use `tstats` for Fast Queries
```spl
# ❌ SLOW (full index scan)
index=fortianalyzer | stats count by src_ip

# ✅ FAST (uses data model acceleration)
| tstats count WHERE datamodel=Fortinet_Security.Security_Events BY Security_Events.src_ip
```

### 2. Limit Search Time Ranges
```json
"queryParameters": {
  "earliest": "-1h",    // ✅ Not "-24h" or "alltime"
  "latest": "now"
}
```

### 3. Use Summary Indexes
```spl
# ❌ SLOW (recalculate every refresh)
index=fortianalyzer earliest=-24h | stats count by src_ip | where count > 100

# ✅ FAST (pre-calculated hourly)
index=summary_fw marker="correlation_detection=*" | stats sum(count) as count by src_ip
```

### 4. Optimize Refresh Intervals
```json
"refresh": "5m",      // ✅ Reasonable for stats
"refresh": "30s",     // ⚠️ Only for critical real-time data
"refresh": "1h",      // ✅ Good for historical trends
```

---

## Common Mistakes

### 1. Forgetting `.earliest` and `.latest` for Time Ranges
```json
// ❌ WRONG
"queryParameters": {
  "earliest": "$global_time$",   // Invalid
  "latest": "$global_time$"
}

// ✅ CORRECT
"queryParameters": {
  "earliest": "$global_time.earliest$",
  "latest": "$global_time.latest$"
}
```

### 2. Using SPL in `query` Instead of `queryParameters`
```json
// ❌ WRONG (tokens won't substitute)
"query": "index=fortianalyzer earliest=$time$ | stats count"

// ✅ CORRECT (tokens in queryParameters)
"query": "index=fortianalyzer | stats count",
"queryParameters": {
  "earliest": "$time.earliest$"
}
```

### 3. Trying to Execute REST API Modifications
```json
// ❌ NOT POSSIBLE in Dashboard Studio
"query": "| rest /services/saved/searches/MySearch POST disabled=1"
```

**Solution**: Use Simple XML with JavaScript for REST API modifications.

---

## Troubleshooting

### Dashboard Doesn't Load
```bash
# Check dashboard syntax
splunk btool --debug dashboards list

# Validate JSON
jq empty configs/dashboards/studio/my-dashboard.json
```

### Tokens Not Substituting
```spl
# Test token value
| makeresults | eval test="$my_token$"
```

### Data Source Not Refreshing
```json
// Verify refresh configuration
"refresh": "1m",
"refreshType": "delay",  // Not "interval" for most cases
```

---

## Quick Start Template

```json
{
  "visualizations": {
    "viz_metric": {
      "type": "splunk.singlevalue",
      "dataSources": { "primary": "ds_main" },
      "options": {
        "majorValue": "> primary | seriesByName('count')",
        "unit": "events"
      },
      "title": "Total Events"
    }
  },
  "dataSources": {
    "ds_main": {
      "type": "ds.search",
      "options": {
        "query": "index=fortianalyzer | stats count",
        "queryParameters": {
          "earliest": "$global_time.earliest$",
          "latest": "$global_time.latest$"
        },
        "refresh": "1m",
        "refreshType": "delay"
      }
    }
  },
  "inputs": {
    "input_time": {
      "type": "input.timerange",
      "options": {
        "token": "global_time",
        "defaultValue": "-24h@h,now"
      },
      "title": "Time Range"
    }
  },
  "layout": {
    "type": "grid",
    "options": { "width": 1440 },
    "structure": [
      {
        "item": "viz_metric",
        "position": { "x": 0, "y": 0, "w": 720, "h": 300 }
      }
    ],
    "globalInputs": ["input_time"]
  },
  "title": "My Dashboard",
  "description": "Dashboard description"
}
```

---

## Official Resources

1. **Dashboard Studio Docs**: https://docs.splunk.com/Documentation/Splunk/latest/DashStudio
2. **Token Reference**: https://docs.splunk.com/Documentation/Splunk/latest/DashStudio/tokens
3. **Drilldown Guide**: https://www.splunk.com/en_us/blog/tips-and-tricks/dashboard-studio-drilldown-to-new-features-in-splunk-cloud-platform-9-0-2305.html
4. **REST API Endpoints**: https://docs.splunk.com/Documentation/Splunk/latest/DashStudio/RESTusage

---

**Version**: 1.0 (Splunk 9.0+)
**Compatibility**: Splunk Enterprise 9.0+, Splunk Cloud 9.0.2305+
**Last Updated**: 2025-10-24
