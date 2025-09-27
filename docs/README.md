# Splunk FortiManager Dashboard

🛡️ **Enterprise-grade FortiManager Security Operations Dashboard**

실시간 보안 모니터링 | 1,055개 디바이스 관리 | Splunk 통합

## 🚀 자동배포 설정

### Cloudflare Pages 배포
```bash
# 1. GitHub Repository 연결
# 2. 빌드 설정:
Build command: npm run pages:build
Build output directory: /dist
Root directory: /

# 3. 환경변수 설정:
NODE_ENV=production
```

### GitHub Secrets 설정
```bash
CLOUDFLARE_API_TOKEN=TmGwtpr-eAy6_xpz6oX7BRJensk5MGeYXaFC84zO
CLOUDFLARE_ACCOUNT_ID=a8d9c67f586acdd15eebcc65ca3aa5bb
```

## 🔄 배포 플로우

1. **코드 푸시** → main 브랜치
2. **자동 빌드** → GitHub Actions
3. **Cloudflare 배포** → Pages/Workers
4. **실시간 반영** → splunk.jclee.me

## 📊 주요 기능

- ✅ 3계층 방화벽 아키텍처 모니터링
- ✅ Policy Lookup 실시간 조회
- ✅ 1,055개 디바이스 통합 관리
- ✅ Splunk XML 다운로드
- ✅ 자동배포 시스템

## 🛠️ 개발환경

```bash
npm install          # 의존성 설치
npm run build        # 빌드
npm run pages:dev    # 로컬 개발서버
npm run deploy       # Workers 배포
```

## 📝 아키텍처

```
Internet → Perimeter FW → Internal FW → DMZ FW → Services
    ↓
FortiManager (1,055 devices) → Splunk HEC → Dashboard
```

Live Demo: **https://splunk.jclee.me** 🚀