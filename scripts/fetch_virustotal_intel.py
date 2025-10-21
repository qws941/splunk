#!/usr/bin/env python3
"""
VirusTotal File Hash Intelligence Fetcher

Fetches file hash reputation data from VirusTotal API and updates lookup table.
Designed to run on-demand when new file hashes are detected in FortiGate logs.

Installation:
1. Set API key: export VIRUSTOTAL_API_KEY="your_api_key_here"
2. Run on-demand or via Splunk scripted input

Usage:
  python3 fetch_virustotal_intel.py --hash a1b2c3d4...
  python3 fetch_virustotal_intel.py --batch /path/to/hashes.txt
  python3 fetch_virustotal_intel.py --source splunk

Phase 3.1 - External Threat Intelligence Integration
"""

import os
import sys
import json
import csv
import argparse
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import time

# Configuration
VIRUSTOTAL_API_URL = "https://www.virustotal.com/api/v3/files/{hash}"
API_KEY = os.environ.get('VIRUSTOTAL_API_KEY', '')
LOOKUP_FILE = os.path.join(os.path.dirname(__file__), '../lookups/virustotal_lookup.csv')
API_RATE_LIMIT = 4  # Free tier: 4 requests per minute

def check_file_hash(file_hash, api_key=None):
    """
    Check file hash against VirusTotal

    Args:
        file_hash: SHA256 file hash
        api_key: VirusTotal API key (or use env var)

    Returns:
        dict: File reputation data or None if error
    """
    if not api_key:
        api_key = API_KEY

    if not api_key:
        print("ERROR: VIRUSTOTAL_API_KEY not set", file=sys.stderr)
        return None

    try:
        # Build request
        url = VIRUSTOTAL_API_URL.format(hash=file_hash)

        headers = {
            'x-apikey': api_key,
            'Accept': 'application/json'
        }

        req = Request(url, headers=headers)

        # Make API call
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Extract file analysis data
        attributes = data.get('data', {}).get('attributes', {})
        last_analysis = attributes.get('last_analysis_stats', {})
        file_info = attributes.get('type_description', '')
        file_size = attributes.get('size', 0)

        # Calculate detection rate
        malicious = last_analysis.get('malicious', 0)
        total = sum(last_analysis.values())
        detection_rate = f"{malicious}/{total}" if total > 0 else "0/0"

        # Determine threat category
        if malicious == 0:
            threat_category = 'clean'
        elif malicious < 5:
            threat_category = 'suspicious'
        else:
            threat_category = 'malicious'

        # Extract malware type and family
        malware_type = 'Unknown'
        malware_family = ''
        vendor_detections = []

        results = attributes.get('last_analysis_results', {})
        for vendor, result in results.items():
            if result.get('category') == 'malicious':
                vendor_detections.append(vendor)
                if not malware_type or malware_type == 'Unknown':
                    malware_type = result.get('result', 'Unknown').split('.')[0]

        # Get timestamps
        first_seen = attributes.get('first_submission_date', '')
        last_seen = attributes.get('last_analysis_date', '')

        if first_seen:
            first_seen = datetime.fromtimestamp(first_seen).isoformat() + 'Z'
        if last_seen:
            last_seen = datetime.fromtimestamp(last_seen).isoformat() + 'Z'

        return {
            'hash': file_hash,
            'detection_rate': detection_rate,
            'malware_type': malware_type,
            'malware_family': malware_family,
            'first_seen': first_seen,
            'last_seen': last_seen,
            'vendor_detections': ','.join(vendor_detections[:10]),  # Top 10 vendors
            'file_type': file_info,
            'file_size': str(file_size),
            'threat_category': threat_category
        }

    except HTTPError as e:
        if e.code == 404:
            print(f"INFO: Hash {file_hash} not found in VirusTotal", file=sys.stderr)
        else:
            print(f"ERROR: HTTP {e.code} for hash {file_hash}: {e.reason}", file=sys.stderr)
        return None
    except URLError as e:
        print(f"ERROR: Network error for hash {file_hash}: {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Failed to check hash {file_hash}: {e}", file=sys.stderr)
        return None

def fetch_from_splunk():
    """
    Fetch file hashes from Splunk FortiGate logs

    Returns:
        list: List of file hashes
    """
    try:
        print("INFO: Fetching file hashes from Splunk index=fw", file=sys.stderr)

        # For now, return empty list (requires Splunk SDK integration)
        # TODO: Implement Splunk REST API integration
        # Query: index=fw filehash=* | dedup filehash | table filehash
        print("WARNING: Splunk integration not yet implemented", file=sys.stderr)
        return []

    except Exception as e:
        print(f"ERROR: Failed to fetch from Splunk: {e}", file=sys.stderr)
        return []

def update_lookup_table(hash_data_list):
    """
    Update VirusTotal lookup table CSV

    Args:
        hash_data_list: List of file hash reputation dictionaries

    Returns:
        bool: Success status
    """
    if not hash_data_list:
        print("WARNING: No hash data to update", file=sys.stderr)
        return False

    try:
        # Read existing lookup data
        existing_data = {}
        if os.path.exists(LOOKUP_FILE):
            with open(LOOKUP_FILE, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('hash') and not row['hash'].startswith('#'):
                        existing_data[row['hash']] = row

        # Merge new data (new data takes precedence)
        for hash_data in hash_data_list:
            existing_data[hash_data['hash']] = hash_data

        # Write updated lookup table
        fieldnames = ['hash', 'detection_rate', 'malware_type', 'malware_family',
                      'first_seen', 'last_seen', 'vendor_detections', 'file_type',
                      'file_size', 'threat_category']

        with open(LOOKUP_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Sort by threat category (malicious first)
            category_order = {'malicious': 0, 'suspicious': 1, 'clean': 2}
            sorted_data = sorted(existing_data.values(),
                               key=lambda x: category_order.get(x.get('threat_category', 'clean'), 3))

            for row in sorted_data:
                writer.writerow(row)

        print(f"SUCCESS: Updated {LOOKUP_FILE} with {len(existing_data)} hashes", file=sys.stderr)
        return True

    except Exception as e:
        print(f"ERROR: Failed to update lookup table: {e}", file=sys.stderr)
        return False

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Fetch VirusTotal file hash intelligence')
    parser.add_argument('--source', choices=['splunk', 'file', 'cli'], default='cli',
                       help='Source of file hashes')
    parser.add_argument('--hash', help='Single file hash (SHA256)')
    parser.add_argument('--batch', help='File containing hashes (one per line)')
    parser.add_argument('--api-key', help='VirusTotal API key (or use env var)')

    args = parser.parse_args()

    # Override API key if provided
    api_key = args.api_key or API_KEY
    if not api_key:
        print("ERROR: VirusTotal API key not provided", file=sys.stderr)
        print("   Set VIRUSTOTAL_API_KEY env var or use --api-key", file=sys.stderr)
        sys.exit(1)

    hash_data_list = []

    # Fetch hashes from source
    if args.source == 'splunk':
        hashes = fetch_from_splunk()
    elif args.source == 'file' and args.batch:
        with open(args.batch, 'r') as f:
            hashes = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    elif args.source == 'cli' and args.hash:
        hashes = [args.hash]
    else:
        print("ERROR: No hash source provided", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Check each hash (respect API rate limit)
    print(f"INFO: Checking {len(hashes)} file hashes...", file=sys.stderr)
    print(f"INFO: API rate limit: {API_RATE_LIMIT} requests/minute", file=sys.stderr)

    for i, file_hash in enumerate(hashes):
        # Rate limiting (free tier: 4 requests/minute)
        if i > 0 and i % API_RATE_LIMIT == 0:
            print(f"INFO: Rate limit pause (60 seconds)...", file=sys.stderr)
            time.sleep(60)

        print(f"INFO: Checking {file_hash}...", file=sys.stderr)
        hash_data = check_file_hash(file_hash, api_key)

        if hash_data:
            hash_data_list.append(hash_data)
            print(f"  ✓ {file_hash}: {hash_data['threat_category']} ({hash_data['detection_rate']})", file=sys.stderr)
        else:
            print(f"  ✗ {file_hash}: Failed to check or not found", file=sys.stderr)

    # Update lookup table
    if hash_data_list:
        success = update_lookup_table(hash_data_list)
        sys.exit(0 if success else 1)
    else:
        print("ERROR: No hash data retrieved", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
