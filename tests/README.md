# Test Suite

## Overview

This directory will contain test files for validating alert logic, SPL queries, and Python scripts.

## Planned Tests

### 1. SPL Validation Tests
- Syntax validation for all 15 alerts
- LogID macro completeness
- State tracker logic verification

### 2. Python Unit Tests
- Slack message formatting
- CSV state tracker operations
- Error handling

### 3. Integration Tests
- End-to-end alert workflow
- Slack webhook delivery
- State persistence

### 4. Performance Tests
- Alert execution time (<60s)
- State tracker scalability (>10,000 rows)
- Concurrent alert handling

## Test Data

*To be added: Sample FortiGate log files for testing*

## Running Tests

```bash
# Validate all alert SPL
splunk btool savedsearches list --debug

# Test specific alert
splunk search "`fortigate_index` `logids_vpn_tunnel` earliest=-1h | head 10"

# Verify state trackers
for csv in lookups/*_state_tracker.csv; do
  echo "Testing $csv..."
  splunk search "| inputlookup $(basename $csv) | stats count"
done
```

## Test Coverage

*To be added: Coverage reports and metrics*
