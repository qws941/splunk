#!/bin/bash
# scripts/deploy.sh - Environment-specific deployment wrapper
# Routes deployment calls to environment-specific scripts
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <dev|prod> [additional-args]"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Deploy to development"
    echo "  $0 prod                   # Deploy to production"
    exit 1
fi

ENVIRONMENT=$1
shift

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_SCRIPT="${SCRIPT_DIR}/../infra/deploy/${ENVIRONMENT}/deploy.sh"

if [[ ! -f "$DEPLOY_SCRIPT" ]]; then
    echo "Error: Deployment script not found: $DEPLOY_SCRIPT"
    echo ""
    echo "Available environments:"
    ls -1 "${SCRIPT_DIR}/../infra/deploy/" 2>/dev/null | grep -v '^$' | sed 's/^/  - /'
    exit 1
fi

exec "$DEPLOY_SCRIPT" "$@"
