#!/usr/bin/env python3
"""
AbuseIPDB Threat Intelligence Fetcher

Fetches IP reputation data from AbuseIPDB API and updates lookup table.
Designed to run as a Splunk scripted input or standalone cron job.

Installation:
1. Set API key: export ABUSEIPDB_API_KEY="your_api_key_here"
2. Configure cron: */30 * * * * /path/to/fetch_abuseipdb_intel.py
3. Or use as Splunk scripted input in inputs.conf

Usage:
  python3 fetch_abuseipdb_intel.py --source splunk
  python3 fetch_abuseipdb_intel.py --ips 192.168.1.100,10.0.0.50
  python3 fetch_abuseipdb_intel.py --batch /path/to/ips.txt

Phase 3.1 - External Threat Intelligence Integration
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Configuration
ABUSEIPDB_API_URL = "https://api.abuseipdb.com/api/v2/check"
ABUSEIPDB_BULK_URL = "https://api.abuseipdb.com/api/v2/check-block"
API_KEY = os.environ.get("ABUSEIPDB_API_KEY", "")
LOOKUP_FILE = os.path.join(os.path.dirname(__file__), "../lookups/abuseipdb_lookup.csv")
MAX_AGE_DAYS = 90  # Look back 90 days for abuse reports


def check_ip(ip_address, api_key=None):
    """
    Check single IP address against AbuseIPDB

    Args:
        ip_address: IP address to check
        api_key: AbuseIPDB API key (or use env var)

    Returns:
        dict: IP reputation data or None if error
    """
    if not api_key:
        api_key = API_KEY

    if not api_key:
        print("ERROR: ABUSEIPDB_API_KEY not set", file=sys.stderr)
        return None

    try:
        # Build request
        params = f"ipAddress={ip_address}&maxAgeInDays={MAX_AGE_DAYS}&verbose"
        url = f"{ABUSEIPDB_API_URL}?{params}"

        headers = {"Key": api_key, "Accept": "application/json"}

        req = Request(url, headers=headers)

        # Make API call
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        # Extract relevant fields
        ip_data = data.get("data", {})

        return {
            "ip": ip_address,
            "abuse_score": ip_data.get("abuseConfidenceScore", 0),
            "country": ip_data.get("countryCode", "Unknown"),
            "isp": ip_data.get("isp", "Unknown"),
            "usage_type": ip_data.get("usageType", "Unknown"),
            "domain": ip_data.get("domain", ""),
            "is_whitelisted": (
                "true" if ip_data.get("isWhitelisted", False) else "false"
            ),
            "total_reports": ip_data.get("totalReports", 0),
            "last_reported": ip_data.get("lastReportedAt", ""),
            "confidence_score": ip_data.get("abuseConfidenceScore", 0),
        }

    except HTTPError as e:
        print(f"ERROR: HTTP {e.code} for IP {ip_address}: {e.reason}", file=sys.stderr)
        return None
    except URLError as e:
        print(f"ERROR: Network error for IP {ip_address}: {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Failed to check IP {ip_address}: {e}", file=sys.stderr)
        return None


def fetch_from_splunk():
    """
    Fetch suspicious IPs from Splunk and check them

    Returns:
        list: List of IP reputation data
    """
    try:
        # Use Splunk REST API to get recent denied IPs
        # This requires splunk-sdk-python or direct API calls
        print("INFO: Fetching IPs from Splunk index=fw action=deny", file=sys.stderr)

        # For now, return empty list (requires Splunk SDK integration)
        # TODO: Implement Splunk REST API integration
        print("WARNING: Splunk integration not yet implemented", file=sys.stderr)
        return []

    except Exception as e:
        print(f"ERROR: Failed to fetch from Splunk: {e}", file=sys.stderr)
        return []


def update_lookup_table(ip_data_list):
    """
    Update AbuseIPDB lookup table CSV

    Args:
        ip_data_list: List of IP reputation dictionaries

    Returns:
        bool: Success status
    """
    if not ip_data_list:
        print("WARNING: No IP data to update", file=sys.stderr)
        return False

    try:
        # Read existing lookup data
        existing_data = {}
        if os.path.exists(LOOKUP_FILE):
            with open(LOOKUP_FILE, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("ip") and not row["ip"].startswith("#"):
                        existing_data[row["ip"]] = row

        # Merge new data (new data takes precedence)
        for ip_data in ip_data_list:
            existing_data[ip_data["ip"]] = ip_data

        # Write updated lookup table
        fieldnames = [
            "ip",
            "abuse_score",
            "country",
            "isp",
            "usage_type",
            "domain",
            "is_whitelisted",
            "total_reports",
            "last_reported",
            "confidence_score",
        ]

        with open(LOOKUP_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Sort by abuse score (highest first)
            sorted_data = sorted(
                existing_data.values(),
                key=lambda x: int(x.get("abuse_score", 0)),
                reverse=True,
            )

            for row in sorted_data:
                writer.writerow(row)

        print(
            f"SUCCESS: Updated {LOOKUP_FILE} with {len(existing_data)} IPs",
            file=sys.stderr,
        )
        return True

    except Exception as e:
        print(f"ERROR: Failed to update lookup table: {e}", file=sys.stderr)
        return False


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Fetch AbuseIPDB threat intelligence")
    parser.add_argument(
        "--source",
        choices=["splunk", "file", "cli"],
        default="cli",
        help="Source of IP addresses",
    )
    parser.add_argument("--ips", help="Comma-separated list of IP addresses")
    parser.add_argument("--batch", help="File containing IP addresses (one per line)")
    parser.add_argument("--api-key", help="AbuseIPDB API key (or use env var)")

    args = parser.parse_args()

    # Override API key if provided
    api_key = args.api_key or API_KEY
    if not api_key:
        print("ERROR: AbuseIPDB API key not provided", file=sys.stderr)
        print("   Set ABUSEIPDB_API_KEY env var or use --api-key", file=sys.stderr)
        sys.exit(1)

    ip_data_list = []

    # Fetch IPs from source
    if args.source == "splunk":
        ips = fetch_from_splunk()
    elif args.source == "file" and args.batch:
        with open(args.batch, "r") as f:
            ips = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    elif args.source == "cli" and args.ips:
        ips = [ip.strip() for ip in args.ips.split(",")]
    else:
        print("ERROR: No IP source provided", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Check each IP
    print(f"INFO: Checking {len(ips)} IP addresses...", file=sys.stderr)

    for ip in ips:
        print(f"INFO: Checking {ip}...", file=sys.stderr)
        ip_data = check_ip(ip, api_key)

        if ip_data:
            ip_data_list.append(ip_data)
            print(f"  ✓ {ip}: Abuse Score = {ip_data['abuse_score']}", file=sys.stderr)
        else:
            print(f"  ✗ {ip}: Failed to check", file=sys.stderr)

    # Update lookup table
    if ip_data_list:
        success = update_lookup_table(ip_data_list)
        sys.exit(0 if success else 1)
    else:
        print("ERROR: No IP data retrieved", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
