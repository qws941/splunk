#!/bin/bash
# 🔑 Cloudflare KV Namespace Data Setup Script
# Initializes KV stores with configuration and cache data

set -e

echo "🔑 KV Namespace Data Setup Script"
echo "================================="

# Configuration - Following jclee.me naming conventions
PROD_KV_ID="${PROD_KV_NAMESPACE_ID:-your-splunk-cache-id}"
STAGING_KV_ID="${STAGING_KV_NAMESPACE_ID:-your-splunk-cache-staging-id}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v wrangler >/dev/null 2>&1; then
        error "Wrangler CLI is not installed"
        exit 1
    fi

    if ! wrangler whoami >/dev/null 2>&1; then
        error "Wrangler is not authenticated. Please run: wrangler login"
        exit 1
    fi

    success "Prerequisites check completed"
}

# Set KV key-value pair
set_kv_key() {
    local namespace_id=$1
    local key=$2
    local value=$3
    local env_label=$4

    if [ "$namespace_id" = "your-splunk-cache-id" ] || [ "$namespace_id" = "your-splunk-cache-staging-id" ]; then
        warning "Skipping $env_label - placeholder namespace ID detected"
        return 0
    fi

    if wrangler kv:key put "$key" "$value" --namespace-id "$namespace_id" 2>/dev/null; then
        success "Set $key in $env_label KV store"
    else
        error "Failed to set $key in $env_label KV store"
        return 1
    fi
}

# Setup application configuration
setup_app_config() {
    local namespace_id=$1
    local env_label=$2

    log "Setting up application configuration for $env_label..."

    # Application metadata
    set_kv_key "$namespace_id" "config:version" "1.0.0" "$env_label"
    set_kv_key "$namespace_id" "config:environment" "$env_label" "$env_label"
    set_kv_key "$namespace_id" "config:last_updated" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$env_label"

    # Feature flags
    set_kv_key "$namespace_id" "feature:real_time_alerts" "true" "$env_label"
    set_kv_key "$namespace_id" "feature:auto_sync" "true" "$env_label"
    set_kv_key "$namespace_id" "feature:backup_enabled" "true" "$env_label"
    set_kv_key "$namespace_id" "feature:debug_mode" "false" "$env_label"

    # Cache settings
    set_kv_key "$namespace_id" "cache:ttl_security_events" "300" "$env_label"    # 5 minutes
    set_kv_key "$namespace_id" "cache:ttl_device_status" "60" "$env_label"      # 1 minute
    set_kv_key "$namespace_id" "cache:ttl_policy_list" "600" "$env_label"       # 10 minutes
    set_kv_key "$namespace_id" "cache:max_events_per_page" "100" "$env_label"

    # Integration settings
    set_kv_key "$namespace_id" "integration:fortigate_timeout" "30" "$env_label"
    set_kv_key "$namespace_id" "integration:splunk_timeout" "30" "$env_label"
    set_kv_key "$namespace_id" "integration:sync_interval" "300" "$env_label"   # 5 minutes
    set_kv_key "$namespace_id" "integration:max_retry_attempts" "3" "$env_label"
}

# Setup system status cache
setup_system_status() {
    local namespace_id=$1
    local env_label=$2

    log "Setting up system status cache for $env_label..."

    # System health
    set_kv_key "$namespace_id" "status:system_health" "healthy" "$env_label"
    set_kv_key "$namespace_id" "status:last_health_check" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$env_label"

    # Device connectivity status
    set_kv_key "$namespace_id" "status:fortigate_devices_total" "5" "$env_label"
    set_kv_key "$namespace_id" "status:fortigate_devices_online" "4" "$env_label"
    set_kv_key "$namespace_id" "status:fortigate_devices_offline" "1" "$env_label"

    # Splunk integration status
    set_kv_key "$namespace_id" "status:splunk_connection" "connected" "$env_label"
    set_kv_key "$namespace_id" "status:splunk_last_sync" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$env_label"
    set_kv_key "$namespace_id" "status:splunk_events_today" "15420" "$env_label"

    # Performance metrics
    set_kv_key "$namespace_id" "metrics:avg_response_time" "125" "$env_label"    # milliseconds
    set_kv_key "$namespace_id" "metrics:requests_per_minute" "45" "$env_label"
    set_kv_key "$namespace_id" "metrics:error_rate" "0.01" "$env_label"         # 1%
}

# Setup security data cache
setup_security_cache() {
    local namespace_id=$1
    local env_label=$2

    log "Setting up security data cache for $env_label..."

    # Alert statistics
    set_kv_key "$namespace_id" "alerts:critical_count" "2" "$env_label"
    set_kv_key "$namespace_id" "alerts:high_count" "8" "$env_label"
    set_kv_key "$namespace_id" "alerts:medium_count" "15" "$env_label"
    set_kv_key "$namespace_id" "alerts:low_count" "23" "$env_label"

    # Recent events summary
    local recent_events_json='{
        "last_24h": 156,
        "last_1h": 12,
        "blocked_attempts": 45,
        "policy_violations": 8,
        "malware_detections": 3
    }'
    set_kv_key "$namespace_id" "cache:recent_events_summary" "$recent_events_json" "$env_label"

    # Top threat sources (JSON)
    local threat_sources_json='[
        {"ip": "203.0.113.45", "attempts": 25, "country": "Unknown"},
        {"ip": "198.51.100.42", "attempts": 18, "country": "Unknown"},
        {"ip": "192.0.2.123", "attempts": 12, "country": "Unknown"}
    ]'
    set_kv_key "$namespace_id" "cache:top_threat_sources" "$threat_sources_json" "$env_label"

    # Policy effectiveness stats
    local policy_stats_json='{
        "total_policies": 67,
        "active_policies": 62,
        "disabled_policies": 5,
        "most_used_policy": "Allow Web Browsing",
        "least_used_policy": "Emergency Deny All"
    }'
    set_kv_key "$namespace_id" "cache:policy_effectiveness" "$policy_stats_json" "$env_label"
}

# Setup user preferences and session data
setup_user_data() {
    local namespace_id=$1
    local env_label=$2

    log "Setting up user data cache for $env_label..."

    # Default dashboard settings
    local dashboard_config_json='{
        "refresh_interval": 30,
        "default_time_range": "1h",
        "charts_per_page": 6,
        "show_low_severity": false,
        "auto_refresh": true
    }'
    set_kv_key "$namespace_id" "user:default_dashboard_config" "$dashboard_config_json" "$env_label"

    # API rate limiting
    set_kv_key "$namespace_id" "ratelimit:api_requests_per_minute" "100" "$env_label"
    set_kv_key "$namespace_id" "ratelimit:bulk_operations_per_hour" "10" "$env_label"

    # Session configuration
    set_kv_key "$namespace_id" "session:default_timeout" "3600" "$env_label"     # 1 hour
    set_kv_key "$namespace_id" "session:max_concurrent" "50" "$env_label"
    set_kv_key "$namespace_id" "session:remember_me_duration" "2592000" "$env_label"  # 30 days
}

# Setup sample cached API responses
setup_api_cache() {
    local namespace_id=$1
    local env_label=$2

    log "Setting up API response cache for $env_label..."

    # Device list cache
    local device_list_json='[
        {"id": 1, "hostname": "FGT-HQ-01", "status": "active", "cpu": 23.5},
        {"id": 2, "hostname": "FGT-HQ-02", "status": "active", "cpu": 18.2},
        {"id": 3, "hostname": "FGT-BR-01", "status": "active", "cpu": 45.1},
        {"id": 4, "hostname": "FGT-BR-02", "status": "maintenance", "cpu": 0.0},
        {"id": 5, "hostname": "FGT-DC-01", "status": "active", "cpu": 31.7}
    ]'
    set_kv_key "$namespace_id" "api:device_list" "$device_list_json" "$env_label"

    # Quick stats for dashboard
    local quick_stats_json='{
        "total_devices": 5,
        "online_devices": 4,
        "total_policies": 67,
        "active_alerts": 8,
        "events_today": 156,
        "last_updated": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
    }'
    set_kv_key "$namespace_id" "api:quick_stats" "$quick_stats_json" "$env_label"

    # Timezone and localization
    set_kv_key "$namespace_id" "locale:default_timezone" "UTC" "$env_label"
    set_kv_key "$namespace_id" "locale:date_format" "YYYY-MM-DD HH:mm:ss" "$env_label"
    set_kv_key "$namespace_id" "locale:default_language" "en" "$env_label"
}

# List all keys in namespace
list_kv_keys() {
    local namespace_id=$1
    local env_label=$2

    if [ "$namespace_id" = "your-splunk-cache-id" ] || [ "$namespace_id" = "your-splunk-cache-staging-id" ]; then
        warning "Cannot list keys - placeholder namespace ID for $env_label"
        return 0
    fi

    log "Listing all keys in $env_label KV namespace..."
    if wrangler kv:key list --namespace-id "$namespace_id" 2>/dev/null; then
        success "Listed keys for $env_label KV namespace"
    else
        error "Failed to list keys for $env_label KV namespace"
    fi
}

# Get KV key value
get_kv_key() {
    local namespace_id=$1
    local key=$2
    local env_label=$3

    if [ "$namespace_id" = "your-splunk-cache-id" ] || [ "$namespace_id" = "your-splunk-cache-staging-id" ]; then
        warning "Cannot get key - placeholder namespace ID for $env_label"
        return 0
    fi

    if wrangler kv:key get "$key" --namespace-id "$namespace_id" 2>/dev/null; then
        success "Retrieved $key from $env_label KV store"
    else
        error "Failed to retrieve $key from $env_label KV store"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [ENVIRONMENT] [OPTIONS]"
    echo ""
    echo "ENVIRONMENT:"
    echo "  prod, production    Setup production KV store only"
    echo "  staging            Setup staging KV store only"
    echo "  both               Setup both KV stores (default)"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  -l, --list ENV     List all keys in KV store"
    echo "  -g, --get KEY ENV  Get specific key value"
    echo ""
    echo "Environment Variables:"
    echo "  PROD_KV_NAMESPACE_ID     Production KV namespace ID"
    echo "  STAGING_KV_NAMESPACE_ID  Staging KV namespace ID"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Setup both environments"
    echo "  $0 prod                               # Setup production only"
    echo "  PROD_KV_NAMESPACE_ID=abc123 $0 prod   # Setup with specific namespace ID"
    echo "  $0 --list prod                        # List production keys"
    echo "  $0 --get config:version prod          # Get specific key value"
}

# Main setup function
setup_kv_data() {
    local target_env=${1:-"both"}

    case $target_env in
        "prod"|"production")
            envs=("production")
            namespace_ids=("$PROD_KV_ID")
            ;;
        "staging")
            envs=("staging")
            namespace_ids=("$STAGING_KV_ID")
            ;;
        "both"|*)
            envs=("production" "staging")
            namespace_ids=("$PROD_KV_ID" "$STAGING_KV_ID")
            ;;
    esac

    for i in "${!envs[@]}"; do
        local env="${envs[i]}"
        local namespace_id="${namespace_ids[i]}"

        echo ""
        log "Setting up KV data for $env environment"
        log "Namespace ID: $namespace_id"
        echo "================================"

        setup_app_config "$namespace_id" "$env"
        setup_system_status "$namespace_id" "$env"
        setup_security_cache "$namespace_id" "$env"
        setup_user_data "$namespace_id" "$env"
        setup_api_cache "$namespace_id" "$env"

        echo ""
        success "KV data setup completed for $env environment"
    done
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_usage
        exit 0
        ;;
    -l|--list)
        check_prerequisites
        env_name=${2:-"production"}
        if [ "$env_name" = "production" ] || [ "$env_name" = "prod" ]; then
            list_kv_keys "$PROD_KV_ID" "production"
        elif [ "$env_name" = "staging" ]; then
            list_kv_keys "$STAGING_KV_ID" "staging"
        else
            error "Invalid environment: $env_name"
            exit 1
        fi
        exit 0
        ;;
    -g|--get)
        if [ -z "$2" ] || [ -z "$3" ]; then
            error "Key and environment required for get option"
            show_usage
            exit 1
        fi
        check_prerequisites
        key="$2"
        env_name="$3"
        if [ "$env_name" = "production" ] || [ "$env_name" = "prod" ]; then
            get_kv_key "$PROD_KV_ID" "$key" "production"
        elif [ "$env_name" = "staging" ]; then
            get_kv_key "$STAGING_KV_ID" "$key" "staging"
        else
            error "Invalid environment: $env_name"
            exit 1
        fi
        exit 0
        ;;
    *)
        check_prerequisites
        setup_kv_data "$1"

        echo ""
        echo "🎉 ===== KV DATA SETUP COMPLETED ====="
        success "All KV stores have been initialized successfully!"
        echo ""
        echo "📊 Verification commands:"
        echo "  # List all keys"
        echo "  $0 --list production"
        echo "  $0 --list staging"
        echo ""
        echo "  # Get specific values"
        echo "  $0 --get config:version production"
        echo "  $0 --get status:system_health production"
        echo ""
        echo "📋 Management commands:"
        echo "  # Update a value"
        echo "  wrangler kv:key put \"config:version\" \"1.0.1\" --namespace-id $PROD_KV_ID"
        echo "  # Get all keys"
        echo "  wrangler kv:key list --namespace-id $PROD_KV_ID"
        ;;
esac