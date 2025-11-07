# Security Alert System v2.0.4 - Quick Start

**Package:** security_alert-v2.0.4-production.tar.gz (585 KB)
**Status:** Production Ready ✅

---

## 🚀 Deploy in 5 Minutes

```bash
# 1. Extract (30 seconds)
cd /opt/splunk/etc/apps/
tar -xzf security_alert-v2.0.4-production.tar.gz

# 2. Permissions (10 seconds)
chown -R splunk:splunk security_alert
chmod -R 755 security_alert/lib/

# 3. Verify (1 minute)
cd security_alert
bash bin/install.sh

# 4. Configure (1 minute)
mkdir -p local
cat > local/alert_actions.conf <<EOF
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF

# 5. Restart (2 minutes)
/opt/splunk/bin/splunk restart
```

---

## ✅ Verify Installation

```spl
# Check app loaded
index=_internal source=*splunkd.log security_alert
| stats count by log_level

# Check alerts
| rest /services/saved/searches
| search title="*Alert*"
| table title, disabled, cron_schedule

# Test bundled libraries
cd /opt/splunk/etc/apps/security_alert/bin
python3 -c "import sys; sys.path.insert(0, '../lib/python3'); import requests; print('✓ OK')"
```

---

## 📚 Documentation Quick Links

### For Quick Reference
- **README-DEPLOYMENT.txt** - This file (simplest)

### For Step-by-Step Deployment
- **DEPLOYMENT-SUMMARY-v2.0.4.md** - Comprehensive guide

### For What's New
- **RELEASE-NOTES-v2.0.4.md** - Changes and features

### For Development
- **CLAUDE.md** - Complete architecture

### For File Reference
- **FILES-INDEX.md** - Navigate all files

### For Project Status
- **FINAL-STATUS.md** - Complete metrics

---

## 🆘 Common Issues

**No module named 'requests'**
```bash
chmod -R 755 /opt/splunk/etc/apps/security_alert/lib/
bash bin/install.sh
```

**Slack not sending**
```bash
cat local/alert_actions.conf | grep webhook_url
# Verify webhook URL exists
```

**Alerts not running**
```spl
index=_internal source=*scheduler.log
| search savedsearch_name="*Alert*"
| stats count by status
```

---

## 📊 What You Get

### 15 Active Alerts
- VPN Tunnel monitoring
- Hardware health checks
- HA state tracking
- Interface status
- CPU/Memory anomalies
- Resource limits
- Admin login failures
- Brute force detection
- Traffic spike analysis
- And more...

### 11 State Trackers
- Eliminates duplicate notifications
- EMS-based state management
- Persistent CSV storage
- FortiManager sync tracking

### Bundled Libraries
- No pip install required
- Air-gapped deployment support
- Python dependencies included

---

## 🎯 Success Criteria

After deployment, you should see:
- ✅ App in Splunk Web: Apps > Security Alert System
- ✅ 15 alerts enabled: Settings > Searches, reports, and alerts
- ✅ No errors in logs: `index=_internal security_alert error`
- ✅ State trackers working: `| inputlookup vpn_state_tracker`

---

## 📞 Support

**Team:** NextTrade Security Team
**Repository:** https://github.com/qws941/splunk.git
**Email:** security@nexttrade.com

---

**Version:** 2.0.4
**Package Size:** 585 KB
**Self-Contained:** Yes (no pip required)
**Air-Gapped:** Supported
