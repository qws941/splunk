#!/bin/bash
# scripts/auto-sync-airgap.sh - Wrapper for airgap sync
exec "$(dirname "$0")/../tools/scripts/deploy/auto-sync-airgap.sh" "$@"
