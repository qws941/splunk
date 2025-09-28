#!/bin/bash
# 🗄️ Cloudflare D1 Database & KV Namespace 설정 스크립트

set -e

echo "🗄️ Setting up Cloudflare D1 Database & KV Namespace..."
echo "======================================================"

# Cloudflare API Token 확인
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "❌ CLOUDFLARE_API_TOKEN 환경 변수가 설정되지 않았습니다."
    echo "📝 다음 단계를 따라 API Token을 생성하세요:"
    echo "   1. https://dash.cloudflare.com/profile/api-tokens 접속"
    echo "   2. 'Create Token' 클릭"
    echo "   3. 'Custom token' 선택"
    echo "   4. 권한 설정:"
    echo "      - Account: Cloudflare Workers Scripts:Edit"
    echo "      - Zone: Zone:Read, Workers Routes:Edit"
    echo "      - D1: D1:Edit"
    echo "      - Workers KV: Workers KV Storage:Edit"
    echo "   5. export CLOUDFLARE_API_TOKEN=your-token-here"
    exit 1
fi

echo "✅ Cloudflare API Token 확인됨"

# 1. D1 Database 생성
echo ""
echo "🗄️ Creating D1 Database for security data..."

# Production D1 Database - Following jclee.me naming conventions
echo "📊 Creating production splunk events database..."
D1_PROD_OUTPUT=$(wrangler d1 create splunk_events 2>/dev/null || echo "ERROR")

if [[ "$D1_PROD_OUTPUT" == *"database_id"* ]]; then
    D1_PROD_ID=$(echo "$D1_PROD_OUTPUT" | grep -o '"database_id": "[^"]*"' | cut -d'"' -f4)
    echo "✅ Production D1 Database created: $D1_PROD_ID"
else
    echo "⚠️ Production D1 Database creation failed or already exists"
    D1_PROD_ID="your-d1-database-id"
fi

# Staging D1 Database - Following jclee.me naming conventions
echo "📊 Creating staging splunk events database..."
D1_STAGING_OUTPUT=$(wrangler d1 create splunk_events_staging 2>/dev/null || echo "ERROR")

if [[ "$D1_STAGING_OUTPUT" == *"database_id"* ]]; then
    D1_STAGING_ID=$(echo "$D1_STAGING_OUTPUT" | grep -o '"database_id": "[^"]*"' | cut -d'"' -f4)
    echo "✅ Staging D1 Database created: $D1_STAGING_ID"
else
    echo "⚠️ Staging D1 Database creation failed or already exists"
    D1_STAGING_ID="staging-d1-database-id"
fi

# 2. KV Namespace 생성
echo ""
echo "🔑 Creating KV Namespaces for security cache..."

# Production KV Namespace - Following jclee.me naming conventions
echo "💾 Creating production KV namespace..."
KV_PROD_OUTPUT=$(wrangler kv:namespace create "SPLUNK_CACHE" 2>/dev/null || echo "ERROR")

if [[ "$KV_PROD_OUTPUT" == *"id"* ]]; then
    KV_PROD_ID=$(echo "$KV_PROD_OUTPUT" | grep -o 'id = "[^"]*"' | cut -d'"' -f2)
    echo "✅ Production KV Namespace created: $KV_PROD_ID"
else
    echo "⚠️ Production KV Namespace creation failed or already exists"
    KV_PROD_ID="your-kv-namespace-id"
fi

# Production KV Preview Namespace - Following jclee.me naming conventions
echo "💾 Creating production KV preview namespace..."
KV_PREVIEW_OUTPUT=$(wrangler kv:namespace create "SPLUNK_CACHE" --preview 2>/dev/null || echo "ERROR")

if [[ "$KV_PREVIEW_OUTPUT" == *"id"* ]]; then
    KV_PREVIEW_ID=$(echo "$KV_PREVIEW_OUTPUT" | grep -o 'id = "[^"]*"' | cut -d'"' -f2)
    echo "✅ Production KV Preview Namespace created: $KV_PREVIEW_ID"
else
    echo "⚠️ Production KV Preview Namespace creation failed or already exists"
    KV_PREVIEW_ID="your-preview-kv-namespace-id"
fi

# Staging KV Namespace - Following jclee.me naming conventions
echo "💾 Creating staging KV namespace..."
KV_STAGING_OUTPUT=$(wrangler kv:namespace create "SPLUNK_CACHE_STAGING" 2>/dev/null || echo "ERROR")

if [[ "$KV_STAGING_OUTPUT" == *"id"* ]]; then
    KV_STAGING_ID=$(echo "$KV_STAGING_OUTPUT" | grep -o 'id = "[^"]*"' | cut -d'"' -f2)
    echo "✅ Staging KV Namespace created: $KV_STAGING_ID"
else
    echo "⚠️ Staging KV Namespace creation failed or already exists"
    KV_STAGING_ID="staging-kv-namespace-id"
fi

# 3. wrangler.toml 업데이트용 설정 출력
echo ""
echo "📝 wrangler.toml 업데이트 정보:"
echo "================================="

cat << EOF

# Production KV Namespace - Following jclee.me naming conventions
[[kv_namespaces]]
binding = "SPLUNK_CACHE"
id = "$KV_PROD_ID"
preview_id = "$KV_PREVIEW_ID"

# Production D1 Database - Following jclee.me naming conventions
[[d1_databases]]
binding = "SPLUNK_EVENTS"
database_name = "splunk_events"
database_id = "$D1_PROD_ID"

# Staging Environment
[env.staging]
[[env.staging.kv_namespaces]]
binding = "SPLUNK_CACHE"
id = "$KV_STAGING_ID"

[[env.staging.d1_databases]]
binding = "SPLUNK_EVENTS"
database_name = "splunk_events_staging"
database_id = "$D1_STAGING_ID"

EOF

# 4. D1 Database 초기화 스키마 생성
echo ""
echo "🗄️ Creating D1 Database schema..."

cat > /tmp/schema.sql << 'EOF'
-- Security Events Table
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    raw_data TEXT,
    processed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- FortiGate Policies Table
CREATE TABLE IF NOT EXISTS fortigate_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    source_zone TEXT,
    dest_zone TEXT,
    action TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- System Configuration Table
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_fortigate_policies_status ON fortigate_policies(status);
EOF

echo "💾 Applying schema to production database..."
wrangler d1 execute splunk_events --file=/tmp/schema.sql 2>/dev/null || echo "⚠️ Schema creation failed"

echo "💾 Applying schema to staging database..."
wrangler d1 execute splunk_events_staging --file=/tmp/schema.sql 2>/dev/null || echo "⚠️ Schema creation failed"

# 5. KV 초기 데이터 설정
echo ""
echo "🔑 Setting up initial KV data..."

# Production KV 초기 설정
wrangler kv:key put "config:version" "1.0.0" --namespace-id "$KV_PROD_ID" 2>/dev/null || echo "⚠️ KV setup failed"
wrangler kv:key put "cache:last_sync" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --namespace-id "$KV_PROD_ID" 2>/dev/null || echo "⚠️ KV setup failed"

# Staging KV 초기 설정
wrangler kv:key put "config:version" "1.0.0-staging" --namespace-id "$KV_STAGING_ID" 2>/dev/null || echo "⚠️ KV setup failed"

# 정리
rm -f /tmp/schema.sql

echo ""
echo "🎉 D1 Database & KV Namespace 설정 완료!"
echo "========================================"
echo "📊 Production D1 Database ID: $D1_PROD_ID"
echo "📊 Staging D1 Database ID: $D1_STAGING_ID"
echo "🔑 Production KV Namespace ID: $KV_PROD_ID"
echo "🔑 Preview KV Namespace ID: $KV_PREVIEW_ID"
echo "🔑 Staging KV Namespace ID: $KV_STAGING_ID"
echo ""
echo "📝 다음 단계:"
echo "  1. wrangler.toml 파일 업데이트"
echo "  2. git commit 및 배포 테스트"
echo "  3. 데이터베이스 연결 테스트"

echo ""
echo "🔧 관리 명령어:"
echo "  # D1 데이터베이스 조회"
echo "  wrangler d1 execute splunk_events --command 'SELECT * FROM security_events LIMIT 5;'"
echo ""
echo "  # KV 데이터 조회"
echo "  wrangler kv:key list --namespace-id $KV_PROD_ID"
echo ""
echo "  # 데이터베이스 목록"
echo "  wrangler d1 list"