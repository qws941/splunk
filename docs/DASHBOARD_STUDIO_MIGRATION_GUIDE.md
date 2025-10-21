# Dashboard Studio Migration Guide

**Purpose**: Guide for migrating FortiGate Security Dashboard from Simple XML to Dashboard Studio to enable custom visualizations (Sankey, Heatmap, Geo Map).

**Current State**: Simple XML Dashboard (Classic)
**Target State**: Dashboard Studio (Modern)

---

## 🎯 Why Dashboard Studio?

### Limitations of Simple XML (Current):
- ❌ No custom visualization support (Sankey, Heatmap, Geo)
- ❌ Limited layout flexibility
- ❌ No drag-and-drop editor
- ❌ Limited styling options
- ❌ No real-time collaboration

### Benefits of Dashboard Studio:
- ✅ Custom visualizations (100+ types)
- ✅ Advanced layout control (Grid system)
- ✅ Visual drag-and-drop editor
- ✅ Rich styling and themes
- ✅ Better performance optimization
- ✅ Future-proof (Splunk's modern platform)

---

## 🔍 Current Dashboard Analysis

### Dashboard Metrics:
- **Format**: Simple XML (`<dashboard>`)
- **Panels**: 28 (5 rows of metrics, 4 MITRE panels, alerts)
- **Visualizations**: single (9), table (8), chart (6)
- **Size**: 22KB XML
- **Complexity**: Medium (base search pattern, lookups, drill-downs)

### Components to Migrate:
| Component | Count | Dashboard Studio Support |
|-----------|-------|-------------------------|
| Base Search | 1 | ✅ Data Sources |
| Single Value Panels | 9 | ✅ Single Value Viz |
| Tables | 8 | ✅ Table Viz |
| Charts (Pie, Area, Column, Bar) | 6 | ✅ Chart Viz |
| HTML Panels | 5 | ✅ Text Viz |
| Time Picker | 1 | ✅ Global Input |
| Device Filter | 1 | ✅ Global Input |
| Drill-downs | 4 | ✅ Drill-down Actions |

**Migration Complexity**: Medium (2-3 days effort)

---

## 🚀 Migration Strategy

### Phase 1: Preparation (1 day)

1. **Enable Dashboard Studio**:
   ```bash
   # Check Splunk version (Dashboard Studio requires 9.0+)
   $SPLUNK_HOME/bin/splunk version

   # Enable Dashboard Studio feature
   # Splunk Web → Settings → User Interface → Navigation Menus
   # Enable "Dashboard Studio"
   ```

2. **Backup Current Dashboard**:
   ```bash
   cp dashboards/fortinet-dashboard.xml dashboards/fortinet-dashboard.xml.backup-pre-studio
   ```

3. **Export Dashboard Data**:
   ```bash
   # Extract all SPL queries
   grep -A 10 "<query>" dashboards/fortinet-dashboard.xml > /tmp/dashboard-queries.txt

   # Extract panel configurations
   grep -A 5 "<title>" dashboards/fortinet-dashboard.xml > /tmp/dashboard-panels.txt
   ```

---

### Phase 2: Manual Migration (2 days)

#### Step 1: Create New Dashboard Studio Dashboard

**Splunk Web UI**:
1. Navigate to **Dashboards** → **Create New Dashboard**
2. Select **Dashboard Studio** (NOT Classic Dashboard)
3. Name: `FortiGate Security Dashboard (Studio)`
4. Save as: `fortinet_dashboard_studio`

#### Step 2: Configure Data Source (Base Search)

**Dashboard Studio UI**:
1. Click **Edit** → **Data Sources**
2. Add **New Data Source**:
   - Name: `base_fw_search`
   - Query: (Copy from Simple XML)
   ```spl
   index=fw devname=$device_filter$
   | fields _time, devname, level, action, logid, msg, srcip, dstip,
         srcport, dstport, protocol, app, user, bytes,
         cpu, mem, session, srcintf, dstintf,
         cfgpath, cfgobj, cfgattr
   | eval severity_level = case(
       level="critical" OR level="emergency" OR level="alert", "critical",
       level="high" OR level="error" OR level="warning", "high",
       level="medium" OR level="notice", "medium",
       1=1, "low"
     )
   | eval event_category = case(
       action="deny" OR action="block" OR action="drop", "blocked",
       action="allow" OR action="accept", "allowed",
       1=1, "other"
     )
   | eval config_change_type = case(
       logid="0100044547", "Deleted",
       logid="0100044546", "Edited",
       logid="0100044545", "Added",
       1=1, null()
     )
   ```
   - Time Range: Use Global Time Input `$time_picker$`

#### Step 3: Add Global Inputs

**Dashboard Studio UI**:
1. Click **Add Input** → **Time Range**
   - Token: `time_picker`
   - Default: Last 24 hours

2. Click **Add Input** → **Dropdown**
   - Token: `device_filter`
   - Label: "Device Filter"
   - Options: `*` (All), specific devices
   - Search: `index=fw | stats count by devname`

#### Step 4: Migrate Panels (Example: Critical Events)

**Simple XML** (Original):
```xml
<panel>
  <title>🔴 Critical Events</title>
  <single>
    <search base="base_fw_search">
      <query>
        search (level=critical OR level=alert)
        | stats count
      </query>
    </search>
  </single>
</panel>
```

**Dashboard Studio** (Migrated):
1. **Add Visualization** → **Single Value**
2. **Configure**:
   - Title: `🔴 Critical Events`
   - Data Source: `base_fw_search | search (level=critical OR level=alert) | stats count`
   - Number Format: Integer
   - Color: Red (#DC143C) if count > 0
   - Drill-down: Link to search

#### Step 5: Add Custom Visualizations

**Now Available in Dashboard Studio**:

##### Sankey Diagram (Traffic Flow):
```json
{
  "type": "viz.sankey",
  "options": {
    "linkColor": "gradient",
    "nodeWidth": 15,
    "nodePadding": 10
  },
  "dataSources": {
    "primary": "base_fw_search | stats sum(bytes) as Bytes by srcip, dstip | head 20"
  }
}
```

##### Heatmap (Attack Timeline):
```json
{
  "type": "viz.heatmap",
  "options": {
    "colorMode": "sequential",
    "colorPalette": "red"
  },
  "dataSources": {
    "primary": "base_fw_search | where severity_level IN (\"critical\", \"high\") | timechart span=1h count by level"
  }
}
```

##### Geographic Map (Attack Source):
```json
{
  "type": "viz.choropleth.svg",
  "options": {
    "svg": "world_countries",
    "colorMode": "sequential"
  },
  "dataSources": {
    "primary": "base_fw_search | iplocation srcip | geostats count by Country"
  }
}
```

---

### Phase 3: Testing & Validation (Half day)

#### Validation Checklist:
- [ ] All 28 panels migrated
- [ ] Base search functioning
- [ ] Time picker working
- [ ] Device filter working
- [ ] Drill-downs operational
- [ ] MITRE lookup integration
- [ ] Custom visualizations rendering
- [ ] Performance acceptable (<3s load)
- [ ] WCAG AA compliance maintained

#### Performance Testing:
```spl
# Compare load times
| rest /services/search/jobs
| search label="*fortinet_dashboard*"
| stats avg(runDuration) as avg_load by label
| sort - avg_load
```

Expected: Dashboard Studio ≤ Simple XML load time

---

## 📊 Feature Comparison

| Feature | Simple XML | Dashboard Studio |
|---------|------------|------------------|
| **Sankey Diagram** | ❌ | ✅ |
| **Heatmap** | ❌ | ✅ |
| **Geo Map** | ❌ | ✅ |
| **Drag-and-Drop Editor** | ❌ | ✅ |
| **Grid Layout** | ❌ | ✅ |
| **Responsive Design** | Limited | ✅ |
| **Theme Support** | Limited | ✅ |
| **Version Control** | XML | JSON |
| **Export Format** | XML | JSON |
| **Learning Curve** | Low | Medium |

---

## 🔧 Dashboard Studio JSON Structure

**Example Dashboard Definition**:
```json
{
  "visualizations": {
    "viz_critical_events": {
      "type": "viz.singlevalue",
      "title": "🔴 Critical Events",
      "dataSources": {
        "primary": "ds_base_fw_search_critical"
      },
      "options": {
        "majorValue": "> sparklineValues | lastPoint()",
        "trendValue": "> sparklineValues | delta(-2)",
        "numberPrecision": 0,
        "majorColor": "#DC143C"
      }
    }
  },
  "dataSources": {
    "ds_base_fw_search": {
      "type": "ds.search",
      "options": {
        "query": "index=fw devname=$device_filter$ | ...",
        "earliest": "$time_picker.earliest$",
        "latest": "$time_picker.latest$"
      }
    }
  },
  "inputs": {
    "input_time_picker": {
      "type": "input.timerange",
      "options": {
        "token": "time_picker",
        "defaultValue": "-24h,now"
      }
    }
  },
  "layout": {
    "type": "absolute",
    "options": {
      "width": 1440,
      "height": 2000
    }
  }
}
```

---

## ⚠️ Migration Risks & Mitigation

### Risk 1: Feature Parity
**Risk**: Some Simple XML features may not have exact equivalents
**Mitigation**: Test each panel thoroughly, use workarounds documented in Splunk docs

### Risk 2: Performance Regression
**Risk**: Dashboard Studio may be slower initially
**Mitigation**: Optimize data sources, use search acceleration

### Risk 3: User Adoption
**Risk**: Users familiar with Simple XML may resist change
**Mitigation**: Run both dashboards side-by-side during transition period

### Risk 4: Custom SPL Compatibility
**Risk**: Complex SPL queries may need adjustment
**Mitigation**: Test all queries in Search app before migrating

---

## 🚀 Deployment Plan

### Week 1: Preparation
- Day 1: Enable Dashboard Studio, backup current dashboard
- Day 2: Extract and document all SPL queries
- Day 3: Create Dashboard Studio dashboard shell
- Day 4: Configure data sources and global inputs
- Day 5: Testing and validation

### Week 2: Panel Migration
- Day 1-2: Migrate Row 1-3 panels (metrics, events)
- Day 3: Migrate Row 4 (MITRE ATT&CK panels)
- Day 4: Add custom visualizations (Sankey, Heatmap, Geo)
- Day 5: Testing and bug fixes

### Week 3: Validation & Deployment
- Day 1-2: User acceptance testing
- Day 3: Performance optimization
- Day 4: Documentation updates
- Day 5: Production deployment

---

## 📚 Resources

### Splunk Documentation
- [Dashboard Studio Overview](https://docs.splunk.com/Documentation/SplunkCloud/latest/DashStudio/IntroFrame)
- [Migrate Classic to Studio](https://docs.splunk.com/Documentation/SplunkCloud/latest/DashStudio/migration)
- [Custom Visualizations](https://docs.splunk.com/Documentation/SplunkCloud/latest/DashStudio/visualizations)

### Example Dashboards
- [Dashboard Studio Examples (GitHub)](https://github.com/splunk/dashboard-studio-resources)
- [Security Dashboard Templates](https://splunkbase.splunk.com/apps/#/category/security)

### Training
- Splunk .conf23 - Dashboard Studio Deep Dive
- Splunk Education - Dashboard Studio Fundamentals

---

## ✅ Success Criteria

Migration is successful when:
- ✅ All 28 panels functional in Dashboard Studio
- ✅ Custom visualizations (Sankey, Heatmap, Geo) working
- ✅ Performance ≤ Simple XML baseline
- ✅ WCAG AA compliance maintained
- ✅ User acceptance achieved
- ✅ Drill-downs and interactions working
- ✅ MITRE lookup integration functional

---

## 📝 Rollback Plan

If migration fails:
1. Restore Simple XML dashboard from backup
2. Disable Dashboard Studio dashboard
3. Document issues encountered
4. Plan remediation for next attempt

```bash
# Rollback command
cp dashboards/fortinet-dashboard.xml.backup-pre-studio dashboards/fortinet-dashboard.xml
# Splunk Web → Dashboards → Delete "FortiGate Security Dashboard (Studio)"
```

---

**Status**: 📄 Documentation Ready
**Effort**: 2-3 days (experienced Splunk admin)
**Recommendation**: Schedule migration during low-traffic period
**Support**: Contact Splunk Support if complex issues arise

---

**Author**: Claude Code
**Date**: 2025-10-21
**Version**: 1.0.0
