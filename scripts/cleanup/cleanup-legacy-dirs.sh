#!/bin/bash
# File: scripts/cleanup-legacy-dirs.sh
# Purpose: Delete legacy directories (nextrade/, archive-dev/, xwiki/)
# Requires: Phase 1 backup completed first

set -e  # Exit on error

BACKUP_VERIFIED=false
BACKUP_DIR=$(ls -td ~/backups/splunk_cleanup_* 2>/dev/null | head -1)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Legacy Directory Cleanup (Phase 2)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verify backup exists
if [ -f "$BACKUP_DIR/nextrade_backup.tar.gz" ] && \
   [ -f "$BACKUP_DIR/archive-dev_backup.tar.gz" ]; then
    echo "✅ Backup verified: $BACKUP_DIR"
    BACKUP_VERIFIED=true
else
    echo "❌ ERROR: Backup not found."
    echo ""
    echo "Run Phase 1 backup first:"
    echo "  cd /home/jclee/app/splunk"
    echo "  BACKUP_DATE=\$(date +%Y%m%d_%H%M%S)"
    echo "  mkdir -p ~/backups/splunk_cleanup_\${BACKUP_DATE}"
    echo "  tar -czf ~/backups/splunk_cleanup_\${BACKUP_DATE}/nextrade_backup.tar.gz nextrade/"
    echo "  tar -czf ~/backups/splunk_cleanup_\${BACKUP_DATE}/archive-dev_backup.tar.gz archive-dev/"
    echo ""
    exit 1
fi

# Delete legacy directories
if [ "$BACKUP_VERIFIED" = true ]; then
    cd /home/jclee/app/splunk

    # Check if directories exist before deletion
    if [ -d "nextrade" ]; then
        FILE_COUNT=$(find nextrade -type f | wc -l)
        echo "Deleting nextrade/ ($FILE_COUNT files)..."
        rm -rf nextrade/
        echo "✅ nextrade/ deleted"
    else
        echo "ℹ️  nextrade/ already deleted"
    fi

    if [ -d "archive-dev" ]; then
        FILE_COUNT=$(find archive-dev -type f | wc -l)
        echo "Deleting archive-dev/ ($FILE_COUNT files)..."
        rm -rf archive-dev/
        echo "✅ archive-dev/ deleted"
    else
        echo "ℹ️  archive-dev/ already deleted"
    fi

    if [ -d "xwiki" ]; then
        echo "Deleting xwiki/ (empty directory)..."
        rmdir xwiki/ 2>/dev/null || rm -rf xwiki/
        echo "✅ xwiki/ deleted"
    else
        echo "ℹ️  xwiki/ already deleted"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Phase 2 Complete: Legacy directories deleted"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Backup location: $BACKUP_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Run Phase 3: bash scripts/consolidate-duplicates.sh"
    echo "  2. Review configs/: bash scripts/review-configs.sh"
    echo "  3. Git commit: git add . && git commit -m 'chore: Remove legacy directories'"
    echo ""
fi
