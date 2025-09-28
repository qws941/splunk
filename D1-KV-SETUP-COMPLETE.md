# 🗄️ D1 Database & KV Namespace 완전 설정 가이드

## 📋 개요

Splunk-FortiNet 보안 통합 플랫폼을 위한 Cloudflare D1 Database와 KV Namespace의 완전한 설정 및 마이그레이션 시스템이 구축되었습니다.

## 🚨 현재 배포 실패 해결

### 문제 상황
- **배포 실패**: Cloudflare Workers 배포 단계에서 실패
- **원인**: `wrangler.toml`의 placeholder ID들 (`your-kv-namespace-id`, `your-d1-database-id`)
- **해결책**: 실제 D1 Database와 KV Namespace 생성 후 설정 업데이트

## 🛠️ 설정 단계

### 1. Cloudflare API Token 생성 (필수)

```bash
# 1. API Token 생성 URL 접속
# https://dash.cloudflare.com/profile/api-tokens

# 2. 권한 설정:
# - Account: Cloudflare Workers Scripts:Edit
# - Zone: Zone:Read, Workers Routes:Edit
# - D1: D1:Edit
# - Workers KV: Workers KV Storage:Edit

# 3. 환경 변수 설정
export CLOUDFLARE_API_TOKEN=your-api-token-here
```

### 2. 자동 리소스 생성 (jclee.me 네이밍 규칙 적용)

```bash
# 모든 리소스 자동 생성 (새로운 네이밍 규칙 적용)
./scripts/setup-d1-kv-resources.sh

# 또는 개별 실행 (새로운 네이밍 규칙)
wrangler d1 create splunk_events
wrangler d1 create splunk_events_staging
wrangler kv:namespace create "SPLUNK_CACHE"
wrangler kv:namespace create "SPLUNK_CACHE" --preview
wrangler kv:namespace create "SPLUNK_CACHE_STAGING"
```

### 3. 데이터베이스 마이그레이션

```bash
# 전체 마이그레이션 (프로덕션 + 스테이징)
./scripts/migrate-d1-database.sh

# 개별 환경 마이그레이션
./scripts/migrate-d1-database.sh prod
./scripts/migrate-d1-database.sh staging

# 마이그레이션 검증 (새로운 네이밍)
./scripts/migrate-d1-database.sh --verify splunk_events
```

### 4. KV 데이터 초기화

```bash
# KV 네임스페이스에 초기 데이터 설정
PROD_KV_NAMESPACE_ID=your-actual-id ./scripts/setup-kv-data.sh

# 개별 환경 설정
PROD_KV_NAMESPACE_ID=prod-id ./scripts/setup-kv-data.sh prod
STAGING_KV_NAMESPACE_ID=staging-id ./scripts/setup-kv-data.sh staging
```

### 5. wrangler.toml 업데이트

생성된 실제 ID들로 `wrangler.toml` 파일 업데이트 (jclee.me 네이밍 규칙 적용):

```toml
# Production KV Namespace - Following jclee.me naming conventions
[[kv_namespaces]]
binding = "SPLUNK_CACHE"
id = "실제_생성된_KV_ID"
preview_id = "실제_생성된_PREVIEW_ID"

# Production D1 Database - Following jclee.me naming conventions
[[d1_databases]]
binding = "SPLUNK_EVENTS"
database_name = "splunk_events"
database_id = "실제_생성된_D1_ID"

# Staging Environment
[env.staging]
[[env.staging.kv_namespaces]]
binding = "SPLUNK_CACHE"
id = "실제_생성된_STAGING_KV_ID"

[[env.staging.d1_databases]]
binding = "SPLUNK_EVENTS"
database_name = "splunk_events_staging"
database_id = "실제_생성된_STAGING_D1_ID"
```

## 📊 데이터베이스 스키마

### 주요 테이블 구조

#### 1. security_events (보안 이벤트)
```sql
- id: 고유 식별자
- event_uuid: UUID
- timestamp: 이벤트 발생 시간
- source: fortigate|fortianalyzer|splunk|system
- event_type: 이벤트 유형
- severity: critical|high|medium|low|info
- title: 이벤트 제목
- message: 상세 메시지
- raw_data: JSON 원본 데이터
- source_ip, dest_ip: 소스/목적지 IP
- protocol: 프로토콜
- action_taken: 취해진 조치
```

#### 2. fortigate_policies (FortiGate 정책)
```sql
- policy_id: 정책 ID
- name: 정책 이름
- source_zone, dest_zone: 소스/목적지 존
- action: accept|deny|reject
- status: enabled|disabled
- fortigate_device: 디바이스 참조
- hit_count: 히트 수
- last_hit: 마지막 히트 시간
```

#### 3. fortigate_devices (FortiGate 디바이스)
```sql
- hostname: 호스트명
- ip_address: IP 주소
- serial_number: 시리얼 번호
- model: 모델명
- firmware_version: 펌웨어 버전
- status: active|inactive|maintenance
- sync_status: connected|disconnected|error
```

#### 4. 기타 테이블
- `splunk_integration`: Splunk 연동 상태
- `user_sessions`: 사용자 세션 관리
- `audit_logs`: 감사 로그
- `system_config`: 시스템 설정
- `alert_rules`: 알림 규칙

## 🔑 KV Store 데이터 구조

### 설정 키들
```javascript
// 애플리케이션 설정
"config:version": "1.0.0"
"config:environment": "production"
"feature:real_time_alerts": "true"

// 시스템 상태
"status:system_health": "healthy"
"status:fortigate_devices_online": "4"
"status:splunk_connection": "connected"

// 캐시 설정
"cache:ttl_security_events": "300"  // 5분
"cache:recent_events_summary": "{...}"  // JSON

// 성능 메트릭
"metrics:avg_response_time": "125"
"metrics:requests_per_minute": "45"
```

## 🔧 관리 명령어

### D1 Database 관리
```bash
# 데이터베이스 목록
wrangler d1 list

# 쿼리 실행 (새로운 네이밍)
wrangler d1 execute splunk_events --command "SELECT COUNT(*) FROM security_events;"

# 백업 생성 (새로운 네이밍)
./scripts/migrate-d1-database.sh --backup splunk_events

# 통계 확인 (새로운 네이밍)
./scripts/migrate-d1-database.sh --stats splunk_events
```

### KV Namespace 관리
```bash
# 키 목록 확인
./scripts/setup-kv-data.sh --list production

# 특정 값 조회
./scripts/setup-kv-data.sh --get config:version production

# 값 업데이트
wrangler kv:key put "config:version" "1.0.1" --namespace-id [namespace-id]
```

## 📁 생성된 파일 구조

```
📁 splunk/
├── 📁 migrations/
│   ├── 001_initial_security_schema.sql     # 데이터베이스 스키마
│   └── 002_sample_data_insertion.sql       # 샘플 데이터
├── 📁 scripts/
│   ├── setup-d1-kv-resources.sh           # 리소스 자동 생성
│   ├── migrate-d1-database.sh              # DB 마이그레이션
│   └── setup-kv-data.sh                    # KV 데이터 초기화
├── 📁 backups/                             # 자동 백업 저장소
├── cloudflare-resources-setup.md           # 설정 가이드
└── D1-KV-SETUP-COMPLETE.md                # 이 문서
```

## 🚀 배포 테스트

### 1. 로컬 테스트
```bash
# 개발 서버 실행
wrangler dev

# 특정 환경 테스트
wrangler dev --env staging
```

### 2. 스테이징 배포
```bash
# 스테이징 배포
wrangler deploy --env staging

# 헬스체크
curl https://splunk-staging.jclee.me/health
```

### 3. 프로덕션 배포
```bash
# 프로덕션 배포
wrangler deploy

# 검증
curl https://splunk.jclee.me/health
curl https://splunk.jclee.me/api/test
```

## 🔍 문제 해결

### 일반적인 오류들

#### 1. API Token 권한 오류
```bash
Error: Insufficient permissions
# 해결: API Token 권한 재설정
```

#### 2. Namespace ID 오류
```bash
Error: Unknown namespace
# 해결: wrangler.toml의 ID 확인 및 업데이트
```

#### 3. 마이그레이션 실패
```bash
Error: SQL syntax error
# 해결: 마이그레이션 파일 구문 확인
```

### 디버깅 명령어
```bash
# 실시간 로그 확인
wrangler tail

# 배포 상태 확인
wrangler deployments list

# 네임스페이스 확인
wrangler kv:namespace list
wrangler d1 list
```

## 📊 모니터링 & 성능

### Cloudflare 대시보드
- **Workers & Pages**: 배포 및 성능 모니터링
- **D1**: 데이터베이스 사용량 및 쿼리 성능
- **KV**: 네임스페이스 요청 수 및 응답 시간

### 사용량 한계 (Free Tier)
- **D1**: 5개 데이터베이스, 100MB/데이터베이스
- **KV**: 100개 네임스페이스, 1GB 저장공간
- **Workers**: 100,000 요청/일

## ✅ 배포 성공 확인

설정이 완료되면 다음을 확인하세요:

1. **D1 Database 연결**: 웹 인터페이스에서 디바이스 목록 표시
2. **KV Cache 작동**: 설정 값들이 정상적으로 로드
3. **API 엔드포인트**: `/api/devices`, `/api/events` 등이 정상 응답
4. **실시간 데이터**: FortiGate와 Splunk 연동 상태 확인

## 🎯 다음 단계

1. **실제 FortiGate 연동**: API 크리덴셜 설정
2. **Splunk HEC 연동**: HTTP Event Collector 설정
3. **실시간 모니터링**: 대시보드 활성화
4. **알림 시스템**: 이메일/Slack 통합
5. **백업 자동화**: 정기적인 데이터 백업 스케줄

---

**중요**: Cloudflare API Token을 안전하게 보관하고, 정기적으로 교체하세요. 모든 설정이 완료되면 placeholder ID들을 실제 생성된 ID로 업데이트하는 것을 잊지 마세요.