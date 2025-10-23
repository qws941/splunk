#!/bin/bash
# Cleanup Legacy Files for React Dashboard Migration
# This script archives old XML dashboards and enhanced duplicates

set -e

PROJECT_ROOT="/home/jclee/app/splunk"
ARCHIVE_DIR="$PROJECT_ROOT/archive-$(date +%Y%m%d)"

echo "🧹 Starting legacy cleanup..."
echo "Archive directory: $ARCHIVE_DIR"

# Create archive directory
mkdir -p "$ARCHIVE_DIR"/{dashboards,scripts,domains}

# Archive XML dashboards (replaced by React components)
echo ""
echo "📦 Archiving XML dashboards..."
if [ -d "$PROJECT_ROOT/configs/dashboards" ]; then
  cp -r "$PROJECT_ROOT/configs/dashboards" "$ARCHIVE_DIR/"
  echo "  ✓ Archived configs/dashboards/"
fi

if [ -d "$PROJECT_ROOT/dashboards" ]; then
  cp -r "$PROJECT_ROOT/dashboards" "$ARCHIVE_DIR/"
  rm -rf "$PROJECT_ROOT/dashboards"
  echo "  ✓ Archived and removed dashboards/"
fi

# Archive enhanced duplicates
echo ""
echo "📦 Archiving enhanced/duplicate files..."

enhanced_files=(
  "domains/integration/slack-webhook-handler-enhanced.js"
  "scripts/splunk-alert-action-enhanced.py"
  "scripts/slack-alert-cli-enhanced.js"
)

for file in "${enhanced_files[@]}"; do
  if [ -f "$PROJECT_ROOT/$file" ]; then
    mkdir -p "$(dirname "$ARCHIVE_DIR/$file")"
    cp "$PROJECT_ROOT/$file" "$ARCHIVE_DIR/$file"
    rm "$PROJECT_ROOT/$file"
    echo "  ✓ Archived and removed $file"
  fi
done

# Archive old deployment scripts (replaced by React build)
old_scripts=(
  "scripts/deploy-to-splunk.sh"
  "scripts/export-dashboards.js"
  "scripts/optimize-dashboard.py"
)

for script in "${old_scripts[@]}"; do
  if [ -f "$PROJECT_ROOT/$script" ]; then
    mkdir -p "$(dirname "$ARCHIVE_DIR/$script")"
    cp "$PROJECT_ROOT/$script" "$ARCHIVE_DIR/$script"
    rm "$PROJECT_ROOT/$script"
    echo "  ✓ Archived and removed $script"
  fi
done

echo ""
echo "✅ Legacy cleanup complete!"
echo ""
echo "Summary:"
echo "  - XML dashboards archived"
echo "  - Enhanced duplicates removed"
echo "  - Old deployment scripts archived"
echo ""
echo "Archive location: $ARCHIVE_DIR"
echo ""
echo "To restore files: cp -r $ARCHIVE_DIR/* $PROJECT_ROOT/"
