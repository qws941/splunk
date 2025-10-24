# Slack Alert Control Dashboard

## Overview

Simple XML dashboard for controlling Slack notifications on correlation detection rules. Allows operators to enable/disable alerts without modifying saved search configurations manually.

## Features

- ✅ **Enable/Disable All**: Bulk control for all 6 correlation rules
- 🎯 **Individual Control**: Toggle each rule independently
- 📊 **Real-time Status**: Live display of current alert states
- 🔄 **Auto-refresh**: Reload button to sync latest status

## Deployment

### Method 1: Splunk Web UI (Recommended)

1. Navigate to **Settings → User Interface → Views**
2. Click **New View**
3. Upload `configs/dashboards/slack-control.xml`
4. Set **App**: `search` (or your correlation rules app)
5. Set **Permissions**: Shared in App, Read access for role `power`

### Method 2: REST API

```bash
# Deploy dashboard via REST API
curl -k -u admin:password \
  -d "eai:data=$(cat configs/dashboards/slack-control.xml)" \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/slack_control
```

### Method 3: File System Copy

```bash
# Copy to Splunk app directory
sudo cp configs/dashboards/slack-control.xml \
  /opt/splunk/etc/apps/search/local/data/ui/views/slack_control.xml

# Restart Splunk
sudo /opt/splunk/bin/splunk restart
```

## Controlled Correlation Rules

This dashboard controls the `action.slack` parameter for:

1. **Correlation_Multi_Factor_Threat_Score** - Multi-factor threat scoring
2. **Correlation_Repeated_High_Risk_Events** - Repeated high-risk event detection
3. **Correlation_Weak_Signal_Combination** - Weak signal aggregation
4. **Correlation_Geo_Attack_Pattern** - Geographic attack pattern analysis
5. **Correlation_Time_Based_Anomaly** - Time-based anomaly detection
6. **Correlation_Cross_Event_Type** - Cross-event type correlation

## How It Works

### REST API Calls

**Get Current Status:**
```
GET /en-US/splunkd/__raw/servicesNS/nobody/search/saved/searches/{rule_name}
```

**Update Alert Setting:**
```
POST /en-US/splunkd/__raw/servicesNS/nobody/search/saved/searches/{rule_name}
Data: action.slack=1  (enable) or action.slack=0 (disable)
```

### JavaScript Implementation

- Uses **jQuery** and **Splunk SDK** for REST API calls
- CDATA-wrapped JavaScript for XML compatibility
- DOM parsing for XML response handling
- Staggered updates (200ms delay) to prevent API rate limiting

## Permissions Required

**User Role Requirements:**
- **Read**: `saved/searches` capability
- **Write**: `edit_search_schedule_priority` capability
- **Admin**: Recommended for full control

Grant permissions:
```bash
# Via Splunk CLI
splunk edit role power -grant_capability edit_search_schedule_priority
```

## Troubleshooting

### Issue: "Failed to update rule. Check permissions."

**Solution:**
```bash
# Check user capabilities
splunk list role power | grep -E "(saved|schedule|edit)"

# Grant required permissions
splunk edit role power -grant_capability edit_search_schedule_priority
splunk edit role power -grant_capability edit_search_scheduler
```

### Issue: Dashboard shows "Loading..." indefinitely

**Solution:**
```bash
# Check if saved searches exist
splunk list search | grep "Correlation_"

# Verify REST API accessible
curl -k -u admin:password \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/saved/searches/Correlation_Multi_Factor_Threat_Score
```

### Issue: "action.slack" not found in response

**Cause:** Slack plugin not configured or `action.slack` parameter missing from saved search.

**Solution:**
```bash
# Add action.slack to saved search
splunk edit saved-search "Correlation_Multi_Factor_Threat_Score" \
  -action.slack 1 \
  -action.slack.param.webhook_url "https://hooks.slack.com/services/..."
```

## Use Cases

### Maintenance Window

Disable all alerts during scheduled maintenance:
```
1. Click "🔴 Disable All Alerts"
2. Perform maintenance tasks
3. Click "✅ Enable All Alerts" when complete
```

### Testing New Rules

Enable single rule for testing:
```
1. Click "🔴 Disable All Alerts" first
2. Enable specific rule (e.g., "Correlation_Geo_Attack_Pattern")
3. Monitor Slack for test alerts
4. Re-enable other rules when satisfied
```

### Emergency Alert Storm

Quickly disable noisy rule:
```
1. Identify spammy rule in Slack
2. Click "Disable" button for that specific rule
3. Investigate root cause
4. Re-enable when issue resolved
```

## Technical Notes

- **Dashboard Format**: Simple XML (Classic), not Dashboard Studio
- **Browser Compatibility**: Chrome 90+, Firefox 88+, Safari 14+
- **Splunk Version**: 8.0+ (tested on 9.x)
- **Response Time**: ~200-500ms per rule update
- **Concurrent Updates**: Staggered by 200ms to prevent API throttling

## Related Files

- **Plugin**: `plugins/slack-notification-alert_232.tgz`
- **Config**: `configs/alert_actions.conf`
- **Rules**: `configs/correlation-rules.conf`
- **Deployment Script**: `scripts/deploy-dashboards.js`

## Support

For issues or questions:
- Check Splunk logs: `/opt/splunk/var/log/splunk/splunkd.log`
- Review browser console for JavaScript errors
- Verify Slack plugin configuration: Settings → Alert actions → Slack
