#!/usr/bin/env node

/**
 * Slack Alert CLI Tool
 * Purpose: Send alerts from Splunk dashboard to Slack via command line
 * Usage: node slack-alert-cli.js --webhook=URL --message="Alert message" --severity=high [--data=JSON]
 */

import SlackWebhookHandler from '../domains/integration/slack-webhook-handler.js';

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {
    webhook: null,
    message: null,
    severity: 'medium',
    data: {}
  };

  args.forEach(arg => {
    const [key, value] = arg.split('=');
    const cleanKey = key.replace(/^--/, '');

    if (cleanKey === 'webhook') {
      parsed.webhook = value;
    } else if (cleanKey === 'message') {
      parsed.message = value;
    } else if (cleanKey === 'severity') {
      parsed.severity = value;
    } else if (cleanKey === 'data') {
      try {
        parsed.data = JSON.parse(value);
      } catch {
        console.error('❌ Invalid JSON data');
      }
    } else if (cleanKey === 'test') {
      parsed.test = true;
    }
  });

  return parsed;
}

// Display usage help
function showHelp() {
  console.log(`
📢 Slack Alert CLI Tool
========================

사용법:
  node slack-alert-cli.js --webhook=URL --message="메시지" [옵션]

필수 파라미터:
  --webhook=URL         Slack Webhook URL
  --message="메시지"    전송할 알람 메시지

선택 파라미터:
  --severity=LEVEL      심각도 (critical|high|medium|low) [기본값: medium]
  --data=JSON           추가 데이터 (JSON 형식)
  --test                연결 테스트만 수행

예제:
  # 기본 알람 전송
  node slack-alert-cli.js \\
    --webhook="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \\
    --message="설정 변경 감지" \\
    --severity=high

  # 추가 데이터 포함
  node slack-alert-cli.js \\
    --webhook="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \\
    --message="방화벽 정책 변경" \\
    --severity=critical \\
    --data='{"장비":"FW-01","관리자":"admin","작업":"삭제"}'

  # 연결 테스트
  node slack-alert-cli.js \\
    --webhook="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \\
    --test

환경 변수:
  SLACK_WEBHOOK_URL     Webhook URL을 환경 변수로 설정 가능
  `);
}

// Main function
async function main() {
  const args = parseArgs();

  // Show help if no arguments
  if (process.argv.length <= 2) {
    showHelp();
    process.exit(0);
  }

  // Get webhook URL from args or environment
  const webhookUrl = args.webhook || process.env.SLACK_WEBHOOK_URL;

  if (!webhookUrl) {
    console.error('❌ Slack Webhook URL이 설정되지 않았습니다.');
    console.error('   --webhook 파라미터 또는 SLACK_WEBHOOK_URL 환경 변수를 설정하세요.\n');
    showHelp();
    process.exit(1);
  }

  // Initialize handler
  const handler = new SlackWebhookHandler(webhookUrl);

  console.log('🔧 Slack Webhook Handler 초기화...');
  console.log(`   Webhook: ${handler.maskWebhookUrl(webhookUrl)}`);

  // Test mode
  if (args.test) {
    console.log('\n🧪 연결 테스트 중...');
    const success = await handler.testConnection();
    process.exit(success ? 0 : 1);
  }

  // Validate message
  if (!args.message) {
    console.error('\n❌ --message 파라미터가 필요합니다.\n');
    showHelp();
    process.exit(1);
  }

  // Send alert
  console.log('\n📢 Slack 알람 전송 중...');
  console.log(`   Message: ${args.message}`);
  console.log(`   Severity: ${args.severity}`);
  if (Object.keys(args.data).length > 0) {
    console.log(`   Data: ${JSON.stringify(args.data)}`);
  }

  try {
    const success = await handler.sendDashboardAlert({
      message: args.message,
      severity: args.severity,
      data: args.data
    });

    if (success) {
      console.log('\n✅ Slack 알람 전송 성공');
      process.exit(0);
    } else {
      console.error('\n❌ Slack 알람 전송 실패');
      process.exit(1);
    }
  } catch (error) {
    console.error('\n❌ 오류 발생:', error.message);
    process.exit(1);
  }
}

// Run
main().catch(error => {
  console.error('❌ Unexpected error:', error);
  process.exit(1);
});
