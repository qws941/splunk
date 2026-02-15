#!/bin/bash
# File: scripts/review-configs.sh
# Purpose: Review configs/ directory for duplicate or unnecessary files
# Requires: Manual decision after review

cd /home/jclee/app/splunk

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   configs/ Directory Review (Phase 4)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if configs/ directory exists
if [ ! -d "configs" ]; then
    echo "ℹ️  configs/ directory does not exist"
    echo ""
    exit 0
fi

# List all files in configs/
echo "1. Files in configs/ directory:"
echo ""

TOTAL_FILES=$(find configs/ -type f | wc -l)
TOTAL_SIZE=$(du -sh configs/ | cut -f1)

echo "   Total: $TOTAL_FILES files ($TOTAL_SIZE)"
echo ""

find configs/ -type f | while read file; do
    SIZE=$(du -h "$file" | cut -f1)
    echo "   - $file ($SIZE)"
done

# List all config files in security_alert/default/
echo ""
echo "2. Config files in security_alert/default/:"
echo ""

if [ -d "security_alert/default" ]; then
    TOTAL_FILES=$(find security_alert/default/ -type f -name "*.conf" | wc -l)
    echo "   Total: $TOTAL_FILES .conf files"
    echo ""

    find security_alert/default/ -type f -name "*.conf" | while read file; do
        SIZE=$(du -h "$file" | cut -f1)
        BASENAME=$(basename "$file")
        echo "   - $BASENAME ($SIZE)"
    done
else
    echo "   ⚠️  security_alert/default/ not found"
fi

# Compare if there are duplicate config files
echo ""
echo "3. Checking for duplicate config names:"
echo ""

DUPLICATES_FOUND=false

find configs/ -type f -name "*.conf" 2>/dev/null | while read config_file; do
    BASENAME=$(basename "$config_file")

    if [ -f "security_alert/default/$BASENAME" ]; then
        echo "   ⚠️  $BASENAME exists in both configs/ and security_alert/default/"

        if diff -q "$config_file" "security_alert/default/$BASENAME" > /dev/null 2>&1; then
            echo "      → Files are IDENTICAL (safe to delete configs/$BASENAME)"
        else
            echo "      → Files are DIFFERENT (review needed)"
        fi

        DUPLICATES_FOUND=true
    fi
done

if [ "$DUPLICATES_FOUND" = false ]; then
    echo "   ✅ No duplicate config file names found"
fi

# Summary and recommendations
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Review Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Decision Points:"
echo ""
echo "1. If configs/ contains deployment examples for different environments:"
echo "   → KEEP configs/ directory"
echo ""
echo "2. If configs/ duplicates security_alert/default/ with identical files:"
echo "   → DELETE configs/ directory"
echo ""
echo "3. If configs/ contains unique configuration examples:"
echo "   → KEEP configs/ and document purpose in README.md"
echo ""

echo "Manual Commands:"
echo ""
echo "# To delete configs/ directory (if duplicate):"
echo "  rm -rf configs/"
echo ""
echo "# To keep configs/ directory (if unique examples):"
echo "  echo 'configs/ contains deployment examples' >> README.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  Manual decision required - review output above"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
