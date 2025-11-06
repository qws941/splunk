#!/bin/bash
# Security Alert System - Installation Script
# Purpose: Verify dependencies and permissions after deployment
# Version: 2.0.4

set -e

APP_NAME="security_alert"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "Security Alert System - Installation"
echo "Version: 2.0.4"
echo "=============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
        return 0
    else
        echo -e "${RED}✗ $1${NC}"
        return 1
    fi
}

info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# 1. Check app directory structure
echo "1. Checking directory structure..."
required_dirs=(
    "$APP_DIR/bin"
    "$APP_DIR/default"
    "$APP_DIR/lookups"
    "$APP_DIR/lib/python3"
    "$APP_DIR/metadata"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        check_status "Directory exists: $(basename $dir)"
    else
        echo -e "${RED}✗ Missing directory: $dir${NC}"
        exit 1
    fi
done
echo ""

# 2. Check bundled Python libraries
echo "2. Checking bundled Python libraries..."
LIB_DIR="$APP_DIR/lib/python3"
required_libs=("requests" "urllib3" "charset_normalizer" "certifi" "idna")

for lib in "${required_libs[@]}"; do
    if [ -d "$LIB_DIR/$lib" ]; then
        check_status "Library bundled: $lib"
    else
        echo -e "${RED}✗ Missing library: $lib${NC}"
        exit 1
    fi
done
echo ""

# 3. Check Python scripts are executable
echo "3. Checking Python scripts..."
python_scripts=(
    "$APP_DIR/bin/slack.py"
    "$APP_DIR/bin/fortigate_auto_response.py"
    "$APP_DIR/bin/post_install_check.py"
    "$APP_DIR/bin/deployment_health_check.py"
    "$APP_DIR/bin/auto_validator.py"
    "$APP_DIR/bin/splunk_feature_checker.py"
)

for script in "${python_scripts[@]}"; do
    if [ -f "$script" ]; then
        chmod +x "$script" 2>/dev/null || true
        check_status "Script exists: $(basename $script)"
    else
        echo -e "${YELLOW}⚠ Optional script missing: $(basename $script)${NC}"
    fi
done
echo ""

# 4. Check CSV lookup files
echo "4. Checking CSV lookup files..."
if [ -d "$APP_DIR/lookups" ]; then
    csv_count=$(find "$APP_DIR/lookups" -name "*.csv" | wc -l)
    if [ "$csv_count" -ge 10 ]; then
        check_status "CSV files found: $csv_count"
    else
        echo -e "${YELLOW}⚠ Expected 10+ CSV files, found: $csv_count${NC}"
    fi

    # Set permissions
    chmod 644 "$APP_DIR/lookups"/*.csv 2>/dev/null || true
    check_status "CSV permissions set to 644"
fi
echo ""

# 5. Test Python imports
echo "5. Testing Python imports..."
cd "$APP_DIR/bin"
python3 -c "
import sys
import os
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath('$SCRIPT_DIR')))
LIB_DIR = os.path.join(APP_DIR, 'lib', 'python3')
sys.path.insert(0, LIB_DIR)

try:
    import requests
    print('✓ requests imported successfully')
except ImportError as e:
    print(f'✗ Failed to import requests: {e}')
    sys.exit(1)

try:
    import urllib3
    print('✓ urllib3 imported successfully')
except ImportError as e:
    print(f'✗ Failed to import urllib3: {e}')
    sys.exit(1)

print('✓ All bundled libraries can be imported')
"
check_status "Bundled libraries test"
echo ""

# 6. Check configuration files
echo "6. Checking configuration files..."
config_files=(
    "$APP_DIR/default/app.conf"
    "$APP_DIR/default/alert_actions.conf"
    "$APP_DIR/default/savedsearches.conf"
    "$APP_DIR/default/macros.conf"
    "$APP_DIR/default/transforms.conf"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        check_status "Config exists: $(basename $file)"
    else
        echo -e "${RED}✗ Missing config: $(basename $file)${NC}"
        exit 1
    fi
done
echo ""

# 7. Summary
echo "=============================================="
echo -e "${GREEN}Installation check completed successfully!${NC}"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Configure Slack webhook URL in local/alert_actions.conf"
echo "2. Restart Splunk: /opt/splunk/bin/splunk restart"
echo "3. Verify in Splunk UI: Apps > Security Alert System"
echo ""
echo "For detailed configuration, see:"
echo "  - README.md"
echo "  - DEPLOYMENT-CHECKLIST.md"
echo ""
