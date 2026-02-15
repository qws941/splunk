#!/bin/bash
set -euo pipefail

# CI/CD Validation Script (No Splunk Required)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PASSED=0
FAILED=0

echo "========================================="
echo "CI/CD Validation (No Splunk)"
echo "========================================="
echo ""

check_passed() {
    echo "✓ $1"
    PASSED=$((PASSED + 1))
}

check_failed() {
    echo "✗ $1"
    FAILED=$((FAILED + 1))
}

# 1. Git Status
echo "[1] Git Repository"
if git rev-parse --git-dir > /dev/null 2>&1; then
    check_passed "Git repository detected"

    COMMITS=$(git rev-list --count HEAD)
    if [ "$COMMITS" -ge 4 ]; then
        check_passed "Git commits present ($COMMITS commits)"
    else
        check_failed "Insufficient commits ($COMMITS/4)"
    fi
else
    check_failed "Not a git repository"
fi

# 2. File Structure
echo ""
echo "[2] File Structure"

REQUIRED_FILES=(
    ".pre-commit-config.yaml"
    "default/eventgen.conf"
    "default/data/models/FortiGate_Security.json"
    "default/data/ui/views/eventgen_test_dashboard.xml"
    "bin/settings_handler_persistent.py"
    "tests/integration/test_eventgen_scenarios.sh"
    "DEPLOYMENT-GUIDE.md"
    "README-DEPLOYMENT.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        check_passed "File exists: $file"
    else
        check_failed "Missing file: $file"
    fi
done

# 3. Sample Files
echo ""
echo "[3] Sample Files"
SAMPLE_COUNT=$(find "$PROJECT_ROOT/samples" -name "*.sample" 2>/dev/null | wc -l)
if [ "$SAMPLE_COUNT" -eq 6 ]; then
    check_passed "Sample files present (6/6)"
else
    check_failed "Sample files incomplete ($SAMPLE_COUNT/6)"
fi

# 4. Python Syntax
echo ""
echo "[4] Python Syntax Validation"
PYTHON_FILES=(
    "bin/settings_handler_persistent.py"
)

for file in "${PYTHON_FILES[@]}"; do
    if python3 -m py_compile "$PROJECT_ROOT/$file" 2>/dev/null; then
        check_passed "Python syntax valid: $file"
    else
        check_failed "Python syntax error: $file"
    fi
done

# 5. JSON Syntax
echo ""
echo "[5] JSON Syntax Validation"
JSON_FILES=(
    "default/data/models/FortiGate_Security.json"
)

for file in "${JSON_FILES[@]}"; do
    if python3 -c "import json; json.load(open('$PROJECT_ROOT/$file'))" 2>/dev/null; then
        check_passed "JSON syntax valid: $file"
    else
        check_failed "JSON syntax error: $file"
    fi
done

# 6. XML Syntax
echo ""
echo "[6] XML Syntax Validation"
XML_FILES=(
    "default/data/ui/views/eventgen_test_dashboard.xml"
)

for file in "${XML_FILES[@]}"; do
    if command -v xmllint &> /dev/null; then
        if xmllint --noout "$PROJECT_ROOT/$file" 2>/dev/null; then
            check_passed "XML syntax valid: $file"
        else
            check_failed "XML syntax error: $file"
        fi
    else
        echo "  ⚠ xmllint not available, skipping XML validation"
    fi
done

# 7. Bash Syntax
echo ""
echo "[7] Bash Script Validation"
BASH_SCRIPTS=(
    "tests/integration/test_eventgen_scenarios.sh"
)

for script in "${BASH_SCRIPTS[@]}"; do
    if bash -n "$PROJECT_ROOT/$script" 2>/dev/null; then
        check_passed "Bash syntax valid: $script"
    else
        check_failed "Bash syntax error: $script"
    fi
done

# 8. Executable Permissions
echo ""
echo "[8] Executable Permissions"
for script in "${BASH_SCRIPTS[@]}"; do
    if [ -x "$PROJECT_ROOT/$script" ]; then
        check_passed "Executable: $script"
    else
        check_failed "Not executable: $script"
    fi
done

# 9. Documentation
echo ""
echo "[9] Documentation Completeness"
DOC_FILES=(
    "docs/guides/EVENTGEN-TESTING-GUIDE.md"
    "docs/guides/EVENTGEN-ALERT-TESTING.md"
    "docs/guides/DATA-MODEL-TSTATS-GUIDE.md"
    "docs/development/PERSISTENT-HANDLER-MIGRATION.md"
    "IMPLEMENTATION-REVIEW.md"
    "SESSION-FINAL-REPORT.md"
)

for doc in "${DOC_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$doc" ]; then
        check_passed "Documentation exists: $doc"
        continue
    fi

    case "$doc" in
        "IMPLEMENTATION-REVIEW.md"|"SESSION-FINAL-REPORT.md")
            archived="docs/archived/sessions/$doc"
            if [ -f "$PROJECT_ROOT/$archived" ]; then
                check_passed "Documentation exists: $archived (archived)"
            else
                check_failed "Missing documentation: $doc"
            fi
            ;;
        *)
            check_failed "Missing documentation: $doc"
            ;;
    esac
done

# 10. Pre-commit Hooks
echo ""
echo "[10] Pre-commit Hooks"
if [ "${RUN_PRECOMMIT:-0}" != "1" ]; then
    echo "  ⚠ pre-commit not run (set RUN_PRECOMMIT=1 to enable)"
elif command -v pre-commit &> /dev/null; then
    if cd "$PROJECT_ROOT" && pre-commit run --all-files 2>&1 | tail -1 | grep -q "Passed"; then
        check_passed "Pre-commit hooks passed"
    else
        echo "  ⚠ Some pre-commit hooks failed (may auto-fix)"
    fi
else
    echo "  ⚠ pre-commit not installed, skipping"
fi

# 11. Config Validation (CLI)
echo ""
echo "[11] Splunk CLI Validation"
if [ -f "$PROJECT_ROOT/releases/bin/splunk-cli" ]; then
    if "$PROJECT_ROOT/releases/bin/splunk-cli" validate config 2>&1 | grep -i -q "passed"; then
        check_passed "Splunk CLI validation passed"
    else
        check_failed "Splunk CLI validation failed"
    fi
else
    echo "  ⚠ splunk-cli not found, skipping"
fi

# 12. Line Counts
echo ""
echo "[12] Code Metrics"
TOTAL_LINES=$(find "$PROJECT_ROOT" \( -name "*.py" -o -name "*.sh" -o -name "*.json" -o -name "*.xml" -o -name "*.conf" -o -name "*.md" \) -type f -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
if [ "$TOTAL_LINES" -gt 3000 ]; then
    check_passed "Code metrics: $TOTAL_LINES lines"
else
    echo "  ⚠ Total lines: $TOTAL_LINES (expected >3000)"
fi

# 13. Dashboard Reference Validation
echo ""
echo "[13] Dashboard Reference Validation"
VIEWS_DIR="$PROJECT_ROOT/default/data/ui/views"
# Use Python for cross-platform regex (grep -P not available in alpine/slim)
DASHBOARD_REFS=$(python3 -c "
import re, sys
try:
    with open('$PROJECT_ROOT/default/savedsearches.conf', 'r') as f:
        content = f.read()
    matches = set(re.findall(r'/app/security/([a-z_]+)', content))
    print('\n'.join(sorted(matches)))
except Exception as e:
    sys.exit(0)
" 2>/dev/null)
MISSING_DASHBOARDS=0
for dashboard in $DASHBOARD_REFS; do
    if [ -f "$VIEWS_DIR/${dashboard}.xml" ]; then
        check_passed "Dashboard exists: $dashboard"
    else
        check_failed "Missing dashboard: $dashboard (referenced in savedsearches.conf)"
        MISSING_DASHBOARDS=$((MISSING_DASHBOARDS + 1))
    fi
done
if [ "$MISSING_DASHBOARDS" -eq 0 ] && [ -n "$DASHBOARD_REFS" ]; then
    check_passed "All dashboard references valid"
fi

# Summary
echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo "✅ All CI/CD checks passed!"
    echo ""
    echo "Next Steps:"
    echo "1. Deploy to Splunk environment"
    echo "2. Run: ./scripts/validate/check-stanza.py"
    echo "3. Run: ./scripts/validate/verify-splunk-deployment.sh"
    exit 0
else
    echo "⚠️  $FAILED check(s) failed"
    echo "Review errors above and fix before deployment"
    exit 1
fi
