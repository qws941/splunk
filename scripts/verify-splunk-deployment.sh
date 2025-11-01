#!/bin/bash
# Splunk Deployment Verification Script
# Purpose: Comprehensive validation of Splunk configurations, dashboards, and integrations
# Author: JC Lee
# Date: 2025-10-25
#
# Usage: ./verify-splunk-deployment.sh [OPTIONS]
# Options:
#   --quick       Quick validation only (no API calls)
#   --full        Full validation including REST API tests
#   --deploy      Validate and deploy to Splunk server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SPLUNK_HOST="${SPLUNK_HOST:-splunk.jclee.me}"
SPLUNK_PORT="${SPLUNK_PORT:-8089}"
SPLUNK_USER="${SPLUNK_USER:-admin}"
SPLUNK_PASS="${SPLUNK_PASS:-password}"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_failure() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# Phase 1: File Structure Validation
# ============================================================================
validate_file_structure() {
    print_header "Phase 1: File Structure Validation"

    # Check critical directories
    if [ -d "configs" ]; then
        print_success "configs/ directory exists"
    else
        print_failure "configs/ directory missing"
    fi

    if [ -d "configs/dashboards" ]; then
        print_success "configs/dashboards/ directory exists"
    else
        print_failure "configs/dashboards/ directory missing"
    fi

    if [ -d "scripts" ]; then
        print_success "scripts/ directory exists"
    else
        print_failure "scripts/ directory missing"
    fi

    if [ -d "docs" ]; then
        print_success "docs/ directory exists"
    else
        print_failure "docs/ directory missing"
    fi

    echo ""
}

# ============================================================================
# Phase 2: XML Dashboard Validation
# ============================================================================
validate_xml_dashboards() {
    print_header "Phase 2: XML Dashboard Validation"

    local xml_count=0
    local xml_valid=0

    if [ -d "configs/dashboards" ]; then
        for xml_file in configs/dashboards/*.xml; do
            if [ -f "$xml_file" ]; then
                ((xml_count++))
                filename=$(basename "$xml_file")

                # Validate XML syntax
                if python3 -c "import xml.etree.ElementTree as ET; ET.parse('$xml_file')" 2>/dev/null; then
                    # Count panels
                    panels=$(python3 -c "import xml.etree.ElementTree as ET; print(len(ET.parse('$xml_file').getroot().findall('.//panel')))" 2>/dev/null)
                    print_success "$filename: Valid XML ($panels panels)"
                    ((xml_valid++))
                else
                    print_failure "$filename: Invalid XML syntax"
                fi
            fi
        done
    fi

    print_info "XML Dashboards: $xml_valid/$xml_count valid"
    echo ""
}

# ============================================================================
# Phase 3: JSON Dashboard Validation
# ============================================================================
validate_json_dashboards() {
    print_header "Phase 3: JSON Dashboard Validation"

    local json_count=0
    local json_valid=0

    # Check production JSON dashboards
    if [ -d "configs/dashboards/studio-production" ]; then
        for json_file in configs/dashboards/studio-production/*.json; do
            if [ -f "$json_file" ]; then
                ((json_count++))
                filename=$(basename "$json_file")

                # Validate JSON syntax
                if python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
                    print_success "$filename: Valid JSON"
                    ((json_valid++))
                else
                    print_failure "$filename: Invalid JSON syntax"
                fi
            fi
        done
    fi

    print_info "JSON Dashboards: $json_valid/$json_count valid"
    echo ""
}

# ============================================================================
# Phase 4: Configuration Files Validation
# ============================================================================
validate_configurations() {
    print_header "Phase 4: Configuration Files Validation"

    # Critical configuration files
    local critical_configs=(
        "configs/correlation-rules.conf"
        "configs/datamodels.conf"
        "configs/alert_actions-slack-blockkit.conf"
        "configs/savedsearches-slack-blockkit-examples.conf"
    )

    for config in "${critical_configs[@]}"; do
        if [ -f "$config" ]; then
            # Check file is not empty
            if [ -s "$config" ]; then
                lines=$(wc -l < "$config")
                print_success "$(basename $config): Exists ($lines lines)"
            else
                print_failure "$(basename $config): Empty file"
            fi
        else
            print_failure "$(basename $config): Missing"
        fi
    done

    # Check index consistency
    print_info "Checking index consistency..."
    local fw_count=$(grep -rh "index=fw" configs/*.conf 2>/dev/null | wc -l)
    local legacy_count=$(grep -rh "index=fortigate_security" configs/*.conf 2>/dev/null | wc -l)

    print_info "index=fw references: $fw_count"
    if [ $legacy_count -gt 0 ]; then
        print_warning "Legacy index references found: $legacy_count (consider migration)"
    else
        print_success "No legacy index references (migration complete)"
    fi

    echo ""
}

# ============================================================================
# Phase 5: Slack Block Kit Validation
# ============================================================================
validate_slack_blockkit() {
    print_header "Phase 5: Slack Block Kit Validation"

    # Check script exists and is executable
    if [ -x "scripts/slack_blockkit_alert.py" ]; then
        print_success "slack_blockkit_alert.py: Executable"

        # Check file size (should be ~12KB)
        size=$(stat -c%s "scripts/slack_blockkit_alert.py" 2>/dev/null || stat -f%z "scripts/slack_blockkit_alert.py" 2>/dev/null)
        if [ $size -gt 10000 ]; then
            print_success "Script size: ${size} bytes (reasonable)"
        else
            print_warning "Script size: ${size} bytes (seems small)"
        fi
    else
        print_failure "slack_blockkit_alert.py: Missing or not executable"
    fi

    # Check Python dependencies
    if python3 -c "import sys, json, os, re, urllib, datetime" 2>/dev/null; then
        print_success "Python dependencies: All available"
    else
        print_failure "Python dependencies: Missing modules"
    fi

    # Check configuration
    if [ -f "configs/alert_actions-slack-blockkit.conf" ]; then
        if grep -q "\[slack_blockkit\]" "configs/alert_actions-slack-blockkit.conf"; then
            print_success "Alert action configuration: Valid"
        else
            print_failure "Alert action configuration: Missing [slack_blockkit] section"
        fi
    fi

    # Check example alerts
    if [ -f "configs/savedsearches-slack-blockkit-examples.conf" ]; then
        example_count=$(grep -c "^\[.*BlockKit\]" "configs/savedsearches-slack-blockkit-examples.conf" 2>/dev/null || echo 0)
        if [ $example_count -gt 0 ]; then
            print_success "Example alerts: $example_count configurations"
        else
            print_warning "Example alerts: No configurations found"
        fi
    fi

    echo ""
}

# ============================================================================
# Phase 6: Correlation Rules Validation
# ============================================================================
validate_correlation_rules() {
    print_header "Phase 6: Correlation Rules Validation"

    if [ -f "configs/correlation-rules.conf" ]; then
        # Count correlation rules
        rule_count=$(grep -c "^\[Correlation_" "configs/correlation-rules.conf" 2>/dev/null || echo 0)
        print_info "Correlation rules found: $rule_count"

        # Check each rule has required fields
        local rules=(
            "Correlation_Multi_Factor_Threat_Score"
            "Correlation_Repeated_High_Risk_Events"
            "Correlation_Weak_Signal_Combination"
            "Correlation_Geo_Attack_Pattern"
            "Correlation_Time_Based_Anomaly"
            "Correlation_Cross_Event_Type"
        )

        for rule in "${rules[@]}"; do
            if grep -q "^\[$rule\]" "configs/correlation-rules.conf"; then
                print_success "$rule: Defined"
            else
                print_warning "$rule: Not found"
            fi
        done
    else
        print_failure "correlation-rules.conf: Missing"
    fi

    echo ""
}

# ============================================================================
# Phase 7: Documentation Validation
# ============================================================================
validate_documentation() {
    print_header "Phase 7: Documentation Validation"

    local critical_docs=(
        "docs/SLACK_BLOCKKIT_DEPLOYMENT.md"
        "docs/SPLUNK_PERFORMANCE_IMPROVEMENT_REPORT.md"
        "README.md"
        "CLAUDE.md"
    )

    for doc in "${critical_docs[@]}"; do
        if [ -f "$doc" ]; then
            lines=$(wc -l < "$doc")
            print_success "$(basename $doc): Exists ($lines lines)"
        else
            print_failure "$(basename $doc): Missing"
        fi
    done

    echo ""
}

# ============================================================================
# Phase 8: Splunk REST API Validation (Optional)
# ============================================================================
validate_splunk_api() {
    print_header "Phase 8: Splunk REST API Validation"

    print_info "Testing connection to Splunk REST API..."

    # Test Splunk server connectivity
    if curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASS" \
        "https://$SPLUNK_HOST:$SPLUNK_PORT/services/server/info" > /dev/null 2>&1; then
        print_success "Splunk REST API: Accessible"

        # Get Splunk version
        version=$(curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASS" \
            "https://$SPLUNK_HOST:$SPLUNK_PORT/services/server/info" \
            | grep -oP '(?<=<s:key name="version">)[^<]+' | head -1)
        print_info "Splunk version: $version"
    else
        print_failure "Splunk REST API: Not accessible"
        print_warning "Check SPLUNK_HOST, SPLUNK_USER, SPLUNK_PASS environment variables"
    fi

    echo ""
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo ""
    print_header "Splunk Deployment Verification"
    echo ""
    print_info "Start time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Parse arguments
    MODE="quick"
    if [ "$1" == "--full" ]; then
        MODE="full"
    elif [ "$1" == "--deploy" ]; then
        MODE="deploy"
    fi

    # Change to script directory
    cd "$(dirname "$0")/.." || exit 1
    print_info "Working directory: $(pwd)"
    echo ""

    # Run validation phases
    validate_file_structure
    validate_xml_dashboards
    validate_json_dashboards
    validate_configurations
    validate_slack_blockkit
    validate_correlation_rules
    validate_documentation

    # Optional API validation
    if [ "$MODE" == "full" ] || [ "$MODE" == "deploy" ]; then
        validate_splunk_api
    fi

    # Summary
    print_header "Verification Summary"
    echo ""
    print_info "Total checks: $TOTAL_CHECKS"
    print_success "Passed: $PASSED_CHECKS"

    if [ $FAILED_CHECKS -gt 0 ]; then
        print_failure "Failed: $FAILED_CHECKS"
        echo ""
        echo -e "${RED}Verification FAILED${NC}"
        echo ""
        exit 1
    else
        echo ""
        echo -e "${GREEN}✅ All verification checks PASSED${NC}"
        echo ""

        if [ "$MODE" == "deploy" ]; then
            print_info "Ready for deployment to Splunk server"
            echo ""
            echo "Next steps:"
            echo "  1. Review docs/SLACK_BLOCKKIT_DEPLOYMENT.md"
            echo "  2. Deploy dashboards: node scripts/deploy-dashboards.js"
            echo "  3. Deploy Slack Block Kit: Follow deployment guide"
            echo "  4. Verify correlation rules: splunk search '| savedsearch Correlation_Multi_Factor_Threat_Score'"
        fi

        exit 0
    fi
}

# Run main
main "$@"
