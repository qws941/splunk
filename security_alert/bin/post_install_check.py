#!/usr/bin/env python3
"""
Splunk App Post-Installation Verification Script
Purpose: Verify all critical dependencies and configurations after deployment
Run this immediately after extracting the app to Splunk
"""

import sys
import os
import subprocess
from pathlib import Path

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def check_item(name, status, detail=""):
    icon = f"{Colors.GREEN}✓" if status else f"{Colors.RED}✗"
    status_text = f"{Colors.GREEN}OK" if status else f"{Colors.RED}FAIL"
    print(f"{icon} {name:.<50} {status_text}{Colors.RESET}")
    if detail:
        print(f"  {Colors.YELLOW}→ {detail}{Colors.RESET}")
    return status

def check_python_modules():
    """Check required Python modules"""
    print_header("Python Modules Check")

    required = {
        'requests': 'pip install requests',
        'json': 'stdlib',
        'logging': 'stdlib',
        'os': 'stdlib',
        'sys': 'stdlib',
        'datetime': 'stdlib',
        'csv': 'stdlib',
        're': 'stdlib',
        'subprocess': 'stdlib',
        'gzip': 'stdlib'
    }

    all_ok = True
    for module, install_cmd in required.items():
        try:
            __import__(module)
            check_item(f"Module: {module}", True)
        except ImportError:
            all_ok = False
            detail = f"Install: {install_cmd}" if install_cmd != 'stdlib' else "Missing stdlib module!"
            check_item(f"Module: {module}", False, detail)

    return all_ok

def check_file_structure():
    """Check critical file structure"""
    print_header("File Structure Check")

    app_root = Path(__file__).parent.parent

    critical_files = {
        'default/app.conf': 'App configuration',
        'default/savedsearches.conf': '15 alert definitions',
        'default/macros.conf': 'LogID macros',
        'default/transforms.conf': 'Lookup definitions',
        'default/alert_actions.conf': 'Slack configuration',
        'bin/slack.py': 'Slack alert action',
        'bin/fortigate_auto_response.py': 'Auto-response engine',
        'lookups/vpn_state_tracker.csv': 'State tracker',
    }

    all_ok = True
    for file_path, description in critical_files.items():
        full_path = app_root / file_path
        exists = full_path.exists()
        check_item(f"{file_path}", exists, description)
        if not exists:
            all_ok = False

    return all_ok

def check_csv_permissions():
    """Check CSV file permissions"""
    print_header("CSV File Permissions Check")

    app_root = Path(__file__).parent.parent
    lookups_dir = app_root / 'lookups'

    if not lookups_dir.exists():
        check_item("lookups/ directory", False, "Directory not found!")
        return False

    csv_files = list(lookups_dir.glob('*.csv'))
    all_ok = True

    for csv_file in csv_files:
        stat_info = csv_file.stat()
        mode = oct(stat_info.st_mode)[-3:]

        # Check if readable/writable (should be 644 or 664)
        is_readable = mode[0] == '6' and mode[1] in ['4', '6']
        check_item(f"{csv_file.name} (mode: {mode})", is_readable)
        if not is_readable:
            all_ok = False

    return all_ok

def check_python_scripts():
    """Check Python scripts are executable"""
    print_header("Python Scripts Check")

    app_root = Path(__file__).parent.parent
    bin_dir = app_root / 'bin'

    scripts = [
        'slack.py',
        'fortigate_auto_response.py',
        'splunk_feature_checker.py',
        'deployment_health_check.py',
        'auto_validator.py'
    ]

    all_ok = True
    for script in scripts:
        script_path = bin_dir / script
        if script_path.exists():
            # Try to compile
            try:
                with open(script_path) as f:
                    compile(f.read(), script_path, 'exec')
                check_item(f"{script}", True, "Syntax OK")
            except SyntaxError as e:
                check_item(f"{script}", False, f"Syntax error: {e}")
                all_ok = False
        else:
            check_item(f"{script}", False, "File not found")
            all_ok = False

    return all_ok

def check_environment_variables():
    """Check critical environment variables"""
    print_header("Environment Variables Check")

    # These are optional but recommended
    env_vars = {
        'SLACK_WEBHOOK_URL': 'Optional - Slack webhook for alerts',
        'FORTIMANAGER_URL': 'Optional - FortiManager for auto-response',
        'FORTIMANAGER_TOKEN': 'Optional - FortiManager API token'
    }

    for var, description in env_vars.items():
        value = os.environ.get(var)
        if value:
            masked = value[:10] + '***' if len(value) > 10 else '***'
            check_item(f"{var}", True, f"Set: {masked}")
        else:
            check_item(f"{var}", False, f"Not set - {description}")

    # Always return True since these are optional
    return True

def check_savedsearches():
    """Count and validate saved searches"""
    print_header("Saved Searches Check")

    app_root = Path(__file__).parent.parent
    savedsearches = app_root / 'default' / 'savedsearches.conf'

    if not savedsearches.exists():
        check_item("savedsearches.conf", False, "File not found!")
        return False

    with open(savedsearches) as f:
        content = f.read()

    # Count alert definitions (stanzas starting with [)
    import re
    alerts = re.findall(r'^\[([^\]]+)\]', content, re.MULTILINE)
    alerts = [a for a in alerts if not a.startswith('default')]

    expected_count = 15
    actual_count = len(alerts)

    is_ok = actual_count >= expected_count
    detail = f"Found {actual_count} alerts (expected {expected_count})"
    check_item("Alert definitions", is_ok, detail)

    # Check for critical macros
    macros_to_check = ['fortigate_index', 'enrich_with_logid_lookup']
    all_macros_found = all(f'`{macro}`' in content for macro in macros_to_check)
    check_item("Critical macros used", all_macros_found)

    return is_ok and all_macros_found

def check_slack_config():
    """Check Slack configuration"""
    print_header("Slack Configuration Check")

    app_root = Path(__file__).parent.parent

    # Check default config
    default_config = app_root / 'default' / 'alert_actions.conf'
    local_config = app_root / 'local' / 'alert_actions.conf'

    webhook_configured = False

    # Check local config first (overrides default)
    if local_config.exists():
        with open(local_config) as f:
            content = f.read()
            if 'param.webhook_url' in content and 'hooks.slack.com' in content:
                webhook_configured = True
                check_item("Slack webhook (local)", True, "Configured in local/alert_actions.conf")

    if not webhook_configured:
        check_item("Slack webhook", False,
                  "⚠️  Set webhook_url in local/alert_actions.conf before enabling alerts!")

    # Check environment variable fallback
    env_webhook = os.environ.get('SLACK_WEBHOOK_URL')
    if env_webhook:
        check_item("Slack webhook (env)", True, "Set via SLACK_WEBHOOK_URL")
        webhook_configured = True

    return True  # Non-critical for initial deployment

def generate_deployment_commands():
    """Generate deployment commands"""
    print_header("Deployment Commands")

    print(f"{Colors.YELLOW}Required steps after uploading to Splunk:{Colors.RESET}\n")

    print("1. Set Slack webhook URL:")
    print("   vim /opt/splunk/etc/apps/security_alert/local/alert_actions.conf")
    print("   # Set: param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL\n")

    print("2. Set permissions:")
    print("   chown -R splunk:splunk /opt/splunk/etc/apps/security_alert")
    print("   chmod 664 /opt/splunk/etc/apps/security_alert/lookups/*.csv\n")

    print("3. Verify index exists:")
    print("   /opt/splunk/bin/splunk list index | grep fw")
    print("   # If not exists: /opt/splunk/bin/splunk add index fw\n")

    print("4. Restart Splunk:")
    print("   /opt/splunk/bin/splunk restart\n")

    print("5. Verify app loaded:")
    print("   /opt/splunk/bin/splunk display app security_alert\n")

def main():
    print_header("Splunk App Post-Installation Check")
    print(f"{Colors.YELLOW}App: Security Alert System v2.0.4{Colors.RESET}")
    print(f"{Colors.YELLOW}Purpose: Verify deployment readiness{Colors.RESET}\n")

    results = {
        'Python Modules': check_python_modules(),
        'File Structure': check_file_structure(),
        'CSV Permissions': check_csv_permissions(),
        'Python Scripts': check_python_scripts(),
        'Environment Variables': check_environment_variables(),
        'Saved Searches': check_savedsearches(),
        'Slack Configuration': check_slack_config(),
    }

    # Summary
    print_header("Summary")

    passed = sum(results.values())
    total = len(results)

    for check, status in results.items():
        icon = f"{Colors.GREEN}✓" if status else f"{Colors.RED}✗"
        print(f"{icon} {check}{Colors.RESET}")

    print(f"\n{Colors.BLUE}Result: {passed}/{total} checks passed{Colors.RESET}\n")

    if passed == total:
        print(f"{Colors.GREEN}✓ App is ready for deployment!{Colors.RESET}\n")
    else:
        print(f"{Colors.RED}✗ Fix the issues above before deploying{Colors.RESET}\n")

    generate_deployment_commands()

    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
