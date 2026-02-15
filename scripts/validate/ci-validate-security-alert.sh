#!/bin/bash
set -euo pipefail

# CI/CD Validation for Splunk Security Alert System
# Validates security_alert app structure and syntax

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PASSED=0
FAILED=0

check_passed() {
    echo "✓ $1"
    PASSED=$((PASSED + 1))
}

check_failed() {
    echo "✗ $1"
    FAILED=$((FAILED + 1))
}

echo "========================================="
echo "CI/CD Validation - Security Alert App"
echo "========================================="
echo ""

# 1. Git Repository
echo "[1] Git Repository"
if git rev-parse --git-dir > /dev/null 2>&1; then
    check_passed "Git repository detected"
else
    check_failed "Not a git repository"
fi

# 2. App Structure - Required Directories
echo ""
echo "[2] App Structure - Directories"
REQUIRED_DIRS=(
    "security_alert"
    "security_alert/default"
    "security_alert/bin"
    "security_alert/lookups"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        check_passed "Directory exists: $dir"
    else
        check_failed "Missing directory: $dir"
    fi
done

# 3. App Structure - Required Files
echo ""
echo "[3] App Structure - Required Files"
REQUIRED_APP_FILES=(
    "security_alert/default/app.conf"
    "security_alert/default/alert_actions.conf"
    "security_alert/default/savedsearches.conf"
    "security_alert/default/props.conf"
    "security_alert/default/transforms.conf"
)

for file in "${REQUIRED_APP_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        check_passed "File exists: $file"
    else
        check_failed "Missing file: $file"
    fi
done

# 4. Python Scripts
echo ""
echo "[4] Python Scripts"
# Check for Python scripts in either location
PYTHON_SCRIPTS=(
    "security_alert/bin/fortigate_auto_response.py"
    "security_alert/bin/slack_blockkit_alert.py"
    "security_alert/bin/auto_validator.py"
)

PYTHON_FOUND=0
for script in "${PYTHON_SCRIPTS[@]}"; do
    if [ -f "$PROJECT_ROOT/$script" ]; then
        check_passed "Python script found: $script"
        PYTHON_FOUND=$((PYTHON_FOUND + 1))
    fi
done

if [ "$PYTHON_FOUND" -lt 2 ]; then
    check_failed "Insufficient Python scripts ($PYTHON_FOUND/3)"
fi

# 5. Python Syntax Validation
echo ""
echo "[5] Python Syntax Validation"
PYTHON_FILES=(
    "security_alert/bin/fortigate_auto_response.py"
    "security_alert/bin/slack_blockkit_alert.py"
)

for file in "${PYTHON_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        if python3 -m py_compile "$PROJECT_ROOT/$file" 2>/dev/null; then
            check_passed "Python syntax valid: $file"
        else
            check_failed "Python syntax error: $file"
        fi
    fi
done

# 6. CSV Lookup Files
echo ""
echo "[6] CSV Lookup Files"
CSV_COUNT=$(find "$PROJECT_ROOT/security_alert/lookups" -name "*.csv" 2>/dev/null | wc -l)
if [ "$CSV_COUNT" -ge 10 ]; then
    check_passed "CSV lookup files present ($CSV_COUNT files)"
else
    check_failed "CSV lookup files incomplete ($CSV_COUNT expected >= 10)"
fi

# 7. Documentation
echo ""
echo "[7] Documentation"
REQUIRED_DOCS=(
    "README.md"
)

for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f "$PROJECT_ROOT/$doc" ]; then
        check_passed "Documentation found: $doc"
    else
        check_failed "Missing documentation: $doc"
    fi
done

# 8. GitHub Workflows
echo ""
echo "[8] GitHub Workflows"
if [ -f "$PROJECT_ROOT/.github/workflows/ci.yml" ]; then
    check_passed "CI workflow found: .github/workflows/ci.yml"
else
    check_failed "Missing CI workflow: .github/workflows/ci.yml"
fi

if [ -f "$PROJECT_ROOT/.github/workflows/deploy.yml" ]; then
    check_passed "Deploy workflow found: .github/workflows/deploy.yml"
else
    check_failed "Missing deploy workflow: .github/workflows/deploy.yml"
fi

# 9. Python Requirements
echo ""
echo "[9] Python Requirements"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    check_passed "Requirements file found: requirements.txt"
else
    check_failed "Missing requirements file: requirements.txt"
fi

if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
    check_passed "Project config found: pyproject.toml"
else
    check_failed "Missing project config: pyproject.toml"
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
    exit 0
else
    echo "⚠️  $FAILED check(s) failed"
    exit 1
fi
