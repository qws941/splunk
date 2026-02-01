# SECURITY_ALERT KNOWLEDGE BASE

**Parent:** [../AGENTS.md](../AGENTS.md)

## OVERVIEW

Core Splunk app for FortiGate security alerting. 15 alerts with EMS state tracking and Slack Block Kit integration.

## STRUCTURE

```
security_alert/
├── bin/                  # Python handlers (5 scripts)
│   ├── slack_blockkit_alert.py      # Slack formatter (283 LOC)
│   ├── auto_validator.py            # Config validator (390 LOC)
│   ├── deployment_health_check.py   # Health check (533 LOC)
│   ├── splunk_feature_checker.py    # Feature detection (727 LOC)
│   └── fortigate_auto_response.py   # Auto-response (optional)
├── default/              # Read-only app configs
│   ├── savedsearches.conf  # 15 alert definitions
│   ├── macros.conf         # Centralized SPL params
│   ├── transforms.conf     # Lookup definitions
│   ├── alert_actions.conf  # Slack action spec
│   └── props.conf          # Field extractions
├── local/                # User overrides (gitignored)
└── lookups/              # CSV state trackers (13 files)
```

## ALERT CATEGORIES

| Range | Type | Count | Pattern |
|-------|------|-------|---------|
| 001-005 | Event-driven | 5 | Single event triggers |
| 006-010 | Threshold | 3 | Baseline anomaly detection |
| 011-015 | Binary state | 4 | EMS state tracking |
| 016-017 | Hybrid | 3 | State tracking only (enableSched=0) |

## WHERE TO LOOK

| Task | File | Stanza/Section |
|------|------|----------------|
| Add new alert | `default/savedsearches.conf` | Copy existing, change 0XX |
| Add LogID group | `default/macros.conf` | `[logids_*]` section |
| Map LogID metadata | `lookups/fortigate_logid_notification_map.csv` | Add row |
| Change thresholds | `default/macros.conf` | `[*_threshold]` stanzas |
| Modify Slack format | `bin/slack_blockkit_alert.py` | `blocks` array (line 62-167) |

## EMS STATE TRACKING PATTERN

```spl
# Binary state alerts use this pattern to prevent duplicates
| eval current_state = if(condition, "DOWN", "UP")
| join device [| inputlookup *_state_tracker]
| eval changed = if(prev_state != current_state, 1, 0)
| where changed=1
| outputlookup append=t *_state_tracker
```

**State CSV format:**
```csv
device,prev_state,current_state,last_change,_key
firewall-01,DOWN,UP,2025-11-04 10:35:12,firewall-01_vpn1
```

## ANTI-PATTERNS

| NEVER | Why | Do Instead |
|-------|-----|------------|
| `print()` in bin/*.py | Breaks Splunk protocol | Use `sys.stderr.write()` |
| Tokens in `default/` | Exposes credentials | Use `local/` (gitignored) |
| Edit `local/` in Git | User-specific overrides | Only edit `default/` |
| 6-field cron | Splunk uses 5-field | `* * * * *` format |

## CONVENTIONS

| Item | Format | Example |
|------|--------|---------|
| Alert name | `0XX_Description` | `002_VPN_Tunnel` |
| Macro call | Backticks | `` `fortigate_index` `` |
| Cron schedule | 5-field | `*/5 * * * *` |
| Suppression | By device | `alert.suppress.fields = device` |

## PYTHON SCRIPT REQUIREMENTS

```python
# All bin/*.py scripts must:
# 1. Use Python 3 (python.version = python3 in alert_actions.conf)
# 2. Handle gzipped input (Splunk passes compressed results)
# 3. Exit 0 on success, non-zero on failure
# 4. Never use print() - use sys.stderr for debugging
```

## CRITICAL CONFIGS

### savedsearches.conf (Alert Definition)

```ini
[002_VPN_Tunnel]
search = `fortigate_index` `logids_vpn_tunnel` \
| `enrich_with_logid_lookup` \
| eval current_state = ...
cron_schedule = * * * * *
enableSched = 1
action.slack = 1
action.slack.param.channel = #security-firewall-alert
```

### macros.conf (Centralized Params)

```ini
[fortigate_index]
definition = index=fw

[logids_vpn_tunnel]
definition = (logid=0101037124 OR logid=0101037131)

[cpu_high_threshold]
definition = 80
```

## DEPLOYMENT

```bash
# From repository root
tar -czf security_alert.tar.gz security_alert/

# Install via Splunk Web UI or CLI
# Web: Apps → Manage Apps → Install from file
# CLI: tar -xzf security_alert.tar.gz -C /opt/splunk/etc/apps/
```
