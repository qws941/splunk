#!/bin/bash
# Configuration Validation Script
# Validates environment variables and connections

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Configuration Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo -e "${YELLOW}  Run: cp .env.example .env${NC}"
    exit 1
fi

# Load .env
source .env

# 1. Check FortiAnalyzer Configuration
echo -e "${BLUE}[1/4] FortiAnalyzer Configuration${NC}"
if [ -z "${FAZ_HOST:-}" ]; then
    echo -e "${RED}  ✗ FAZ_HOST is not set${NC}"
else
    echo -e "${GREEN}  ✓ FAZ_HOST: ${FAZ_HOST}${NC}"
fi

if [ -z "${FAZ_USERNAME:-}" ]; then
    echo -e "${RED}  ✗ FAZ_USERNAME is not set${NC}"
else
    echo -e "${GREEN}  ✓ FAZ_USERNAME: ${FAZ_USERNAME}${NC}"
fi

if [ -z "${FAZ_PASSWORD:-}" ]; then
    echo -e "${RED}  ✗ FAZ_PASSWORD is not set${NC}"
else
    echo -e "${GREEN}  ✓ FAZ_PASSWORD: [HIDDEN]${NC}"
fi

# Test FAZ Connection
if [ -n "${FAZ_HOST:-}" ] && [ -n "${FAZ_USERNAME:-}" ] && [ -n "${FAZ_PASSWORD:-}" ]; then
    echo -e "${YELLOW}  → Testing FAZ connection...${NC}"
    RESPONSE=$(curl -k -s -X POST "https://${FAZ_HOST}/jsonrpc" \
        -H "Content-Type: application/json" \
        -d "{
            \"method\": \"exec\",
            \"params\": [{
                \"url\": \"/sys/login/user\",
                \"data\": {\"user\": \"${FAZ_USERNAME}\", \"passwd\": \"${FAZ_PASSWORD}\"}
            }],
            \"id\": 1
        }" 2>&1 || echo "FAILED")

    if echo "$RESPONSE" | grep -q '"code":0'; then
        echo -e "${GREEN}  ✓ FAZ connection successful${NC}"
    else
        echo -e "${RED}  ✗ FAZ connection failed${NC}"
        echo -e "${YELLOW}    Response: ${RESPONSE}${NC}"
    fi
fi

echo ""

# 2. Check Splunk HEC Configuration
echo -e "${BLUE}[2/4] Splunk HEC Configuration${NC}"
if [ -z "${SPLUNK_HEC_HOST:-}" ]; then
    echo -e "${RED}  ✗ SPLUNK_HEC_HOST is not set${NC}"
else
    echo -e "${GREEN}  ✓ SPLUNK_HEC_HOST: ${SPLUNK_HEC_HOST}${NC}"
fi

if [ -z "${SPLUNK_HEC_TOKEN:-}" ]; then
    echo -e "${RED}  ✗ SPLUNK_HEC_TOKEN is not set${NC}"
else
    echo -e "${GREEN}  ✓ SPLUNK_HEC_TOKEN: ${SPLUNK_HEC_TOKEN:0:8}...${NC}"
fi

if [ -z "${SPLUNK_INDEX_FORTIGATE:-}" ]; then
    echo -e "${RED}  ✗ SPLUNK_INDEX_FORTIGATE is not set${NC}"
else
    echo -e "${GREEN}  ✓ SPLUNK_INDEX_FORTIGATE: ${SPLUNK_INDEX_FORTIGATE}${NC}"
fi

# Validate HEC Token Format (UUID)
if [[ "${SPLUNK_HEC_TOKEN:-}" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    echo -e "${GREEN}  ✓ HEC token format is valid (UUID)${NC}"
else
    echo -e "${YELLOW}  ⚠ HEC token format is not UUID (may still work)${NC}"
fi

# Test Splunk HEC Health
if [ -n "${SPLUNK_HEC_HOST:-}" ]; then
    echo -e "${YELLOW}  → Testing Splunk HEC health...${NC}"
    HEC_PORT="${SPLUNK_HEC_PORT:-8088}"
    HEC_SCHEME="${SPLUNK_HEC_SCHEME:-https}"
    HEALTH=$(curl -k -s "${HEC_SCHEME}://${SPLUNK_HEC_HOST}:${HEC_PORT}/services/collector/health" 2>&1 || echo "FAILED")

    if echo "$HEALTH" | grep -q '"code":17'; then
        echo -e "${GREEN}  ✓ Splunk HEC is healthy${NC}"
    else
        echo -e "${RED}  ✗ Splunk HEC health check failed${NC}"
        echo -e "${YELLOW}    Response: ${HEALTH}${NC}"
    fi
fi

echo ""

# 3. Check Slack Configuration
echo -e "${BLUE}[3/4] Slack Configuration${NC}"
if [ "${SLACK_ENABLED:-false}" = "true" ]; then
    if [ -z "${SLACK_BOT_TOKEN:-}" ]; then
        echo -e "${RED}  ✗ SLACK_BOT_TOKEN is not set${NC}"
    else
        echo -e "${GREEN}  ✓ SLACK_BOT_TOKEN: ${SLACK_BOT_TOKEN:0:10}...${NC}"

        # Validate Slack token format
        if [[ "${SLACK_BOT_TOKEN}" =~ ^xoxb- ]]; then
            echo -e "${GREEN}  ✓ Slack Bot token format is valid${NC}"
        else
            echo -e "${RED}  ✗ Slack Bot token must start with 'xoxb-'${NC}"
        fi
    fi

    if [ -z "${SLACK_CHANNEL:-}" ]; then
        echo -e "${RED}  ✗ SLACK_CHANNEL is not set${NC}"
    else
        echo -e "${GREEN}  ✓ SLACK_CHANNEL: ${SLACK_CHANNEL}${NC}"
    fi

    # Test Slack API
    if [ -n "${SLACK_BOT_TOKEN:-}" ]; then
        echo -e "${YELLOW}  → Testing Slack API...${NC}"
        SLACK_TEST=$(curl -s -X POST https://slack.com/api/auth.test \
            -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" 2>&1 || echo "FAILED")

        if echo "$SLACK_TEST" | grep -q '"ok":true'; then
            echo -e "${GREEN}  ✓ Slack API authentication successful${NC}"
            TEAM=$(echo "$SLACK_TEST" | grep -o '"team":"[^"]*"' | cut -d'"' -f4)
            USER=$(echo "$SLACK_TEST" | grep -o '"user":"[^"]*"' | cut -d'"' -f4)
            echo -e "${GREEN}    Team: ${TEAM}, User: ${USER}${NC}"
        else
            echo -e "${RED}  ✗ Slack API authentication failed${NC}"
            echo -e "${YELLOW}    Response: ${SLACK_TEST}${NC}"
        fi
    fi
else
    echo -e "${YELLOW}  ⚠ Slack integration is disabled${NC}"
    echo -e "${YELLOW}    Set SLACK_ENABLED=true to enable${NC}"
fi

echo ""

# 4. Check Application Configuration
echo -e "${BLUE}[4/4] Application Configuration${NC}"
echo -e "${GREEN}  ✓ NODE_ENV: ${NODE_ENV:-production}${NC}"
echo -e "${GREEN}  ✓ TZ: ${TZ:-Asia/Seoul}${NC}"
echo -e "${GREEN}  ✓ LOG_LEVEL: ${LOG_LEVEL:-info}${NC}"
echo -e "${GREEN}  ✓ POLLING_INTERVAL: ${POLLING_INTERVAL:-60000}ms${NC}"
echo -e "${GREEN}  ✓ EVENT_BATCH_SIZE: ${EVENT_BATCH_SIZE:-100}${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Validation Complete${NC}"
echo -e "${BLUE}========================================${NC}"
