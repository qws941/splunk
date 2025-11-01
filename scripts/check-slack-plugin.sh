#!/bin/bash
#
# Splunk Slack Plugin Verification Script
# Purpose: Check Slack Add-on installation and configuration
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

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Splunk Slack Plugin Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# =============================================================================
# 1. Check Splunk Apps Directory
# =============================================================================

log_info "Checking Splunk installation..."

SPLUNK_HOME="${SPLUNK_HOME:-/opt/splunk}"
APPS_DIR="$SPLUNK_HOME/etc/apps"

if [[ ! -d "$SPLUNK_HOME" ]]; then
    log_error "Splunk not found at: $SPLUNK_HOME"
    log_warning "Set SPLUNK_HOME environment variable if installed elsewhere"
    exit 1
fi

log_success "Splunk found: $SPLUNK_HOME"
echo

# =============================================================================
# 2. Check Slack Add-on Installation
# =============================================================================

log_info "Checking Slack Add-on installation..."

SLACK_APP_NAMES=(
    "slack_alerts"
    "TA-slack"
    "slack-notification-alert"
    "splunk-add-on-for-slack"
)

SLACK_APP_FOUND=""

for app_name in "${SLACK_APP_NAMES[@]}"; do
    if [[ -d "$APPS_DIR/$app_name" ]]; then
        SLACK_APP_FOUND="$app_name"
        log_success "Slack Add-on found: $app_name"
        break
    fi
done

if [[ -z "$SLACK_APP_FOUND" ]]; then
    log_error "Slack Add-on NOT installed"
    echo
    echo "INSTALLATION METHODS:"
    echo "  1. Splunk Web UI: Apps → Find More Apps → Search 'Slack'"
    echo "  2. Splunkbase: https://splunkbase.splunk.com/app/2878/"
    echo "  3. Manual: Download .tgz → Extract to $APPS_DIR/"
    echo
    echo "RECOMMENDED: Slack Notification Alert (Official)"
    echo "  https://splunkbase.splunk.com/app/2878/"
    echo
    exit 1
fi

SLACK_APP_DIR="$APPS_DIR/$SLACK_APP_FOUND"
echo

# =============================================================================
# 3. Check Alert Actions Configuration
# =============================================================================

log_info "Checking alert_actions.conf..."

ALERT_ACTIONS_CONF="$SLACK_APP_DIR/local/alert_actions.conf"

if [[ -f "$ALERT_ACTIONS_CONF" ]]; then
    log_success "Configuration file found: alert_actions.conf"

    # Check webhook URL
    if grep -q "webhook_url" "$ALERT_ACTIONS_CONF"; then
        WEBHOOK_URL=$(grep "webhook_url" "$ALERT_ACTIONS_CONF" | cut -d= -f2 | tr -d ' ')

        if [[ -n "$WEBHOOK_URL" ]] && [[ "$WEBHOOK_URL" != "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" ]]; then
            log_success "Webhook URL configured: ${WEBHOOK_URL:0:50}..."
        else
            log_error "Webhook URL not configured or using default"
        fi
    fi

    # Check bot token (newer method)
    if grep -q "bot_token" "$ALERT_ACTIONS_CONF"; then
        BOT_TOKEN=$(grep "bot_token" "$ALERT_ACTIONS_CONF" | cut -d= -f2 | tr -d ' ')

        if [[ -n "$BOT_TOKEN" ]] && [[ "$BOT_TOKEN" =~ ^xoxb- ]]; then
            log_success "Bot token configured: ${BOT_TOKEN:0:20}..."
        else
            log_error "Bot token not configured or invalid format"
        fi
    fi

    # Check channel
    if grep -q "channel" "$ALERT_ACTIONS_CONF"; then
        CHANNEL=$(grep "channel" "$ALERT_ACTIONS_CONF" | cut -d= -f2 | tr -d ' ')

        if [[ -n "$CHANNEL" ]]; then
            log_success "Default channel: $CHANNEL"
        fi
    fi

else
    log_warning "Configuration file not found: $ALERT_ACTIONS_CONF"
    log_warning "Run Slack Add-on setup via Splunk Web UI"
fi

echo

# =============================================================================
# 4. Check Saved Searches with Slack Actions
# =============================================================================

log_info "Checking saved searches with Slack actions..."

SAVEDSEARCHES_CONF="$SPLUNK_HOME/etc/apps/search/local/savedsearches.conf"

if [[ -f "$SAVEDSEARCHES_CONF" ]]; then
    SLACK_ALERTS=$(grep -c "action.slack" "$SAVEDSEARCHES_CONF" 2>/dev/null || echo "0")

    if [[ $SLACK_ALERTS -gt 0 ]]; then
        log_success "Found $SLACK_ALERTS saved search(es) with Slack action"

        echo
        echo "Slack-enabled alerts:"
        grep -B 5 "action.slack" "$SAVEDSEARCHES_CONF" | grep "^\[" | sed 's/\[//g' | sed 's/\]//g' | while read -r alert_name; do
            echo "  - $alert_name"
        done
    else
        log_warning "No saved searches configured with Slack action"
        echo
        echo "TO CREATE SLACK ALERT:"
        echo "  1. Splunk Web UI: Settings → Searches, reports, and alerts"
        echo "  2. Create New Alert → Add Actions → Send to Slack"
        echo "  3. Configure channel and message format"
    fi
else
    log_warning "savedsearches.conf not found"
fi

echo

# =============================================================================
# 5. Test Slack Connectivity (Optional)
# =============================================================================

log_info "Testing Slack connectivity..."

if [[ -f "$ALERT_ACTIONS_CONF" ]]; then
    # Extract webhook URL for testing
    WEBHOOK_URL=$(grep "^webhook_url" "$ALERT_ACTIONS_CONF" 2>/dev/null | cut -d= -f2 | tr -d ' ' | tr -d '"')

    if [[ -n "$WEBHOOK_URL" ]] && [[ "$WEBHOOK_URL" =~ ^https://hooks.slack.com ]]; then
        echo
        read -p "Send test message to Slack? (y/n): " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            TEST_MESSAGE='{"text":"✅ Splunk Slack Integration Test\n\nFrom: '"$(hostname)"'\nTime: '"$(date)"'\nStatus: Connection successful"}'

            RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
                -H "Content-Type: application/json" \
                -d "$TEST_MESSAGE" \
                "$WEBHOOK_URL")

            if [[ "$RESPONSE" == "200" ]]; then
                log_success "Test message sent successfully (HTTP $RESPONSE)"
            else
                log_error "Test message failed (HTTP $RESPONSE)"
            fi
        fi
    else
        log_warning "Webhook URL not configured, skipping connectivity test"
    fi
fi

echo

# =============================================================================
# 6. Check Slack Alert Status via REST API
# =============================================================================

log_info "Checking alert status via REST API..."

if command -v curl &> /dev/null; then
    echo
    read -p "Enter Splunk admin username (default: admin): " SPLUNK_USER
    SPLUNK_USER=${SPLUNK_USER:-admin}

    read -s -p "Enter Splunk admin password: " SPLUNK_PASSWORD
    echo

    if [[ -n "$SPLUNK_PASSWORD" ]]; then
        RESPONSE=$(curl -s -k -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
            "https://localhost:8089/servicesNS/nobody/search/saved/searches?output_mode=json&search=action.slack%3D1" 2>/dev/null)

        if [[ -n "$RESPONSE" ]]; then
            ALERT_COUNT=$(echo "$RESPONSE" | jq -r '.entry | length' 2>/dev/null || echo "0")

            if [[ $ALERT_COUNT -gt 0 ]]; then
                log_success "Found $ALERT_COUNT Slack-enabled alert(s) via REST API"

                echo
                echo "Alert details:"
                echo "$RESPONSE" | jq -r '.entry[] | "  - \(.name) (disabled: \(.content.disabled))"' 2>/dev/null || echo "  (jq not installed, cannot parse details)"
            else
                log_warning "No Slack-enabled alerts found via REST API"
            fi
        else
            log_error "REST API query failed"
        fi
    fi
else
    log_warning "curl not installed, skipping REST API check"
fi

echo

# =============================================================================
# 7. Summary & Recommendations
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "Verification Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ -n "$SLACK_APP_FOUND" ]]; then
    log_success "Slack Add-on: Installed ($SLACK_APP_FOUND)"
else
    log_error "Slack Add-on: NOT installed"
fi

if [[ -f "$ALERT_ACTIONS_CONF" ]]; then
    log_success "Configuration: Found"
else
    log_warning "Configuration: Not found (run setup)"
fi

echo
echo "NEXT STEPS:"
echo "  1. Configure Slack webhook or bot token"
echo "  2. Create test alert: Settings → Alerts → New Alert"
echo "  3. Add Slack action to alert"
echo "  4. Monitor: index=_internal source=*slack* earliest=-1h"
echo
echo "DOCUMENTATION:"
echo "  - Splunk docs: https://docs.splunk.com/Documentation/Splunk/latest/Alert/Slacknotification"
echo "  - Slack App setup: https://api.slack.com/apps"
echo

log_success "Verification complete!"
