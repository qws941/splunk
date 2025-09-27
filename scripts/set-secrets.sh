#!/bin/bash

# 간단한 GitHub Secrets 설정 스크립트

export PATH="$HOME/.local/bin:$PATH"

echo "🔐 GitHub Secrets 설정"
echo ""

# 환경변수
CLOUDFLARE_API_TOKEN="TmGwtpr-eAy6_xpz6oX7BRJensk5MGeYXaFC84zO"
CLOUDFLARE_ACCOUNT_ID="a8d9c67f586acdd15eebcc65ca3aa5bb"

echo "GitHub에 로그인이 필요합니다."
echo "다음 명령을 실행하세요:"
echo ""
echo "gh auth login"
echo ""
echo "로그인 후 다음 명령들을 실행하세요:"
echo ""
echo "# Repository 이름을 설정하세요 (예: username/repo-name)"
echo "REPO=\"your-username/splunk-dashboard\""
echo ""
echo "# Secrets 설정"
echo "echo '$CLOUDFLARE_API_TOKEN' | gh secret set CLOUDFLARE_API_TOKEN --repo=\$REPO"
echo "echo '$CLOUDFLARE_ACCOUNT_ID' | gh secret set CLOUDFLARE_ACCOUNT_ID --repo=\$REPO"
echo ""
echo "# 설정 확인"
echo "gh secret list --repo=\$REPO"
echo ""
echo "🚀 완료되면 git push로 자동배포가 시작됩니다!"