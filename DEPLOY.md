# 🚀 자동배포 설정 가이드

## 1단계: GitHub CLI 설치 및 인증

```bash
# GitHub CLI 인증
gh auth login

# 브라우저에서 GitHub 로그인 후 토큰 인증
```

## 2단계: GitHub Repository 생성

```bash
# 새 Repository 생성
gh repo create splunk-dashboard --public

# 또는 기존 Repository 사용
```

## 3단계: GitHub Secrets 설정

```bash
# Repository 이름 설정 (본인의 username으로 변경)
export REPO="YOUR_USERNAME/splunk-dashboard"

# Cloudflare Secrets 등록
echo 'TmGwtpr-eAy6_xpz6oX7BRJensk5MGeYXaFC84zO' | gh secret set CLOUDFLARE_API_TOKEN --repo=$REPO
echo 'a8d9c67f586acdd15eebcc65ca3aa5bb' | gh secret set CLOUDFLARE_ACCOUNT_ID --repo=$REPO

# 설정 확인
gh secret list --repo=$REPO
```

## 4단계: 코드 Push 및 자동배포

```bash
# Git 초기화
git init
git add .
git commit -m "Initial commit: Splunk FortiManager Dashboard"

# Remote Repository 연결
git remote add origin https://github.com/YOUR_USERNAME/splunk-dashboard.git

# Push 및 자동배포 시작
git push -u origin main
```

## ✅ 자동배포 확인

- **배포 상태**: https://github.com/YOUR_USERNAME/splunk-dashboard/actions
- **라이브 사이트**: https://splunk.jclee.me
- **Workers 대시보드**: https://dash.cloudflare.com

## 🔄 이후 업데이트 방법

```bash
# 코드 수정 후
git add .
git commit -m "Update dashboard"
git push

# 자동으로 배포됩니다! 🎉
```

---

**필요한 Secrets:**
- `CLOUDFLARE_API_TOKEN`: TmGwtpr-eAy6_xpz6oX7BRJensk5MGeYXaFC84zO
- `CLOUDFLARE_ACCOUNT_ID`: a8d9c67f586acdd15eebcc65ca3aa5bb