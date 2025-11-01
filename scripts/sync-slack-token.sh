#!/bin/bash
# Slack Token Synchronization Script
# Automatically sync token from alert_actions.conf to .env
# Usage: bash scripts/sync-slack-token.sh

set -e

ALERT_ACTIONS="configs/alert_actions.conf"
ENV_FILE=".env"

echo "🔄 Syncing Slack token from alert_actions.conf to .env..."

# Extract token from alert_actions.conf
TOKEN=$(grep "^param.token" "$ALERT_ACTIONS" | sed 's/param.token = //' | sed 's/ *#.*//' | xargs)

if [ -z "$TOKEN" ]; then
    echo "❌ No token found in $ALERT_ACTIONS"
    exit 1
fi

if [ "$TOKEN" = "xoxb-your-slack-bot-token" ]; then
    echo "⚠️  Token is still placeholder!"
    echo "   Edit $ALERT_ACTIONS line 17 first"
    exit 1
fi

# Update .env file
if [ -f "$ENV_FILE" ]; then
    # Replace existing SLACK_BOT_TOKEN line
    if grep -q "^SLACK_BOT_TOKEN=" "$ENV_FILE"; then
        sed -i "s|^SLACK_BOT_TOKEN=.*|SLACK_BOT_TOKEN=$TOKEN|" "$ENV_FILE"
        echo "✅ Updated SLACK_BOT_TOKEN in $ENV_FILE"
    else
        # Add if not exists
        echo "SLACK_BOT_TOKEN=$TOKEN" >> "$ENV_FILE"
        echo "✅ Added SLACK_BOT_TOKEN to $ENV_FILE"
    fi
else
    echo "❌ $ENV_FILE not found"
    exit 1
fi

echo ""
echo "📋 Current configuration:"
echo "   alert_actions.conf: $TOKEN"
echo "   .env: $(grep "^SLACK_BOT_TOKEN=" "$ENV_FILE" | cut -d= -f2)"
echo ""
echo "✅ Sync complete! Both files now use the same token."
echo ""
echo "💡 Usage:"
echo "   1. Edit configs/alert_actions.conf line 17"
echo "   2. Run: bash scripts/sync-slack-token.sh"
echo "   3. Both files automatically updated!"
