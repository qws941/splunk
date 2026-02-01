#!/bin/bash
#
# sync-wiki.sh - Sync documentation to GitHub Wiki
#
# Usage: ./sync-wiki.sh
#
# Environment variables:
#   GITHUB_TOKEN - GitHub token for authentication (required)
#   WIKI_SOURCE  - Source directory (default: docs/wiki or splunk.wiki)
#
# GitHub Wiki notes:
#   - Wiki repo: https://github.com/{owner}/{repo}.wiki.git
#   - home.md -> Home.md (GitHub Wiki convention)
#   - _sidebar.md -> _Sidebar.md
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
REPO_URL="${GITHUB_REPOSITORY:-jclee-homelab/splunk}"
WIKI_REPO="https://github.com/${REPO_URL}.wiki.git"

# Determine wiki source directory
if [[ -d "docs/wiki" ]]; then
    WIKI_SOURCE="${WIKI_SOURCE:-docs/wiki}"
elif [[ -d "splunk.wiki" ]]; then
    WIKI_SOURCE="${WIKI_SOURCE:-splunk.wiki}"
else
    log_error "No wiki source directory found (docs/wiki or splunk.wiki)"
    exit 1
fi

log_info "Wiki source: ${WIKI_SOURCE}"
log_info "Wiki repo: ${WIKI_REPO}"

# Check GITHUB_TOKEN
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    log_error "GITHUB_TOKEN is not set"
    exit 1
fi

# Create temporary directory for wiki clone
WIKI_TMP=$(mktemp -d)
trap "rm -rf ${WIKI_TMP}" EXIT

# Configure git for push
git config --global user.email "github-actions[bot]@users.noreply.github.com"
git config --global user.name "github-actions[bot]"

# Clone or initialize wiki repository
log_info "Cloning wiki repository..."
WIKI_AUTH_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${REPO_URL}.wiki.git"

if git clone "${WIKI_AUTH_URL}" "${WIKI_TMP}" 2>/dev/null; then
    log_info "Wiki repository cloned successfully"
else
    log_warn "Wiki repo not found, initializing new wiki..."
    cd "${WIKI_TMP}"
    git init
    git remote add origin "${WIKI_AUTH_URL}"
    echo "# Welcome to the Wiki" > Home.md
    git add Home.md
    git commit -m "Initial wiki commit"
fi

cd "${WIKI_TMP}"

# Remove old wiki files (except .git)
find . -maxdepth 1 -type f -name "*.md" -delete

# Copy wiki files from source
log_info "Copying wiki files from ${WIKI_SOURCE}..."
cd - > /dev/null

# Copy all markdown files
for file in "${WIKI_SOURCE}"/*.md; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        
        # GitHub Wiki naming conventions
        case "$filename" in
            home.md)
                dest_name="Home.md"
                ;;
            _sidebar.md)
                dest_name="_Sidebar.md"
                ;;
            _footer.md)
                dest_name="_Footer.md"
                ;;
            *)
                # Keep original name but ensure first letter is capitalized for consistency
                dest_name="$filename"
                ;;
        esac
        
        cp "$file" "${WIKI_TMP}/${dest_name}"
        log_info "  Copied: $filename -> $dest_name"
    fi
done

# Copy subdirectories (e.g., docs/, images/)
for dir in "${WIKI_SOURCE}"/*/; do
    if [[ -d "$dir" ]]; then
        dirname=$(basename "$dir")
        cp -r "$dir" "${WIKI_TMP}/${dirname}"
        log_info "  Copied directory: $dirname/"
    fi
done

# Commit and push changes
cd "${WIKI_TMP}"

# Check if there are changes
if git diff --quiet && git diff --staged --quiet; then
    # Check for new files
    if [[ -z "$(git status --porcelain)" ]]; then
        log_info "No changes to commit"
        exit 0
    fi
fi

git add -A

# Create commit message with file count
FILE_COUNT=$(git diff --cached --name-only | wc -l)
COMMIT_MSG="docs: sync wiki documentation (${FILE_COUNT} files)"

git commit -m "${COMMIT_MSG}" || {
    log_info "No changes to commit"
    exit 0
}

log_info "Pushing to wiki repository..."
git push origin HEAD:master || git push origin HEAD:main

log_info "Wiki sync completed successfully!"

# Summary
echo ""
echo "=== Wiki Sync Summary ==="
echo "Source: ${WIKI_SOURCE}"
echo "Files synced: ${FILE_COUNT}"
echo "Wiki URL: https://github.com/${REPO_URL}/wiki"
