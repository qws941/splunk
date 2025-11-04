# Cleanup Automation Scripts

**Purpose**: Automated cleanup of legacy files and duplicate CSVs from Splunk repository

**Created**: 2025-11-04
**Documentation**: See `docs/CLEANUP-PROPOSAL.md` for detailed analysis

---

## 📋 Scripts Overview

### Master Script

**`run-full-cleanup.sh`** - Run all cleanup phases automatically
- Creates backup
- Deletes legacy directories
- Consolidates duplicate CSVs
- Reviews configs/ directory
- Provides rollback instructions

**Usage**:
```bash
cd /home/jclee/app/splunk
bash scripts/run-full-cleanup.sh
```

### Individual Phase Scripts

**`cleanup-legacy-dirs.sh`** (Phase 2)
- Deletes: nextrade/, archive-dev/, xwiki/
- Requires Phase 1 backup completed first
- Removes 242 files (~4.7MB)

**`consolidate-duplicates.sh`** (Phase 3)
- Consolidates duplicate CSV files to security_alert/lookups/
- Compares files before deletion
- Safe duplicate removal

**`review-configs.sh`** (Phase 4)
- Reviews configs/ directory
- Detects duplicates with security_alert/default/
- Provides manual decision guidance

---

## ✅ Execution Order

**Recommended workflow**:

```bash
# 1. Commit current state
git add . && git commit -m "chore: Pre-cleanup checkpoint"

# 2. Run full cleanup (includes Phase 1-4)
bash scripts/run-full-cleanup.sh

# 3. Review git status
git status

# 4. Test deployment package
tar -czf security_alert.tar.gz security_alert/
ls -lh security_alert.tar.gz  # Should be ~26KB

# 5. Commit cleanup
git add .
git commit -m "chore: Remove legacy files (242 files, ~4.7MB)"

# 6. Push to remote
git push origin master
```

---

## 🚨 Rollback Instructions

If cleanup causes issues:

```bash
# Find latest backup
BACKUP_DIR=$(ls -td ~/backups/splunk_cleanup_* | head -1)

# Restore from backup
cd /home/jclee/app/splunk
tar -xzf $BACKUP_DIR/nextrade_backup.tar.gz
tar -xzf $BACKUP_DIR/archive-dev_backup.tar.gz

# Verify restoration
ls -la nextrade/ archive-dev/

echo "✅ Rollback completed"
```

---

## 📊 Expected Results

**Before Cleanup**:
```
/home/jclee/app/splunk/
├── security_alert/ (42 files)
├── configs/ (4 files)
├── lookups/ (8 files)
├── nextrade/ (30 files) ← DELETE
├── archive-dev/ (212 files) ← DELETE
└── xwiki/ (0 files) ← DELETE
```

**After Cleanup**:
```
/home/jclee/app/splunk/
├── security_alert/ (42 files)
├── configs/ (4 files) - REVIEW
├── docs/
│   └── CLEANUP-PROPOSAL.md
└── scripts/
    ├── run-full-cleanup.sh
    ├── cleanup-legacy-dirs.sh
    ├── consolidate-duplicates.sh
    └── review-configs.sh
```

**Space Savings**: ~4.7MB (242 files removed)

---

## 🔒 Safety Features

All scripts include:
- ✅ Mandatory backup verification before deletion
- ✅ File existence checks (no errors if already deleted)
- ✅ Duplicate file comparison (detects differences before deletion)
- ✅ Detailed logging of all actions
- ✅ Rollback instructions

---

## 📝 Manual Phase 1 (Alternative)

If you prefer manual backup instead of run-full-cleanup.sh:

```bash
cd /home/jclee/app/splunk
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p ~/backups/splunk_cleanup_${BACKUP_DATE}

# Create backups
tar -czf ~/backups/splunk_cleanup_${BACKUP_DATE}/nextrade_backup.tar.gz nextrade/
tar -czf ~/backups/splunk_cleanup_${BACKUP_DATE}/archive-dev_backup.tar.gz archive-dev/

# Verify backup
ls -lh ~/backups/splunk_cleanup_${BACKUP_DATE}/

# Then run Phase 2-4 individually
bash scripts/cleanup-legacy-dirs.sh
bash scripts/consolidate-duplicates.sh
bash scripts/review-configs.sh
```

---

**Status**: Ready for execution
**Risk Level**: Low (full backup + rollback available)
**Estimated Time**: 5-10 minutes
