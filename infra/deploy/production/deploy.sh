#!/bin/bash
#
# Production Deployment Script for Splunk Security App
# Version: 4.1.438
# Usage: ./deploy.sh <splunk-server-ip> <admin-password> <slack-bot-token>
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_VERSION="4.1.438"
PROXY_SERVER="${PROXY_SERVER:-http://172.16.4.217:5001}"
SLACK_CHANNEL="${SLACK_CHANNEL:-일반}"
PACKAGE_NAME="security-${APP_VERSION}_*.tar.gz"

# Arguments
SPLUNK_SERVER="${1:-}"
ADMIN_PASSWORD="${2:-}"
SLACK_BOT_TOKEN="${3:-}"

# Validation
if [[ -z "$SPLUNK_SERVER" ]]; then
    echo -e "${RED}❌ Error: Splunk server IP required${NC}"
    echo "Usage: $0 <splunk-server-ip> <admin-password> <slack-bot-token>"
    exit 1
fi

if [[ -z "$ADMIN_PASSWORD" ]]; then
    echo -e "${RED}❌ Error: Admin password required${NC}"
    exit 1
fi

if [[ -z "$SLACK_BOT_TOKEN" ]]; then
    echo -e "${RED}❌ Error: Slack bot token required${NC}"
    exit 1
fi

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command '$1' not found"
        exit 1
    fi
}

# Pre-flight checks
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Splunk Security App - Production Deployment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
log_info "Version: ${APP_VERSION}"
log_info "Target: ${SPLUNK_SERVER}"
log_info "Proxy: ${PROXY_SERVER}"
echo ""

# Check required commands
log_info "Checking prerequisites..."
check_command "scp"
check_command "ssh"
check_command "nc"
check_command "curl"
log_success "All prerequisites met"

# Find package
log_info "Locating deployment package..."
PACKAGE_PATH=$(ls -t releases/${PACKAGE_NAME} 2>/dev/null | head -1)
if [[ -z "$PACKAGE_PATH" ]]; then
    log_error "Package not found: releases/${PACKAGE_NAME}"
    exit 1
fi
PACKAGE_SIZE=$(du -h "$PACKAGE_PATH" | cut -f1)
log_success "Found: $PACKAGE_PATH (${PACKAGE_SIZE})"

# Test proxy connectivity
log_info "Testing proxy connectivity..."
if nc -z -w5 172.16.4.217 5001 2>/dev/null; then
    log_success "Proxy server reachable (172.16.4.217:5001)"
else
    log_warning "Cannot reach proxy server - continuing anyway"
fi

# Test Splunk server connectivity
log_info "Testing Splunk server connectivity..."
if nc -z -w5 "$SPLUNK_SERVER" 22 2>/dev/null; then
    log_success "Splunk server reachable (${SPLUNK_SERVER}:22)"
else
    log_error "Cannot reach Splunk server"
    exit 1
fi

# Upload package
echo ""
log_info "📦 Uploading package to Splunk server..."
if scp -o ConnectTimeout=10 "$PACKAGE_PATH" "admin@${SPLUNK_SERVER}:/tmp/" 2>/dev/null; then
    log_success "Package uploaded successfully"
else
    log_error "Failed to upload package"
    exit 1
fi

# Deploy on remote server
echo ""
log_info "🚀 Deploying application..."

REMOTE_SCRIPT=$(cat <<'REMOTESCRIPT'
set -euo pipefail

PACKAGE_FILE="/tmp/$(basename %PACKAGE_PATH%)"
SPLUNK_HOME="/opt/splunk"
APP_DIR="${SPLUNK_HOME}/etc/apps/security"

# Extract package
echo "  → Extracting package..."
cd "${SPLUNK_HOME}/etc/apps"
if [[ -d "security" ]]; then
    echo "  → Backing up existing app..."
    mv security "security.backup.$(date +%Y%m%d_%H%M%S)"
fi
tar -xzf "$PACKAGE_FILE"
chown -R splunk:splunk security
echo "  → Extraction complete"

# Create local directory
mkdir -p "${APP_DIR}/local"
chown splunk:splunk "${APP_DIR}/local"

# Configure proxy
echo "  → Configuring proxy settings..."
cat > "${APP_DIR}/local/app.conf" << 'CONF'
[id]
version = %APP_VERSION%

[security]
proxy_server = %PROXY_SERVER%
slack_channel = %SLACK_CHANNEL%
CONF
chown splunk:splunk "${APP_DIR}/local/app.conf"

# Restart Splunk
echo "  → Restarting Splunk..."
sudo -u splunk "${SPLUNK_HOME}/bin/splunk" restart --accept-license --answer-yes --no-prompt

# Wait for Splunk to start
echo "  → Waiting for Splunk to start..."
for i in {1..30}; do
    if curl -k -s https://localhost:8089/services/server/info &>/dev/null; then
        echo "  → Splunk started successfully"
        break
    fi
    if [[ $i -eq 30 ]]; then
        echo "  → Timeout waiting for Splunk"
        exit 1
    fi
    sleep 2
done

echo "✅ Deployment complete"
REMOTESCRIPT
)

# Replace variables in remote script
REMOTE_SCRIPT="${REMOTE_SCRIPT//%PACKAGE_PATH%/$PACKAGE_PATH}"
REMOTE_SCRIPT="${REMOTE_SCRIPT//%APP_VERSION%/$APP_VERSION}"
REMOTE_SCRIPT="${REMOTE_SCRIPT//%PROXY_SERVER%/$PROXY_SERVER}"
REMOTE_SCRIPT="${REMOTE_SCRIPT//%SLACK_CHANNEL%/$SLACK_CHANNEL}"

# Execute remote script
if ssh -o ConnectTimeout=10 "admin@${SPLUNK_SERVER}" "bash -s" <<< "$REMOTE_SCRIPT"; then
    log_success "Application deployed successfully"
else
    log_error "Deployment failed"
    exit 1
fi

# Configure Slack Bot Token
echo ""
log_info "🔐 Configuring Slack Bot Token..."

TOKEN_RESPONSE=$(curl -k -s -w "\n%{http_code}" -u "admin:${ADMIN_PASSWORD}" -X POST \
    "https://${SPLUNK_SERVER}:8089/servicesNS/nobody/security/storage/passwords" \
    -d "name=slack_bot_token" \
    -d "password=${SLACK_BOT_TOKEN}" \
    -d "realm=security" 2>/dev/null || echo "000")

HTTP_CODE=$(echo "$TOKEN_RESPONSE" | tail -1)
if [[ "$HTTP_CODE" == "201" ]] || [[ "$HTTP_CODE" == "200" ]]; then
    log_success "Slack Bot Token configured"
else
    log_error "Failed to configure Slack Bot Token (HTTP $HTTP_CODE)"
    exit 1
fi

# Verification
echo ""
log_info "🔍 Running verification checks..."

# Check app is installed
APP_CHECK=$(curl -k -s -u "admin:${ADMIN_PASSWORD}" \
    "https://${SPLUNK_SERVER}:8089/services/apps/local/security" 2>/dev/null | grep -c "security" || echo "0")
if [[ "$APP_CHECK" -gt 0 ]]; then
    log_success "App installed and visible"
else
    log_warning "App not visible in REST API"
fi

# Check proxy setting
PROXY_CHECK=$(ssh "admin@${SPLUNK_SERVER}" \
    "grep -c 'proxy_server' /opt/splunk/etc/apps/security/local/app.conf 2>/dev/null" || echo "0")
if [[ "$PROXY_CHECK" -gt 0 ]]; then
    log_success "Proxy configuration present"
else
    log_warning "Proxy configuration not found"
fi

# Test Slack connectivity through proxy
log_info "Testing Slack API through proxy..."
SLACK_TEST=$(ssh "admin@${SPLUNK_SERVER}" \
    "curl -x ${PROXY_SERVER} -s -o /dev/null -w '%{http_code}' https://slack.com/api 2>/dev/null" || echo "000")
if [[ "$SLACK_TEST" == "200" ]]; then
    log_success "Slack API reachable through proxy"
else
    log_warning "Cannot reach Slack API through proxy (HTTP $SLACK_TEST)"
fi

# Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Deployment Successful${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "  1. Access Splunk Web: https://${SPLUNK_SERVER}:8000"
echo "  2. Navigate to: Security App → Testing → Slack Test"
echo "  3. Click 'Send Test Alert' button"
echo "  4. Check Slack channel '${SLACK_CHANNEL}' for message"
echo ""
echo -e "${BLUE}📊 Monitoring Commands:${NC}"
echo ""
echo "  # View debug logs"
echo "  ssh admin@${SPLUNK_SERVER} 'tail -f /tmp/slack_alert_debug.log'"
echo ""
echo "  # Check internal logs"
echo "  index=_internal sourcetype=splunkd slack_alert | tail 50"
echo ""
echo "  # Monitor alert execution"
echo "  index=_internal sourcetype=scheduler | stats count by savedsearch_name, status"
echo ""
echo -e "${GREEN}✨ Deployment completed at $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
