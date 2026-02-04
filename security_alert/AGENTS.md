# SECURITY_ALERT KNOWLEDGE BASE

**Scope:** Core Splunk app for FortiGate security alerting

## OVERVIEW

Splunk app with 15 saved searches, EMS state tracking, and Slack Block Kit notifications. Packaged as tarball for deployment.

## STRUCTURE

```
security_alert/
├── bin/                 # Python alert handlers
│   ├── slack_blockkit_alert.py   # Main Slack notifier (283 LOC)
│   ├── auto_validator.py         # Config integrity (390 LOC)
│   ├── deployment_health_check.py # Health check (533 LOC)
│   └── splunk_feature_checker.py  # Feature detection (727 LOC) ★
├── default/             # Splunk configs
│   ├── savedsearches.conf        # 15 alerts (~800 LOC)
│   ├── macros.conf               # SPL parameters (~150 LOC)
│   ├── transforms.conf           # Field extractions
│   └── alert_actions.conf        # Slack action config
├── local/               # Instance-specific (gitignored)
└── lookups/             # State tracking CSVs (13 files)
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new alert | `default/savedsearches.conf` |
| Modify LogID mappings | `default/macros.conf` → `[logids_*]` |
| Change Slack format | `bin/slack_blockkit_alert.py` |
| Add state tracker | `lookups/` (CSV) + update EMS join |

## ALERT NAMING

```
0XX_Alert_Name
│└─ 3-digit prefix (001-017)
└── Underscore separator
```

| Range | Type |
|-------|------|
| 001-005 | Event-driven |
| 006-010 | Threshold-based |
| 011-015 | Binary state |
| 016-017 | Hybrid |

## EMS STATE PATTERN

```spl
| eval current_state = ...
| join type=left device 
    [| inputlookup {tracker}.csv]
| eval changed = if(current_state != previous_state, 1, 0)
| where changed = 1
| outputlookup {tracker}.csv
```

## CONVENTIONS

| Rule | Convention |
|------|------------|
| Cron format | 5-field only: `*/5 * * * *` |
| Macro syntax | Backtick: `` `macro_name` `` |
| Suppression | `suppress.by_device = true` |
| Severity | 1-5 (1=critical) |

## ANTI-PATTERNS

| NEVER | Use Instead |
|-------|-------------|
| `print()` in bin/*.py | `sys.stderr.write()` |
| Tokens in `default/` | `local/` (gitignored) |
| 6-field cron | 5-field (no seconds) |
| Edit `local/` in git | Instance-specific, excluded |
| Modify `bin/lib/` | Vendored dependencies |

## LOOKUPS

| File | Tracks |
|------|--------|
| `vpn_state_tracker.csv` | VPN connection states |
| `admin_login_tracker.csv` | Admin login events |
| `threat_state_tracker.csv` | Threat detection states |

## REFACTOR CANDIDATES

| File | LOC | Issue |
|------|-----|-------|
| `splunk_feature_checker.py` | 727 | HIGH complexity, split needed |
| `deployment_health_check.py` | 533 | MEDIUM-HIGH, modularize |

## VIOLATIONS (KNOWN)

- 6 bin/*.py files use `print()` instead of `sys.stderr.write()`
- Should be fixed to comply with Splunk alert protocol
