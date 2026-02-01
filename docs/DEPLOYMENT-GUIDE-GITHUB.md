# GitHub Deployment Guide (v2.0.5+)

## Overview

This guide documents new deployment features and configuration options introduced in v2.0.5. The Splunk Security App now supports:

- ✅ Automatic development deployments on `develop` branch commits
- ✅ Parameterized configuration for proxy and Slack integration
- ✅ Dynamic Git repository URL detection
- ✅ Improved CI/CD performance (30 seconds faster)

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Deployment Methods](#deployment-methods)
3. [Testing Develop Branch](#testing-develop-branch)
4. [Custom Configuration](#custom-configuration)
5. [Migration from GitLab](#migration-from-gitlab)
6. [Troubleshooting](#troubleshooting)

---

## Environment Variables

### PROXY_SERVER

Used by the production deployment script to route traffic through a corporate proxy.

| Property | Value |
|----------|-------|
| **Variable Name** | `PROXY_SERVER` |
| **Default** | `http://172.16.4.217:5001` |
| **Format** | `http://hostname:port` or `http://ip:port` |
| **Required** | No (uses default if not set) |
| **Scope** | Production deployment only |

**Example Usage:**
```bash
# Use default proxy
./infra/deploy/production/deploy.sh

# Use custom proxy
export PROXY_SERVER="http://proxy.company.com:3128"
./infra/deploy/production/deploy.sh

# Use direct IP
export PROXY_SERVER="http://10.0.0.1:8080"
./infra/deploy/production/deploy.sh

# Unset to use default
unset PROXY_SERVER
./infra/deploy/production/deploy.sh
```

### SLACK_CHANNEL

Target Slack channel for deployment notifications and status updates.

| Property | Value |
|----------|-------|
| **Variable Name** | `SLACK_CHANNEL` |
| **Default** | `일반` (Korean: "General") |
| **Format** | Channel name or ID |
| **Required** | No (uses default if not set) |
| **Scope** | Production deployment notifications |

**Example Usage:**
```bash
# Use default channel (General)
./infra/deploy/production/deploy.sh

# Use custom channel
export SLACK_CHANNEL="deployment-alerts"
./infra/deploy/production/deploy.sh

# Use production channel
export SLACK_CHANNEL="prod-ops"
./infra/deploy/production/deploy.sh

# Multiple channels (space-separated, in shell)
export SLACK_CHANNEL="prod-ops security-alerts"
./infra/deploy/production/deploy.sh
```

---

## Deployment Methods

### Method 1: Develop Branch (Automatic)

**When to use**: Development, testing, and staging deployments

**How it works**:
1. Commit code to `develop` branch
2. Push to GitHub: `git push origin develop`
3. GitHub Actions automatically triggers `deploy-dev` workflow
4. Deployment completes automatically (5-10 minutes)

**Process**:
```bash
# 1. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# 2. Make changes and commit
echo "my changes" > file.txt
git add file.txt
git commit -m "feat: add new feature"

# 3. Push to develop branch (after merge or direct push)
git checkout develop
git merge feature/my-feature
git push origin develop

# 4. Monitor deployment
# Go to: https://github.com/jclee-homelab/splunk/actions
# Look for: deploy-dev workflow
# Wait for: ✅ Success status
```

**Verification**:
```bash
# Check that develop branch exists
git branch -a | grep develop

# See recent commits on develop
git log origin/develop --oneline -5

# Monitor GitHub Actions
open https://github.com/jclee-homelab/splunk/actions
```

### Method 2: Production Deployment (Manual)

**When to use**: Production environment updates, critical patches

**How it works**:
1. Run deployment script locally
2. Script validates environment and conditions
3. Deployment executes with custom configuration
4. Slack notification sent to configured channel

**Process**:
```bash
# 1. Navigate to repository
cd /home/jclee/dev/splunk

# 2. Ensure you're on master or main branch
git checkout master
git pull origin master

# 3. Configure environment (optional)
export PROXY_SERVER="http://custom-proxy:5001"
export SLACK_CHANNEL="prod-alerts"

# 4. Run deployment
./infra/deploy/production/deploy.sh

# 5. Monitor output for status and any errors
# Script will show:
#   - Configuration being used
#   - Deployment steps
#   - Status messages
#   - Slack notification confirmation
```

**Verification**:
```bash
# Check production deployment script exists
ls -la ./infra/deploy/production/deploy.sh

# View script to see what it will do
cat ./infra/deploy/production/deploy.sh | head -30

# Check log if available
tail -f ./infra/deploy/production/deploy.log
```

### Method 3: Airgap Sync (Isolated Networks)

**When to use**: Synchronizing to airgapped environments without external internet

**How it works**:
1. Script detects local Git repository URL
2. Syncs code to airgapped environment
3. No hardcoded URLs required (automatically detected)

**Process**:
```bash
# 1. Navigate to repository
cd /home/jclee/dev/splunk

# 2. Verify Git remote
git remote get-url origin
# Should output: https://github.com/jclee-homelab/splunk.git

# 3. Run airgap sync (auto-detects repository)
./tools/scripts/deploy/auto-sync-airgap.sh

# 4. Script will sync to airgapped environment
# Output will show:
#   - Detected repository URL
#   - Sync progress
#   - Completion status
```

**Verification**:
```bash
# Check airgap script exists
ls -la ./tools/scripts/deploy/auto-sync-airgap.sh

# View current Git remote configuration
git remote -v

# Test airgap sync in dry-run mode (if supported)
./tools/scripts/deploy/auto-sync-airgap.sh --dry-run
```

---

## Testing Develop Branch

### Step 1: Create Test Branch

```bash
# Switch to develop
git checkout develop
git pull origin develop

# Create test branch
git checkout -b test/verify-deploy

# Make a test change
echo "test content $(date)" > test-file.txt
git add test-file.txt
git commit -m "test: verify develop deployment"
```

### Step 2: Push to Develop (Trigger Deployment)

```bash
# Switch back to develop
git checkout develop

# Merge test branch
git merge test/verify-deploy

# Push to GitHub (this triggers the workflow)
git push origin develop
```

### Step 3: Monitor GitHub Actions

```bash
# Open GitHub Actions page
open https://github.com/jclee-homelab/splunk/actions

# Or check from command line
git log origin/develop -1 --pretty=format:"%h - %s"

# Wait for workflow to complete (check status badge)
```

### Step 4: Verify Deployment

```bash
# Check if deployment completed successfully
# Method 1: GitHub UI
# - Navigate to: https://github.com/jclee-homelab/splunk/actions
# - Look for: deploy-dev workflow
# - Status should be: ✅ Success

# Method 2: Check Slack notification
# - Look in your Slack channel for deployment notification
# - Should show: "Deploy Successful" or similar

# Method 3: Check actual deployment
# - Log into your development environment
# - Verify new version is deployed
```

### Step 5: Cleanup Test Branch

```bash
# Delete local test branch
git branch -d test/verify-deploy

# Delete remote test branch (if pushed)
git push origin --delete test/verify-deploy
```

---

## Custom Configuration

### Example 1: Custom Proxy Only

```bash
# Set custom proxy for corporate environment
export PROXY_SERVER="http://172.16.1.100:3128"

# Run deployment with custom proxy
./infra/deploy/production/deploy.sh

# Slack notification goes to default channel
```

### Example 2: Custom Slack Channel Only

```bash
# Set custom channel for notifications
export SLACK_CHANNEL="ops-team"

# Run deployment with default proxy and custom channel
./infra/deploy/production/deploy.sh

# Deployment notifications sent to ops-team channel
```

### Example 3: Both Custom

```bash
# Configure both proxy and Slack channel
export PROXY_SERVER="http://proxy.company.com:8080"
export SLACK_CHANNEL="security-alerts"

# Run deployment with all custom settings
./infra/deploy/production/deploy.sh
```

### Example 4: Reset to Defaults

```bash
# Clear environment variables to use defaults
unset PROXY_SERVER
unset SLACK_CHANNEL

# Verify variables are cleared
echo "PROXY_SERVER: $PROXY_SERVER"      # Should be empty
echo "SLACK_CHANNEL: $SLACK_CHANNEL"    # Should be empty

# Run deployment with defaults
./infra/deploy/production/deploy.sh
```

### Example 5: Persistent Configuration

**For repeated deployments, add to your shell profile:**

```bash
# Add to ~/.bashrc or ~/.zshrc
export PROXY_SERVER="http://proxy.company.com:3128"
export SLACK_CHANNEL="deployment-alerts"

# Then all future deployments use these settings
# without re-exporting each time
```

---

## Git URL Auto-Detection

The airgap sync script now automatically detects your Git repository URL using:

```bash
git remote get-url origin
```

**Before (v2.0.4)**:
```bash
GITLAB_URL="https://gitlab.example.com"  # Hardcoded
```

**After (v2.0.5)**:
```bash
REMOTE_URL=$(git remote get-url origin)  # Auto-detected
# Works with: GitHub, GitLab, Gitea, or any Git provider
```

**Benefits**:
- ✅ No script editing needed for different repositories
- ✅ Works with any Git provider (GitHub, GitLab, Gitea, etc.)
- ✅ Automatic URL detection
- ✅ More maintainable codebase

**Verification**:
```bash
# Check current Git remote
git remote get-url origin

# Should show something like:
# https://github.com/jclee-homelab/splunk.git

# The script will use this URL automatically
./tools/scripts/deploy/auto-sync-airgap.sh
```

---

## Migration from GitLab

### What Changed

All hardcoded GitLab references have been removed and replaced with:
- ✅ Environment variables (configuration)
- ✅ Dynamic URL detection (Git remote)
- ✅ GitHub-compatible workflows

### What You Need to Do

**Nothing!** The migration is automatic.

**However, verify**:
```bash
# 1. Confirm using GitHub repository
git remote get-url origin
# Should show: https://github.com/jclee-homelab/splunk.git

# 2. Verify workflow file points to GitHub
cat .github/workflows/deploy.yml | grep -i github
# Should show GitHub Actions references

# 3. Check wiki submodule is updated
git config -f .gitmodules --get submodule.splunk.wiki.url
# Should show GitHub URL

# 4. Verify no GitLab references remain
grep -r "gitlab" . --include="*.sh" --include="*.yml" --include="*.yaml" --include="*.md"
# Should return no results
```

### Configuration Changes

If you were using GitLab-specific settings, update to use environment variables:

**Old (GitLab)**:
```bash
# Edit script to change URL
vi tools/scripts/deploy/auto-sync-airgap.sh
# Change: GITLAB_URL="https://gitlab.example.com"
```

**New (GitHub)**:
```bash
# No script editing needed
# Just run script (auto-detects from git remote)
./tools/scripts/deploy/auto-sync-airgap.sh

# Or use environment variables for custom settings
export PROXY_SERVER="http://custom:port"
export SLACK_CHANNEL="custom-channel"
```

---

## Troubleshooting

### Issue: Develop Branch Not Triggering Deployment

**Symptoms**:
- Commit pushed to develop branch
- GitHub Actions workflow not running
- No deploy-dev job in actions list

**Diagnosis**:
```bash
# 1. Verify branch name is exactly "develop"
git branch -a | grep develop

# 2. Check GitHub Actions is enabled
# Go to: Settings > Actions > General
# Should have: "Allow GitHub Actions to create and approve pull requests" enabled

# 3. Verify workflow file exists
ls -la .github/workflows/deploy.yml

# 4. Check workflow file has develop trigger
grep -A 5 "on:" .github/workflows/deploy.yml | grep develop
```

**Solution**:
```bash
# 1. Verify branch name
git branch -r  # Should show: origin/develop

# 2. If branch doesn't exist, create it
git checkout -b develop
git push origin develop

# 3. Enable GitHub Actions (if disabled)
# Go to: GitHub repo > Settings > Actions > Enable Actions

# 4. Push a test commit
echo "test" > test.txt
git add test.txt
git commit -m "test: trigger workflow"
git push origin develop

# 5. Monitor actions
open https://github.com/jclee-homelab/splunk/actions
```

### Issue: Custom Proxy Not Being Used

**Symptoms**:
- Set PROXY_SERVER environment variable
- Deployment still uses default proxy
- Script shows default proxy in output

**Diagnosis**:
```bash
# 1. Verify environment variable is set
echo $PROXY_SERVER
# Should show your custom proxy

# 2. Check variable is set before running script
echo "PROXY_SERVER=$PROXY_SERVER"

# 3. Verify script is reading the variable
grep "PROXY_SERVER" ./infra/deploy/production/deploy.sh
```

**Solution**:
```bash
# 1. Set variable with correct format
export PROXY_SERVER="http://hostname:port"
# Format: http://[hostname or IP]:[port]

# 2. Verify it's set
echo $PROXY_SERVER

# 3. Run script in same shell
./infra/deploy/production/deploy.sh

# 4. Check script output for configured proxy
# Output should show: PROXY_SERVER=http://hostname:port
```

### Issue: Slack Notification Goes to Wrong Channel

**Symptoms**:
- Set SLACK_CHANNEL environment variable
- Notification appears in different channel
- Default channel receives message instead

**Diagnosis**:
```bash
# 1. Verify environment variable is set
echo $SLACK_CHANNEL
# Should show: your-channel-name

# 2. Check if channel exists in Slack
# Go to: Slack workspace > Channels
# Look for your channel

# 3. Verify bot has access to channel
# In Slack: Channel > Details > Members
# Look for: Deployment Bot or similar
```

**Solution**:
```bash
# 1. Set channel variable with correct name
export SLACK_CHANNEL="channel-name"
# Note: Use channel name, not #channel

# 2. Verify channel exists in Slack workspace
# Go to Slack and check channel is available

# 3. Verify bot has been added to channel
# Go to Slack > Channel > Add bot/app

# 4. Run deployment with correct channel
./infra/deploy/production/deploy.sh

# 5. Check deployment output for channel name
# Output should show: SLACK_CHANNEL=channel-name
```

### Issue: Git Remote URL Not Detected

**Symptoms**:
- Airgap sync fails
- Error: "Could not detect Git remote"
- Script output shows empty URL

**Diagnosis**:
```bash
# 1. Check if in a Git repository
git status
# Should show: On branch master/develop

# 2. Verify Git remote is configured
git remote -v
# Should show: origin https://github.com/...

# 3. Check remote name is "origin"
git remote
# Should show: origin
```

**Solution**:
```bash
# 1. Ensure you're in Git repository
cd /home/jclee/dev/splunk
git status  # Should work

# 2. Check Git remote exists
git remote get-url origin
# Should show: https://github.com/jclee-homelab/splunk.git

# 3. If remote is missing, add it
git remote add origin https://github.com/jclee-homelab/splunk.git

# 4. Run airgap script
./tools/scripts/deploy/auto-sync-airgap.sh

# 5. Verify URL was detected
# Output should show: Detected repository: https://github.com/...
```

### Issue: Permission Denied When Running Scripts

**Symptoms**:
- Error: "Permission denied"
- Script: ./infra/deploy/production/deploy.sh
- Error: bash: ./tools/scripts/deploy/auto-sync-airgap.sh: Permission denied

**Diagnosis**:
```bash
# Check file permissions
ls -la ./infra/deploy/production/deploy.sh
# Should show: -rwxr-xr-x (executable)
```

**Solution**:
```bash
# Make script executable
chmod +x ./infra/deploy/production/deploy.sh
chmod +x ./tools/scripts/deploy/auto-sync-airgap.sh

# Or run with bash explicitly
bash ./infra/deploy/production/deploy.sh
bash ./tools/scripts/deploy/auto-sync-airgap.sh

# Verify permissions are set
ls -la ./infra/deploy/production/deploy.sh
# Should show: rwx (owner can execute)
```

---

## FAQ

**Q: Can I use both proxy and Slack channel settings?**
A: Yes! Set both environment variables before running the script.
```bash
export PROXY_SERVER="http://proxy:port"
export SLACK_CHANNEL="channel-name"
./infra/deploy/production/deploy.sh
```

**Q: What if I don't set environment variables?**
A: The script uses sensible defaults.
```bash
PROXY_SERVER="http://172.16.4.217:5001"
SLACK_CHANNEL="일반"
```

**Q: How do I check which settings are being used?**
A: The script outputs configuration at startup.
```bash
./infra/deploy/production/deploy.sh
# First output line shows: Configuration: PROXY_SERVER=... SLACK_CHANNEL=...
```

**Q: Can I override settings without editing script?**
A: Yes, use environment variables (as shown above).

**Q: How often should I deploy?**
A: 
- **Develop branch**: After each feature merge (~daily)
- **Production**: As needed for patches/releases (~weekly or on-demand)

**Q: What if deployment fails?**
A: Check the Slack notification for error details, then see Troubleshooting section.

---

## Performance Notes

### Improvements in v2.0.5

- **Pipeline Speed**: ~30 seconds faster (Python 3.9 setup removed)
- **Develop Trigger**: Immediate (no longer requires manual action)
- **Configuration Override**: No script editing needed
- **URL Detection**: Automatic (no hardcoding required)

### Before vs After

| Task | Before (v2.0.4) | After (v2.0.5) | Improvement |
|------|-----------------|----------------|-------------|
| Workflow execution | 2:15 | 1:45 | -30 seconds |
| Develop trigger | Manual | Automatic | Immediate |
| Config change | Edit script | Environment var | Faster |
| URL change | Edit script | Auto-detect | Automated |

---

## Additional Resources

- **CHANGELOG**: See `CHANGELOG.md` for detailed fix descriptions
- **Deployment Checklist**: See `docs/deployment-checklist.md` for step-by-step procedures
- **GitHub Actions**: https://github.com/jclee-homelab/splunk/actions
- **Repository**: https://github.com/jclee-homelab/splunk

---

**Last Updated**: 2025-02-01  
**Version**: 2.0.5+  
**Status**: Current
