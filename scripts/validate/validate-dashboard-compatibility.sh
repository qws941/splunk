#!/bin/bash
#
# Splunk Dashboard Compatibility Validator
# Purpose: Check Dashboard Studio JSON for version-specific features
# Author: JC Lee
# Date: 2025-10-25
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DASHBOARD_DIR="$PROJECT_ROOT/configs/dashboards/studio-production"

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Splunk Dashboard Compatibility Validator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# =============================================================================
# 1. Check Splunk Version Requirements
# =============================================================================

log_info "Checking Splunk version requirements..."

if command -v splunk &> /dev/null; then
  SPLUNK_VERSION=$(splunk version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  MAJOR_VERSION=$(echo "$SPLUNK_VERSION" | cut -d. -f1)
  MINOR_VERSION=$(echo "$SPLUNK_VERSION" | cut -d. -f2)

  log_info "Detected Splunk version: $SPLUNK_VERSION"

  if [[ $MAJOR_VERSION -ge 9 ]]; then
    log_success "Splunk $SPLUNK_VERSION supports Dashboard Studio"
  else
    log_error "Dashboard Studio requires Splunk 9.0+, found: $SPLUNK_VERSION"
    echo
    echo "RECOMMENDATION:"
    echo "  - Upgrade to Splunk 9.0 or higher"
    echo "  - Or use Legacy XML dashboards in configs/dashboards/production/"
    exit 1
  fi
else
  log_warning "Splunk CLI not found, skipping version check"
fi

echo

# =============================================================================
# 2. Validate Dashboard JSON Syntax
# =============================================================================

log_info "Validating JSON syntax..."

VALID_COUNT=0
INVALID_COUNT=0

for dashboard in "$DASHBOARD_DIR"/*.json; do
  if [[ -f "$dashboard" ]]; then
    dashboard_name=$(basename "$dashboard")

    if jq empty "$dashboard" 2>/dev/null; then
      log_success "Valid JSON: $dashboard_name"
      ((VALID_COUNT++))
    else
      log_error "Invalid JSON: $dashboard_name"
      ((INVALID_COUNT++))
      jq empty "$dashboard" 2>&1 | head -3
    fi
  fi
done

echo
log_info "JSON Validation: $VALID_COUNT valid, $INVALID_COUNT invalid"
echo

# =============================================================================
# 3. Check Version-Specific Features
# =============================================================================

log_info "Checking version-specific features..."

echo
echo "Feature Compatibility Matrix:"
echo "┌─────────────────────────────────┬──────────────┬────────────┐"
echo "│ Feature                         │ Min Version  │ Status     │"
echo "├─────────────────────────────────┼──────────────┼────────────┤"

check_feature() {
  local feature_name=$1
  local min_version=$2
  local search_pattern=$3
  local count=$(grep -r "$search_pattern" "$DASHBOARD_DIR" 2>/dev/null | wc -l)

  if [[ $count -gt 0 ]]; then
    printf "│ %-31s │ %-12s │ " "$feature_name" "$min_version"

    # Version comparison
    if [[ -n "${SPLUNK_VERSION:-}" ]]; then
      MIN_MAJOR=$(echo "$min_version" | cut -d. -f1)
      MIN_MINOR=$(echo "$min_version" | cut -d. -f2)

      if [[ $MAJOR_VERSION -gt $MIN_MAJOR ]] || \
         [[ $MAJOR_VERSION -eq $MIN_MAJOR && $MINOR_VERSION -ge $MIN_MINOR ]]; then
        echo -e "${GREEN}✅ OK${NC}       │"
      else
        echo -e "${RED}❌ FAIL${NC}     │"
        HAS_INCOMPATIBLE=1
      fi
    else
      echo -e "${YELLOW}⚠ UNKNOWN${NC}  │"
    fi
  fi
}

HAS_INCOMPATIBLE=0

# Dashboard Studio base
check_feature "Dashboard Studio (JSON)" "9.0" '"type": "viz\.'

# Visualization types
check_feature "Choropleth Map (geo)" "9.0" '"type": "viz.choropleth'
check_feature "Markdown panels" "9.0" '"type": "viz.markdown'
check_feature "Single Value sparklines" "9.0" '"sparklineValues"'
check_feature "Table row coloring" "9.0" '"rowColors"'

# SPL features
check_feature "REST API queries" "7.0" '| rest '
check_feature "tstats (accelerated)" "6.3" '| tstats '
check_feature "timechart" "4.0" '| timechart '

# Data model
check_feature "Data Models" "6.0" 'datamodel='

echo "└─────────────────────────────────┴──────────────┴────────────┘"
echo

if [[ $HAS_INCOMPATIBLE -eq 1 ]]; then
  log_error "Incompatible features detected for Splunk $SPLUNK_VERSION"
  exit 1
else
  log_success "All features compatible with Splunk $SPLUNK_VERSION"
fi

# =============================================================================
# 4. Check Index References
# =============================================================================

log_info "Checking index references..."

INDEXES=$(grep -roh 'index=[a-z_]*' "$DASHBOARD_DIR" 2>/dev/null | cut -d= -f2 | sort -u)

echo
echo "Required indexes:"
for idx in $INDEXES; do
  echo "  - $idx"
done

echo
log_warning "Ensure these indexes exist and contain data"
echo "  Test command: index=fw earliest=-1h | head 1"

echo

# =============================================================================
# 5. Check SPL Query Syntax
# =============================================================================

log_info "Checking SPL query syntax..."

# Extract all queries
QUERIES_FILE="/tmp/splunk-queries-$$.txt"
jq -r '.dataSources | to_entries[] | .value.options.query // empty' "$DASHBOARD_DIR"/*.json > "$QUERIES_FILE"

QUERY_COUNT=$(wc -l < "$QUERIES_FILE")
log_info "Found $QUERY_COUNT SPL queries"

# Check for common syntax issues
echo
echo "Syntax Checks:"

check_syntax() {
  local check_name=$1
  local pattern=$2
  local count=$(grep -c "$pattern" "$QUERIES_FILE" 2>/dev/null || echo "0")

  printf "  %-40s " "$check_name:"
  if [[ $count -gt 0 ]]; then
    echo -e "${GREEN}$count found${NC}"
  else
    echo -e "${BLUE}not used${NC}"
  fi
}

check_syntax "Pipes (|) usage" "|"
check_syntax "stats aggregations" "| stats"
check_syntax "timechart time series" "| timechart"
check_syntax "table output" "| table"
check_syntax "REST API calls" "| rest"
check_syntax "eval field calculations" "| eval"

rm -f "$QUERIES_FILE"

echo

# =============================================================================
# 6. Summary & Recommendations
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "Validation Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ -n "${SPLUNK_VERSION:-}" ]]; then
  log_success "Splunk Version: $SPLUNK_VERSION"
else
  log_warning "Splunk Version: Not detected (install Splunk CLI)"
fi

log_success "JSON Validation: $VALID_COUNT/$((VALID_COUNT + INVALID_COUNT)) passed"

if [[ $HAS_INCOMPATIBLE -eq 0 ]]; then
  log_success "Feature Compatibility: All features compatible"
else
  log_error "Feature Compatibility: Some features incompatible"
fi

echo
echo "NEXT STEPS:"
echo "  1. Deploy to test environment first"
echo "  2. Verify data in indexes: $INDEXES"
echo "  3. Test dashboard loading in Splunk Web UI"
echo "  4. Monitor for errors: index=_internal source=*splunkd.log dashboard=*"
echo
echo "DEPLOYMENT COMMAND:"
echo "  Splunk Web UI: Dashboards → Create New Dashboard → Dashboard Studio → Source → Paste JSON"
echo

log_success "Validation complete!"
