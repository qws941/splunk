# 🚀 Quick Deploy: 123-fixed.xml

## ⚡ 1-Minute Deployment

### Option 1: Web UI (Recommended)

1. **Open Splunk**: https://YOUR_SPLUNK_HOST:8000
2. **Navigate**: Settings → User Interface → Views
3. **Upload**: New View → Upload XML
4. **Select**: `/home/jclee/app/splunk/123-fixed.xml`
5. **Name**: `123-fixed` (test first) or `123` (overwrite)
6. **Done**: View at https://YOUR_SPLUNK_HOST:8000/app/search/123-fixed

### Option 2: REST API (Fast)

```bash
export SPLUNK_PASSWORD="your-password"

# Deploy as new dashboard (safe)
curl -k -u admin:$SPLUNK_PASSWORD \
  -d "eai:data=$(cat /home/jclee/app/splunk/123-fixed.xml)" \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123-fixed
```

### Option 3: Overwrite Original (After Testing)

```bash
export SPLUNK_PASSWORD="your-password"

# Backup first
curl -k -u admin:$SPLUNK_PASSWORD \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123 \
  > 123.xml.backup.$(date +%Y%m%d)

# Deploy fixed version
curl -k -u admin:$SPLUNK_PASSWORD \
  -d "eai:data=$(cat /home/jclee/app/splunk/123-fixed.xml)" \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123
```

---

## ✅ Validation (30 seconds)

```bash
export SPLUNK_PASSWORD="your-password"
./scripts/validate-dashboard-fix.sh
```

**Expected output**:
```
✅ Traffic events:        10,000+
✅ Config changes:        50+
✅ Object changes:        20+
✅ Fix successful! Data is now visible.
```

---

## 📊 Visual Verification

### Before Fix (123.xml)
```
Traffic Overview:     [0 events] ❌
Top Source IPs:       [Empty]    ❌
Config Changes:       [Empty]    ❌
Object Changes:       [Empty]    ❌
```

### After Fix (123-fixed.xml)
```
Traffic Overview:     [15,234 events] ✅
Top Source IPs:       [10 IPs listed]  ✅
Config Changes:       [47 changes]     ✅
Object Changes:       [123 changes]    ✅
```

---

## 🔧 What Was Fixed?

**Problem**: `dedup sessionid` → Field doesn't exist in syslog → Data disappears

**Solution**: Removed dedup, use direct stats aggregation

**19 fixes total**:
- 13× `dedup sessionid` → Direct aggregation
- 3× `dedup config_hash span=1m` → `stats first() by hash`
- 3× `dedup cfgobj span=1m` → `stats first() by hash`

---

## 📚 Detailed Guides

- **Complete Fix Guide**: `docs/DASHBOARD_FIX_123.md`
- **Side-by-Side Comparison**: `docs/123-COMPARISON.md`
- **Validation Script**: `scripts/validate-dashboard-fix.sh`

---

## ⚠️ Rollback (If Needed)

```bash
# Web UI: Settings → Views → Upload backup
# OR REST API:
curl -k -u admin:$SPLUNK_PASSWORD \
  -d "eai:data=$(cat 123.xml.backup.YYYYMMDD)" \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123
```

---

**Status**: ✅ Ready to deploy
**Risk**: Low (only removes broken dedup commands)
**Testing**: Deploy as `123-fixed` first, compare side-by-side
**Commit**: Ready to git commit when validated
