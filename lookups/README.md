# Splunk Lookup Tables

This directory contains CSV lookup tables used for enriching FortiGate security events in Splunk dashboards.

## Available Lookups

### fortinet_mitre_mapping.csv

**Purpose**: Maps FortiGate LogIDs to MITRE ATT&CK Framework tactics and techniques.

**Fields**:
- `logid` - FortiGate LogID (e.g., 0100044545, 0100032001)
- `event_type` - Event classification (config_add, utm_virus, traffic_deny, etc.)
- `tactic_id` - MITRE ATT&CK Tactic ID (e.g., TA0003)
- `tactic_name` - MITRE Tactic Name (e.g., Persistence, Defense Evasion)
- `technique_id` - MITRE ATT&CK Technique ID (e.g., T1098)
- `technique_name` - MITRE Technique Name (e.g., Account Manipulation)
- `description` - Human-readable description of the event
- `severity` - Severity level (critical, high, medium, low)

**Coverage**:
- Configuration Management Events (3 LogIDs)
- UTM Events (5 LogIDs - Virus, IPS, WebFilter, AppCtrl, Botnet)
- Traffic Events (3 LogIDs)
- Session Events (2 LogIDs)
- VPN Events (3 LogIDs)
- Admin Access Events (3 LogIDs)
- System Events (2 LogIDs)
- HA Events (2 LogIDs)

**Total**: 23 LogID mappings

## Usage in Splunk

### 1. Deploy Lookup Table

```bash
# Copy to Splunk lookups directory
cp lookups/fortinet_mitre_mapping.csv $SPLUNK_HOME/etc/apps/search/lookups/

# Or use Splunk Web UI:
# Settings → Lookups → Lookup table files → New Lookup Table File
```

### 2. Create Lookup Definition

In Splunk Web UI:
- Settings → Lookups → Lookup definitions → New Lookup Definition
- Name: `fortinet_mitre`
- Type: File-based
- Lookup file: `fortinet_mitre_mapping.csv`
- Supported fields: `logid`, `tactic_id`, `technique_id`

Or via `transforms.conf`:
```ini
[fortinet_mitre]
filename = fortinet_mitre_mapping.csv
case_sensitive_match = false
match_type = WILDCARD(logid)
```

### 3. Use in SPL Queries

**Basic Enrichment**:
```spl
index=fw
| lookup fortinet_mitre logid OUTPUT tactic_name, technique_name, severity
| table _time, logid, tactic_name, technique_name, severity, msg
```

**MITRE Dashboard Panel**:
```spl
index=fw
| lookup fortinet_mitre logid OUTPUT tactic_name, technique_id, technique_name
| stats count by tactic_name, technique_name
| sort - count
```

**High-Risk MITRE Events**:
```spl
index=fw
| lookup fortinet_mitre logid OUTPUT tactic_name, technique_name, severity
| where severity IN ("critical", "high")
| stats count by tactic_name, technique_name
| sort - count
```

## MITRE ATT&CK Framework Reference

- **Official Site**: https://attack.mitre.org/
- **Tactics**: 14 high-level categories (Initial Access, Execution, Persistence, etc.)
- **Techniques**: 200+ specific attack methods

### Tactic Coverage in This Lookup

| Tactic ID | Tactic Name | Techniques Mapped |
|-----------|-------------|-------------------|
| TA0001 | Initial Access | 3 |
| TA0003 | Persistence | 1 |
| TA0005 | Defense Evasion | 2 |
| TA0006 | Credential Access | 2 |
| TA0007 | Discovery | 2 |
| TA0009 | Collection | 1 |
| TA0010 | Exfiltration | 1 |
| TA0011 | Command and Control | 4 |
| TA0040 | Impact | 7 |

## Maintenance

### Adding New Mappings

1. Identify new FortiGate LogIDs from logs
2. Research MITRE ATT&CK framework for appropriate mapping
3. Add row to CSV with all required fields
4. Test in Splunk: `| inputlookup fortinet_mitre_mapping.csv | search logid=NEW_LOGID`
5. Reload lookup in Splunk: Settings → Lookups → Lookup table files → Actions → Reload

### Validation

```spl
| inputlookup fortinet_mitre_mapping.csv
| stats count by tactic_name
| sort - count
```

Expected: All 23 LogIDs mapped to 9 tactics.

## Integration with Dashboards

This lookup table is automatically used in:
- **MITRE ATT&CK Dashboard Panel** - Shows tactic/technique distribution
- **Enriched Event Tables** - Displays MITRE context alongside FortiGate events
- **Slack Alerts** - Includes MITRE information in critical event notifications

See `dashboards/fortinet-dashboard.xml` for implementation examples.

---

**Created**: 2025-10-21 (Phase 2 Optimization)
**Version**: 1.0.0
**Author**: Claude Code
