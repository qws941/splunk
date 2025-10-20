#!/bin/bash
# Splunk Dashboard Deployment Helper Script
#
# This script helps deploy dashboards to Splunk automatically

set -e

echo "🚀 Splunk Dashboard Deployment"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found"
    echo ""
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created"
    echo ""
    echo "⚠️  Please configure Splunk credentials in .env:"
    echo "   SPLUNK_HOST=splunk.jclee.me"
    echo "   SPLUNK_PORT=8089"
    echo "   SPLUNK_USERNAME=admin"
    echo "   SPLUNK_PASSWORD=your_password"
    echo ""
    exit 1
fi

# Source .env
export $(grep -v '^#' .env | xargs)

# Check for Splunk password
if [ -z "$SPLUNK_PASSWORD" ]; then
    echo "❌ SPLUNK_PASSWORD not configured in .env"
    echo ""
    echo "📝 Please add to .env:"
    echo "   SPLUNK_PASSWORD=your_admin_password"
    echo ""
    echo "💡 Or use manual upload method (see README_DASHBOARDS.md)"
    exit 1
fi

echo "✅ Environment variables loaded"
echo "📡 Target: ${SPLUNK_HOST:-splunk.jclee.me}"
echo "👤 User: ${SPLUNK_USERNAME:-admin}"
echo ""

# Export dashboards
echo "📊 Step 1: Exporting dashboards to XML..."
node scripts/export-dashboards.js

if [ $? -ne 0 ]; then
    echo "❌ Dashboard export failed"
    exit 1
fi

echo ""
echo "🚀 Step 2: Deploying to Splunk..."
node scripts/deploy-dashboards.js

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "🌐 Access dashboards at:"
    echo "   https://${SPLUNK_HOST:-splunk.jclee.me}/app/search/dashboards"
    echo ""
else
    echo ""
    echo "⚠️  Deployment failed"
    echo ""
    echo "💡 Alternative: Manual Upload"
    echo "   1. Open Splunk Web UI: https://${SPLUNK_HOST:-splunk.jclee.me}"
    echo "   2. Go to: Settings → Dashboards → Create New Dashboard"
    echo "   3. Upload XML files from: dashboards/"
    echo ""
    echo "📖 See README_DASHBOARDS.md for detailed instructions"
    exit 1
fi
