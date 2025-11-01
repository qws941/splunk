# ✅ Splunk Plugin Installation Complete

**Date**: 2025-10-30
**Status**: Plugins Installed, Container Restart Blocked

---

## 📦 Installation Summary

### Plugins Successfully Installed

All 3 plugins extracted to `/opt/splunk/etc/apps/` in `splunk-test` container:

| Plugin | Directory | Status |
|--------|-----------|--------|
| **Slack Notification Alert v2.3.2** | `slack_alerts` | ✅ Installed |
| **FortiGate TA v1.69** | `Splunk_TA_fortinet_fortigate` | ✅ Installed |
| **Splunk CIM v6.2.0** | `Splunk_SA_CIM` | ✅ Installed |

### Installation Method Used

Due to Docker `cp` pipe closure errors, used **stdin pipe method**:

```bash
# Copy files via stdin (bypasses docker cp issues)
cat plugin.tgz | docker exec -i splunk-test sh -c 'cat > /tmp/plugin.tgz'

# Extract as splunk user (correct permissions)
docker exec -u splunk splunk-test tar -xzf /tmp/plugin.tgz -C /opt/splunk/etc/apps/
```

---

## ⚠️ Container Restart Issue

### Problem

`docker restart splunk-test` fails with:

```
Error: unable to start container process: error during container init:
error mounting "/home/jclee/app/splunk/configs/inputs-udp.conf" to rootfs
at "/opt/splunk/etc/apps/search/local/inputs.conf":
cannot create subdirectories: not a directory
```

### Root Cause

Container has bind mount for `/home/jclee/app/splunk/configs/inputs-udp.conf` but:
1. File doesn't exist on host (likely archived or deleted)
2. Target directory structure inside container doesn't match

### Current Bind Mounts

```json
{
  "Source": "/home/jclee/app/splunk/configs/inputs-udp.conf",
  "Destination": "/opt/splunk/etc/apps/search/local/inputs.conf",
  "Mode": "rw"
}
```

**Conflicting with**:
- `/home/jclee/app/splunk/configs/savedsearches-fortigate-alerts.conf`
- `/home/jclee/app/splunk/configs/dashboards` (directory mount)

---

## 🔧 Fix Options

### Option 1: Remove Bind Mount (Recommended)

**Pros**: Clean solution, no legacy config files
**Cons**: Requires recreating container

```bash
# 1. Stop container
docker stop splunk-test

# 2. Remove container (volumes persist)
docker rm splunk-test

# 3. Recreate without inputs-udp.conf mount
docker run -d \
  --name splunk-test \
  --hostname splunk \
  -p 8800:8000 \
  -p 8089:8089 \
  -p 8088:8088 \
  -p 9514:9514/udp \
  -e SPLUNK_START_ARGS=--accept-license \
  -e SPLUNK_PASSWORD=changeme \
  -v splunk-var:/opt/splunk/var \
  -v splunk-etc:/opt/splunk/etc \
  -v /home/jclee/app/splunk/configs/savedsearches-fortigate-alerts.conf:/opt/splunk/etc/apps/search/local/savedsearches.conf:rw \
  -v /home/jclee/app/splunk/configs/dashboards:/opt/splunk/etc/apps/search/local/data/ui/views:rw \
  splunk/splunk:latest

# Note: Plugins already in volume, will be available after restart
```

### Option 2: Create Placeholder File

**Pros**: Quick fix
**Cons**: Leaves unused file

```bash
# Create empty file (may need sudo)
sudo touch /home/jclee/app/splunk/configs/inputs-udp.conf

# Or copy from archived version if exists
cp configs/archive-2025-10-29/inputs-udp.conf configs/inputs-udp.conf

# Then start container
docker start splunk-test
```

### Option 3: Use Docker Compose

**Pros**: Declarative, version controlled
**Cons**: Requires docker-compose.yml update

Update `docker-compose.yml` to remove `inputs-udp.conf` mount, then:

```bash
docker-compose up -d splunk-test
```

---

## ✅ Post-Fix Verification

After container starts successfully:

### 1. Verify Plugins Active

```bash
# Check Web UI
http://localhost:8800
Apps → Manage Apps → Should see:
- Slack Notification Alert (v2.3.2)
- Fortinet FortiGate Add-on for Splunk (v1.69)
- Splunk Common Information Model (v6.2.0)

# Or via CLI
docker exec splunk-test /opt/splunk/bin/splunk list app -auth admin:changeme
```

### 2. Configure Slack Plugin

```bash
# Web UI
Settings → Alert actions → Setup Slack Alerts

# Enter Webhook URL
https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Test
| sendalert slack param.channel="#test" param.message="Plugin test"
```

### 3. Run Diagnostic Queries

Execute 6 queries from `docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md`:
- Step 1: Data flow check
- Step 2: Registered alerts
- Step 3: Alert execution logs
- Step 4: Critical Events query test
- Step 5: Slack action logs
- Step 6: Suppression settings

---

## 📊 Current Status

**Plugins**: ✅ Installed (in Docker volume)
**Container**: ❌ Stopped (mount config issue)
**Next Step**: Fix bind mount issue using Option 1, 2, or 3

**Files Installed** (verified in `/opt/splunk/etc/apps/`):
```
slack_alerts/
Splunk_TA_fortinet_fortigate/
Splunk_SA_CIM/
```

---

## 📚 Related Documentation

- **Diagnostic Guide**: `docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md` (6 queries + troubleshooting)
- **Alert Manager Guide**: `docs/ALERT-MANAGER-GUIDE.md` (Enterprise v3.6.0)
- **Work Summary**: `docs/DIAGNOSTIC-AND-PLUGIN-SUMMARY.md` (complete checklist)
- **Web UI Install Guide**: `docs/PLUGIN-WEBUI-INSTALL-GUIDE.txt` (alternative method)

---

**Next Action Required**: User must fix bind mount issue using one of the 3 options above, then restart container to activate plugins.
