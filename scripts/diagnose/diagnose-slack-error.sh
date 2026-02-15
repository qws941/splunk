#!/bin/bash
# Diagnose Splunk Slack sendalert error code 1

echo "🔍 Splunk Slack Alert 에러 진단"
echo "=================================================="
echo ""

# 1. Check Splunk logs for sendalert errors
echo "📋 Step 1: Splunk 로그에서 sendalert 에러 확인"
echo "--------------------------------------------------"

if [ -d "/opt/splunk/var/log/splunk" ]; then
    echo "✅ Splunk 로그 디렉토리 접근 가능"
    echo ""
    echo "최근 sendalert 에러 (최근 100줄):"
    tail -100 /opt/splunk/var/log/splunk/splunkd.log | grep -i "sendalert\|alert.*error\|slack" | tail -20
else
    echo "❌ Splunk 로그 디렉토리 접근 불가: /opt/splunk/var/log/splunk"
    echo "   → Splunk가 설치되어 있는지 확인하세요."
fi

echo ""
echo ""

# 2. Check Slack plugin installation
echo "📦 Step 2: Slack Plugin 설치 확인"
echo "--------------------------------------------------"

SLACK_APP_DIR="/opt/splunk/etc/apps/slack_alerts"
if [ -d "$SLACK_APP_DIR" ]; then
    echo "✅ Slack App 디렉토리 존재: $SLACK_APP_DIR"

    # Check alert_actions.conf
    if [ -f "$SLACK_APP_DIR/local/alert_actions.conf" ]; then
        echo "✅ alert_actions.conf 존재"
        echo ""
        echo "설정 내용:"
        cat "$SLACK_APP_DIR/local/alert_actions.conf" | grep -v "^#" | grep -v "^$"
    else
        echo "❌ alert_actions.conf 없음: $SLACK_APP_DIR/local/alert_actions.conf"
        echo "   → Slack plugin 설정이 완료되지 않았습니다."
    fi

    echo ""

    # Check alert script
    ALERT_SCRIPT="$SLACK_APP_DIR/bin/slack.py"
    if [ -f "$ALERT_SCRIPT" ]; then
        echo "✅ Alert script 존재: $ALERT_SCRIPT"
        ls -lh "$ALERT_SCRIPT"
    else
        echo "❌ Alert script 없음: $ALERT_SCRIPT"
    fi
else
    echo "❌ Slack App 디렉토리 없음: $SLACK_APP_DIR"
    echo "   → Slack plugin이 설치되지 않았습니다."
    echo ""
    echo "💡 해결 방법:"
    echo "   1. Splunk Web UI → Settings → Apps → Find More Apps"
    echo "   2. 'Slack Notification Alert' 검색 및 설치"
fi

echo ""
echo ""

# 3. Check alert_actions.conf permissions
echo "🔐 Step 3: 파일 권한 확인"
echo "--------------------------------------------------"

if [ -f "$SLACK_APP_DIR/local/alert_actions.conf" ]; then
    ls -lh "$SLACK_APP_DIR/local/alert_actions.conf"

    if [ -f "$SLACK_APP_DIR/bin/slack.py" ]; then
        ls -lh "$SLACK_APP_DIR/bin/slack.py"

        # Check if executable
        if [ -x "$SLACK_APP_DIR/bin/slack.py" ]; then
            echo "✅ slack.py 실행 권한 있음"
        else
            echo "❌ slack.py 실행 권한 없음"
            echo "   → chmod +x $SLACK_APP_DIR/bin/slack.py"
        fi
    fi
fi

echo ""
echo ""

# 4. Common solutions
echo "💡 일반적인 해결 방법"
echo "=================================================="
echo ""
echo "1️⃣ Token 설정 확인"
echo "   Splunk Web UI → Settings → Alert actions → Slack"
echo "   - Token: xoxb-로 시작하는 Bot User OAuth Token"
echo "   - Channel: #splunk-alerts"
echo ""
echo "2️⃣ Bot 채널 초대"
echo "   Slack 채널에서: /invite @Splunk FortiGate Alert"
echo ""
echo "3️⃣ Splunk 재시작"
echo "   /opt/splunk/bin/splunk restart"
echo ""
echo "4️⃣ 로그 실시간 모니터링"
echo "   tail -f /opt/splunk/var/log/splunk/splunkd.log | grep -i slack"
echo ""
echo "5️⃣ 수동 테스트"
echo "   Splunk Search:"
echo "   | makeresults | sendalert slack param.channel=\"#splunk-alerts\" param.message=\"Test\""
echo ""
