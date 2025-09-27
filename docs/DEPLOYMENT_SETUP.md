# 🚀 Cloudflare 자동 배포 구성 가이드

## 📋 필수 GitHub Secrets 설정

자동 배포를 위해 다음 GitHub Repository Secrets를 설정해야 합니다:

### 1. Cloudflare API 설정
```bash
CLOUDFLARE_API_TOKEN    # Cloudflare API 토큰 (Edit Cloudflare Workers:Edit 권한 필요)
CLOUDFLARE_ACCOUNT_ID   # Cloudflare 계정 ID: a8d9c67f586acdd15eebcc65ca3aa5bb
```

### 2. Slack 알림 설정 (선택사항)
```bash
SLACK_WEBHOOK_DEPLOY    # 배포 알림용 Slack Webhook URL
```

## 🔧 Cloudflare API 토큰 생성 방법

1. **Cloudflare Dashboard 접속**
   - https://dash.cloudflare.com/profile/api-tokens

2. **API 토큰 생성**
   - "Create Token" 클릭
   - "Custom token" 사용

3. **권한 설정**
   ```
   Permissions:
   - Account: Cloudflare Workers:Edit
   - Zone: Zone:Read
   - Zone: Page Rules:Edit (필요시)

   Account Resources:
   - Include: All accounts

   Zone Resources:
   - Include: Specific zone: jclee.me
   ```

4. **토큰 복사 및 저장**
   - 생성된 토큰을 GitHub Secrets에 `CLOUDFLARE_API_TOKEN`으로 저장

## 📄 현재 구성 정보

### Cloudflare Worker 설정
- **Worker Name**: `splunk`
- **Account ID**: `a8d9c67f586acdd15eebcc65ca3aa5bb`
- **Zone ID**: `ed060daac18345f6900fc5a661dc94f9`
- **Domain**: `splunk.jclee.me/*`

### GitHub Actions 워크플로우
- **파일**: `.github/workflows/deploy.yml`
- **트리거**: main 브랜치 push시 자동 실행
- **포함 경로**: `src/**`, `package.json`, `wrangler.toml`

### 배포 프로세스
1. 📥 코드 체크아웃
2. 🟢 Node.js 18 설정
3. 📦 의존성 설치
4. 🔍 ESLint 실행 (있는 경우)
5. 🧪 테스트 실행 (있는 경우)
6. 🚀 Cloudflare Workers 배포
7. ⏳ 배포 전파 대기 (15초)
8. 🏥 포괄적 헬스체크:
   - 메인 페이지 (/)
   - 헬스 엔드포인트 (/health)
   - API 엔드포인트 (/api/test)
9. 📊 배포 결과 요약

## 🧪 배포 테스트

### 로컬 테스트
```bash
# Wrangler를 사용한 로컬 배포 테스트
npx wrangler deploy --dry-run

# 실제 배포
npx wrangler deploy
```

### 자동 배포 트리거
```bash
# 변경사항 커밋 후 자동 배포
git add .
git commit -m "feat: update worker code"
git push origin main
```

### 수동 워크플로우 실행
- GitHub > Actions > "Splunk Fortinet Policy System Auto Deploy" > "Run workflow"

## 🔍 헬스체크 엔드포인트

배포 후 다음 엔드포인트들이 자동으로 테스트됩니다:

- **메인 페이지**: https://splunk.jclee.me/
- **헬스체크**: https://splunk.jclee.me/health
- **API 정보**: https://splunk.jclee.me/api/test

## 📞 문제 해결

### 일반적인 오류
1. **API 토큰 오류**: `CLOUDFLARE_API_TOKEN` 권한 확인
2. **배포 실패**: wrangler.toml 설정 확인
3. **헬스체크 실패**: 배포 전파 시간 부족 (대기 시간 증가 필요)

### 로그 확인
- GitHub Actions 로그: Repository > Actions > 해당 워크플로우 실행
- Cloudflare 로그: Dashboard > Workers & Pages > splunk > Logs

## 🎯 다음 단계

1. ✅ GitHub Secrets 설정 완료
2. ✅ 첫 번째 자동 배포 테스트
3. ✅ Slack 알림 설정 (선택사항)
4. ✅ 모니터링 및 알림 구성

---

**참고**: 이 설정은 Splunk-FortiNet 정책 확인 시스템의 완전 자동 배포를 위한 것입니다.