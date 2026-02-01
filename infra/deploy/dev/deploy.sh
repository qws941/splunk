#!/bin/bash
#
# Development Deployment Script for Splunk Security App
# Purpose: Deploy to local or dev Splunk instance for testing
# Usage: ./deploy.sh [options]
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration (from env or defaults)
SPLUNK_HOST="${SPLUNK_HOST:-https://localhost:8089}"
SPLUNK_USER="${SPLUNK_USER:-admin}"
SPLUNK_PASS="${SPLUNK_PASS:-changeme}"
SPLUNK_VERIFY_SSL="${SPLUNK_VERIFY_SSL:-false}"

# App configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
APP_NAME="security"
APP_VERSION=$(grep -E "^version\s*=" "$PROJECT_ROOT/default/app.conf" 2>/dev/null | sed 's/.*=\s*//' | tr -d ' ' || echo "unknown")

# Build tarball
echo -e "${BLUE}🔨 Building app tarball...${NC}"
cd "$PROJECT_ROOT"

# Create tarball
TARBALL="releases/${APP_NAME}-${APP_VERSION}_$(date +%s).tar.gz"
mkdir -p releases
tar -czf "$TARBALL" \
    --exclude='.git' \
    --exclude='.github' \
    --exclude='bazel-*' \
    --exclude='releases' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='.DS_Store' \
    --transform="s,^,$APP_NAME/," \
    default/ bin/ static/ metadata/ README.md 2>/dev/null || true

if [[ ! -f "$TARBALL" ]]; then
    echo -e "${RED}✗ Failed to create tarball${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Tarball created: $TARBALL${NC}"

# Install via REST API
echo -e "${BLUE}🚀 Installing app to Splunk at $SPLUNK_HOST...${NC}"

# Determine SSL flag
if [[ "$SPLUNK_VERIFY_SSL" == "false" ]]; then
    SSL_FLAG="-k"
else
    SSL_FLAG=""
fi

# Upload app
CURL_CMD="curl -s -u $SPLUNK_USER:$SPLUNK_PASS $SSL_FLAG -X POST"
CURL_CMD="$CURL_CMD -F file=@$TARBALL"
RESPONSE=$($CURL_CMD "$SPLUNK_HOST/services/apps/local" 2>&1 || echo "FAILED")

if echo "$RESPONSE" | grep -q "\"name\":\"$APP_NAME\""; then
    echo -e "${GREEN}✓ App installed successfully${NC}"
    echo -e "${YELLOW}App Version: $APP_VERSION${NC}"
    echo -e "${YELLOW}Splunk Host: $SPLUNK_HOST${NC}"
    exit 0
else
    echo -e "${RED}✗ Installation failed${NC}"
    echo -e "${YELLOW}Response: ${RESPONSE:0:200}...${NC}"
    exit 1
fi
