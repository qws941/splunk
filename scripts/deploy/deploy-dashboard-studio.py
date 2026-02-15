#!/usr/bin/env python3
"""
Dashboard Studio JSON Deployment Script
Purpose: Deploy Dashboard Studio JSON files via file copy + Splunk reload
Method: Direct file placement (REST API doesn't support Dashboard Studio JSON)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Configuration
SPLUNK_CONTAINER = "splunk-test"
DASHBOARD_DIR = "/home/jclee/app/splunk/configs/dashboards"
SPLUNK_VIEWS_DIR = "/opt/splunk/etc/apps/search/local/data/ui/views"


def validate_json(file_path):
    """Validate JSON file structure"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check for Dashboard Studio required fields
        required_fields = ["visualizations", "dataSources", "layout"]
        missing = [field for field in required_fields if field not in data]

        if missing:
            print(f"⚠️  Warning: Missing recommended fields: {', '.join(missing)}")
            print(
                "   (Dashboard Studio JSON should have: visualizations, dataSources, layout)"
            )

        return True, data
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False, None


def deploy_to_splunk(json_file, dashboard_name):
    """Deploy Dashboard Studio JSON to Splunk container"""
    print(f"\n📄 Deploying: {dashboard_name}")
    print(f"   Source: {json_file}")

    # Validate JSON
    is_valid, data = validate_json(json_file)
    if not is_valid:
        return False

    print("   ✅ JSON validated")

    # Create dashboard wrapper for Dashboard Studio
    dashboard_wrapper = {
        "title": dashboard_name,
        "description": f"Dashboard Studio: {dashboard_name}",
        "definition": data,
    }

    # Create temp file with wrapper
    temp_file = f"/tmp/{dashboard_name}.json"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(dashboard_wrapper, f, ensure_ascii=False, indent=2)

    # Copy to Splunk container
    try:
        # Create views directory if not exists (as root, then chown to splunk)
        cmd_mkdir = (
            f"docker exec -u root {SPLUNK_CONTAINER} mkdir -p {SPLUNK_VIEWS_DIR}"
        )
        subprocess.run(cmd_mkdir, shell=True, check=True, capture_output=True)

        # Fix ownership
        cmd_chown_dir = f"docker exec -u root {SPLUNK_CONTAINER} chown -R splunk:splunk /opt/splunk/etc/apps/search/local"
        subprocess.run(cmd_chown_dir, shell=True, check=True, capture_output=True)

        # Copy JSON file
        target_path = f"{SPLUNK_VIEWS_DIR}/{dashboard_name}.json"
        cmd_copy = f"docker cp {temp_file} {SPLUNK_CONTAINER}:{target_path}"
        subprocess.run(cmd_copy, shell=True, check=True, capture_output=True, text=True)

        print(f"   ✅ Copied to: {target_path}")

        # Set permissions
        cmd_chown = (
            f"docker exec -u root {SPLUNK_CONTAINER} chown splunk:splunk {target_path}"
        )
        subprocess.run(cmd_chown, shell=True, check=True, capture_output=True)

        # Reload Splunk dashboards (lightweight, no full restart)
        print("   🔄 Reloading Splunk dashboards...")
        cmd_reload = f"docker exec {SPLUNK_CONTAINER} /opt/splunk/bin/splunk refresh dashboard -auth admin:changeme"
        subprocess.run(cmd_reload, shell=True, check=False, capture_output=True)

        # Clean up temp file
        os.remove(temp_file)

        print(f"   ✅ Dashboard deployed: {dashboard_name}")
        print(
            f"   🌐 Access: https://localhost:8000/app/search/dashboard_{dashboard_name}"
        )

        return True

    except subprocess.CalledProcessError as e:
        print(f"   ❌ Deployment failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def main():
    print("=" * 70)
    print("🚀 Dashboard Studio JSON Deployment")
    print("   Method: File copy + Splunk reload (REST API limitation)")
    print("=" * 70)

    # Check if Splunk container is running
    result = subprocess.run(
        f"docker ps | grep {SPLUNK_CONTAINER}",
        shell=True,
        capture_output=True,
        text=True,
    )
    if SPLUNK_CONTAINER not in result.stdout:
        print(f"\n❌ Splunk container '{SPLUNK_CONTAINER}' is not running")
        print("   Start it with: docker start splunk-test")
        return 1

    print(f"\n✅ Splunk container '{SPLUNK_CONTAINER}' is running")

    # Find all JSON files in dashboard directory
    dashboard_files = []
    for file in Path(DASHBOARD_DIR).glob("*.json"):
        dashboard_files.append(file)

    if not dashboard_files:
        print(f"\n❌ No JSON dashboard files found in: {DASHBOARD_DIR}")
        return 1

    print(f"\n📊 Found {len(dashboard_files)} Dashboard Studio JSON file(s):")
    for i, file in enumerate(dashboard_files, 1):
        print(f"   {i}. {file.name} ({file.stat().st_size} bytes)")

    # Deploy each dashboard
    success_count = 0
    failed_count = 0

    for file in dashboard_files:
        dashboard_name = file.stem  # Filename without extension
        if deploy_to_splunk(str(file), dashboard_name):
            success_count += 1
        else:
            failed_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("📊 Deployment Summary")
    print("=" * 70)
    print(f"✅ Successfully deployed: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📁 Total processed: {len(dashboard_files)}")

    if success_count > 0:
        print("\n🌐 Access dashboards:")
        print("   https://localhost:8000/app/search/")
        print("   Navigate to: Dashboards → View All Dashboards")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
