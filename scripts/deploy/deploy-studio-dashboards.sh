#!/bin/bash
#
# Splunk Studio Dashboard Deployment Script
#
# Purpose: Deploy JavaScript-free Studio JSON dashboards to Splunk
# Author: JC Lee
# Date: 2025-10-25
# Version: 1.0

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DASHBOARD_DIR="$PROJECT_ROOT/configs/dashboards/studio-production"

SPLUNK_HOST="${SPLUNK_HOST:-splunk.jclee.me}"
SPLUNK_PORT="${SPLUNK_PORT:-8089}"
SPLUNK_USER="${SPLUNK_USER:-admin}"
SPLUNK_PASSWORD="${SPLUNK_PASSWORD:-}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if jq is installed (for JSON validation)
    if ! command -v jq &> /dev/null; then
        log_warning "jq not found. Installing..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install jq
        else
            sudo apt-get install -y jq || sudo yum install -y jq
        fi
    fi

    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi

    # Check if dashboard directory exists
    if [[ ! -d "$DASHBOARD_DIR" ]]; then
        log_error "Dashboard directory not found: $DASHBOARD_DIR"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

prompt_credentials() {
    if [[ -z "$SPLUNK_PASSWORD" ]]; then
        echo -n "Enter Splunk password for user '$SPLUNK_USER': "
        read -s SPLUNK_PASSWORD
        echo
    fi
}

validate_json() {
    local file=$1
    log_info "Validating JSON: $(basename "$file")"

    if jq empty "$file" 2>/dev/null; then
        log_success "Valid JSON: $(basename "$file")"
        return 0
    else
        log_error "Invalid JSON: $(basename "$file")"
        return 1
    fi
}

deploy_dashboard() {
    local dashboard_file=$1
    local dashboard_name=$(basename "$dashboard_file" .json)

    log_info "Deploying: $dashboard_name"

    # Validate JSON first
    if ! validate_json "$dashboard_file"; then
        return 1
    fi

    # Deploy via REST API
    local response=$(curl -k -s -w "\n%{http_code}" \
        -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
        -H "Content-Type: application/json" \
        -d @"$dashboard_file" \
        "https://$SPLUNK_HOST:$SPLUNK_PORT/servicesNS/nobody/search/data/ui/views" 2>&1)

    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [[ "$http_code" == "201" ]] || [[ "$http_code" == "200" ]]; then
        log_success "Deployed: $dashboard_name (HTTP $http_code)"
        return 0
    else
        log_error "Failed to deploy: $dashboard_name (HTTP $http_code)"
        log_error "Response: $body"
        return 1
    fi
}

deploy_all() {
    log_info "Starting dashboard deployment..."
    echo

    local success_count=0
    local failed_count=0

    for dashboard in "$DASHBOARD_DIR"/*.json; do
        if [[ -f "$dashboard" ]]; then
            if deploy_dashboard "$dashboard"; then
                ((success_count++))
            else
                ((failed_count++))
            fi
            echo
        fi
    done

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "Deployment Summary"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_success "Successfully deployed: $success_count"

    if [[ $failed_count -gt 0 ]]; then
        log_error "Failed deployments: $failed_count"
        return 1
    else
        log_success "All dashboards deployed successfully!"
        return 0
    fi
}

list_dashboards() {
    log_info "Available Studio dashboards in $DASHBOARD_DIR:"
    echo

    local count=0
    for dashboard in "$DASHBOARD_DIR"/*.json; do
        if [[ -f "$dashboard" ]]; then
            ((count++))
            local name=$(basename "$dashboard")
            local size=$(du -h "$dashboard" | cut -f1)
            echo "  $count. $name ($size)"
        fi
    done

    echo
    log_info "Total: $count dashboards"
}

verify_deployment() {
    log_info "Verifying deployed dashboards..."
    echo

    local response=$(curl -k -s \
        -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
        "https://$SPLUNK_HOST:$SPLUNK_PORT/servicesNS/nobody/search/data/ui/views?output_mode=json&count=-1")

    for dashboard in "$DASHBOARD_DIR"/*.json; do
        local dashboard_name=$(basename "$dashboard" .json)

        if echo "$response" | jq -e ".entry[] | select(.name==\"$dashboard_name\")" > /dev/null 2>&1; then
            log_success "Verified: $dashboard_name"
        else
            log_warning "Not found: $dashboard_name"
        fi
    done
}

show_usage() {
    cat << EOF
Splunk Studio Dashboard Deployment Script

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -l, --list              List available dashboards
    -d, --deploy            Deploy all dashboards
    -v, --verify            Verify deployed dashboards
    -s, --host HOST         Splunk host (default: splunk.jclee.me)
    -p, --port PORT         Splunk port (default: 8089)
    -u, --user USER         Splunk username (default: admin)

Environment Variables:
    SPLUNK_HOST             Splunk hostname
    SPLUNK_PORT             Splunk REST API port
    SPLUNK_USER             Splunk username
    SPLUNK_PASSWORD         Splunk password (will prompt if not set)

Examples:
    # List available dashboards
    $0 --list

    # Deploy all dashboards
    $0 --deploy

    # Deploy to specific host
    $0 --deploy --host splunk.example.com --user admin

    # Verify deployment
    $0 --verify

EOF
}

# ============================================================================
# Main
# ============================================================================

main() {
    local action=""

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -l|--list)
                action="list"
                shift
                ;;
            -d|--deploy)
                action="deploy"
                shift
                ;;
            -v|--verify)
                action="verify"
                shift
                ;;
            -s|--host)
                SPLUNK_HOST="$2"
                shift 2
                ;;
            -p|--port)
                SPLUNK_PORT="$2"
                shift 2
                ;;
            -u|--user)
                SPLUNK_USER="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Show header
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Splunk Studio Dashboard Deployment"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo

    # Execute action
    case $action in
        list)
            check_prerequisites
            list_dashboards
            ;;
        deploy)
            check_prerequisites
            prompt_credentials
            deploy_all
            ;;
        verify)
            check_prerequisites
            prompt_credentials
            verify_deployment
            ;;
        "")
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
