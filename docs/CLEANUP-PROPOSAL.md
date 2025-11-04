# File Cleanup and Modularization Proposal

**Generated**: 2025-11-04
**Purpose**: Eliminate legacy files, consolidate duplicates, optimize directory structure
**Estimated Space Savings**: ~4.8MB (242 legacy files)

---

## 📊 Current State Analysis

### Directory Breakdown

| Category | Directory | Files | Status | Action |
|----------|-----------|-------|--------|--------|
| ✅ ACTIVE | `security_alert/` | 42 | Production (v2.0.4) | **KEEP** |
| 📚 REFERENCE | `configs/` | 4 | Config examples | **KEEP** |
| 📚 REFERENCE | `lookups/` | 8 | CSV templates | **REVIEW** |
| ❌ LEGACY | `nextrade/` | 30 | v2.0.3 deprecated | **DELETE** |
| ❌ LEGACY | `archive-dev/` | 212 | Development archive | **DELETE** |
| ❌ LEGACY | `xwiki/` | 0 | Old documentation | **DELETE** |

### File Type Distribution

| Type | Total | Active | Legacy | Action |
|------|-------|--------|--------|--------|
| Markdown (.md) | 110 | 14 | 96 | Delete 96 legacy |
| Python (.py) | 8 | 5 | 3 | Delete 3 duplicates |
| Config (.conf) | 24 | 6 | 18 | Delete 18 legacy |
| CSV (.csv) | 44 | 17 | 27 | Consolidate duplicates |

---

## 🎯 Cleanup Strategy

### Phase 1: Safe Backup (MANDATORY)

**Before any deletion**:
```bash
# Create timestamped backup
cd /home/jclee/app/splunk
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p ~/backups/splunk_cleanup_${BACKUP_DATE}

# Backup legacy directories
tar -czf ~/backups/splunk_cleanup_${BACKUP_DATE}/nextrade_backup.tar.gz nextrade/
tar -czf ~/backups/splunk_cleanup_${BACKUP_DATE}/archive-dev_backup.tar.gz archive-dev/
tar -czf ~/backups/splunk_cleanup_${BACKUP_DATE}/xwiki_backup.tar.gz xwiki/ 2>/dev/null || true

# Verify backup
ls -lh ~/backups/splunk_cleanup_${BACKUP_DATE}/
```

### Phase 2: Delete Legacy Directories

**nextrade/ (v2.0.3 - 30 files)**:
- Purpose: Previous version before v2.0.4 refactor
- Reason for deletion: Superseded by `security_alert/` production code
- Files to delete:
  ```
  nextrade/bin/*.py (5 Python scripts)
  nextrade/default/*.conf (6 config files)
  nextrade/lookups/*.csv (17 CSV files)
  nextrade/metadata/default.meta
  nextrade/README.md
  ```

**archive-dev/ (212 files)**:
- Purpose: Development archive from iterative development
- Reason for deletion: No production value, clutters repository
- Files to delete:
  ```
  archive-dev/docs/*.md (96 markdown files)
  archive-dev/scripts/*.sh (multiple shell scripts)
  archive-dev/configs/*.conf (legacy configurations)
  archive-dev/test-data/*.json (test data)
  ```

**xwiki/ (0 files)**:
- Purpose: Empty directory for old documentation
- Reason for deletion: No content, obsolete structure

**Deletion Script**:
```bash
#!/bin/bash
# File: scripts/cleanup-legacy-dirs.sh

set -e  # Exit on error

BACKUP_VERIFIED=false
BACKUP_DIR=$(ls -td ~/backups/splunk_cleanup_* 2>/dev/null | head -1)

# Verify backup exists
if [ -f "$BACKUP_DIR/nextrade_backup.tar.gz" ] && \
   [ -f "$BACKUP_DIR/archive-dev_backup.tar.gz" ]; then
    echo "✅ Backup verified: $BACKUP_DIR"
    BACKUP_VERIFIED=true
else
    echo "❌ ERROR: Backup not found. Run Phase 1 first."
    exit 1
fi

# Delete legacy directories
if [ "$BACKUP_VERIFIED" = true ]; then
    cd /home/jclee/app/splunk

    echo "Deleting nextrade/ (30 files)..."
    rm -rf nextrade/

    echo "Deleting archive-dev/ (212 files)..."
    rm -rf archive-dev/

    echo "Deleting xwiki/ (empty)..."
    rmdir xwiki/ 2>/dev/null || true

    echo "✅ Legacy directories deleted"
    echo "Backup location: $BACKUP_DIR"
fi
```

### Phase 3: Consolidate Duplicate Files

**Duplicate Python Scripts** (Keep only `security_alert/bin/` versions):

| File | Locations | Action |
|------|-----------|--------|
| `fortigate_auto_response.py` | 3 copies | Delete from nextrade/bin/, archive-dev/scripts/ |
| `auto_validator.py` | 2 copies | Delete from archive-dev/scripts/ |
| `deployment_health_check.py` | 2 copies | Delete from archive-dev/scripts/ |

**Duplicate CSV Files** (Consolidate to `security_alert/lookups/`):

| CSV File | Locations | Size | Action |
|----------|-----------|------|--------|
| `fortigate_logid_notification_map.csv` | 3 copies | 6KB each | Keep security_alert/, delete lookups/, nextrade/ |
| `abuseipdb_lookup.csv` | 2 copies | 2KB each | Keep security_alert/, delete lookups/ |
| `auto_response_actions.csv` | 3 copies | 1KB each | Keep security_alert/, delete lookups/, nextrade/ |
| `severity_priority.csv` | 2 copies | 1KB each | Keep security_alert/, delete lookups/ |

**Consolidation Script**:
```bash
#!/bin/bash
# File: scripts/consolidate-duplicates.sh

set -e

cd /home/jclee/app/splunk

# Compare files before deletion (sanity check)
echo "Comparing duplicate CSV files..."

compare_files() {
    local file1=$1
    local file2=$2
    if [ -f "$file1" ] && [ -f "$file2" ]; then
        if diff -q "$file1" "$file2" > /dev/null; then
            echo "✅ $file1 == $file2 (safe to delete duplicate)"
        else
            echo "⚠️  $file1 != $file2 (REVIEW BEFORE DELETE)"
        fi
    fi
}

# Compare CSVs
compare_files "security_alert/lookups/fortigate_logid_notification_map.csv" "lookups/fortigate_logid_notification_map.csv"
compare_files "security_alert/lookups/abuseipdb_lookup.csv" "lookups/abuseipdb_lookup.csv"
compare_files "security_alert/lookups/auto_response_actions.csv" "lookups/auto_response_actions.csv"
compare_files "security_alert/lookups/severity_priority.csv" "lookups/severity_priority.csv"

# Delete duplicates from lookups/ (root level)
echo -e "\nDeleting duplicate CSVs from lookups/..."
rm -f lookups/fortigate_logid_notification_map.csv
rm -f lookups/abuseipdb_lookup.csv
rm -f lookups/auto_response_actions.csv
rm -f lookups/severity_priority.csv

echo "✅ Duplicate CSVs consolidated to security_alert/lookups/"
```

### Phase 4: Review configs/ Directory

**Current Status**: 4 config example files
- `configs/example.conf`
- `configs/alert_rules/`
- `configs/provisioning/`

**Recommendation**:
- ✅ KEEP if these are deployment examples for different environments
- ❌ DELETE if they duplicate `security_alert/default/`

**Review Script**:
```bash
#!/bin/bash
# File: scripts/review-configs.sh

cd /home/jclee/app/splunk

echo "=== configs/ Directory Review ==="
echo ""

# List all config files
echo "Config files in configs/:"
find configs/ -type f -name "*.conf" -o -name "*.yml" -o -name "*.yaml" | while read file; do
    echo "  - $file ($(du -h "$file" | cut -f1))"
done

echo ""
echo "Config files in security_alert/default/:"
find security_alert/default/ -type f -name "*.conf" | while read file; do
    echo "  - $file ($(du -h "$file" | cut -f1))"
done

echo ""
echo "❓ Review needed: Determine if configs/ files are unique or duplicates"
```

---

## 📈 Expected Results

### Space Savings Breakdown

| Item | Files | Estimated Size | Action |
|------|-------|----------------|--------|
| nextrade/ | 30 | ~150KB | DELETE |
| archive-dev/ | 212 | ~4.5MB | DELETE |
| xwiki/ | 0 | 0KB | DELETE |
| Duplicate CSVs | 12 | ~40KB | CONSOLIDATE |
| **TOTAL** | **254** | **~4.7MB** | **CLEANUP** |

### Repository Structure After Cleanup

```
/home/jclee/app/splunk/
├── security_alert/              # ✅ ACTIVE (v2.0.4)
│   ├── bin/                     # 5 Python scripts
│   ├── default/                 # 6 Config files
│   ├── lookups/                 # 17 CSV files (consolidated)
│   ├── local/                   # User overrides (gitignored)
│   └── metadata/                # Permission settings
│
├── security_alert.tar.gz        # Deployment package (26KB)
│
├── configs/                     # Config examples (4 files) - REVIEW
│
├── docs/                        # Documentation
│   ├── CLEANUP-PROPOSAL.md      # This file
│   └── [other documentation]
│
├── scripts/                     # Cleanup automation scripts
│   ├── cleanup-legacy-dirs.sh
│   ├── consolidate-duplicates.sh
│   └── review-configs.sh
│
├── CLAUDE.md                    # Developer guide (1,045 lines)
├── README.md                    # User documentation (Korean)
└── .gitignore
```

---

## ✅ Validation Checklist

**Before Execution**:
- [ ] Backup created and verified (`~/backups/splunk_cleanup_YYYYMMDD_HHMMSS/`)
- [ ] Git status clean (commit any pending changes first)
- [ ] Production deployment package (`security_alert.tar.gz`) tested and working

**During Execution**:
- [ ] Phase 1: Backup completed successfully
- [ ] Phase 2: Legacy directories deleted
- [ ] Phase 3: Duplicate CSVs consolidated
- [ ] Phase 4: configs/ directory reviewed

**After Execution**:
- [ ] Git status shows expected deletions
- [ ] `security_alert/` directory unchanged (42 files)
- [ ] Create new deployment package: `tar -czf security_alert.tar.gz security_alert/`
- [ ] Test deployment package on test Splunk instance
- [ ] Commit cleanup: `git commit -m "chore: Remove legacy files and consolidate duplicates"`

---

## 🚨 Rollback Procedure

**If cleanup causes issues**:

```bash
# Restore from backup
BACKUP_DIR=$(ls -td ~/backups/splunk_cleanup_* | head -1)
cd /home/jclee/app/splunk

# Extract backups
tar -xzf $BACKUP_DIR/nextrade_backup.tar.gz
tar -xzf $BACKUP_DIR/archive-dev_backup.tar.gz

# Verify restoration
ls -la nextrade/
ls -la archive-dev/

echo "✅ Rollback completed. Repository restored to pre-cleanup state."
```

---

## 📝 Execution Order (Recommended)

1. **Commit current state**: `git add . && git commit -m "chore: Pre-cleanup checkpoint"`
2. **Run Phase 1**: Create backup
3. **Review backup**: Verify tarballs exist and are valid
4. **Run Phase 2**: Delete legacy directories
5. **Run Phase 3**: Consolidate duplicate CSVs
6. **Run Phase 4**: Review configs/ directory (manual decision)
7. **Test**: Create new `security_alert.tar.gz` and deploy to test environment
8. **Commit cleanup**: `git add . && git commit -m "chore: Remove legacy files (254 files, ~4.7MB)"`
9. **Push to remote**: `git push origin master`

---

## 🔍 Additional Recommendations

### Git History Cleanup (Optional - Advanced)

**Current Issue**: Deleted files remain in Git history, repository size not reduced

**Solution**: Use `git filter-repo` to purge history (CAUTION: Rewrites Git history)

```bash
# Install git-filter-repo
pip3 install git-filter-repo

# Remove directories from entire Git history
git filter-repo --path nextrade/ --invert-paths
git filter-repo --path archive-dev/ --invert-paths
git filter-repo --path xwiki/ --invert-paths

# Force push (requires coordination with team)
git push --force origin master
```

**⚠️ WARNING**: This rewrites Git history. Only do this if:
- You have full team coordination
- All team members can re-clone the repository
- This is approved by repository owner

### Directory Protection (.gitignore)

**Prevent future legacy accumulation**:

```gitignore
# Add to .gitignore
**/archive-*/
**/legacy-*/
**/*-old/
**/*-backup/
**/*.bak
**/*.backup
```

---

## 📊 Summary

**Cleanup Impact**:
- ✅ Remove 254 legacy/duplicate files (~4.7MB)
- ✅ Consolidate CSV files to single source of truth
- ✅ Simplify repository structure (6 → 3 top-level directories)
- ✅ Reduce cognitive load for future developers
- ✅ Faster Git operations (smaller working tree)

**Risk Level**: Low (with proper backup and validation)

**Estimated Execution Time**: 15-20 minutes

**Reversibility**: High (full backup created in Phase 1)

---

**Document Status**: Ready for Review
**Next Action**: User approval required before executing cleanup scripts
