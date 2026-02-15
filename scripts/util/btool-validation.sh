#!/bin/bash
# ========================================
# Splunk btool Validation Script
# App: security_alert v2.0.4
# ========================================

set -euo pipefail

APP_NAME="security_alert"
APP_DIR="/opt/splunk/etc/apps/${APP_NAME}"
SPLUNK_BIN="/opt/splunk/bin/splunk"

echo "========================================="
echo "Splunk btool Validation"
echo "App: ${APP_NAME}"
echo "========================================="
echo ""

# Check if running as splunk user or root
if [[ $EUID -ne 0 ]] && [[ "$(whoami)" != "splunk" ]]; then
    echo "⚠️  Warning: Not running as root or splunk user"
    echo "   Some btool commands may require elevated privileges"
    echo ""
fi

# Check if app directory exists
if [[ ! -d "$APP_DIR" ]]; then
    echo "❌ App directory not found: $APP_DIR"
    echo "   Please install the app first"
    exit 1
fi

echo "✓ App directory found: $APP_DIR"
echo ""

# 1. Validate app.conf
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. App Configuration (app.conf)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v "$SPLUNK_BIN" &> /dev/null; then
    $SPLUNK_BIN btool app list "$APP_NAME" --debug 2>&1 | grep -A5 "^\[${APP_NAME}\]" || echo "⚠️  btool not available or no output"
else
    echo "⚠️  Splunk binary not found at $SPLUNK_BIN"
    echo "   Checking file directly..."
    if [[ -f "$APP_DIR/default/app.conf" ]]; then
        echo "✓ app.conf exists"
        cat "$APP_DIR/default/app.conf"
    else
        echo "❌ app.conf not found"
    fi
fi
echo ""

# 2. Validate alert_actions.conf
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Alert Actions (alert_actions.conf)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ -f "$APP_DIR/default/alert_actions.conf" ]]; then
    echo "✓ alert_actions.conf exists"
    grep -A15 "^\[slack\]" "$APP_DIR/default/alert_actions.conf" || echo "⚠️  No [slack] stanza found"
else
    echo "❌ alert_actions.conf not found"
fi
echo ""

# 3. Validate transforms.conf (lookup definitions)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Lookup Definitions (transforms.conf)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ -f "$APP_DIR/default/transforms.conf" ]]; then
    echo "✓ transforms.conf exists"
    LOOKUP_COUNT=$(grep -c "^\[.*\]" "$APP_DIR/default/transforms.conf" || echo "0")
    echo "  Lookup definitions: $LOOKUP_COUNT"

    # List all lookup definitions
    echo ""
    echo "  Lookup stanzas:"
    grep "^\[.*\]" "$APP_DIR/default/transforms.conf" | sed 's/\[//;s/\]//' | sed 's/^/    - /'
else
    echo "❌ transforms.conf not found"
fi
echo ""

# 4. Validate props.conf (automatic lookups)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Automatic Lookups (props.conf)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ -f "$APP_DIR/default/props.conf" ]]; then
    echo "✓ props.conf exists"
    AUTO_LOOKUP_COUNT=$(grep -c "^LOOKUP-" "$APP_DIR/default/props.conf" || echo "0")
    echo "  Automatic lookups: $AUTO_LOOKUP_COUNT"

    # List all automatic lookups
    echo ""
    echo "  LOOKUP definitions:"
    grep "^LOOKUP-" "$APP_DIR/default/props.conf" | sed 's/^/    /'
else
    echo "❌ props.conf not found"
fi
echo ""

# 5. Validate savedsearches.conf (alerts)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Alert Definitions (savedsearches.conf)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ -f "$APP_DIR/default/savedsearches.conf" ]]; then
    echo "✓ savedsearches.conf exists"
    ALERT_COUNT=$(grep -c "^\[.*Alert.*\]" "$APP_DIR/default/savedsearches.conf" || echo "0")
    echo "  Total alerts: $ALERT_COUNT"

    # Count enabled vs disabled alerts
    ENABLED_COUNT=$(grep -c "enableSched = 1" "$APP_DIR/default/savedsearches.conf" || echo "0")
    DISABLED_COUNT=$(grep -c "enableSched = 0" "$APP_DIR/default/savedsearches.conf" || echo "0")
    echo "  Enabled alerts: $ENABLED_COUNT"
    echo "  Disabled alerts: $DISABLED_COUNT"

    echo ""
    echo "  Alert list:"
    grep "^\[.*Alert.*\]" "$APP_DIR/default/savedsearches.conf" | sed 's/\[//;s/\]//' | while read -r alert; do
        ENABLED=$(grep -A50 "^\[${alert}\]" "$APP_DIR/default/savedsearches.conf" | grep "enableSched" | head -1 | grep -o "[01]" || echo "?")
        STATUS="?"
        if [[ "$ENABLED" == "1" ]]; then
            STATUS="✅ ENABLED"
        elif [[ "$ENABLED" == "0" ]]; then
            STATUS="⏸️  DISABLED"
        fi
        echo "    $STATUS - $alert"
    done
else
    echo "❌ savedsearches.conf not found"
fi
echo ""

# 6. Validate CSV lookup files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Lookup CSV Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ -d "$APP_DIR/lookups" ]]; then
    CSV_COUNT=$(find "$APP_DIR/lookups" -name "*.csv" | wc -l)
    echo "✓ Lookups directory exists"
    echo "  CSV files: $CSV_COUNT"

    echo ""
    echo "  CSV file list:"
    find "$APP_DIR/lookups" -name "*.csv" -exec basename {} \; | sort | sed 's/^/    - /'

    # Check for empty CSV files
    echo ""
    echo "  Empty CSV files:"
    EMPTY_COUNT=0
    find "$APP_DIR/lookups" -name "*.csv" | while read -r csv; do
        if [[ ! -s "$csv" ]]; then
            echo "    ⚠️  $(basename "$csv") - EMPTY"
            ((EMPTY_COUNT++))
        fi
    done
    if [[ $EMPTY_COUNT -eq 0 ]]; then
        echo "    ✓ No empty CSV files"
    fi
else
    echo "❌ Lookups directory not found"
fi
echo ""

# 7. Validate Python scripts
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. Python Scripts"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ -d "$APP_DIR/bin" ]]; then
    PY_COUNT=$(find "$APP_DIR/bin" -name "*.py" | wc -l)
    echo "✓ Bin directory exists"
    echo "  Python scripts: $PY_COUNT"

    echo ""
    echo "  Python script permissions:"
    find "$APP_DIR/bin" -name "*.py" | while read -r script; do
        PERMS=$(stat -c "%a" "$script" 2>/dev/null || stat -f "%A" "$script" 2>/dev/null)
        BASENAME=$(basename "$script")
        if [[ "$PERMS" == "755" ]] || [[ "$PERMS" == "775" ]]; then
            echo "    ✓ $BASENAME - $PERMS (executable)"
        else
            echo "    ⚠️  $BASENAME - $PERMS (not executable)"
        fi
    done

    # Python syntax check
    echo ""
    echo "  Python syntax validation:"
    find "$APP_DIR/bin" -name "*.py" | while read -r script; do
        BASENAME=$(basename "$script")
        if python3 -m py_compile "$script" 2>/dev/null; then
            echo "    ✓ $BASENAME - syntax OK"
        else
            echo "    ❌ $BASENAME - SYNTAX ERROR"
        fi
    done
else
    echo "❌ Bin directory not found"
fi
echo ""

# 8. Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8. Validation Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ERRORS=0
WARNINGS=0

# Check critical files
[[ ! -f "$APP_DIR/default/app.conf" ]] && echo "❌ Missing: app.conf" && ((ERRORS++))
[[ ! -f "$APP_DIR/default/alert_actions.conf" ]] && echo "❌ Missing: alert_actions.conf" && ((ERRORS++))
[[ ! -f "$APP_DIR/default/transforms.conf" ]] && echo "❌ Missing: transforms.conf" && ((ERRORS++))
[[ ! -f "$APP_DIR/default/props.conf" ]] && echo "❌ Missing: props.conf" && ((ERRORS++))
[[ ! -f "$APP_DIR/default/savedsearches.conf" ]] && echo "❌ Missing: savedsearches.conf" && ((ERRORS++))
[[ ! -d "$APP_DIR/lookups" ]] && echo "❌ Missing: lookups directory" && ((ERRORS++))
[[ ! -d "$APP_DIR/bin" ]] && echo "❌ Missing: bin directory" && ((ERRORS++))

# Check for executable Python scripts
if [[ -d "$APP_DIR/bin" ]]; then
    NON_EXEC=$(find "$APP_DIR/bin" -name "*.py" ! -perm -111 | wc -l)
    if [[ $NON_EXEC -gt 0 ]]; then
        echo "⚠️  Warning: $NON_EXEC Python script(s) not executable"
        ((WARNINGS++))
    fi
fi

echo ""
if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    echo "✅ VALIDATION PASSED"
    echo "   No errors or warnings found"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo "⚠️  VALIDATION PASSED WITH WARNINGS"
    echo "   Errors: $ERRORS"
    echo "   Warnings: $WARNINGS"
    exit 0
else
    echo "❌ VALIDATION FAILED"
    echo "   Errors: $ERRORS"
    echo "   Warnings: $WARNINGS"
    exit 1
fi
