# 🗄️ Cloudflare D1 Database & KV Namespace 설정 가이드

## 📋 현재 상황

**배포 실패 원인**: `wrangler.toml`에 placeholder ID들이 있어서 Cloudflare Workers 배포가 실패하고 있습니다.

```toml
# 현재 문제가 되는 설정들
id = "your-kv-namespace-id"           # ❌ Placeholder
database_id = "your-d1-database-id"  # ❌ Placeholder
```

## 🛠️ 해결 방법

### 1. Cloudflare API Token 생성 (필수)

1. **API Token 페이지 접속**: https://dash.cloudflare.com/profile/api-tokens
2. **Create Token** → **Custom token** 선택
3. **권한 설정**:
   ```
   Account: Cloudflare Workers Scripts:Edit
   Zone: Zone:Read, Workers Routes:Edit
   D1: D1:Edit
   Workers KV: Workers KV Storage:Edit
   ```
4. **환경 변수 설정**:
   ```bash
   export CLOUDFLARE_API_TOKEN=your-api-token-here
   ```

### 2. 자동 설정 스크립트 실행

```bash
# API 토큰 설정 후 실행
export CLOUDFLARE_API_TOKEN=your-token
./scripts/setup-d1-kv-resources.sh
```

### 3. 수동 리소스 생성 (대안)

#### D1 Database 생성
```bash
# Production Database
wrangler d1 create security-db-prod

# Staging Database
wrangler d1 create security-db-staging
```

#### KV Namespace 생성
```bash
# Production KV
wrangler kv:namespace create "SECURITY_KV"

# Preview KV
wrangler kv:namespace create "SECURITY_KV" --preview

# Staging KV
wrangler kv:namespace create "SECURITY_KV_STAGING"
```

## 🗄️ D1 Database 구조

### 테이블 스키마
```sql
-- 보안 이벤트 테이블
CREATE TABLE security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL,           -- FortiGate, FortiAnalyzer, Splunk
    event_type TEXT NOT NULL,       -- alert, policy_violation, login_attempt
    severity TEXT NOT NULL,         -- high, medium, low
    message TEXT NOT NULL,
    raw_data TEXT,                  -- JSON 형태의 원본 데이터
    processed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- FortiGate 정책 테이블
CREATE TABLE fortigate_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    source_zone TEXT,
    dest_zone TEXT,
    action TEXT NOT NULL,           -- allow, deny, reject
    status TEXT DEFAULT 'active',   -- active, disabled
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 시스템 설정 테이블
CREATE TABLE system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔑 KV Namespace 용도

### SECURITY_KV (메인 캐시)
```javascript
// 캐시된 데이터 예시
{
  "config:version": "1.0.0",
  "cache:last_sync": "2025-09-28T06:50:00Z",
  "fortigate:device_count": "80",
  "splunk:connection_status": "connected",
  "alerts:high_priority": "5",
  "policies:last_update": "2025-09-28T06:30:00Z"
}
```

### 사용 패턴
- **설정 캐싱**: API 응답 속도 향상
- **상태 정보**: 실시간 연결 상태
- **임시 데이터**: 세션 정보, 토큰 캐시
- **통계 데이터**: 대시보드 성능 최적화

## 📊 리소스 관리 명령어

### D1 Database 관리
```bash
# 데이터베이스 목록
wrangler d1 list

# 쿼리 실행
wrangler d1 execute security-db-prod --command "SELECT COUNT(*) FROM security_events;"

# 스키마 적용
wrangler d1 execute security-db-prod --file=schema.sql

# 백업
wrangler d1 export security-db-prod --output=backup.sql
```

### KV Namespace 관리
```bash
# 네임스페이스 목록
wrangler kv:namespace list

# 키 목록 확인
wrangler kv:key list --namespace-id [namespace-id]

# 값 설정/조회
wrangler kv:key put "key" "value" --namespace-id [namespace-id]
wrangler kv:key get "key" --namespace-id [namespace-id]

# 일괄 업로드
wrangler kv:bulk put data.json --namespace-id [namespace-id]
```

## 🔧 wrangler.toml 업데이트 템플릿

스크립트 실행 후 다음과 같이 업데이트:

```toml
name = "splunk"
main = "src/worker.js"
compatibility_date = "2024-01-01"
account_id = "a8d9c67f586acdd15eebcc65ca3aa5bb"

# Production KV Namespace
[[kv_namespaces]]
binding = "SECURITY_KV"
id = "[GENERATED_KV_ID]"
preview_id = "[GENERATED_PREVIEW_ID]"

# Production D1 Database
[[d1_databases]]
binding = "SECURITY_DB"
database_name = "security-db-prod"
database_id = "[GENERATED_D1_ID]"

# R2 Bucket (선택적)
[[r2_buckets]]
binding = "SECURITY_BUCKET"
bucket_name = "security-files-prod"

# Staging Environment
[env.staging]
name = "splunk-staging"

[[env.staging.kv_namespaces]]
binding = "SECURITY_KV"
id = "[GENERATED_STAGING_KV_ID]"

[[env.staging.d1_databases]]
binding = "SECURITY_DB"
database_name = "security-db-staging"
database_id = "[GENERATED_STAGING_D1_ID]"
```

## 🚀 배포 테스트

리소스 생성 완료 후:

```bash
# 로컬 개발 테스트
wrangler dev

# 스테이징 배포
wrangler deploy --env staging

# 프로덕션 배포
wrangler deploy

# 배포 후 테스트
curl https://splunk.jclee.me/health
curl https://splunk.jclee.me/api/test
```

## 📈 모니터링 & 사용량

### Cloudflare Dashboard
- **Workers & Pages**: 배포 상태 및 메트릭
- **D1**: 데이터베이스 사용량 및 쿼리 통계
- **KV**: 네임스페이스 사용량 및 요청 수

### 사용량 제한 (Free Tier)
- **D1**: 5 databases, 100MB/database
- **KV**: 100 namespaces, 1GB storage
- **Workers**: 100,000 requests/day

## 🔒 보안 고려사항

1. **API Token 보안**: 최소 권한 원칙 적용
2. **D1 액세스**: Workers에서만 접근 가능
3. **KV 데이터**: 민감 정보는 암호화 저장
4. **백업**: 정기적인 D1 백업 수행

## 📋 체크리스트

- [ ] Cloudflare API Token 생성 및 설정
- [ ] D1 Database 생성 (Production, Staging)
- [ ] KV Namespace 생성 (Production, Preview, Staging)
- [ ] wrangler.toml 업데이트
- [ ] 스키마 적용 및 초기 데이터 설정
- [ ] 배포 테스트 및 검증
- [ ] 모니터링 설정 완료

이 과정을 완료하면 배포 실패 문제가 해결되고 완전한 FortiNet-Splunk 통합 시스템이 작동하게 됩니다.