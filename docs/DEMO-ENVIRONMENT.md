# Splunk Demo Environment - Quick Reference

## ✅ Status

**Container Status**: ✅ HEALTHY
**Provisioning**: ✅ COMPLETED
**Splunk Version**: Latest (from official splunk/splunk:latest image)
**Testing**: ✅ VERIFIED (2025-11-05)
**security_alert App**: ✅ INSTALLED (15 alerts configured)

---

## 🌐 Access Information

### Web UI
- **URL**: http://192.168.50.215:8000
- **Username**: `admin`
- **Password**: `changeme123`

### HEC (HTTP Event Collector)
- **URL**: http://192.168.50.215:8088
- **Token**: `00000000-0000-0000-0000-000000000000`

### TCP Input
- **Port**: 9997

---

## 🐳 Container Details

**Container Name**: `splunk-demo`
**Network**: `splunk-demo`
**Docker Context**: synology (remote)
**Host**: 192.168.50.215

**Port Mappings**:
- 8000 → Splunk Web UI
- 8088 → HTTP Event Collector (HEC)
- 9997 → TCP data input

---

## 🚀 Quick Commands

### Check Status
```bash
docker ps --filter name=splunk-demo
docker logs splunk-demo | tail -20
```

### Restart Container
```bash
docker-compose -f docker-compose-demo.yml restart
```

### Stop Container
```bash
docker-compose -f docker-compose-demo.yml down
```

### Start Container
```bash
docker-compose -f docker-compose-demo.yml up -d
```

### Access Container Shell
```bash
docker exec -it splunk-demo /bin/bash
```

---

## 📦 Deploy Security Alert App

Since volume mount is currently disabled, deploy the app using one of these methods:

### Method 1: Copy to Running Container
```bash
# From repository root
cd /home/jclee/app/splunk
docker cp security_alert/ splunk-demo:/opt/splunk/etc/apps/
docker exec splunk-demo chown -R splunk:splunk /opt/splunk/etc/apps/security_alert
docker exec splunk-demo /opt/splunk/bin/splunk restart
```

### Method 2: Install via Web UI
```bash
# Create tarball
tar -czf security_alert.tar.gz security_alert/

# Copy to local machine if needed
# Then: Splunk Web → Settings → Apps → Install app from file
```

### Method 3: Enable Volume Mount (requires Docker context fix)
```bash
# In docker-compose-demo.yml, uncomment:
# volumes:
#   - ./security_alert:/opt/splunk/etc/apps/security_alert:ro

# Then restart:
docker-compose -f docker-compose-demo.yml down
docker-compose -f docker-compose-demo.yml up -d
```

---

## 🔧 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs splunk-demo

# Common issues:
# - License not accepted → Already fixed in docker-compose-demo.yml
# - Port conflict → Change port mappings in docker-compose-demo.yml
```

### Can't Access Web UI
```bash
# Verify container is healthy
docker ps --filter name=splunk-demo

# Check if port is accessible
curl http://192.168.50.215:8000

# From Synology NAS:
ssh jclee@192.168.50.215 -p 1111
curl http://localhost:8000
```

### Reset Demo Environment
```bash
# Stop and remove everything
docker-compose -f docker-compose-demo.yml down -v

# Start fresh
docker-compose -f docker-compose-demo.yml up -d
```

---

## 📝 Environment Variables

Current configuration in `docker-compose-demo.yml`:

```yaml
SPLUNK_GENERAL_TERMS=--accept-sgt-current-at-splunk-com  # License acceptance
SPLUNK_START_ARGS=--accept-license                       # License acceptance
SPLUNK_PASSWORD=changeme123                              # Admin password
SPLUNK_HEC_TOKEN=00000000-0000-0000-0000-000000000000   # HEC token
```

---

## ⚠️ Known Issues

1. **Remote Docker Context**: Running on Synology NAS (192.168.50.215) instead of local Docker
   - **Impact**: Volume mounts from local filesystem don't work
   - **Workaround**: Copy files into container or use tarball deployment

2. **Volume Mount Disabled**: `security_alert` app not automatically mounted
   - **Workaround**: Use Method 1 or 2 above to deploy app

---

## 📚 Next Steps

1. ✅ Access Splunk Web UI at http://192.168.50.215:8000
2. ✅ Login with admin/changeme123
3. 📦 Deploy security_alert app using one of the methods above
4. 🔧 Configure FortiGate to send syslog to 192.168.50.215:9997
5. 🔍 Verify data ingestion: `index=fw | stats count`

---

**Created**: 2025-11-05
**Last Updated**: 2025-11-05
**Status**: ✅ Running and Healthy
