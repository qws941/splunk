/**
 * FortiAnalyzer to Splunk HEC Integration
 *
 * Purpose: FAZ 보안 이벤트 수집 → Splunk HEC 전송 → Slack 알림
 */

import http from 'http';
import FortiAnalyzerDirectConnector from './domains/integration/fortianalyzer-direct-connector.js';
import SplunkHECConnector from './domains/integration/splunk-api-connector.js';
import SlackConnector from './domains/integration/slack-connector.js';
import SecurityEventProcessor from './domains/security/security-event-processor.js';

class FAZSplunkIntegration {
  constructor() {
    this.faz = new FortiAnalyzerDirectConnector();
    this.splunk = new SplunkHECConnector();
    this.slack = new SlackConnector();
    this.processor = new SecurityEventProcessor();
    this.startTime = Date.now();
    this.metrics = {
      processedEvents: 0,
      criticalEvents: 0,
      highEvents: 0,
      mediumEvents: 0,
      lowEvents: 0,
      errorCount: 0,
      splunkSent: 0,
      slackNotifications: 0
    };
  }

  async initialize() {
    console.log('🚀 FAZ → Splunk HEC Integration 시작...\n');

    // 환경변수 확인
    this.checkEnvironmentVariables();

    // 커넥터 초기화
    await this.initializeConnectors();

    // 이벤트 처리 시작
    await this.startEventProcessing();
  }

  checkEnvironmentVariables() {
    const required = [
      'FAZ_HOST', 'FAZ_USERNAME', 'FAZ_PASSWORD',
      'SPLUNK_HEC_HOST', 'SPLUNK_HEC_PORT', 'SPLUNK_HEC_TOKEN',
      'SPLUNK_INDEX_FORTIGATE'
    ];

    const missing = required.filter(v => !process.env[v]);

    if (missing.length > 0) {
      console.error('❌ 필수 환경변수가 설정되지 않았습니다:');
      missing.forEach(v => console.error(`   - ${v}`));
      console.error('\n.env 파일을 확인하세요. (.env.example 참고)');
      process.exit(1);
    }

    console.log('✅ 환경변수 확인 완료\n');
  }

  async initializeConnectors() {
    try {
      console.log('🔌 커넥터 초기화 중...');

      // FortiAnalyzer 연결
      console.log('  - FortiAnalyzer 연결...');
      await this.faz.initialize();

      // Splunk HEC 연결
      console.log('  - Splunk HEC 연결...');
      await this.splunk.initialize();

      // Slack 연결
      console.log('  - Slack 연결...');
      await this.slack.initialize();

      // SecurityEventProcessor 초기화 (Splunk + Slack)
      console.log('  - SecurityEventProcessor 초기화...');
      await this.processor.initialize({
        splunkConnector: this.splunk,
        slackConnector: this.slack
      });

      console.log('✅ 모든 커넥터 초기화 완료\n');

    } catch (error) {
      console.error('❌ 커넥터 초기화 실패:', error.message);
      throw error;
    }
  }

  async startEventProcessing() {
    console.log('📊 이벤트 처리 시작\n');

    // FortiAnalyzer에서 보안 이벤트 수집 (1분마다)
    setInterval(async () => {
      try {
        const events = await this.faz.getSecurityEvents({
          timeRange: '-5m',
          limit: 100
        });

        if (events && events.length > 0) {
          console.log(`📥 ${events.length}개 이벤트 수신`);

          // SecurityEventProcessor로 처리
          // - 위험도 분석
          // - Splunk HEC 전송
          // - 임계치 초과 시 Slack 알림
          for (const event of events) {
            await this.processor.processEvent(event);
          }

          console.log(`✅ ${events.length}개 이벤트 처리 완료`);
        }

      } catch (error) {
        console.error('❌ 이벤트 처리 오류:', error.message);
      }
    }, 60000); // 1분마다 실행

    console.log('⏰ 이벤트 폴링 시작 (1분 간격)');
    console.log('🎯 Splunk HEC로 실시간 전송 중');
    console.log('📢 Critical/High 이벤트 → Slack 알림\n');
    console.log('Press Ctrl+C to stop\n');
  }

  async getStatus() {
    return {
      fortianalyzer: this.faz.getStatus(),
      splunk: this.splunk.getStatus ? this.splunk.getStatus() : { connected: true },
      slack: this.slack.getStatus(),
      processor: this.processor.getStats(),
      timestamp: new Date().toISOString()
    };
  }

  // Health Check Endpoint
  createHealthEndpoint() {
    const healthPort = process.env.HEALTH_CHECK_PORT || 8080;

    const server = http.createServer((req, res) => {
      // Health Check
      if (req.url === '/health' && req.method === 'GET') {
        const uptime = Math.floor((Date.now() - this.startTime) / 1000);
        const fazStatus = this.faz.getStatus();
        const slackStatus = this.slack.getStatus();
        const processorStats = this.processor.getStats();

        const health = {
          status: 'healthy',
          service: 'faz-splunk-integration',
          version: '1.0.0',
          uptime_seconds: uptime,
          timestamp: new Date().toISOString(),
          components: {
            fortianalyzer: {
              connected: fazStatus.authenticated || false,
              status: fazStatus.authenticated ? 'healthy' : 'degraded'
            },
            splunk: {
              connected: true,
              status: 'healthy'
            },
            slack: {
              connected: slackStatus.connected || false,
              status: slackStatus.connected ? 'healthy' : 'degraded'
            }
          },
          metrics: {
            processed_events: processorStats.processedCount || 0,
            critical_events: processorStats.criticalEvents || 0,
            high_events: processorStats.highEvents || 0,
            error_count: processorStats.errorCount || 0
          }
        };

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(health, null, 2));
        return;
      }

      // Metrics Endpoint (Prometheus format)
      if (req.url === '/metrics' && req.method === 'GET') {
        const processorStats = this.processor.getStats();
        const uptime = Math.floor((Date.now() - this.startTime) / 1000);

        const metrics = [
          '# HELP faz_splunk_uptime_seconds Service uptime in seconds',
          '# TYPE faz_splunk_uptime_seconds gauge',
          `faz_splunk_uptime_seconds ${uptime}`,
          '',
          '# HELP faz_splunk_processed_events_total Total processed events',
          '# TYPE faz_splunk_processed_events_total counter',
          `faz_splunk_processed_events_total ${processorStats.processedCount || 0}`,
          '',
          '# HELP faz_splunk_critical_events_total Critical events',
          '# TYPE faz_splunk_critical_events_total counter',
          `faz_splunk_critical_events_total ${processorStats.criticalEvents || 0}`,
          '',
          '# HELP faz_splunk_high_events_total High severity events',
          '# TYPE faz_splunk_high_events_total counter',
          `faz_splunk_high_events_total ${processorStats.highEvents || 0}`,
          '',
          '# HELP faz_splunk_error_count_total Total errors',
          '# TYPE faz_splunk_error_count_total counter',
          `faz_splunk_error_count_total ${processorStats.errorCount || 0}`,
          '',
          '# HELP faz_splunk_component_status Component health status (1=healthy, 0=unhealthy)',
          '# TYPE faz_splunk_component_status gauge',
          `faz_splunk_component_status{component="fortianalyzer"} ${this.faz.getStatus().authenticated ? 1 : 0}`,
          `faz_splunk_component_status{component="splunk"} 1`,
          `faz_splunk_component_status{component="slack"} ${this.slack.getStatus().connected ? 1 : 0}`,
          ''
        ].join('\n');

        res.writeHead(200, { 'Content-Type': 'text/plain; version=0.0.4' });
        res.end(metrics);
        return;
      }

      // 404 Not Found
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not Found' }));
    });

    server.listen(healthPort, () => {
      console.log(`🏥 Health endpoint: http://localhost:${healthPort}/health`);
      console.log(`📊 Metrics endpoint: http://localhost:${healthPort}/metrics\n`);
    });

    return server;
  }
}

// 메인 실행
async function main() {
  const integration = new FAZSplunkIntegration();

  try {
    // Health & Metrics 서버 시작
    integration.createHealthEndpoint();

    // 커넥터 및 이벤트 처리 시작
    await integration.initialize();

    // 상태 출력 (10초마다)
    setInterval(async () => {
      const status = await integration.getStatus();
      console.log('📊 현재 상태:');
      console.log(`   처리된 이벤트: ${status.processor.processedCount}`);
      console.log(`   Critical: ${status.processor.criticalEvents}`);
      console.log(`   High: ${status.processor.highEvents}`);
      console.log(`   오류: ${status.processor.errorCount}\n`);
    }, 10000);

  } catch (error) {
    console.error('❌ 실행 오류:', error);
    process.exit(1);
  }
}

// 프로세스 종료 처리
process.on('SIGINT', () => {
  console.log('\n\n👋 프로그램 종료 중...');
  process.exit(0);
});

// 실행
main();
