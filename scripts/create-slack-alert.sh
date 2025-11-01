#!/bin/bash
# =============================================================================
# Slack Alert Auto-Registration Script
# =============================================================================
# Usage:
#   Interactive mode:
#     ./create-slack-alert.sh
#
#   Auto mode (command-line arguments):
#     ./create-slack-alert.sh --name "alert_name" \
#       --source "fw" \
#       --severity "high" \
#       --schedule "10" \
#       --channel "C09DSD6JH2Q"
#
# Arguments:
#   --name       Alert name (required)
#   --source     Event source: fw|summary_fw|custom (default: fw)
#   --severity   Severity filter: critical|high|all|custom (default: high)
#   --schedule   Check frequency in minutes: 5|10|15|30|60 (default: 10)
#   --channel    Slack channel ID (default: C09DSD6JH2Q)
#   --query      Custom SPL query (for --source custom)
#   --filter     Custom filter (for --severity custom)
#   --auto       Skip confirmation prompt
#
# Examples:
#   # Quick start (all defaults)
#   ./create-slack-alert.sh --name "my_alert" --auto
#
#   # Custom configuration
#   ./create-slack-alert.sh --name "critical_fw" \
#     --source "fw" --severity "critical" --schedule "5" --auto
#
#   # Correlation alerts
#   ./create-slack-alert.sh --name "correlation_high" \
#     --source "summary_fw" --severity "all" \
#     --filter "correlation_score>=80" --schedule "10" --auto
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SPLUNK_URL="${SPLUNK_URL:-https://splunk.jclee.me:8089}"
SPLUNK_USER="${SPLUNK_USER:-admin}"
SPLUNK_PASS="${SPLUNK_PASS:-}"
DEFAULT_CHANNEL="C09DSD6JH2Q"

# Functions
print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}  Slack Alert Registration${NC}"
    echo -e "${BLUE}=================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Get user input
get_alert_config() {
    echo -e "${YELLOW}Alert Configuration:${NC}\n"

    # Alert name
    read -p "Alert name (e.g., fw_critical_events): " ALERT_NAME
    if [[ -z "$ALERT_NAME" ]]; then
        print_error "Alert name cannot be empty"
        exit 1
    fi

    # Add timestamp to make unique
    ALERT_NAME="${ALERT_NAME}_$(date +%Y%m%d_%H%M%S)"

    # Event source
    echo -e "\nSelect event source:"
    echo "1) FortiGate Firewall Logs (index=fw)"
    echo "2) Correlation Detections (index=summary_fw)"
    echo "3) Custom query"
    read -p "Choice [1-3]: " source_choice

    case $source_choice in
        1)
            BASE_QUERY="index=fw"
            ;;
        2)
            BASE_QUERY="index=summary_fw marker=\"correlation_detection=*\""
            ;;
        3)
            read -p "Enter custom SPL query: " BASE_QUERY
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    # Severity filter
    echo -e "\nSelect severity filter:"
    echo "1) Critical only"
    echo "2) Critical or High"
    echo "3) All severities"
    echo "4) Custom filter"
    read -p "Choice [1-4]: " severity_choice

    case $severity_choice in
        1)
            SEVERITY_FILTER="severity=critical"
            ;;
        2)
            SEVERITY_FILTER="severity=critical OR severity=high"
            ;;
        3)
            SEVERITY_FILTER="*"
            ;;
        4)
            read -p "Enter custom filter (e.g., correlation_score>=80): " SEVERITY_FILTER
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    # Schedule
    echo -e "\nSelect check frequency:"
    echo "1) Every 5 minutes"
    echo "2) Every 10 minutes"
    echo "3) Every 15 minutes"
    echo "4) Every 30 minutes"
    echo "5) Every hour"
    echo "6) Custom cron"
    read -p "Choice [1-6]: " schedule_choice

    case $schedule_choice in
        1)
            CRON_SCHEDULE="*/5 * * * *"
            ;;
        2)
            CRON_SCHEDULE="*/10 * * * *"
            ;;
        3)
            CRON_SCHEDULE="*/15 * * * *"
            ;;
        4)
            CRON_SCHEDULE="*/30 * * * *"
            ;;
        5)
            CRON_SCHEDULE="0 * * * *"
            ;;
        6)
            read -p "Enter cron schedule (e.g., */20 * * * *): " CRON_SCHEDULE
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    # Slack channel
    echo -e "\nSelect Slack channel:"
    echo "1) #splunk-alerts (C09DSD6JH2Q) - Default"
    echo "2) Custom channel ID"
    read -p "Choice [1-2]: " channel_choice

    case $channel_choice in
        1)
            SLACK_CHANNEL="$DEFAULT_CHANNEL"
            ;;
        2)
            read -p "Enter channel ID (e.g., C09DSD6JH2Q): " SLACK_CHANNEL
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    # Build complete search query
    if [[ "$SEVERITY_FILTER" == "*" ]]; then
        SEARCH_QUERY="$BASE_QUERY earliest=-15m latest=now | stats count by src_ip, severity, msg | where count > 0"
    else
        SEARCH_QUERY="$BASE_QUERY earliest=-15m latest=now | search $SEVERITY_FILTER | stats count by src_ip, severity, msg | where count > 0"
    fi

    # Slack message template
    SLACK_MESSAGE="🚨 Security Alert: \$result.severity\$

*Source IP:* \$result.src_ip\$
*Severity:* \$result.severity\$
*Event Count:* \$result.count\$
*Message:* \$result.msg\$
*Time:* \$job.latestTime\$

<https://splunk.jclee.me:8000/app/search/search?q=\$result.search\$|View in Splunk>"
}

# Validate configuration
validate_config() {
    echo -e "\n${YELLOW}=== Configuration Summary ===${NC}"
    echo -e "${BLUE}Alert Name:${NC} $ALERT_NAME"
    echo -e "${BLUE}Search Query:${NC} $SEARCH_QUERY"
    echo -e "${BLUE}Schedule:${NC} $CRON_SCHEDULE"
    echo -e "${BLUE}Slack Channel:${NC} $SLACK_CHANNEL"
    echo ""

    read -p "Proceed with registration? [y/N]: " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_warning "Registration cancelled"
        exit 0
    fi
}

# Create saved search via REST API
create_saved_search() {
    print_info "Creating saved search..."

    # Check if Splunk password is set
    if [[ -z "$SPLUNK_PASS" ]]; then
        read -s -p "Enter Splunk admin password: " SPLUNK_PASS
        echo ""
    fi

    # Create saved search
    response=$(curl -k -s -w "\n%{http_code}" -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
        -d "name=${ALERT_NAME}" \
        -d "search=${SEARCH_QUERY}" \
        -d "cron_schedule=${CRON_SCHEDULE}" \
        -d "dispatch.earliest_time=-15m" \
        -d "dispatch.latest_time=now" \
        -d "alert.track=1" \
        -d "alert.condition=search count > 0" \
        -d "action.slack=1" \
        -d "action.slack.param.channel=${SLACK_CHANNEL}" \
        -d "action.slack.param.message=${SLACK_MESSAGE}" \
        -d "is_scheduled=1" \
        -d "disabled=0" \
        "${SPLUNK_URL}/servicesNS/nobody/search/saved/searches")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" == "201" ]] || [[ "$http_code" == "200" ]]; then
        print_success "Alert created successfully!"
        echo -e "\n${GREEN}Alert Name:${NC} $ALERT_NAME"
        echo -e "${GREEN}Status:${NC} ✅ Active and scheduled"
        echo -e "${GREEN}Next Run:${NC} Based on cron: $CRON_SCHEDULE"
        echo -e "\n${BLUE}View/Edit Alert:${NC}"
        echo "https://splunk.jclee.me:8000/app/search/alert?s=${ALERT_NAME}"
    else
        print_error "Failed to create alert (HTTP $http_code)"
        echo -e "\n${RED}Response:${NC}"
        echo "$body"
        exit 1
    fi
}

# Test alert immediately
test_alert() {
    echo -e "\n${YELLOW}Would you like to test the alert now?${NC}"
    read -p "This will run the search once [y/N]: " test_confirm

    if [[ "$test_confirm" =~ ^[Yy]$ ]]; then
        print_info "Running test search..."

        curl -k -s -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
            -d "id=${ALERT_NAME}" \
            "${SPLUNK_URL}/servicesNS/nobody/search/saved/searches/${ALERT_NAME}/dispatch" > /dev/null

        print_success "Test search dispatched. Check Slack channel in 30 seconds."
    fi
}

# Main
main() {
    print_header
    get_alert_config
    validate_config
    create_saved_search
    test_alert

    echo -e "\n${GREEN}=== Registration Complete ===${NC}"
    echo -e "${BLUE}Your alert is now running automatically!${NC}"
    echo -e "${BLUE}No further action needed.${NC}\n"
}

main
