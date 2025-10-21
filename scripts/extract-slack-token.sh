#!/bin/bash
# Slack Token Extraction Script
# Extracts Slack Bot token from encrypted ZIP file

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TOKEN_ZIP="secrets/slack_token.zip"
PASSWORD="admin123!"

echo -e "${BLUE}Slack Token Extraction${NC}"
echo ""

# Check if ZIP file exists
if [ ! -f "$TOKEN_ZIP" ]; then
    echo -e "${RED}✗ Token ZIP file not found: ${TOKEN_ZIP}${NC}"
    exit 1
fi

# Extract token
echo -e "${YELLOW}→ Extracting Slack token...${NC}"
TOKEN=$(unzip -p "$TOKEN_ZIP" -P "$PASSWORD" 2>/dev/null || echo "FAILED")

if [ "$TOKEN" = "FAILED" ]; then
    echo -e "${RED}✗ Failed to extract token${NC}"
    echo -e "${YELLOW}  Check password or ZIP file${NC}"
    exit 1
fi

# Validate token format
if [[ ! "$TOKEN" =~ ^xoxb- ]]; then
    echo -e "${RED}✗ Invalid token format (must start with 'xoxb-')${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Token extracted successfully${NC}"
echo ""
echo -e "${BLUE}Token (masked): ${NC}${TOKEN:0:15}...${TOKEN: -8}"
echo ""
echo -e "${YELLOW}Add to .env file:${NC}"
echo "SLACK_BOT_TOKEN=$TOKEN"
echo ""
echo -e "${YELLOW}Or update directly:${NC}"
echo "sed -i 's/^SLACK_BOT_TOKEN=.*/SLACK_BOT_TOKEN=$TOKEN/' .env"
