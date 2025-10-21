# Threat Intelligence Integration Guide

**Phase**: 3.1 - External Threat Intelligence Integration
**Date**: 2025-10-21
**Status**: Ready for API Key Configuration

---

## 📊 Overview

This guide covers integration of external threat intelligence feeds into the FortiGate Security Dashboard:

1. **AbuseIPDB** - IP reputation and abuse reports
2. **VirusTotal** - File hash malware detection

---

## 🎯 Components

### 1. Lookup Tables

**Location**: `lookups/`

#### AbuseIPDB Lookup (`abuseipdb_lookup.csv`)

**Fields**:
- `ip` - IP address
- `abuse_score` - Abuse confidence score (0-100)
- `country` - ISO country code
- `isp` - Internet Service Provider
- `usage_type` - IP type (Commercial, Data Center, etc.)
- `domain` - Reverse DNS domain
- `is_whitelisted` - Boolean (true/false)
- `total_reports` - Number of abuse reports
- `last_reported` - Timestamp of last report (ISO8601)
- `confidence_score` - Internal confidence score (0-100)

**Update Frequency**: Every 30 minutes (cron)

---

#### VirusTotal Lookup (`virustotal_lookup.csv`)

**Fields**:
- `hash` - File hash (SHA256)
- `detection_rate` - Detection rate (e.g., "45/70")
- `malware_type` - Type of malware (Trojan, Ransomware, etc.)
- `malware_family` - Malware family name
- `first_seen` - First submission timestamp (ISO8601)
- `last_seen` - Last analysis timestamp (ISO8601)
- `vendor_detections` - Comma-separated list of detecting vendors
- `file_type` - File type/extension
- `file_size` - File size in bytes
- `threat_category` - Threat category (malicious, suspicious, clean)

**Update Frequency**: On-demand when new hashes detected

---

### 2. API Fetch Scripts

**Location**: `scripts/`

#### AbuseIPDB Script (`fetch_abuseipdb_intel.py`)

**Purpose**: Fetch IP reputation data from AbuseIPDB API

**Usage**:
```bash
# Check single IP
python3 scripts/fetch_abuseipdb_intel.py --ips 192.168.1.100

# Check multiple IPs
python3 scripts/fetch_abuseipdb_intel.py --ips "192.168.1.100,10.0.0.50,8.8.8.8"

# Batch check from file
python3 scripts/fetch_abuseipdb_intel.py --batch ips.txt

# Fetch from Splunk (requires SDK integration)
python3 scripts/fetch_abuseipdb_intel.py --source splunk
```

**Cron Setup**:
```bash
# Add to crontab (every 30 minutes)
*/30 * * * * cd /home/jclee/app/splunk && python3 scripts/fetch_abuseipdb_intel.py --source splunk >> logs/abuseipdb_fetch.log 2>&1
```

---

#### VirusTotal Script (`fetch_virustotal_intel.py`)

**Purpose**: Fetch file hash reputation from VirusTotal API

**Usage**:
```bash
# Check single hash
python3 scripts/fetch_virustotal_intel.py --hash a1b2c3d4e5f6...

# Batch check from file
python3 scripts/fetch_virustotal_intel.py --batch hashes.txt

# Fetch from Splunk (requires SDK integration)
python3 scripts/fetch_virustotal_intel.py --source splunk
```

**API Rate Limit**: 4 requests/minute (free tier)

---

## 🔧 Configuration

### Step 1: Obtain API Keys

#### AbuseIPDB API Key

1. Register at https://www.abuseipdb.com/account/register
2. Verify email
3. Navigate to https://www.abuseipdb.com/account/api
4. Generate API key (free tier: 1,000 checks/day)

#### VirusTotal API Key

1. Register at https://www.virustotal.com/gui/join-us
2. Verify email
3. Navigate to https://www.virustotal.com/gui/user/{username}/apikey
4. Copy API key (free tier: 4 requests/minute)

---

### Step 2: Set Environment Variables

**Option 1: `.env` file** (recommended for local testing):
```bash
# Add to /home/jclee/app/splunk/.env
ABUSEIPDB_API_KEY=your_abuseipdb_api_key_here
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
```

**Option 2: System environment** (recommended for production):
```bash
# Add to ~/.bashrc or /etc/environment
export ABUSEIPDB_API_KEY="your_abuseipdb_api_key_here"
export VIRUSTOTAL_API_KEY="your_virustotal_api_key_here"

# Reload
source ~/.bashrc
```

**Option 3: Splunk app configuration**:
```bash
# Create app.conf
sudo nano $SPLUNK_HOME/etc/apps/search/local/app.conf

[install]
state = enabled

[launcher]
version = 1.0.0

[ui]
is_visible = 1

[secrets]
ABUSEIPDB_API_KEY = your_key_here
VIRUSTOTAL_API_KEY = your_key_here
```

---

### Step 3: Test API Connectivity

```bash
# Test AbuseIPDB
python3 scripts/fetch_abuseipdb_intel.py --ips 8.8.8.8 --api-key YOUR_KEY

# Expected output:
# INFO: Checking 1 IP addresses...
# INFO: Checking 8.8.8.8...
#   ✓ 8.8.8.8: Abuse Score = 0
# SUCCESS: Updated lookups/abuseipdb_lookup.csv with 1 IPs

# Test VirusTotal
python3 scripts/fetch_virustotal_intel.py \
  --hash 44d88612fea8a8f36de82e1278abb02f \
  --api-key YOUR_KEY

# Expected output:
# INFO: Checking 1 file hashes...
# INFO: Checking 44d88612fea8a8f36de82e1278abb02f...
#   ✓ 44d88612fea8a8f36de82e1278abb02f: clean (0/70)
# SUCCESS: Updated lookups/virustotal_lookup.csv with 1 hashes
```

---

### Step 4: Configure Splunk Lookups

**File**: `$SPLUNK_HOME/etc/apps/search/local/transforms.conf`

```ini
[abuseipdb_lookup]
filename = abuseipdb_lookup.csv
case_sensitive_match = false

[virustotal_lookup]
filename = virustotal_lookup.csv
case_sensitive_match = false
```

**File**: `$SPLUNK_HOME/etc/apps/search/local/props.conf`

```ini
[fw]
# Auto-lookup for AbuseIPDB (applied to all fw events)
# Note: Automatic lookups can impact performance, use on-demand in panels instead
# LOOKUP-abuseipdb = abuseipdb_lookup ip AS srcip OUTPUT abuse_score, country, isp

# Manual lookup in SPL queries recommended:
# index=fw | lookup abuseipdb_lookup ip AS srcip OUTPUT abuse_score, country
```

---

## 📊 SPL Query Examples

### AbuseIPDB Integration

**Basic IP Reputation Check**:
```spl
index=fw action=deny
| lookup abuseipdb_lookup ip AS srcip OUTPUT abuse_score, country, isp, is_whitelisted
| where abuse_score > 50
| table _time, srcip, dstip, abuse_score, country, isp, action
| sort - abuse_score
```

**High-Risk IPs with Abuse Context**:
```spl
index=fw
| stats count by srcip
| lookup abuseipdb_lookup ip AS srcip OUTPUT abuse_score, country, isp, total_reports
| where abuse_score > 75
| eval risk_level = case(
    abuse_score >= 90, "Critical",
    abuse_score >= 75, "High",
    abuse_score >= 50, "Medium",
    1=1, "Low"
  )
| table srcip, abuse_score, risk_level, country, isp, total_reports, count
| sort - abuse_score
```

**Blocked IPs with Abuse Intelligence**:
```spl
index=fw action=deny
| stats count as block_count by srcip
| lookup abuseipdb_lookup ip AS srcip OUTPUT abuse_score, country, is_whitelisted
| where isnotnull(abuse_score)
| eval abuse_category = case(
    abuse_score == 0 AND is_whitelisted=="true", "Whitelisted",
    abuse_score == 0, "Clean",
    abuse_score < 25, "Low Risk",
    abuse_score < 50, "Medium Risk",
    abuse_score < 75, "High Risk",
    1=1, "Critical Risk"
  )
| table srcip, block_count, abuse_score, abuse_category, country
| sort - abuse_score
```

---

### VirusTotal Integration

**Malicious Files Detected**:
```spl
index=fw filehash=*
| lookup virustotal_lookup hash AS filehash OUTPUT detection_rate, malware_type, threat_category
| where threat_category IN ("malicious", "suspicious")
| table _time, filename, filehash, detection_rate, malware_type, threat_category, srcip, dstip
| sort - _time
```

**File Hash Analysis Summary**:
```spl
index=fw filehash=*
| lookup virustotal_lookup hash AS filehash OUTPUT detection_rate, threat_category, vendor_detections
| stats count by threat_category, malware_type
| sort - count
```

---

## 🎨 Dashboard Panel Examples

### Panel 1: Malicious IP Geo Map

```xml
<panel>
  <title>🌍 Malicious IP Sources (AbuseIPDB Abuse Score > 75)</title>
  <map>
    <search>
      <query><![CDATA[
index=fw action=deny
| stats count by srcip
| lookup abuseipdb_lookup ip AS srcip OUTPUT abuse_score, country, isp
| where abuse_score > 75
| iplocation srcip
| geostats latfield=lat longfield=lon count by Country
      ]]></query>
      <earliest>-24h</earliest>
      <latest>now</latest>
    </search>
    <option name="mapping.type">marker</option>
    <option name="mapping.map.center">(0,0)</option>
    <option name="mapping.map.zoom">2</option>
    <option name="mapping.markerLayer.markerMinSize">10</option>
    <option name="mapping.markerLayer.markerMaxSize">50</option>
  </map>
</panel>
```

---

### Panel 2: IP Reputation Table

```xml
<panel>
  <title>🚫 High-Risk IPs (AbuseIPDB Abuse Score > 50)</title>
  <table>
    <search>
      <query><![CDATA[
index=fw
| stats count as event_count by srcip
| lookup abuseipdb_lookup ip AS srcip OUTPUT abuse_score, country, isp, total_reports, is_whitelisted
| where abuse_score > 50
| eval risk_level = case(
    abuse_score >= 90, "Critical",
    abuse_score >= 75, "High",
    abuse_score >= 50, "Medium",
    1=1, "Low"
  )
| table srcip, abuse_score, risk_level, country, isp, total_reports, event_count, is_whitelisted
| sort - abuse_score
| head 20
      ]]></query>
      <earliest>-24h</earliest>
      <latest>now</latest>
    </search>

    <option name="drilldown">row</option>
    <option name="rowNumbers">true</option>

    <!-- Color formatting -->
    <format type="color" field="risk_level">
      <colorPalette type="map">
        {"Critical":#DC143C,"High":#FF6347,"Medium":#FFD700,"Low":#32CD32}
      </colorPalette>
    </format>

    <format type="color" field="abuse_score">
      <colorPalette type="minMidMax" maxColor="#DC143C" midColor="#FFD700" minColor="#32CD32"></colorPalette>
      <scale type="minMidMax" minValue="0" midValue="50" maxValue="100"></scale>
    </format>

    <!-- Drill-down to detailed events -->
    <drilldown>
      <link target="_blank">
        /app/search/search?q=search index=fw srcip=$row.srcip$ earliest=-24h | table _time, srcip, dstip, action, msg
      </link>
    </drilldown>
  </table>
</panel>
```

---

### Panel 3: Malware Detection Summary

```xml
<panel>
  <title>🦠 Malware Detection Summary (VirusTotal)</title>
  <chart>
    <search>
      <query><![CDATA[
index=fw filehash=*
| lookup virustotal_lookup hash AS filehash OUTPUT threat_category, malware_type
| stats count by threat_category, malware_type
| sort - count
      ]]></query>
      <earliest>-7d</earliest>
      <latest>now</latest>
    </search>
    <option name="charting.chart">pie</option>
    <option name="charting.legend.placement">right</option>
    <option name="charting.fieldColors">{
      "malicious":"#DC143C",
      "suspicious":"#FF8C00",
      "clean":"#32CD32"
    }</option>
  </chart>
</panel>
```

---

### Panel 4: Threat Intelligence Coverage

```xml
<panel>
  <title>📊 Threat Intelligence Coverage</title>
  <single>
    <search>
      <query><![CDATA[
| inputlookup abuseipdb_lookup.csv
| stats count as total_ips,
        sum(eval(if(abuse_score > 50, 1, 0))) as high_risk_ips,
        sum(eval(if(is_whitelisted=="true", 1, 0))) as whitelisted_ips
| eval coverage_rate = round((total_ips / 1000) * 100, 2) + "%"
| table total_ips, high_risk_ips, whitelisted_ips, coverage_rate
      ]]></query>
    </search>
    <option name="drilldown">none</option>
    <option name="numberPrecision">0</option>
    <option name="underLabel">IPs in AbuseIPDB Lookup</option>
  </single>
</panel>
```

---

## ⚠️ API Rate Limits & Costs

### AbuseIPDB

**Free Tier**:
- 1,000 checks/day
- 5 checks/minute
- Basic IP information

**Paid Tiers**:
- Basic ($20/month): 10,000 checks/day
- Pro ($40/month): 100,000 checks/day
- Enterprise (custom): Unlimited

**Recommendation**: Start with free tier, upgrade if hitting limits.

---

### VirusTotal

**Free Tier**:
- 4 requests/minute
- 500 requests/day
- Public API access

**Paid Tiers**:
- Premium ($0.12/request): Higher rate limits
- Enterprise (custom): Dedicated API, private scans

**Recommendation**: Use free tier for automated checks, manual premium API calls for critical hashes.

---

## 🔐 Security Considerations

### API Key Storage

1. **Never commit API keys to git**:
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo "*.key" >> .gitignore
   ```

2. **Use environment variables**:
   - System-level: `/etc/environment`
   - User-level: `~/.bashrc`
   - Application-level: `.env` file (gitignored)

3. **Rotate API keys regularly** (every 90 days)

4. **Restrict API key permissions** (read-only when possible)

---

### Data Privacy

1. **Do not send private/internal IPs to external APIs**:
   ```spl
   # Filter out RFC1918 private IPs
   index=fw
   | where NOT (match(srcip, "^10\.") OR match(srcip, "^192\.168\.") OR match(srcip, "^172\.(1[6-9]|2[0-9]|3[01])\."))
   | lookup abuseipdb_lookup ip AS srcip OUTPUT abuse_score
   ```

2. **Hash sensitive data before sending to VirusTotal**

3. **Review API terms of service** for data retention policies

---

## 📈 Performance Optimization

### Lookup Table Size Management

1. **Limit lookup table size**:
   ```bash
   # Keep only top 1,000 high-risk IPs
   python3 -c "
   import csv
   with open('lookups/abuseipdb_lookup.csv', 'r') as f:
       data = list(csv.DictReader(f))
   data_sorted = sorted(data, key=lambda x: int(x.get('abuse_score', 0)), reverse=True)[:1000]
   with open('lookups/abuseipdb_lookup.csv', 'w', newline='') as f:
       writer = csv.DictWriter(f, fieldnames=data[0].keys())
       writer.writeheader()
       writer.writerows(data_sorted)
   "
   ```

2. **Archive old data** (> 90 days):
   ```bash
   # Move to archive
   mv lookups/abuseipdb_lookup.csv lookups/archive/abuseipdb_$(date +%Y%m%d).csv
   ```

3. **Use on-demand lookups** (not automatic):
   - Automatic lookups run on every event (performance impact)
   - Manual lookups in SPL queries (on-demand, faster)

---

### Caching Strategy

1. **Cache API responses** for 24 hours:
   ```python
   # Modify scripts to check lookup table first
   if ip in existing_data and age < 24_hours:
       return cached_data
   else:
       fetch_from_api()
   ```

2. **Batch API calls** when possible:
   - AbuseIPDB: Use `/check-block` endpoint for CIDR blocks
   - VirusTotal: Batch hash submissions

---

## 🧪 Testing

### Unit Tests

```bash
# Test AbuseIPDB script
python3 scripts/fetch_abuseipdb_intel.py --ips 8.8.8.8

# Test VirusTotal script
python3 scripts/fetch_virustotal_intel.py --hash 44d88612fea8a8f36de82e1278abb02f

# Test lookup table update
ls -lh lookups/*.csv
```

### Integration Tests

```bash
# Test SPL query with lookup
$SPLUNK_HOME/bin/splunk search "index=fw | lookup abuseipdb_lookup ip AS srcip OUTPUT abuse_score | head 10"

# Test dashboard panel rendering
# Open Splunk Web → Dashboards → FortiGate Security Dashboard
# Verify new panels display data
```

---

## 📚 References

- **AbuseIPDB API Documentation**: https://docs.abuseipdb.com/
- **VirusTotal API v3**: https://developers.virustotal.com/reference/overview
- **Splunk Lookup Reference**: https://docs.splunk.com/Documentation/Splunk/latest/Knowledge/Aboutlookupsandfieldactions
- **Phase 3.1 Report**: `docs/DASHBOARD_OPTIMIZATION_PHASE3.1_REPORT.md`

---

**Status**: 🚧 Ready for API Key Configuration
**Next Step**: Obtain API keys and configure environment variables
**Estimated Setup Time**: 30 minutes

---

**Author**: Claude Code
**Date**: 2025-10-21
**Version**: Phase 3.1 - External Threat Intelligence Integration
