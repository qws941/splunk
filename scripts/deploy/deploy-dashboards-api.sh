#!/bin/bash
# deploy-dashboards-api.sh
# Deploy Dashboard Studio JSON dashboards via Splunk REST API
# Usage: ./deploy-dashboards-api.sh [host] [port] [user] [password]

set -euo pipefail

# Configuration
SPLUNK_HOST="${1:-192.168.50.150}"
SPLUNK_PORT="${2:-8089}"
SPLUNK_USER="${3:-admin}"
SPLUNK_PASS="${4:-${SPLUNK_PASS:-admin123}}"
APP_NAME="security_alert"

# Dashboard files to deploy
DASHBOARD_DIR="$(dirname "$0")/../configs/dashboards"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to deploy a single dashboard
deploy_dashboard() {
    local json_file="$1"
    local dashboard_name=$(basename "$json_file" .json | tr '-' '_')

    if [[ ! -f "$json_file" ]]; then
        log_error "File not found: $json_file"
        return 1
    fi

    # Read JSON content
    local json_content
    json_content=$(cat "$json_file")

    # Extract title from JSON for display
    local title
    title=$(echo "$json_content" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title', 'Unknown'))" 2>/dev/null || echo "Unknown")

    log_info "Deploying: $title ($dashboard_name)"

    # Check if dashboard exists (app-level, not user-level)
    local exists_check
    exists_check=$(curl -s -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
        "https://${SPLUNK_HOST}:${SPLUNK_PORT}/servicesNS/nobody/${APP_NAME}/data/ui/views/${dashboard_name}?output_mode=json" 2>/dev/null || echo '{"entry":[]}')

    if echo "$exists_check" | grep -q "\"name\":\"${dashboard_name}\""; then
        log_info "  Dashboard exists, updating..."
    else
        log_info "  Creating new dashboard..."
    fi

    # Create XML wrapper for Dashboard Studio JSON
    # Note: Splunk REST API requires XML wrapper even for Dashboard Studio dashboards
    local xml_payload
    xml_payload=$(cat <<EOF
<dashboard version="2">
    <label>${title}</label>
    <definition><![CDATA[${json_content}]]></definition>
</dashboard>
EOF
)

    local response
    local base_url="https://${SPLUNK_HOST}:${SPLUNK_PORT}/servicesNS/nobody/${APP_NAME}/data/ui/views"

    if echo "$exists_check" | grep -q "\"name\":\"${dashboard_name}\""; then
        response=$(curl -s -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
            -X POST \
            --data-urlencode "eai:data=${xml_payload}" \
            "${base_url}/${dashboard_name}" \
            -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")
    else
        response=$(curl -s -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
            -X POST \
            -d "name=${dashboard_name}" \
            --data-urlencode "eai:data=${xml_payload}" \
            "${base_url}" \
            -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")
    fi

    if [[ "$response" == "200" || "$response" == "201" ]]; then
        log_info "  Setting app-level sharing..."
        curl -s -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
            -X POST \
            -d "sharing=app" \
            -d "owner=nobody" \
            "${base_url}/${dashboard_name}/acl" \
            -o /dev/null 2>/dev/null || true
    fi

    if [[ "$response" == "200" || "$response" == "201" ]]; then
        log_info "  ✓ Deployed successfully (HTTP $response)"
        return 0
    else
        log_error "  ✗ Failed to deploy (HTTP $response)"
        return 1
    fi
}

# Function to deploy a single XML dashboard
deploy_xml_dashboard() {
    local xml_file="$1"
    local dashboard_name=$(basename "$xml_file" .xml | tr '-' '_')

    if [[ ! -f "$xml_file" ]]; then
        log_error "File not found: $xml_file"
        return 1
    fi

    # Read XML content
    local xml_payload
    xml_payload=$(cat "$xml_file")

    # Try to extract label/title for logging
    local title
    title=$(grep -oP "(?<=<label>).*?(?=</label>)" "$xml_file" | head -1 || echo "$dashboard_name")

    log_info "Deploying XML: $title ($dashboard_name)"

    # Check if dashboard exists
    local exists_check
    exists_check=$(curl -s -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
        "https://${SPLUNK_HOST}:${SPLUNK_PORT}/servicesNS/nobody/${APP_NAME}/data/ui/views/${dashboard_name}?output_mode=json" 2>/dev/null || echo '{"entry":[]}')

    local response
    local base_url="https://${SPLUNK_HOST}:${SPLUNK_PORT}/servicesNS/nobody/${APP_NAME}/data/ui/views"

    if echo "$exists_check" | grep -q "\"name\":\"${dashboard_name}\""; then
        log_info "  Dashboard exists, updating..."
        response=$(curl -s -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
            -X POST \
            --data-urlencode "eai:data=${xml_payload}" \
            "${base_url}/${dashboard_name}" \
            -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")
    else
        log_info "  Creating new dashboard..."
        response=$(curl -s -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
            -X POST \
            -d "name=${dashboard_name}" \
            --data-urlencode "eai:data=${xml_payload}" \
            "${base_url}" \
            -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")
    fi

    if [[ "$response" == "200" || "$response" == "201" ]]; then
        log_info "  Setting app-level sharing..."
        curl -s -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
            -X POST \
            -d "sharing=app" \
            -d "owner=nobody" \
            "${base_url}/${dashboard_name}/acl" \
            -o /dev/null 2>/dev/null || true
        log_info "  ✓ Deployed successfully (HTTP $response)"
        return 0
    else
        log_error "  ✗ Failed to deploy (HTTP $response)"
        return 1
    fi
}

# Main
main() {
    log_info "Starting Dashboard Studio deployment via REST API"
    log_info "Target: https://${SPLUNK_HOST}:${SPLUNK_PORT}"
    log_info "App: ${APP_NAME}"
    echo ""

    # Check connectivity
    log_info "Checking Splunk connectivity..."
    if ! curl -s -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
        "https://${SPLUNK_HOST}:${SPLUNK_PORT}/services/server/info" \
        -o /dev/null -w "" 2>/dev/null; then
        log_error "Cannot connect to Splunk at ${SPLUNK_HOST}:${SPLUNK_PORT}"
        exit 1
    fi
    log_info "✓ Connected to Splunk"
    echo ""

    # Deploy each dashboard
    local success=0
    local failed=0

    for json_file in "$DASHBOARD_DIR"/*.json; do
        if [[ -f "$json_file" ]]; then
            if deploy_dashboard "$json_file"; then
                success=$((success + 1))
            else
                failed=$((failed + 1))
            fi
            echo ""
        fi
    done

    # Deploy XML dashboards
    for xml_file in "$DASHBOARD_DIR"/*.xml; do
        if [[ -f "$xml_file" ]]; then
            if deploy_xml_dashboard "$xml_file"; then
                success=$((success + 1))
            else
                failed=$((failed + 1))
            fi
            echo ""
        fi
    done

    # Summary
    echo "================================"
    log_info "Deployment Summary"
    log_info "  Successful: $success"
    if [[ $failed -gt 0 ]]; then
        log_error "  Failed: $failed"
        exit 1
    else
        log_info "  Failed: 0"
    fi

    echo ""
    log_info "Dashboards available at:"
    log_info "  http://${SPLUNK_HOST}:8000/en-US/app/${APP_NAME}/"
}

main "$@"
