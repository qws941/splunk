#!/usr/bin/env python3
"""
Stanza 에러 검사 도구
Usage: ./check-stanza.py [conf_file]
"""

import configparser
import sys
from pathlib import Path

APP_DIR = Path("/home/jclee/app/splunk/security_alert")

# Stanza 검증 규칙
STANZA_RULES = {
    "alert_actions.conf": {
        "slack": {
            "required": ["is_custom", "python.version", "label"],
            "params": [
                "param.slack_app_oauth_token",
                "param.webhook_url",
                "param.proxy_enabled",
                "param.proxy_url",
                "param.proxy_port",
                "param.proxy_username",
                "param.proxy_password",
            ],
        }
    },
    "savedsearches.conf": {
        "alert": {  # 001_, 002_ 등으로 시작하는 모든 alert
            "required": ["search", "cron_schedule", "dispatch.earliest_time"],
            "optional": [
                "enableSched",
                "alert.track",
                "alert.severity",
                "action.slack",
            ],
        }
    },
    "transforms.conf": {
        "lookup": {  # _lookup으로 끝나는 모든 stanza
            "required": ["filename"],
            "optional": ["case_sensitive_match"],
        }
    },
}


def check_alert_actions(conf_file):
    """alert_actions.conf 검사"""
    print("\n🔍 Checking alert_actions.conf")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    config = configparser.ConfigParser(interpolation=None)
    config.read(conf_file)

    errors = []
    warnings = []

    if "slack" not in config:
        errors.append("❌ [slack] stanza not found")
        return errors, warnings

    slack = config["slack"]
    rules = STANZA_RULES["alert_actions.conf"]["slack"]

    # Required fields
    for field in rules["required"]:
        if field not in slack:
            errors.append(f"❌ [slack] missing required field: {field}")

    # Parameters
    for param in rules["params"]:
        if param not in slack:
            errors.append(f"❌ [slack] missing parameter: {param}")

    if not errors:
        print("✅ [slack] stanza OK")
        print(f"   - is_custom = {slack.get('is_custom')}")
        print(f"   - python.version = {slack.get('python.version')}")
        print(f"   - {len(rules['params'])} parameters defined")

    return errors, warnings


def check_savedsearches(conf_file):
    """savedsearches.conf 검사"""
    print("\n🔍 Checking savedsearches.conf")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    config = configparser.ConfigParser(interpolation=None)
    config.read(conf_file)

    import re

    alerts = [s for s in config.sections() if re.match(r"^\d{3}_", s)]

    print(f"Found {len(alerts)} alerts")
    print()

    errors = []
    warnings = []
    rules = STANZA_RULES["savedsearches.conf"]["alert"]

    for alert in alerts:
        alert_errors = []
        alert_config = config[alert]

        # Required fields
        for field in rules["required"]:
            if field not in alert_config:
                alert_errors.append(f"missing {field}")

        # Cron format check
        if "cron_schedule" in alert_config:
            cron = alert_config["cron_schedule"]
            fields = cron.split()
            if len(fields) != 5:
                alert_errors.append(f"invalid cron (has {len(fields)} fields, need 5)")

        # Display result
        if alert_errors:
            enabled = alert_config.get("enableSched", "1")
            status = "🟢" if enabled == "1" else "⚪"
            print(f"{status} ❌ [{alert}]")
            for err in alert_errors:
                print(f"      → {err}")
                errors.append(f"[{alert}] {err}")
        else:
            enabled = alert_config.get("enableSched", "1")
            status = "🟢" if enabled == "1" else "⚪"
            slack = "📱" if alert_config.get("action.slack") == "1" else "  "
            print(f"{status} {slack} [{alert}] OK")

    return errors, warnings


def check_transforms(conf_file):
    """transforms.conf 검사"""
    print("\n🔍 Checking transforms.conf")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    config = configparser.ConfigParser(interpolation=None)
    config.read(conf_file)

    lookups_dir = APP_DIR / "lookups"
    stanzas = config.sections()

    print(f"Found {len(stanzas)} lookup definitions")
    print()

    errors = []
    warnings = []

    for stanza in stanzas:
        stanza_config = config[stanza]

        if "filename" not in stanza_config:
            print(f"❌ [{stanza}] missing filename")
            errors.append(f"[{stanza}] missing filename")
            continue

        csv_file = lookups_dir / stanza_config["filename"]
        if not csv_file.exists():
            print(f"❌ [{stanza}] → {stanza_config['filename']} (file not found)")
            errors.append(f"[{stanza}] CSV file not found: {stanza_config['filename']}")
        else:
            size = csv_file.stat().st_size
            if size == 0:
                print(f"⚠️  [{stanza}] → {stanza_config['filename']} (empty file)")
                warnings.append(f"[{stanza}] CSV file is empty")
            else:
                print(f"✅ [{stanza}] → {stanza_config['filename']} ({size} bytes)")

    return errors, warnings


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔍 STANZA ERROR CHECKER")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if len(sys.argv) > 1:
        conf_name = sys.argv[1]
    else:
        # Check all
        conf_name = "all"

    all_errors = []
    all_warnings = []

    if conf_name in ["all", "alert_actions", "alert_actions.conf"]:
        conf_file = APP_DIR / "default/alert_actions.conf"
        if conf_file.exists():
            errors, warnings = check_alert_actions(conf_file)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

    if conf_name in ["all", "savedsearches", "savedsearches.conf"]:
        conf_file = APP_DIR / "default/savedsearches.conf"
        if conf_file.exists():
            errors, warnings = check_savedsearches(conf_file)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

    if conf_name in ["all", "transforms", "transforms.conf"]:
        conf_file = APP_DIR / "default/transforms.conf"
        if conf_file.exists():
            errors, warnings = check_transforms(conf_file)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

    # Summary
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 SUMMARY")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if all_errors:
        print(f"\n❌ ERRORS ({len(all_errors)}):")
        for err in all_errors:
            print(f"   {err}")

    if all_warnings:
        print(f"\n⚠️  WARNINGS ({len(all_warnings)}):")
        for warn in all_warnings:
            print(f"   {warn}")

    if not all_errors and not all_warnings:
        print("\n✅ All stanzas validated successfully")

    print()
    sys.exit(1 if all_errors else 0)


if __name__ == "__main__":
    main()
