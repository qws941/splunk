# Traefik Integration Troubleshooting Guide

**Last Updated**: 2025-11-05
**Environment**: Rocky Linux 9 + Synology NAS (NFS)

---

## Quick Status Check

```bash
# Check all services
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check Traefik routers
docker logs traefik --tail=50 | grep -i splunk

# Check network connectivity
docker network inspect traefik-public | grep splunk

# Test endpoints
curl -I https://splunk.jclee.me
curl -I https://faz-splunk.jclee.me
```

---

## Common Issues & Solutions

### 1. Splunk Container Unhealthy

**Symptoms**:
```
dependency failed to start: container splunk is unhealthy
Warning: cannot create "/opt/splunk/var/log/splunk"
```

**Diagnosis**:
```bash
# Check NFS permissions
ssh -p 1111 jclee@192.168.50.215 "ls -ln /volume1/splunk/data/"

# Expected: UID 41812 (Splunk user)
# var/ → UID: 41812
# etc/ → UID: 41812
```

**Solution**:
```bash
# Fix permissions on NAS
ssh -p 1111 jclee@192.168.50.215
sudo chown -R 41812:41812 /volume1/splunk/data/var
sudo chown -R 41812:41812 /volume1/splunk/data/etc

# Restart container
docker-compose restart splunk

# Wait 60-90 seconds for full startup
```

**Why UID 41812?**
- Splunk container runs as non-root user (UID 41812)
- NFSv4 requires exact UID match between container and NAS
- Different from other apps (postgres=999, redis=999)

---

### 2. Traefik Not Routing to Splunk

**Symptoms**:
```
404 Not Found
502 Bad Gateway
```

**Diagnosis**:
```bash
# Check if Splunk is in traefik-public network
docker network inspect traefik-public --format '{{range .Containers}}{{.Name}} {{end}}' | grep splunk

# Check Traefik router configuration
docker exec traefik cat /etc/traefik/traefik.yml

# Check Traefik logs for routing
docker logs traefik --tail=100 | grep -E "(splunk|Router)"
```

**Solution 1: Network not connected**
```bash
# Reconnect to traefik-public
docker network connect traefik-public splunk
docker-compose restart splunk
```

**Solution 2: Traefik labels incorrect**
```bash
# Verify labels in docker-compose.yml:
# - traefik.enable=true
# - traefik.docker.network=traefik-public
# - traefik.http.routers.splunk.rule=Host(`splunk.jclee.me`)
# - traefik.http.services.splunk-web.loadbalancer.server.port=8000

# Apply changes
docker-compose up -d
```

**Solution 3: DNS not resolving**
```bash
# Test DNS resolution
nslookup splunk.jclee.me

# If fails, add to /etc/hosts (temporary)
echo "192.168.50.215 splunk.jclee.me" | sudo tee -a /etc/hosts
```

---

### 3. HTTPS Certificate Issues

**Symptoms**:
```
SSL certificate problem
TLS handshake failed
```

**Diagnosis**:
```bash
# Check Let's Encrypt certificate
docker exec traefik cat /letsencrypt/acme.json | grep splunk

# Check certificate expiry
echo | openssl s_client -connect splunk.jclee.me:443 2>/dev/null | openssl x509 -noout -dates
```

**Solution**:
```bash
# Force certificate renewal
docker exec traefik rm /letsencrypt/acme.json
docker-compose restart traefik

# Wait 2-3 minutes for new certificate
# Check Traefik logs
docker logs traefik -f | grep -i certificate
```

---

### 4. HTTP Not Redirecting to HTTPS

**Symptoms**:
- http://splunk.jclee.me stays on HTTP
- No automatic HTTPS redirect

**Diagnosis**:
```bash
# Check if http router exists
docker inspect splunk --format '{{json .Config.Labels}}' | grep splunk-http
```

**Solution**:
Ensure these labels exist in docker-compose.yml:
```yaml
labels:
  # HTTP → HTTPS Redirect
  - "traefik.http.routers.splunk-http.rule=Host(`splunk.jclee.me`)"
  - "traefik.http.routers.splunk-http.entrypoints=web"
  - "traefik.http.routers.splunk-http.middlewares=https-redirect"
  - "traefik.http.middlewares.https-redirect.redirectscheme.scheme=https"
  - "traefik.http.middlewares.https-redirect.redirectscheme.permanent=true"
```

Apply:
```bash
docker-compose up -d
```

---

### 5. Health Check Failing

**Symptoms**:
```
health: starting (never becomes healthy)
health: unhealthy
```

**Diagnosis**:
```bash
# Check health check command
docker inspect splunk --format '{{json .State.Health}}' | jq

# Test health check manually
docker exec splunk curl -f http://localhost:8000/en-US/account/login
```

**Solution 1: Splunk not fully started**
```bash
# Wait longer (Splunk takes 60-90 seconds)
docker logs splunk | grep "Ansible playbook complete"

# If stuck, check logs
docker logs splunk --tail=200
```

**Solution 2: Health check path incorrect**
```bash
# Update docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/en-US/account/login"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 90s  # Increase if needed

# Apply
docker-compose up -d
```

---

### 6. faz-splunk-integration Won't Start

**Symptoms**:
```
dependency failed to start: container splunk is unhealthy
Container faz-splunk  Waiting
```

**Diagnosis**:
```bash
# Check dependency in docker-compose.yml
grep -A 3 "depends_on:" docker-compose.yml
```

**Root Cause**: Splunk must be healthy first (see Issue #1)

**Solution**:
```bash
# 1. Fix Splunk first (see Issue #1)
docker-compose restart splunk

# 2. Wait for Splunk to be healthy
docker ps | grep splunk
# Expected: Up X seconds (healthy)

# 3. Start faz-splunk
docker-compose up -d faz-splunk-integration

# 4. Check logs
docker logs faz-splunk -f
```

---

### 7. Traefik entrypoints Not Configured

**Symptoms**:
```
error: entrypoint web doesn't exist
error: entrypoint websecure doesn't exist
```

**Diagnosis**:
```bash
# Check Traefik entrypoints
docker exec traefik cat /etc/traefik/traefik.yml | grep -A 10 entryPoints
```

**Expected Configuration**:
```yaml
entryPoints:
  web:
    address: :80
  websecure:
    address: :443
```

**Solution**:
If entrypoints missing, update Traefik configuration:
```bash
# Traefik is managed globally, contact Synology admin
# Or update Traefik docker-compose.yml on Synology

# Temporary: Use port-based routing
labels:
  - "traefik.http.routers.splunk.rule=Host(`192.168.50.215`)"
  - "traefik.http.services.splunk.loadbalancer.server.port=8000"
```

---

## Verification Steps

After fixing issues, run these checks:

### 1. Container Health
```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(splunk|faz-splunk)"

# Expected:
# splunk    Up X minutes (healthy)
# faz-splunk  Up X minutes (healthy)
```

### 2. Network Connectivity
```bash
docker network inspect traefik-public | grep -A 5 splunk
# Should show both containers
```

### 3. Traefik Routing
```bash
# Test from internal network
curl -I http://192.168.50.215:8000  # Direct access
curl -I -k https://splunk.jclee.me  # Via Traefik

# Expected: HTTP 200 OK or 302 Redirect
```

### 4. External Access
```bash
# From outside network (if DNS configured)
curl -I https://splunk.jclee.me
curl -I https://faz-splunk.jclee.me

# Or add to /etc/hosts first:
# 192.168.50.215 splunk.jclee.me faz-splunk.jclee.me
```

### 5. Splunk Web UI
```
URL: https://splunk.jclee.me
User: admin
Pass: Admin123! (or from .env: SPLUNK_PASSWORD)
```

### 6. HEC Endpoint
```bash
curl -k https://splunk.jclee.me/services/collector/health
# Expected: {"text":"HEC is healthy","code":200}
```

---

## Performance Tuning

### Reduce Startup Time

**Problem**: Splunk takes 90+ seconds to start

**Solution**:
```yaml
# Update docker-compose.yml
splunk:
  environment:
    - SPLUNK_START_ARGS=--accept-license --answer-yes --no-prompt
  healthcheck:
    start_period: 120s  # Increase grace period
```

### Optimize Health Checks

**Problem**: Too frequent health checks increase load

**Solution**:
```yaml
healthcheck:
  interval: 60s       # Increase from 30s
  timeout: 15s        # Increase from 10s
  retries: 3          # Decrease from 5
```

---

## Best Practices

### 1. Use Structured Logging
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service,job"
```

### 2. Enable Health Checks
```yaml
# Always include health checks for Traefik load balancing
labels:
  - "traefik.http.services.splunk-web.loadbalancer.healthcheck.path=/en-US/account/login"
  - "traefik.http.services.splunk-web.loadbalancer.healthcheck.interval=30s"
```

### 3. Set Explicit Priorities
```yaml
# Higher priority = checked first
labels:
  - "traefik.http.routers.splunk-hec.priority=200"  # HEC (specific path)
  - "traefik.http.routers.splunk.priority=100"      # Web UI (general)
```

### 4. Separate Services
```yaml
# Don't use single service for multiple ports
# BAD:
# - "traefik.http.services.splunk.loadbalancer.server.port=8000"
# - "traefik.http.services.splunk.loadbalancer.server.port=8088"  # Ignored!

# GOOD:
# - "traefik.http.services.splunk-web.loadbalancer.server.port=8000"
# - "traefik.http.services.splunk-hec.loadbalancer.server.port=8088"
```

---

## Monitoring & Logs

### Real-time Monitoring
```bash
# Watch container status
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep splunk'

# Follow logs
docker-compose logs -f splunk

# Filter errors only
docker logs splunk 2>&1 | grep -i error

# Check Traefik routing
docker logs traefik -f | grep splunk
```

### Log Locations

**Container Logs**:
```bash
docker logs splunk
docker logs faz-splunk
docker logs traefik
```

**NFS Persistent Logs**:
```bash
ssh -p 1111 jclee@192.168.50.215
ls -lh /volume1/splunk/data/var/log/splunk/
```

**Grafana Loki**:
```
URL: https://grafana.jclee.me
Job: splunk, faz-splunk-integration
```

---

## Emergency Recovery

### Complete Reset

**WARNING**: This will delete all data!

```bash
# 1. Stop and remove containers
docker-compose down -v

# 2. Clear NFS data
ssh -p 1111 jclee@192.168.50.215
sudo rm -rf /volume1/splunk/data/var/*
sudo rm -rf /volume1/splunk/data/etc/*

# 3. Recreate with correct permissions
sudo mkdir -p /volume1/splunk/data/{var,etc}
sudo chown -R 41812:41812 /volume1/splunk/data/

# 4. Start fresh
docker-compose up -d

# 5. Wait 2-3 minutes for initial setup
```

### Rollback to Previous Version

```bash
# 1. Check git history
git log --oneline -5

# 2. Rollback docker-compose.yml
git checkout HEAD~1 docker-compose.yml

# 3. Restart
docker-compose up -d

# 4. If works, commit
git commit -m "Rollback to working configuration"
```

---

## Related Documentation

- **CLAUDE.md**: Project setup and data directory structure
- **docker-compose.yml**: Complete service definitions
- **README.md**: General project overview
- **DEPLOYMENT-STRUCTURE.md**: Deployment architecture

---

## Support Contacts

**Traefik Documentation**: https://doc.traefik.io/traefik/
**Splunk Docker**: https://hub.docker.com/r/splunk/splunk/
**Project Repository**: https://github.com/qws941/splunk.git

---

## Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2025-11-05 | Added HTTP→HTTPS redirect | Security best practice |
| 2025-11-05 | Added separate services for Web/HEC | Traefik routing clarity |
| 2025-11-05 | Added health check paths | Load balancer integration |
| 2025-11-05 | NFS permission troubleshooting | UID 41812 issues |
