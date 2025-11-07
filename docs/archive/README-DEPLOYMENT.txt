================================================================================
Security Alert System v2.0.4 - Quick Deployment Guide
================================================================================

📦 PACKAGE: security_alert-v2.0.4-production.tar.gz (585 KB)
🎯 KEY FEATURE: All dependencies bundled - NO pip install required!

================================================================================
🚀 QUICK START (5 minutes)
================================================================================

1. EXTRACT
   cd /opt/splunk/etc/apps/
   tar -xzf security_alert-v2.0.4-production.tar.gz

2. SET PERMISSIONS
   chown -R splunk:splunk security_alert
   chmod -R 755 security_alert/lib/

3. VERIFY INSTALLATION
   cd security_alert
   bash bin/install.sh
   # Should show: ✓ Installation check completed successfully!

4. CONFIGURE SLACK
   mkdir -p local
   echo '[slack]' > local/alert_actions.conf
   echo 'param.webhook_url = YOUR_WEBHOOK_URL' >> local/alert_actions.conf

5. RESTART SPLUNK
   /opt/splunk/bin/splunk restart

================================================================================
✅ VERIFICATION
================================================================================

After restart, verify:
□ App visible in Splunk Web: Apps > Security Alert System
□ No errors: index=_internal source=*splunkd.log security_alert error
□ Alerts loaded: Settings > Searches, reports, and alerts (15 alerts)
□ Test import: cd bin && python3 -c "import sys; sys.path.insert(0, '../lib/python3'); import requests; print('OK')"

================================================================================
📚 DOCUMENTATION
================================================================================

Full guides:
- CLAUDE.md                        # Complete technical documentation
- DEPLOYMENT-SUMMARY-v2.0.4.md     # Detailed deployment guide
- RELEASE-NOTES-v2.0.4.md          # What's new in v2.0.4
- DEPLOYMENT-CHECKLIST.md          # Pre-deployment checklist

================================================================================
🆘 TROUBLESHOOTING
================================================================================

Issue: "No module named 'requests'"
→ Solution: chmod -R 755 lib/ && bash bin/install.sh

Issue: Slack not sending
→ Solution: Check local/alert_actions.conf has webhook_url

Issue: Alerts not running
→ Solution: Check index=_internal source=*scheduler.log

================================================================================
📞 SUPPORT
================================================================================

Team: NextTrade Security Team
Repo: https://github.com/qws941/splunk.git
Docs: See CLAUDE.md

================================================================================
🎉 ENJOY YOUR SELF-CONTAINED SPLUNK APP!
================================================================================
