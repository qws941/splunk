#!/bin/bash
# File: scripts/run-full-cleanup.sh
# Purpose: Master script to run all cleanup phases in order
# Warning: This will delete 242 legacy files (~4.7MB)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /home/jclee/app/splunk

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Splunk Repository Cleanup - Full Automation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This script will:"
echo "  1. Create backup of legacy directories"
echo "  2. Delete legacy directories (nextrade/, archive-dev/, xwiki/)"
echo "  3. Consolidate duplicate CSV files"
echo "  4. Review configs/ directory (manual decision required)"
echo ""
echo "Estimated:"
echo "  - Files to delete: 242"
echo "  - Space to recover: ~4.7MB"
echo "  - Execution time: 5-10 minutes"
echo ""

# Confirm execution
read -p "Proceed with cleanup? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 1: Creating Backup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/backups/splunk_cleanup_${BACKUP_DATE}"

mkdir -p "$BACKUP_DIR"

echo "Backup directory: $BACKUP_DIR"
echo ""

# Backup nextrade/
if [ -d "nextrade" ]; then
    echo "Backing up nextrade/..."
    tar -czf "$BACKUP_DIR/nextrade_backup.tar.gz" nextrade/
    echo "✅ nextrade/ backed up"
else
    echo "ℹ️  nextrade/ not found (already deleted?)"
fi

# Backup archive-dev/
if [ -d "archive-dev" ]; then
    echo "Backing up archive-dev/..."
    tar -czf "$BACKUP_DIR/archive-dev_backup.tar.gz" archive-dev/
    echo "✅ archive-dev/ backed up"
else
    echo "ℹ️  archive-dev/ not found (already deleted?)"
fi

# Backup xwiki/ (if exists)
if [ -d "xwiki" ]; then
    echo "Backing up xwiki/..."
    tar -czf "$BACKUP_DIR/xwiki_backup.tar.gz" xwiki/
    echo "✅ xwiki/ backed up"
else
    echo "ℹ️  xwiki/ not found (empty or already deleted)"
fi

# Verify backup
echo ""
echo "Backup verification:"
ls -lh "$BACKUP_DIR/"

echo ""
echo "✅ Phase 1 Complete: Backup created"
echo ""

# Phase 2: Delete legacy directories
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 2: Deleting Legacy Directories"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash "$SCRIPT_DIR/cleanup-legacy-dirs.sh"

# Phase 3: Consolidate duplicates
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 3: Consolidating Duplicate CSVs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash "$SCRIPT_DIR/consolidate-duplicates.sh"

# Phase 4: Review configs/ (manual)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 4: Reviewing configs/ Directory"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash "$SCRIPT_DIR/review-configs.sh"

# Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Cleanup Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  - Backup location: $BACKUP_DIR"
echo "  - Legacy directories deleted: nextrade/, archive-dev/, xwiki/"
echo "  - Duplicate CSVs consolidated to: security_alert/lookups/"
echo "  - configs/ review completed (manual decision required)"
echo ""
echo "Next steps:"
echo "  1. Review git status: git status"
echo "  2. Test deployment package: tar -czf security_alert.tar.gz security_alert/"
echo "  3. Commit cleanup: git add . && git commit -m 'chore: Remove legacy files (242 files, ~4.7MB)'"
echo "  4. Push to remote: git push origin master"
echo ""
echo "Rollback (if needed):"
echo "  cd /home/jclee/app/splunk"
echo "  tar -xzf $BACKUP_DIR/nextrade_backup.tar.gz"
echo "  tar -xzf $BACKUP_DIR/archive-dev_backup.tar.gz"
echo ""
