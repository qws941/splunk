# Security Alert System v2.0.4 - Release Notes

**Release Date:** 2025-11-06
**Package:** `security_alert-v2.0.4-production.tar.gz` (585 KB)
**Repository:** https://github.com/qws941/splunk.git

---

## 🎉 Major Features

### 1. Self-Contained Deployment ⭐

**All Python dependencies are now bundled in the app!**

- ✅ No `pip install` required
- ✅ Works on air-gapped/isolated Splunk servers
- ✅ No internet access needed
- ✅ No admin privileges required
- ✅ Consistent versions across all deployments

**Bundled libraries:**
- `requests` (2.32.5)
- `urllib3` (2.5.0)
- `charset-normalizer` (3.4.4)
- `certifi` (2025.10.5)
- `idna` (3.11)

### 2. Automatic Dependency Resolution

Python scripts automatically load bundled libraries from `lib/python3/`:

```python
# Automatic sys.path configuration in bin/slack.py and bin/fortigate_auto_response.py
import sys, os
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(APP_DIR, 'lib', 'python3')
sys.path.insert(0, LIB_DIR)
import requests  # Now works!
```

### 3. Installation Verification Script

New `bin/install.sh` validates:
- Directory structure
- Bundled libraries present and importable
- Python scripts executable
- CSV lookup files readable
- Configuration files valid

Run after deployment:
```bash
cd /opt/splunk/etc/apps/security_alert
bash bin/install.sh
```

### 4. App Manifest (v2.0.0)

New `app.manifest` with:
- Schema version 2.0.0
- All dependencies declared
- Splunk Enterprise compatibility
- Author and licensing information

---

## 🔧 Technical Changes

### Modified Files

| File | Change | Reason |
|------|--------|--------|
| `bin/slack.py` | Added sys.path setup | Load bundled libs |
| `bin/fortigate_auto_response.py` | Added sys.path setup | Load bundled libs |
| `default/app.conf` | Enhanced metadata | Full app info |
| `CLAUDE.md` | Major update | New deployment docs |

### New Files

| File | Purpose |
|------|---------|
| `app.manifest` | App metadata (Splunk v2.0.0 format) |
| `bin/install.sh` | Installation verification script |
| `lib/python3/*` | Bundled Python dependencies (5 packages) |
| `DEPLOYMENT-SUMMARY-v2.0.4.md` | Deployment guide |
| `RELEASE-NOTES-v2.0.4.md` | This file |

### Directory Structure Changes

```diff
security_alert/
  ├── bin/
+ │   ├── install.sh              # NEW
  │   ├── slack.py                # MODIFIED
  │   └── fortigate_auto_response.py  # MODIFIED
+ ├── lib/                        # NEW
+ │   └── python3/                # NEW
+ │       ├── requests/           # NEW
+ │       ├── urllib3/            # NEW
+ │       ├── charset_normalizer/ # NEW
+ │       ├── certifi/            # NEW
+ │       └── idna/               # NEW
+ ├── app.manifest                # NEW
  └── (other files unchanged)
```

---

## 📦 Package Information

### Comparison with Previous Version

| Version | Size | Dependencies | Air-gapped? |
|---------|------|--------------|-------------|
| v2.0.1 | 48 KB | External pip | ❌ No |
| **v2.0.4** | **585 KB** | **Bundled** | **✅ Yes** |

**Size increase:** 537 KB (all from bundled libraries)

### What's Included

```
Total: 585 KB compressed
- Bundled libraries: ~400 KB (68%)
- Application code: ~100 KB (17%)
- Lookups & config: ~50 KB (9%)
- Documentation: ~35 KB (6%)
```

---

## 🚀 Upgrade Instructions

### From v2.0.1 or Earlier

1. **Backup current app:**
   ```bash
   cp -r /opt/splunk/etc/apps/security_alert /tmp/security_alert.backup
   ```

2. **Backup state trackers (important!):**
   ```bash
   mkdir -p /tmp/state_trackers
   cp /opt/splunk/etc/apps/security_alert/lookups/*_state_tracker.csv /tmp/state_trackers/
   ```

3. **Remove old app:**
   ```bash
   rm -rf /opt/splunk/etc/apps/security_alert
   ```

4. **Install new version:**
   ```bash
   cd /opt/splunk/etc/apps/
   tar -xzf security_alert-v2.0.4-production.tar.gz
   chown -R splunk:splunk security_alert
   ```

5. **Restore state trackers:**
   ```bash
   cp /tmp/state_trackers/*.csv security_alert/lookups/
   chown splunk:splunk security_alert/lookups/*.csv
   ```

6. **Run installation check:**
   ```bash
   cd security_alert
   bash bin/install.sh
   ```

7. **Restart Splunk:**
   ```bash
   /opt/splunk/bin/splunk restart
   ```

### Configuration Preservation

Your `local/alert_actions.conf` (Slack webhook) will be preserved if upgrading in-place. If doing a clean install, recreate:

```bash
mkdir -p local
cat > local/alert_actions.conf <<EOF
[slack]
param.webhook_url = YOUR_WEBHOOK_URL
EOF
```

---

## ✅ Testing & Validation

### Pre-Release Testing

All tests passed:

- ✅ **Import test:** All bundled libraries import successfully
- ✅ **Installation check:** All 6 validation checks pass
- ✅ **Alert execution:** slack.py runs without errors
- ✅ **Auto-response:** fortigate_auto_response.py runs without errors
- ✅ **Package integrity:** tar.gz extracts cleanly
- ✅ **Permission test:** chmod 755 on lib/ works

### Tested Environments

- **OS:** Rocky Linux 9 (x86_64)
- **Python:** 3.9+
- **Splunk:** Enterprise 8.x, 9.x compatible
- **Isolation:** Tested on air-gapped system (no internet)

---

## 🐛 Bug Fixes

### Fixed in v2.0.4

1. **Dependency hell resolved**
   - **Issue:** Manual pip install required, often failed
   - **Fix:** All dependencies bundled, automatic loading

2. **Air-gapped deployment failed**
   - **Issue:** Could not install on isolated Splunk servers
   - **Fix:** Self-contained package works offline

3. **Version conflicts**
   - **Issue:** requests version conflicts with other apps
   - **Fix:** Isolated dependencies in lib/python3/

---

## 📚 Documentation Updates

### Updated Files

- `CLAUDE.md` - Complete rewrite with bundled dependency docs
- `README.md` - Updated deployment instructions
- `DEPLOYMENT-CHECKLIST.md` - Enhanced with lib/ validation

### New Documentation

- `DEPLOYMENT-SUMMARY-v2.0.4.md` - Deployment guide
- `RELEASE-NOTES-v2.0.4.md` - This file

---

## 🔮 Future Plans

### v2.0.5 (Planned)

- Add pip-free update mechanism
- Include checksums for bundled libraries
- Add version compatibility matrix

### v2.1.0 (Planned)

- Support for custom CA certificates
- Proxy configuration for bundled requests
- Health check dashboard

---

## ⚠️ Breaking Changes

**None!** This is a backward-compatible release.

- All existing alerts work unchanged
- State trackers preserve data
- Configuration files compatible
- No SPL query changes

---

## 📞 Support

### Getting Help

1. **Installation issues:** Run `bash bin/install.sh` for diagnostics
2. **Import errors:** Check `CLAUDE.md` > Common Issues
3. **Slack not working:** Verify webhook in `local/alert_actions.conf`

### Contact

- **Team:** NextTrade Security Team
- **Email:** security@nexttrade.com
- **Repository:** https://github.com/qws941/splunk.git

---

## 🙏 Acknowledgments

This release was made possible by:
- Python `requests` library maintainers
- Splunk community for packaging best practices
- NextTrade Security Team for testing

---

**🎊 Thank you for using Security Alert System v2.0.4!**

This is now a production-ready, self-contained Splunk app that works anywhere!
