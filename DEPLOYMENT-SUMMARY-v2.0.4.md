# Security Alert System v2.0.4 - Deployment Summary

## 🎉 Major Update: Self-Contained App

**Date:** 2025-11-06
**Version:** 2.0.4 (Bundled Dependencies Edition)
**Package:** `security_alert-v2.0.4-bundled.tar.gz` (586 KB)

---

## ✅ What's New

### 1. **All Python Dependencies Bundled**

The app now includes all required Python libraries - **NO external installation required!**

**Bundled libraries:**
- `requests` (2.32.5) - HTTP client for Slack/FortiManager API
- `urllib3` (2.5.0) - HTTP connection pooling
- `charset-normalizer` (3.4.4) - Character encoding detection
- `certifi` (2025.10.5) - SSL/TLS certificate bundle
- `idna` (3.11) - Internationalized domain names

**Location:** `security_alert/lib/python3/`

### 2. **Automatic Dependency Resolution**

Python scripts automatically load bundled libraries:

```python
# bin/slack.py and bin/fortigate_auto_response.py
import sys
import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(APP_DIR, 'lib', 'python3')
if os.path.exists(LIB_DIR) and LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

import requests  # Works without pip install!
```

### 3. **Installation Verification Script**

New `bin/install.sh` script validates:
- ✅ Directory structure
- ✅ Bundled libraries present
- ✅ Python scripts executable
- ✅ CSV lookup files
- ✅ Import tests
- ✅ Configuration files

### 4. **App Manifest**

Created `app.manifest` with proper metadata:
- Schema version 2.0.0
- All dependencies declared
- Splunk Enterprise compatibility

---

## 🚀 Deployment Instructions

### Step 1: Extract Package

```bash
cd /opt/splunk/etc/apps/
tar -xzf security_alert-v2.0.4-bundled.tar.gz
```

### Step 2: Set Permissions

```bash
chown -R splunk:splunk security_alert
chmod -R 755 security_alert/lib/
chmod 644 security_alert/lookups/*.csv
```

### Step 3: Run Installation Check

```bash
cd security_alert
bash bin/install.sh
```

Expected output:
```
✓ Directory exists: bin
✓ Directory exists: default
✓ Directory exists: lookups
✓ Directory exists: python3
✓ Directory exists: metadata
✓ Library bundled: requests
✓ Library bundled: urllib3
✓ Library bundled: charset_normalizer
✓ Library bundled: certifi
✓ Library bundled: idna
✓ Script exists: slack.py
✓ Script exists: fortigate_auto_response.py
✓ CSV files found: 13
✓ Bundled libraries test
✓ Config exists: app.conf
✓ Config exists: alert_actions.conf
✓ Config exists: savedsearches.conf
✓ Config exists: macros.conf
✓ Config exists: transforms.conf

Installation check completed successfully!
```

### Step 4: Configure Slack Webhook

```bash
mkdir -p local
cat > local/alert_actions.conf <<EOF
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF
```

### Step 5: Restart Splunk

```bash
/opt/splunk/bin/splunk restart
```

---

## ✨ Key Benefits

### For Deployment

- ✅ **Air-gapped ready** - Works on isolated Splunk servers
- ✅ **No internet required** - All dependencies included
- ✅ **No pip install** - No admin privileges needed
- ✅ **Consistent versions** - Same libraries across all deployments
- ✅ **No conflicts** - Isolated from other apps

### For Operations

- ✅ **Zero configuration** - Works out of the box
- ✅ **Automatic validation** - install.sh checks everything
- ✅ **Easy troubleshooting** - Clear error messages
- ✅ **Version controlled** - All deps tracked in manifest

---

## 📊 Package Details

### File Count

```
Total files: ~60
- Configuration files: 8
- Python scripts: 7
- CSV lookups: 13
- Bundled libraries: 5 packages
- Dashboards: 4
- Documentation: 3
```

### Size Breakdown

```
Total: 586 KB compressed (tar.gz)
- Bundled libraries: ~400 KB
- Application code: ~100 KB
- Lookups & config: ~50 KB
- Documentation: ~36 KB
```

### Directory Structure

```
security_alert/
├── app.manifest                    # NEW: App metadata
├── bin/
│   ├── install.sh                  # NEW: Installation validator
│   ├── slack.py                    # UPDATED: Auto-load libs
│   ├── fortigate_auto_response.py  # UPDATED: Auto-load libs
│   └── (other scripts)
├── lib/                            # NEW: Bundled dependencies
│   └── python3/
│       ├── requests/
│       ├── urllib3/
│       ├── charset_normalizer/
│       ├── certifi/
│       └── idna/
├── default/
│   ├── app.conf                    # UPDATED: Full metadata
│   └── (other configs)
└── (other directories)
```

---

## 🧪 Testing Results

### Import Test

```bash
cd /opt/splunk/etc/apps/security_alert
python3 -c "
import sys, os
sys.path.insert(0, 'lib/python3')
import requests, urllib3, certifi, idna
from charset_normalizer import from_bytes
print('✓ All libraries work')
"
```

**Result:** ✅ Pass

### Installation Check

```bash
bash bin/install.sh
```

**Result:** ✅ All checks pass (6/6)

### Alert Execution Test

```bash
# Manual test of slack.py
cd bin
python3 slack.py
```

**Result:** ✅ No import errors

---

## 📋 Migration from Previous Version

### If upgrading from v2.0.1 or earlier:

1. **Backup current state:**
   ```bash
   cp -r /opt/splunk/etc/apps/security_alert /tmp/security_alert.backup
   cp -r security_alert/lookups/*.csv /tmp/state_trackers/
   ```

2. **Remove old app:**
   ```bash
   rm -rf /opt/splunk/etc/apps/security_alert
   ```

3. **Install new version:**
   ```bash
   cd /opt/splunk/etc/apps/
   tar -xzf security_alert-v2.0.4-bundled.tar.gz
   chown -R splunk:splunk security_alert
   ```

4. **Restore state trackers (if needed):**
   ```bash
   cp /tmp/state_trackers/*.csv security_alert/lookups/
   ```

5. **Verify installation:**
   ```bash
   cd security_alert
   bash bin/install.sh
   ```

6. **Restart Splunk:**
   ```bash
   /opt/splunk/bin/splunk restart
   ```

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] App visible in Splunk Web UI: Apps > Security Alert System
- [ ] No errors in splunkd.log: `index=_internal source=*splunkd.log security_alert`
- [ ] Alert actions enabled: Settings > Alert actions > Slack
- [ ] Saved searches loaded: Settings > Searches, reports, and alerts
- [ ] Macros available: Settings > Advanced search > Search macros
- [ ] State trackers accessible: `| inputlookup vpn_state_tracker`
- [ ] No module errors in Python: `index=_internal source=*python.log error`

---

## 🆘 Support

### Common Issues

**Issue:** "No module named 'requests'"
- **Solution:** Run `bash bin/install.sh` to verify lib/ directory

**Issue:** Permission denied on lib/
- **Solution:** `chown -R splunk:splunk lib/ && chmod -R 755 lib/`

**Issue:** Slack not sending
- **Solution:** Check `local/alert_actions.conf` has webhook URL

### Documentation

- **Full guide:** `CLAUDE.md`
- **Deployment checklist:** `DEPLOYMENT-CHECKLIST.md`
- **User manual:** `README.md`

---

## 📞 Contact

**Team:** NextTrade Security Team
**Repository:** https://github.com/qws941/splunk.git
**Version:** 2.0.4 (Bundled Dependencies Edition)
**Release Date:** 2025-11-06

---

**🎊 This is now a production-ready, self-contained Splunk app!**
