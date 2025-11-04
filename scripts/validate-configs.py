#!/usr/bin/env python3
"""
Validate Splunk configuration files without btool
"""

import configparser
import os
import sys
import re
from pathlib import Path

APP_DIR = Path("/home/jclee/app/splunk/security_alert")

def validate_alert_actions():
    """Validate alert_actions.conf"""
    print("📋 Validating alert_actions.conf...")

    conf_file = APP_DIR / "default/alert_actions.conf"
    spec_file = APP_DIR / "README/alert_actions.conf.spec"

    if not conf_file.exists():
        print("  ❌ alert_actions.conf not found")
        return False

    if not spec_file.exists():
        print("  ❌ alert_actions.conf.spec not found")
        return False

    config = configparser.ConfigParser()
    config.read(conf_file)

    # Check [slack] stanza exists
    if 'slack' not in config:
        print("  ❌ [slack] stanza not found")
        return False

    slack = config['slack']

    # Required fields
    required = {
        'is_custom': '1',
        'python.version': 'python3'
    }

    for key, expected in required.items():
        if key not in slack:
            print(f"  ❌ Missing required field: {key}")
            return False
        if slack[key] != expected:
            print(f"  ⚠️  {key} = {slack[key]} (expected: {expected})")

    # Check parameters
    params = [
        'param.slack_app_oauth_token',
        'param.webhook_url',
        'param.proxy_enabled',
        'param.proxy_url',
        'param.proxy_port',
        'param.proxy_username',
        'param.proxy_password'
    ]

    for param in params:
        if param not in slack:
            print(f"  ❌ Missing parameter: {param}")
            return False

    print("  ✅ alert_actions.conf OK")
    return True

def validate_transforms():
    """Validate transforms.conf"""
    print("\n📋 Validating transforms.conf...")

    conf_file = APP_DIR / "default/transforms.conf"
    lookups_dir = APP_DIR / "lookups"

    if not conf_file.exists():
        print("  ❌ transforms.conf not found")
        return False

    config = configparser.ConfigParser()
    config.read(conf_file)

    errors = []

    for stanza in config.sections():
        if 'filename' in config[stanza]:
            csv_file = lookups_dir / config[stanza]['filename']
            if not csv_file.exists():
                errors.append(f"  ❌ [{stanza}] references missing file: {config[stanza]['filename']}")

    if errors:
        for err in errors:
            print(err)
        return False

    print(f"  ✅ transforms.conf OK ({len(config.sections())} lookups)")
    return True

def validate_python_scripts():
    """Validate Python scripts"""
    print("\n📋 Validating Python scripts...")

    bin_dir = APP_DIR / "bin"

    if not bin_dir.exists():
        print("  ❌ bin/ directory not found")
        return False

    scripts = list(bin_dir.glob("*.py"))

    if not scripts:
        print("  ❌ No Python scripts found")
        return False

    errors = []

    for script in scripts:
        # Check if executable
        if not os.access(script, os.X_OK):
            errors.append(f"  ⚠️  {script.name} not executable")

        # Try to compile
        try:
            with open(script, 'r') as f:
                compile(f.read(), script.name, 'exec')
        except SyntaxError as e:
            errors.append(f"  ❌ {script.name} syntax error: {e}")

    if errors:
        for err in errors:
            print(err)
        return False

    print(f"  ✅ Python scripts OK ({len(scripts)} files)")
    return True

def validate_savedsearches():
    """Validate savedsearches.conf"""
    print("\n📋 Validating savedsearches.conf...")

    conf_file = APP_DIR / "default/savedsearches.conf"

    if not conf_file.exists():
        print("  ❌ savedsearches.conf not found")
        return False

    config = configparser.ConfigParser()
    config.read(conf_file)

    alerts = [s for s in config.sections() if s.startswith(('0', '1'))]

    if not alerts:
        print("  ⚠️  No alerts found")
        return False

    errors = []

    for alert in alerts:
        # Check cron_schedule format (5 fields)
        if 'cron_schedule' in config[alert]:
            cron = config[alert]['cron_schedule']
            fields = cron.split()
            if len(fields) != 5:
                errors.append(f"  ❌ [{alert}] invalid cron_schedule: {cron} (need 5 fields)")

        # Check required fields
        if 'search' not in config[alert]:
            errors.append(f"  ❌ [{alert}] missing 'search' field")

    if errors:
        for err in errors[:10]:  # Limit to 10 errors
            print(err)
        return False

    print(f"  ✅ savedsearches.conf OK ({len(alerts)} alerts)")
    return True

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔍 VALIDATING SPLUNK APP CONFIGURATION")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\nApp directory: {APP_DIR}")

    if not APP_DIR.exists():
        print(f"❌ App directory not found: {APP_DIR}")
        sys.exit(1)

    results = []

    results.append(validate_alert_actions())
    results.append(validate_transforms())
    results.append(validate_python_scripts())
    results.append(validate_savedsearches())

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 VALIDATION SUMMARY")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"\n✅ All checks passed ({passed}/{total})")
        sys.exit(0)
    else:
        print(f"\n❌ Some checks failed ({passed}/{total} passed)")
        sys.exit(1)

if __name__ == "__main__":
    main()
