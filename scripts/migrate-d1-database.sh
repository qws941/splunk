#!/bin/bash
# 🗄️ D1 Database Migration Script
# Applies database schema and sample data to Cloudflare D1

set -e

echo "🗄️ D1 Database Migration Script"
echo "================================"

# Configuration - Following jclee.me naming conventions
PROD_DB_NAME="splunk_events"
STAGING_DB_NAME="splunk_events_staging"
MIGRATIONS_DIR="./migrations"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

    # Check if wrangler is installed
    if ! command -v wrangler >/dev/null 2>&1; then
        error "Wrangler CLI is not installed. Please install it first:"
        echo "npm install -g wrangler"
        exit 1
    fi

    # Check if authenticated
    if ! wrangler whoami >/dev/null 2>&1; then
        error "Wrangler is not authenticated. Please run:"
        echo "wrangler login"
        exit 1
    fi

    # Check migrations directory
    if [ ! -d "$MIGRATIONS_DIR" ]; then
        error "Migrations directory not found: $MIGRATIONS_DIR"
        exit 1
    fi

    success "Prerequisites check completed"
}

# List available databases
list_databases() {
    log "Listing available D1 databases..."
    wrangler d1 list || warning "Failed to list databases"
}

# Apply migration to specific database
apply_migration() {
    local db_name=$1
    local migration_file=$2
    local migration_name=$(basename "$migration_file" .sql)

    log "Applying migration '$migration_name' to database '$db_name'..."

    if [ ! -f "$migration_file" ]; then
        error "Migration file not found: $migration_file"
        return 1
    fi

    # Apply the migration
    if wrangler d1 execute "$db_name" --file="$migration_file"; then
        success "Migration '$migration_name' applied successfully to '$db_name'"
        return 0
    else
        error "Failed to apply migration '$migration_name' to '$db_name'"
        return 1
    fi
}

# Verify migration by running test queries
verify_migration() {
    local db_name=$1

    log "Verifying migration for database '$db_name'..."

    # Test query to check if tables exist
    local verification_query="
    SELECT
        name as table_name,
        sql as table_schema
    FROM sqlite_master
    WHERE type='table' AND name NOT LIKE 'sqlite_%'
    ORDER BY name;
    "

    echo "Running verification query..."
    if wrangler d1 execute "$db_name" --command="$verification_query"; then
        success "Database verification completed for '$db_name'"

        # Additional data verification
        echo ""
        log "Checking sample data..."
        local data_check="
        SELECT 'fortigate_devices' as table_name, COUNT(*) as record_count FROM fortigate_devices
        UNION ALL
        SELECT 'fortigate_policies' as table_name, COUNT(*) as record_count FROM fortigate_policies
        UNION ALL
        SELECT 'security_events' as table_name, COUNT(*) as record_count FROM security_events
        UNION ALL
        SELECT 'system_config' as table_name, COUNT(*) as record_count FROM system_config;
        "

        wrangler d1 execute "$db_name" --command="$data_check" || warning "Data verification failed"

    else
        error "Database verification failed for '$db_name'"
        return 1
    fi
}

# Backup database (export data)
backup_database() {
    local db_name=$1
    local backup_file="backups/${db_name}_backup_$(date +%Y%m%d_%H%M%S).sql"

    log "Creating backup of database '$db_name'..."

    # Create backups directory if it doesn't exist
    mkdir -p backups

    # Export database
    if wrangler d1 export "$db_name" --output="$backup_file"; then
        success "Database backup created: $backup_file"
    else
        warning "Failed to create backup for '$db_name'"
    fi
}

# Show database statistics
show_database_stats() {
    local db_name=$1

    log "Database statistics for '$db_name':"

    local stats_query="
    SELECT
        'Total Tables' as metric,
        COUNT(*) as value
    FROM sqlite_master
    WHERE type='table' AND name NOT LIKE 'sqlite_%'

    UNION ALL

    SELECT
        'Total Indexes' as metric,
        COUNT(*) as value
    FROM sqlite_master
    WHERE type='index' AND name NOT LIKE 'sqlite_%'

    UNION ALL

    SELECT
        'Security Events' as metric,
        COUNT(*) as value
    FROM security_events

    UNION ALL

    SELECT
        'Active Devices' as metric,
        COUNT(*) as value
    FROM fortigate_devices
    WHERE status = 'active'

    UNION ALL

    SELECT
        'Active Policies' as metric,
        COUNT(*) as value
    FROM fortigate_policies
    WHERE status = 'enabled';
    "

    wrangler d1 execute "$db_name" --command="$stats_query" || warning "Failed to get statistics"
}

# Main migration function
run_migration() {
    local target_env=${1:-"both"}

    case $target_env in
        "prod"|"production")
            databases=("$PROD_DB_NAME")
            ;;
        "staging")
            databases=("$STAGING_DB_NAME")
            ;;
        "both"|*)
            databases=("$PROD_DB_NAME" "$STAGING_DB_NAME")
            ;;
    esac

    # Get list of migration files
    migration_files=($(find "$MIGRATIONS_DIR" -name "*.sql" | sort))

    if [ ${#migration_files[@]} -eq 0 ]; then
        error "No migration files found in $MIGRATIONS_DIR"
        exit 1
    fi

    log "Found ${#migration_files[@]} migration file(s)"
    for file in "${migration_files[@]}"; do
        echo "  - $(basename "$file")"
    done

    # Apply migrations to each database
    for db_name in "${databases[@]}"; do
        echo ""
        log "Processing database: $db_name"
        echo "================================"

        # Create backup before migration
        backup_database "$db_name"

        # Apply each migration file
        for migration_file in "${migration_files[@]}"; do
            if ! apply_migration "$db_name" "$migration_file"; then
                error "Migration failed for $db_name. Stopping."
                exit 1
            fi
        done

        # Verify the migration
        echo ""
        verify_migration "$db_name"

        # Show statistics
        echo ""
        show_database_stats "$db_name"

        echo ""
        success "Migration completed for database: $db_name"
    done
}

# Show usage information
show_usage() {
    echo "Usage: $0 [ENVIRONMENT] [OPTIONS]"
    echo ""
    echo "ENVIRONMENT:"
    echo "  prod, production    Apply migrations to production database only"
    echo "  staging            Apply migrations to staging database only"
    echo "  both               Apply migrations to both databases (default)"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  -l, --list         List available databases and exit"
    echo "  -v, --verify DB    Verify database schema and exit"
    echo "  -s, --stats DB     Show database statistics and exit"
    echo "  -b, --backup DB    Create database backup and exit"
    echo ""
    echo "Examples:"
    echo "  $0                           # Migrate both databases"
    echo "  $0 prod                      # Migrate production only"
    echo "  $0 staging                   # Migrate staging only"
    echo "  $0 --verify security-db-prod # Verify production database"
    echo "  $0 --stats security-db-prod  # Show production database stats"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_usage
        exit 0
        ;;
    -l|--list)
        check_prerequisites
        list_databases
        exit 0
        ;;
    -v|--verify)
        if [ -z "$2" ]; then
            error "Database name required for verify option"
            exit 1
        fi
        check_prerequisites
        verify_migration "$2"
        exit 0
        ;;
    -s|--stats)
        if [ -z "$2" ]; then
            error "Database name required for stats option"
            exit 1
        fi
        check_prerequisites
        show_database_stats "$2"
        exit 0
        ;;
    -b|--backup)
        if [ -z "$2" ]; then
            error "Database name required for backup option"
            exit 1
        fi
        check_prerequisites
        backup_database "$2"
        exit 0
        ;;
    *)
        # Run full migration
        check_prerequisites
        list_databases
        echo ""
        run_migration "$1"

        echo ""
        echo "🎉 ===== MIGRATION COMPLETED ====="
        success "All database migrations have been applied successfully!"
        echo ""
        echo "📊 Next steps:"
        echo "  1. Test the application with the new database schema"
        echo "  2. Verify data integrity and application functionality"
        echo "  3. Update application code to use the new schema"
        echo "  4. Deploy the updated application"
        echo ""
        echo "📋 Management commands:"
        echo "  # View data"
        echo "  wrangler d1 execute $PROD_DB_NAME --command 'SELECT * FROM security_events LIMIT 5;'"
        echo "  # Get statistics"
        echo "  ./scripts/migrate-d1-database.sh --stats $PROD_DB_NAME"
        echo "  # Create backup"
        echo "  ./scripts/migrate-d1-database.sh --backup $PROD_DB_NAME"
        ;;
esac