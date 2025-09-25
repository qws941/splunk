#!/bin/bash

# GitHub Secrets 자동 설정 스크립트
# Cloudflare 자동배포를 위한 필수 secrets 등록

echo "🔐 GitHub Secrets 설정 시작..."

# 필수 환경변수 설정
CLOUDFLARE_API_TOKEN="TmGwtpr-eAy6_xpz6oX7BRJensk5MGeYXaFC84zO"
CLOUDFLARE_ACCOUNT_ID="a8d9c67f586acdd15eebcc65ca3aa5bb"

# GitHub CLI 설치 확인
if ! command -v gh &> /dev/null; then
    echo "📦 GitHub CLI 설치 중..."

    # Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
        && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
        && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
        && sudo apt update \
        && sudo apt install gh -y
    fi

    # CentOS/RHEL/Fedora
    if command -v yum &> /dev/null; then
        sudo dnf install 'dnf-command(config-manager)' -y
        sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
        sudo dnf install gh -y
    fi

    # macOS
    if command -v brew &> /dev/null; then
        brew install gh
    fi
fi

echo "✅ GitHub CLI 준비 완료"

# GitHub 인증 상태 확인
if ! gh auth status &> /dev/null; then
    echo "🔑 GitHub 인증이 필요합니다."
    echo "다음 명령을 실행하여 인증하세요:"
    echo "gh auth login"
    exit 1
fi

echo "✅ GitHub 인증 확인됨"

# Repository 확인
if [ -z "$1" ]; then
    echo "❌ Repository 이름을 입력하세요."
    echo "사용법: $0 <owner/repo>"
    echo "예시: $0 jclee/splunk-dashboard"
    exit 1
fi

REPO=$1
echo "📂 Repository: $REPO"

# Secrets 설정
echo "🔐 GitHub Secrets 등록 중..."

# CLOUDFLARE_API_TOKEN 설정
echo "Setting CLOUDFLARE_API_TOKEN..."
echo -n "$CLOUDFLARE_API_TOKEN" | gh secret set CLOUDFLARE_API_TOKEN --repo="$REPO"
if [ $? -eq 0 ]; then
    echo "✅ CLOUDFLARE_API_TOKEN 설정 완료"
else
    echo "❌ CLOUDFLARE_API_TOKEN 설정 실패"
fi

# CLOUDFLARE_ACCOUNT_ID 설정
echo "Setting CLOUDFLARE_ACCOUNT_ID..."
echo -n "$CLOUDFLARE_ACCOUNT_ID" | gh secret set CLOUDFLARE_ACCOUNT_ID --repo="$REPO"
if [ $? -eq 0 ]; then
    echo "✅ CLOUDFLARE_ACCOUNT_ID 설정 완료"
else
    echo "❌ CLOUDFLARE_ACCOUNT_ID 설정 실패"
fi

# Secrets 확인
echo ""
echo "📋 설정된 Secrets 목록:"
gh secret list --repo="$REPO"

echo ""
echo "🚀 GitHub Secrets 설정 완료!"
echo ""
echo "이제 다음과 같이 자동배포가 작동합니다:"
echo "1. 코드 수정"
echo "2. git add . && git commit -m 'update'"
echo "3. git push origin main"
echo "4. 🎉 자동으로 https://splunk.jclee.me 에 배포!"
echo ""
echo "배포 상태 확인: https://github.com/$REPO/actions"