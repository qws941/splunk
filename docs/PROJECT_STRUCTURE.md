# Project Structure

## Overview

FortiAnalyzer → Splunk HEC Integration 프로젝트의 디렉토리 구조 가이드입니다.

```
splunk/
├── configs/              # Configuration files
├── dashboards/           # Splunk dashboard XML files
├── docs/                 # Documentation
├── domains/              # Domain-Driven Design Level 3
├── scripts/              # Utility scripts
├── src/                  # Cloudflare Workers source
└── [config files]        # Root configuration files
```

---

## Directory Structure (Detailed)

### 📁 `configs/` - Configuration Files

FortiAnalyzer, Splunk HEC 설정 파일

```
configs/
└── fortigate-hec-setup.conf    # FAZ HEC 직접 설정 (CLI 명령어)
```

**용도**: FortiAnalyzer에서 Splunk HEC로 직접 로그를 전송할 때 사용하는 설정 파일

---

### 📊 `dashboards/` - Splunk Dashboard XML Files

Splunk 대시보드 템플릿 (7개 + 문서 4개)

```
dashboards/
├── archive/                                   # Legacy dashboards
├── DEPLOYMENT_GUIDE.md                        # 대시보드 배포 가이드
├── FINAL_VALIDATION_REPORT.md                 # 최종 검증 보고서
├── INTEGRATION_TEST_REPORT.md                 # 통합 테스트 보고서
├── README.md                                  # 대시보드 개요
├── fortigate-security-overview.xml            # Security Overview (8 panels)
├── fortinet-config-management-final.xml       # Config Management (WCAG, Slack)
├── fortinet-dashboard.xml                     # Main Fortinet Dashboard
├── performance-monitoring.xml                 # Performance (7 panels)
├── splunk-advanced-dashboard.xml              # Advanced Analytics
├── threat-intelligence.xml                    # Threat Intel (10 panels)
└── traffic-analysis.xml                       # Traffic (9 panels)
```

**배포 방법**:
```bash
node scripts/deploy-dashboards.js              # 프로그래밍 방식 배포
```

---

### 📚 `docs/` - Documentation

프로젝트 문서 (배포, 설정, 가이드)

```
docs/
├── archive/                                   # Legacy documentation
├── CLOUDFLARE_DEPLOYMENT.md                   # Cloudflare Workers 배포 가이드
├── DEPLOYMENT_SUMMARY_FINAL.md                # 최종 배포 요약
├── FILE_ORGANIZATION.md                       # 파일 구조 상세 설명
├── PRD_DEPLOYMENT_GUIDE.md                    # 프로덕션 배포 가이드
├── PROXY_SLACK_SETUP_GUIDE.md                 # Slack 프록시 설정
└── README_DASHBOARDS.md                       # 대시보드 사용 가이드
```

**주요 문서**:
- **Cloudflare 배포**: `CLOUDFLARE_DEPLOYMENT.md`
- **프로덕션 배포**: `PRD_DEPLOYMENT_GUIDE.md`
- **파일 가이드**: `FILE_ORGANIZATION.md`

---

### 🏗️ `domains/` - Domain-Driven Design (DDD Level 3)

핵심 비즈니스 로직 (Zero Dependencies Architecture)

```
domains/
├── defense/                                   # Resilience patterns
│   └── circuit-breaker.js                     # Circuit Breaker implementation
│
├── integration/                               # External system connectors
│   ├── fortianalyzer-direct-connector.js      # FAZ REST API client
│   ├── slack-connector.js                     # Slack Bot API
│   ├── slack-webhook-handler.js               # Slack Webhook receiver
│   ├── splunk-api-connector.js                # Splunk HEC client
│   ├── splunk-dashboards.js                   # 4 dashboard templates
│   ├── splunk-queries.js                      # 29 production SPL queries
│   └── splunk-rest-client.js                  # Splunk REST API
│
└── security/                                  # Core domain (Security)
    └── security-event-processor.js            # Event processing engine
```

**Architecture**:
- **Defense**: Circuit Breaker, Retry, Fallback 패턴
- **Integration**: 외부 시스템 연동 (FAZ, Splunk, Slack)
- **Security**: 보안 이벤트 분석, 위험도 계산, 알림 트리거

**Key Features**:
- ✅ Zero Dependencies (Node.js 내장 모듈만 사용)
- ✅ ES Modules (`.js` 확장자 필수)
- ✅ Circuit Breaker로 cascading failure 방지
- ✅ Event Queue (최대 10,000개)

---

### 🛠️ `scripts/` - Utility Scripts

운영 및 관리 스크립트

```
scripts/
├── deploy-dashboards.js                       # Splunk 대시보드 자동 배포
├── deploy-to-splunk.sh                        # Splunk HEC 테스트 전송
├── export-dashboards.js                       # 대시보드 백업/다운로드
├── generate-mock-data.js                      # Mock 이벤트 생성
├── slack-alert-cli.js                         # Slack 알림 테스트 CLI
└── splunk-alert-action.py                     # Splunk Alert Action (Python)
```

**사용 예시**:
```bash
# 대시보드 배포
node scripts/deploy-dashboards.js

# Mock 데이터 생성 및 전송
node scripts/generate-mock-data.js --count=1000 --send

# Slack 알림 테스트
node scripts/slack-alert-cli.js --webhook="URL" --test
```

---

### ☁️ `src/` - Cloudflare Workers Source

서버리스 배포 엔트리 포인트

```
src/
└── worker.js                                  # Cloudflare Worker main file
```

**배포 방법**:
```bash
npm run dev:worker                             # 로컬 개발 서버
npm run deploy:worker                          # 프로덕션 배포
npm run tail:worker                            # 실시간 로그
```

**Features**:
- ✅ Cron Trigger (매 1분 자동 실행)
- ✅ HTTP Endpoints (`/health`, `/trigger`)
- ✅ 글로벌 엣지 네트워크
- ✅ 무료 티어: 100,000 requests/day

---

## Root Files

### Entry Points

| File | Purpose | Usage |
|------|---------|-------|
| `index.js` | 로컬/Docker 실행 | `npm start` |
| `src/worker.js` | Cloudflare Workers | `npm run deploy:worker` |

### Configuration

| File | Purpose |
|------|---------|
| `.env.example` | 환경변수 템플릿 |
| `docker-compose.yml` | Docker Compose 설정 |
| `Dockerfile` | Docker 이미지 빌드 |
| `wrangler.toml` | Cloudflare Workers 설정 |
| `package.json` | Node.js 의존성 (Zero Runtime Dependencies) |

### Scripts

| File | Purpose | Usage |
|------|---------|-------|
| `start-demo.sh` | 데모 실행 스크립트 | `./start-demo.sh` |

### Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Claude Code 프로젝트 가이드 (29KB) |
| `README.md` | 프로젝트 개요 및 사용법 |
| `PROJECT_STRUCTURE.md` | 디렉토리 구조 가이드 (이 문서) |

---

## Key Design Principles

### 1. Zero Dependencies Architecture

```json
// package.json
{
  "dependencies": {},  // 런타임 의존성 없음!
  "devDependencies": {
    "wrangler": "^3.114.15"  // Cloudflare Workers CLI만
  }
}
```

**이점**:
- ✅ 보안 취약점 최소화
- ✅ 배포 패키지 크기 최소화
- ✅ 외부 라이브러리 호환성 문제 없음

### 2. Domain-Driven Design (Level 3)

```
domains/
├── defense/      # 안정성 패턴
├── integration/  # 외부 시스템 연동
└── security/     # 핵심 보안 로직
```

**특징**:
- 도메인별 책임 분리
- 의존성 역전 원칙
- 높은 응집도, 낮은 결합도

### 3. ES Modules

```javascript
// ✅ 올바른 import (.js 필수)
import Connector from './domains/integration/connector.js';

// ❌ 잘못된 import (.js 누락)
import Connector from './domains/integration/connector';
```

### 4. Dual Entry Points

| Entry Point | Use Case | Runtime |
|-------------|----------|---------|
| `index.js` | 로컬 개발, Docker | Node.js 18+ |
| `src/worker.js` | 프로덕션 배포 | Cloudflare Workers |

---

## File Count Summary

```
Total Files: 38
├── Dashboards: 7 XML files
├── Documents: 10 files
├── Scripts: 6 files
├── Domain Code: 10 files
├── Configuration: 5 files
└── Root Files: 5 files
```

---

## Navigation Guide

### "나는 배포하고 싶어요"
→ `docs/PRD_DEPLOYMENT_GUIDE.md` 또는 `docs/CLOUDFLARE_DEPLOYMENT.md`

### "나는 대시보드를 만들고 싶어요"
→ `dashboards/README.md` → `scripts/deploy-dashboards.js`

### "나는 코드를 이해하고 싶어요"
→ `domains/` → `CLAUDE.md`

### "나는 설정을 바꾸고 싶어요"
→ `.env.example` → `configs/fortigate-hec-setup.conf`

### "나는 파일 구조를 이해하고 싶어요"
→ `docs/FILE_ORGANIZATION.md` (16KB 상세 가이드)

---

## Git Workflow

### Current Branch Strategy

```bash
git status                    # 현재 변경사항 확인
git add .                     # 모든 변경사항 스테이징
git commit -m "feat: ..."     # 커밋 (Conventional Commits)
git push origin master        # Master 브랜치에 푸시
```

**Commit Convention**:
- `feat:` - 새로운 기능
- `fix:` - 버그 수정
- `docs:` - 문서 변경
- `refactor:` - 코드 리팩토링
- `chore:` - 빌드/설정 변경

---

## Version History

- **2025-10-21**: 프로젝트 구조화 완료 (깔끔한 디렉토리, Git 정리)
- **2025-10-20**: 대규모 정리 (legacy 파일 삭제)
- **2025-10-14**: 초기 프로젝트 구조 확립 (DDD Level 3)

---

**Last Updated**: 2025-10-21
**Total Directories**: 11
**Total Files**: 38
**Architecture**: Domain-Driven Design Level 3
**Dependencies**: 0 (Zero Dependencies)
