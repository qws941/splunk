#!/bin/bash
# Wiki Synchronization Script
# Syncs splunk.wiki/ repo to GitHub Wiki
# Usage: Called by GitHub Actions CI/CD pipeline

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
WIKI_DIR="${PROJECT_ROOT}/splunk.wiki"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔄 Synchronizing Wiki...${NC}"

# Check wiki directory exists
if [[ ! -d "$WIKI_DIR" ]]; then
    echo -e "${RED}✗ Wiki directory not found: $WIKI_DIR${NC}"
    echo "  Skipping wiki sync (not required)"
    exit 0
fi

# Change to wiki directory
cd "$WIKI_DIR"

# Check git status
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}✗ Not a git repository: $WIKI_DIR${NC}"
    echo "  Skipping wiki sync (not a repo)"
    exit 0
fi

# Configure git if needed (for CI/CD environments)
if [[ -z "$(git config --local user.email)" ]]; then
    git config --local user.email "ci-bot@jclee.me" || true
    git config --local user.name "CI Bot" || true
fi

# Pull latest changes
echo -e "${YELLOW}Pulling latest changes...${NC}"
if git fetch origin 2>/dev/null; then
    git pull origin master 2>/dev/null || echo -e "${YELLOW}⚠ Pull had conflicts (manual sync needed)${NC}"
else
    echo -e "${YELLOW}⚠ Network issue - skipping pull${NC}"
fi

# Check for changes
if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
    echo -e "${YELLOW}📝 Committing changes...${NC}"
    git add -A
    git commit -m "chore(wiki): auto-sync from CI [$(date +%Y-%m-%d\ %H:%M:%S)]" || true

    # Try to push
    echo -e "${YELLOW}🚀 Pushing to origin/master...${NC}"
    if git push origin master 2>/dev/null; then
        echo -e "${GREEN}✅ Wiki pushed successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Push failed (network or auth issue)${NC}"
        echo "  Wiki sync will retry on next CI run"
    fi
else
    echo -e "${YELLOW}ℹ No changes to sync${NC}"
fi

echo -e "${GREEN}✅ Wiki sync complete${NC}"
