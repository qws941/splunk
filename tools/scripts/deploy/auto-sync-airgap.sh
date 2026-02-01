#!/bin/bash
################################################################################
# Auto Sync Airgap - Always keep airgap branch in sync
# Purpose: Automatically sync airgap after build/deploy
# Usage: Called automatically by splunk-cli or manually
################################################################################

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in the right directory
if [[ ! -f "default/app.conf" ]]; then
    echo -e "${RED}✗ Must run from project root${NC}"
    exit 1
fi

# Get version
VERSION=$(grep -E "^version\s*=" default/app.conf | sed 's/.*=\s*//' | tr -d ' ')

# Find latest tarball
TARBALL_NAME=$(ls -t releases/security-*.tar.gz 2>/dev/null | head -1)
if [[ -z "$TARBALL_NAME" ]]; then
    echo -e "${YELLOW}⚠ No tarball found - building first...${NC}"
    ./releases/bin/splunk-cli build
    TARBALL_NAME=$(ls -t releases/security-*.tar.gz 2>/dev/null | head -1)
    if [[ -z "$TARBALL_NAME" ]]; then
        echo -e "${RED}✗ Build failed${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}🔄 Auto-syncing airgap branch (v${VERSION})...${NC}"

# Create temp directory
AIRGAP_DIR="/tmp/airgap-sync-$$"
trap "rm -rf $AIRGAP_DIR" EXIT

# Determine Remote URL (CI compatible)
if [[ -n "$CI_JOB_TOKEN" ]]; then
    # In CI, use the token-embedded URL if origin is not set correctly
    REMOTE_URL=$(git remote get-url origin)
else
    # Local dev
    REMOTE_URL=$(git remote get-url origin)
fi
echo -e "${BLUE}Remote:${NC} ${REMOTE_URL}"

# Clone airgap branch
echo -e "${YELLOW}Cloning airgap branch...${NC}"
if git ls-remote --exit-code --heads "$REMOTE_URL" airgap >/dev/null; then
    git clone --depth 1 -b airgap "$REMOTE_URL" "$AIRGAP_DIR"
else
    echo -e "${YELLOW}Airgap branch not found remote, creating new...${NC}"
    git clone --depth 1 "$REMOTE_URL" "$AIRGAP_DIR"
    cd "$AIRGAP_DIR"
    git checkout --orphan airgap
    git rm -rf .
    cd - > /dev/null
fi

cd "$AIRGAP_DIR"

# Clean and copy files
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
mkdir -p releases docs

TARBALL_PATH="$(cd .. && pwd)/${TARBALL_NAME}"
cp "$TARBALL_PATH" releases/security.tar.gz
cp -r ../docs/* docs/ 2>/dev/null || true
cp ../README.md . 2>/dev/null || true

# Create deployment README
cat > AIRGAP-DEPLOY.md << EOF
# Air-Gapped Deployment - Version ${VERSION}

## Quick Deploy

\`\`\`bash
# 1. Download tarball
git clone -b airgap https://gitlab.jclee.me/nextrade/splunk.git
cd splunk/releases

# 2. Deploy to Splunk
tar -xzf security.tar.gz -C /opt/splunk/etc/apps/
chown -R secmon:secmon /opt/splunk/etc/apps/security

# 3. Reload (no restart needed)
curl -k -u secmon:password -X POST https://localhost:8089/services/apps/local/security/_reload
\`\`\`

## Version Info
- Version: ${VERSION}
- Built: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- Branch: airgap (auto-synced)

## Files
- \`releases/security.tar.gz\` - App package (ready to deploy)
- \`docs/\` - Documentation
- \`README.md\` - General info
EOF

# Commit and push
git add -A
if git diff --cached --quiet; then
    echo -e "${YELLOW}⚠ No changes (already up-to-date)${NC}"
    exit 0
fi

git config user.email "auto-sync@jclee.me"
git config user.name "Auto Sync"
git commit -m "chore(airgap): Auto-sync v${VERSION} [$(date +%Y-%m-%d)]"

# Push
echo -e "${YELLOW}Pushing to origin/airgap...${NC}"
if git push origin airgap; then
    echo -e "${GREEN}✅ Airgap branch synced successfully!${NC}"
    echo -e "${BLUE}📦 Version: ${VERSION}${NC}"
    echo -e "${BLUE}🔗 Download: git clone -b airgap https://gitlab.jclee.me/nextrade/splunk.git${NC}"
else
    echo -e "${RED}✗ Push failed (check credentials or network)${NC}"
    exit 1
fi
