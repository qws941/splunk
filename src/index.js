/**
 * Splunk Dashboard with MCP Slack Notification Integration
 * Main entry point for the notification system
 */

// Import notification modules
import MCPSlackHandler from './mcp-notification-handler.js';
import GrafanaLogMonitor from './grafana-monitor.js';
import DeploymentNotifier from './deployment-notifier.js';
import SlackChannelManager from './channel-manager.js';

// Import core security modules
import FortigateSplunkIntegration from './fortigate-splunk-integration.js';
import SplunkAPIConnector from './splunk-api-connector.js';
import SecurityEventProcessor from './security-event-processor.js';

// Import direct integration connectors (NO MIDDLEWARE)
import FortiManagerDirectConnector from './fortimanager-direct-connector.js';
import FortiAnalyzerDirectConnector from './fortianalyzer-direct-connector.js';

/**
 * Main Application Class
 */
/**
 * Splunk-Fortinet Ecosystem Direct Integration App
 * NO MIDDLEWARE - Direct connections only
 */
class SplunkFortinetEcosystemApp {
  constructor() {
    // Import all security modules
    this.FortigateSplunkIntegration = null;
    this.SplunkAPIConnector = null;
    this.SecurityEventProcessor = null;
    this.MCPSlackHandler = null;

    // Direct integration connectors (NO MIDDLEWARE)
    this.FortiManagerDirectConnector = null;
    this.FortiAnalyzerDirectConnector = null;

    // System state
    this.isInitialized = false;
    this.startTime = new Date();

    // Integration instances (Direct connections)
    this.integrations = {
      fortigateIntegration: null,
      splunkConnector: null,
      securityProcessor: null,
      slackHandler: null,
      // Direct connectors
      fmgDirectConnector: null,
      fazDirectConnector: null
    };
    
    // System metrics
    this.systemMetrics = {
      totalSecurityEvents: 0,
      criticalAlerts: 0,
      systemUptime: 0,
      lastEventProcessed: null
    };
  }

  /**
   * Initialize the complete security integration system
   */
  async initialize() {
    if (this.isInitialized) {
      console.log('⚠️ 시스템이 이미 초기화됨');
      return;
    }

    console.log('🚀 Splunk-Fortinet 생태계 직접 통합 시스템 초기화...');
    console.log('🔧 아키텍처: 직접 연결 (중간 서버 없음)');

    try {
      // 1. Load security modules
      await this.loadSecurityModules();
      
      // 2. Initialize Splunk connector
      console.log('📊 Step 1: Splunk API 커넥터 초기화...');
      await this.initializeSplunkConnector();
      
      // 3. Initialize FortiGate integration
      console.log('🔥 Step 2: FortiGate 통합 시스템 초기화...');
      await this.initializeFortiGateIntegration();
      
      // 4. Initialize security event processor
      console.log('🛡️ Step 3: 보안 이벤트 프로세서 초기화...');
      await this.initializeSecurityProcessor();
      
      // 5. Initialize Slack handler
      console.log('💬 Step 4: MCP Slack 핸들러 초기화...');
      await this.initializeSlackHandler();

      // 6. Initialize FMG Direct Connector (NO MIDDLEWARE)
      console.log('🏢 Step 5: FortiManager 직접 연결 초기화...');
      await this.initializeFMGDirectConnector();

      // 7. Initialize FAZ Direct Connector (NO MIDDLEWARE)
      console.log('📊 Step 6: FortiAnalyzer 직접 연결 초기화...');
      await this.initializeFAZDirectConnector();

      // 8. Start integrated security monitoring
      console.log('🔄 Step 7: 통합 보안 모니터링 시작...');
      await this.startIntegratedSecurityMonitoring();

      // 9. Send startup notification
      await this.sendStartupNotifications();
      
      this.isInitialized = true;
      console.log('✅ Splunk-FortiGate 보안 시스템 초기화 완료!');
      
    } catch (error) {
      console.error('❌ 보안 시스템 초기화 실패:', error);
      await this.handleInitializationError(error);
      throw error;
    }
  }

  /**
   * Load security modules
   */
  async loadSecurityModules() {
    try {
      // Use imported modules
      this.FortigateSplunkIntegration = FortigateSplunkIntegration;
      this.SplunkAPIConnector = SplunkAPIConnector;
      this.SecurityEventProcessor = SecurityEventProcessor;
      this.MCPSlackHandler = MCPSlackHandler;

      // Direct integration connectors (NO MIDDLEWARE)
      this.FortiManagerDirectConnector = FortiManagerDirectConnector;
      this.FortiAnalyzerDirectConnector = FortiAnalyzerDirectConnector;
      
      console.log('📦 보안 모듈 로드 완료');
    } catch (error) {
      throw new Error(`모듈 로드 실패: ${error.message}`);
    }
  }

  /**
   * Initialize Splunk API connector
   */
  async initializeSplunkConnector() {
    if (this.SplunkAPIConnector) {
      this.integrations.splunkConnector = new this.SplunkAPIConnector();
      await this.integrations.splunkConnector.initialize();
      console.log('✅ Splunk 커넥터 준비 완료');
    } else {
      throw new Error('SplunkAPIConnector 모듈을 찾을 수 없음');
    }
  }

  /**
   * Initialize FortiGate integration
   */
  async initializeFortiGateIntegration() {
    if (this.FortigateSplunkIntegration) {
      this.integrations.fortigateIntegration = new this.FortigateSplunkIntegration();
      await this.integrations.fortigateIntegration.initialize();
      console.log('✅ FortiGate 통합 준비 완료');
    } else {
      throw new Error('FortigateSplunkIntegration 모듈을 찾을 수 없음');
    }
  }

  /**
   * Initialize security event processor
   */
  async initializeSecurityProcessor() {
    if (this.SecurityEventProcessor) {
      this.integrations.securityProcessor = new this.SecurityEventProcessor();
      await this.integrations.securityProcessor.initialize(this.integrations);
      console.log('✅ 보안 이벤트 프로세서 준비 완료');
    } else {
      throw new Error('SecurityEventProcessor 모듈을 찾을 수 없음');
    }
  }

  /**
   * Initialize Slack handler
   */
  async initializeSlackHandler() {
    // Use existing MCP Slack handler from notification system
    if (typeof MCPSlackHandler !== 'undefined') {
      this.integrations.slackHandler = new MCPSlackHandler();
      console.log('✅ MCP Slack 핸들러 준비 완료');
    } else {
      console.warn('⚠️ MCP Slack 핸들러를 찾을 수 없음 - 알림 기능 제한됨');
    }
  }

  /**
   * Initialize FMG Direct Connector (NO MIDDLEWARE)
   */
  async initializeFMGDirectConnector() {
    if (this.FortiManagerDirectConnector) {
      this.integrations.fmgDirectConnector = new this.FortiManagerDirectConnector();
      await this.integrations.fmgDirectConnector.initialize();
      console.log('✅ FortiManager 직접 연결 준비 완료');
    } else {
      throw new Error('FortiManagerDirectConnector 모듈을 찾을 수 없음');
    }
  }

  /**
   * Initialize FAZ Direct Connector (NO MIDDLEWARE)
   */
  async initializeFAZDirectConnector() {
    if (this.FortiAnalyzerDirectConnector) {
      this.integrations.fazDirectConnector = new this.FortiAnalyzerDirectConnector();
      await this.integrations.fazDirectConnector.initialize();
      console.log('✅ FortiAnalyzer 직접 연결 준비 완료');
    } else {
      throw new Error('FortiAnalyzerDirectConnector 모듈을 찾을 수 없음');
    }
  }

  /**
   * Start integrated security monitoring for all Fortinet devices
   */
  async startIntegratedSecurityMonitoring() {
    console.log('🔗 통합 보안 모니터링 설정 중...');

    // 1. Connect FortiGate events to security processor
    if (this.integrations.fortigateIntegration && this.integrations.securityProcessor) {
      // Override the original event processing to use security processor
      const originalProcessEvents = this.integrations.fortigateIntegration.processSecurityEvents.bind(
        this.integrations.fortigateIntegration
      );

      this.integrations.fortigateIntegration.processSecurityEvents = async (events) => {
        // Send events to security processor with source identification
        if (events.length > 0) {
          const enrichedEvents = events.map(event => ({
            ...event,
            source_system: 'FortiGate',
            integration_type: 'direct_api'
          }));
          this.integrations.securityProcessor.addEvents(enrichedEvents);
          this.systemMetrics.totalSecurityEvents += events.length;
          this.systemMetrics.lastEventProcessed = Date.now();
        }
      };
      console.log('✅ FortiGate → 보안 프로세서 연결 완료');
    }

    // 2. Start FMG direct monitoring (Policy changes and admin activities)
    if (this.integrations.fmgDirectConnector) {
      console.log('🏢 FortiManager 직접 모니터링 시작...');
      // FMG connector handles its own event forwarding to Splunk HEC
    }

    // 3. Start FAZ direct monitoring (Security analytics and logs)
    if (this.integrations.fazDirectConnector) {
      console.log('📊 FortiAnalyzer 직접 모니터링 시작...');
      // FAZ connector uses built-in log forwarding to Splunk
    }

    // 4. Setup cross-system correlation
    await this.setupCrossSystemCorrelation();

    // 5. Start monitoring dashboard sync
    this.startIntegratedDashboardSync();

    console.log('🎯 통합 Fortinet 생태계 모니터링 활성화됨');
    console.log('📊 데이터 소스: FortiGate API + FMG JSON-RPC + FAZ 내장 전달');
  }

  /**
   * Setup cross-system correlation between FMG, FAZ, and FortiGate
   */
  async setupCrossSystemCorrelation() {
    console.log('🔄 교차 시스템 상관분석 설정...');

    // Create correlation rules between systems
    const correlationRules = {
      // Policy deployment correlation: FMG policy changes → FortiGate events
      policy_deployment: {
        fmg_event: 'policy_change',
        fortigate_expected: 'policy_update',
        correlation_window: 300000 // 5 minutes
      },
      // Security incident correlation: FAZ analysis → FortiGate blocks
      security_incident: {
        faz_event: 'threat_detected',
        fortigate_expected: 'traffic_blocked',
        correlation_window: 60000 // 1 minute
      },
      // Admin activity correlation: FMG admin → FortiGate config
      admin_correlation: {
        fmg_event: 'admin_login',
        fortigate_expected: 'config_change',
        correlation_window: 600000 // 10 minutes
      }
    };

    if (this.integrations.securityProcessor) {
      // Check if the security processor supports correlation rules
      if (typeof this.integrations.securityProcessor.configureCorrelationRules === 'function') {
        this.integrations.securityProcessor.configureCorrelationRules(correlationRules);
        console.log('✅ 교차 시스템 상관분석 규칙 적용됨');
      } else {
        console.log('ℹ️ 교차 시스템 상관분석 설정 (보안 프로세서에서 향후 지원 예정)');
      }
    }
  }

  /**
   * Start integrated dashboard synchronization
   */
  startIntegratedDashboardSync() {
    // Update security dashboard every 5 minutes
    setInterval(async () => {
      try {
        await this.updateIntegratedSecurityDashboard();
      } catch (error) {
        console.error('통합 대시보드 업데이트 실패:', error);
      }
    }, 300000); // 5 minutes

    console.log('📊 통합 Fortinet 대시보드 동기화 시작됨');
  }

  /**
   * Update integrated security dashboard with all Fortinet devices
   */
  async updateIntegratedSecurityDashboard() {
    if (!this.integrations.splunkConnector) return;

    try {
      // Get system metrics from Splunk (all Fortinet sources)
      const metrics = await this.integrations.splunkConnector.getSystemMetrics();

      // Get status from all direct connectors
      const systemStatus = {
        fortigate: this.integrations.fortigateIntegration?.getStatus() || {},
        fmg: this.integrations.fmgDirectConnector?.getStatus() || {},
        faz: this.integrations.fazDirectConnector?.getStatus() || {}
      };

      // Update dashboard with integrated security metrics
      const dashboardXML = this.generateIntegratedSecurityDashboardXML(metrics, systemStatus);

      await this.integrations.splunkConnector.createSecurityDashboard(
        'fortinet_ecosystem_realtime',
        dashboardXML
      );

      console.log('📊 통합 Fortinet 생태계 대시보드 업데이트 완료');
      console.log(`🔗 연결 상태: FG(${systemStatus.fortigate.isConnected || false}) FMG(${systemStatus.fmg.isConnected || false}) FAZ(${systemStatus.faz.isConnected || false})`);

    } catch (error) {
      console.error('통합 대시보드 업데이트 에러:', error);
    }
  }

  /**
   * Generate integrated Fortinet ecosystem security dashboard XML
   * @param {Object} metrics - System metrics
   * @param {Object} systemStatus - Status of all connectors
   */
  generateIntegratedSecurityDashboardXML(metrics, systemStatus) {
    return `
<dashboard version="1.1">
  <label>Fortinet Ecosystem Security Dashboard</label>
  <description>통합 Fortinet 생태계 실시간 보안 모니터링 (FortiGate + FortiManager + FortiAnalyzer)</description>

  <!-- System Status Row -->
  <row>
    <panel>
      <title>FortiGate 연결</title>
      <single>
        <search>
          <query>| makeresults | eval status="${systemStatus.fortigate.isConnected ? '연결됨' : '연결안됨'}"</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">none</option>
        <option name="colorBy">value</option>
      </single>
    </panel>

    <panel>
      <title>FortiManager 연결</title>
      <single>
        <search>
          <query>| makeresults | eval status="${systemStatus.fmg.isConnected ? '연결됨' : '연결안됨'}"</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">none</option>
      </single>
    </panel>

    <panel>
      <title>FortiAnalyzer 연결</title>
      <single>
        <search>
          <query>| makeresults | eval status="${systemStatus.faz.isConnected ? '연결됨' : '연결안됨'}"</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">none</option>
      </single>
    </panel>
  </row>

  <!-- Security Metrics Row -->
  <row>
    <panel>
      <title>전체 보안 이벤트</title>
      <single>
        <search>
          <query>
            (index=fortigate_security OR index=fortimanager_direct OR index=fortianalyzer_security) earliest=-1h
            | stats count
          </query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">none</option>
        <option name="colorBy">trend</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
      </single>
    </panel>

    <panel>
      <title>중요 정책 변경</title>
      <single>
        <search>
          <query>index=fortimanager_direct sourcetype="fortimanager:critical_policy" earliest=-1h | stats count</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">none</option>
        <option name="colorBy">value</option>
      </single>
    </panel>

    <panel>
      <title>위협 분석 결과</title>
      <single>
        <search>
          <query>index=fortianalyzer_security earliest=-1h | stats count</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">none</option>
      </single>
    </panel>
  </row>

  <!-- Cross-System Analysis Row -->
  <row>
    <panel>
      <title>Fortinet 시스템별 이벤트 분포</title>
      <chart>
        <search>
          <query>
            (index=fortigate_security OR index=fortimanager_direct OR index=fortianalyzer_security) earliest=-4h
            | eval system=case(
                index="fortigate_security", "FortiGate",
                index="fortimanager_direct", "FortiManager",
                index="fortianalyzer_security", "FortiAnalyzer"
              )
            | stats count by system
          </query>
          <refresh>60s</refresh>
        </search>
        <option name="charting.chart">pie</option>
      </chart>
    </panel>

    <panel>
      <title>통합 위협 상관분석</title>
      <table>
        <search>
          <query>
            (index=fortigate_security riskLevel=CRITICAL OR riskLevel=HIGH) OR
            (index=fortimanager_direct priority=critical) OR
            (index=fortianalyzer_security severity=high) earliest=-4h
            | eval threat_source=case(
                index="fortigate_security", "Network Traffic",
                index="fortimanager_direct", "Policy Management",
                index="fortianalyzer_security", "Security Analysis"
              )
            | stats count by threat_source, source_ip
            | sort -count | head 15
          </query>
          <refresh>60s</refresh>
        </search>
      </table>
    </panel>
  </row>

  <!-- Real-time Timeline Row -->
  <row>
    <panel>
      <title>통합 Fortinet 보안 이벤트 타임라인</title>
      <chart>
        <search>
          <query>
            (index=fortigate_security OR index=fortimanager_direct OR index=fortianalyzer_security) earliest=-2h
            | eval system=case(
                index="fortigate_security", "FortiGate",
                index="fortimanager_direct", "FortiManager",
                index="fortianalyzer_security", "FortiAnalyzer"
              )
            | timechart span=5m count by system
          </query>
          <refresh>30s</refresh>
        </search>
        <option name="charting.chart">area</option>
        <option name="charting.axisTitleY.text">이벤트 수</option>
      </chart>
    </panel>
  </row>

  <!-- Policy and Admin Activity Row -->
  <row>
    <panel>
      <title>최근 정책 변경 (FortiManager)</title>
      <table>
        <search>
          <query>
            index=fortimanager_direct sourcetype="fortimanager:critical_policy" earliest=-2h
            | table _time, policyid, name, action, srcaddr, dstaddr
            | sort -_time | head 10
          </query>
          <refresh>60s</refresh>
        </search>
      </table>
    </panel>

    <panel>
      <title>관리자 보안 활동</title>
      <table>
        <search>
          <query>
            index=fortimanager_direct sourcetype="fortimanager:admin_security" earliest=-2h
            | table _time, user, action, result, source_ip
            | sort -_time | head 10
          </query>
          <refresh>60s</refresh>
        </search>
      </table>
    </panel>
  </row>

  <!-- Device Status Row -->
  <row>
    <panel>
      <title>FortiGate 장치 상태</title>
      <table>
        <search>
          <query>
            index=fortimanager_direct sourcetype="fortimanager:device_status" earliest=-1h
            | stats latest(conn_status) as connection, latest(conf_status) as config by name, ip
            | sort name
          </query>
          <refresh>60s</refresh>
        </search>
      </table>
    </panel>
  </row>
</dashboard>`;
  }

  /**
   * Send startup notifications
   */
  async sendStartupNotifications() {
    const uptimeMinutes = Math.floor((Date.now() - this.startTime.getTime()) / 60000);

    const startupMessage = `🚀 **Splunk-Fortinet 생태계 통합 보안 시스템 가동**

✅ **시스템 상태**: 정상 가동 중
🏗️ **아키텍처**: 직접 연결 (중간 서버 없음)

📊 **연동 현황**:
  • Splunk Enterprise 연결: ✅
  • FortiGate 다중방화벽: ✅ (${this.getConnectedDeviceCount()}대)
  • FortiManager 직접 연결: ✅ (JSON-RPC)
  • FortiAnalyzer 직접 연결: ✅ (내장 전달)
  • 보안 이벤트 프로세서: ✅
  • MCP Slack 알림: ✅

🔥 **모니터링 대상**:
  • **FortiGate**: 실시간 보안 이벤트 및 위협 탐지
  • **FortiManager**: 정책 변경 및 관리자 활동 감사
  • **FortiAnalyzer**: 보안 분석 및 위협 인텔리전스

🛡️ **통합 보안 기능**:
  • 실시간 위협 탐지 및 분석
  • 교차 시스템 상관분석 (FG↔FMG↔FAZ)
  • 정책 변경 자동 추적 및 알림
  • 지능형 보안 이벤트 상관분석
  • 자동 보안 알림 (CRITICAL/HIGH 우선)
  • 통합 Fortinet 대시보드 실시간 동기화

📈 **데이터 흐름**:
  • FortiGate API → Splunk HEC (실시간)
  • FMG JSON-RPC → Splunk HEC (직접)
  • FAZ 내장 Syslog → Splunk HEC (내장)

⏰ **시작 시간**: ${this.startTime.toLocaleString('ko-KR')}

🎯 **완전한 Fortinet 생태계 보안 모니터링이 시작되었습니다!**
🔧 **NO MIDDLEWARE - 모든 연결이 직접 통신**`;

    // Send to security channels
    if (this.integrations.slackHandler) {
      await this.integrations.slackHandler.sendMessage('splunk', startupMessage);
      await this.integrations.slackHandler.sendMessage('safework', '🛡️ Splunk-Fortinet 생태계 통합 보안 시스템 가동 시작');
    }
  }

  /**
   * Handle system shutdown
   */
  async shutdown() {
    console.log('⏹️ Fortinet 생태계 통합 보안 시스템 종료 중...');

    // Send shutdown notification
    if (this.integrations.slackHandler) {
      await this.integrations.slackHandler.sendMessage('splunk',
        '⏹️ Splunk-Fortinet 생태계 통합 보안 시스템 정상 종료');
    }

    this.isInitialized = false;
  }

  /**
   * Get system status
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      architecture: 'DIRECT_CONNECTION_NO_MIDDLEWARE',
      startTime: this.startTime,
      uptime: Date.now() - this.startTime.getTime(),
      systemMetrics: this.systemMetrics,
      integrations: {
        splunkConnector: this.integrations.splunkConnector?.getStatus(),
        fortigateIntegration: this.integrations.fortigateIntegration?.getStatus(),
        securityProcessor: this.integrations.securityProcessor?.getStatus(),
        // Direct connectors (NO MIDDLEWARE)
        fmgDirectConnector: this.integrations.fmgDirectConnector?.getStatus(),
        fazDirectConnector: this.integrations.fazDirectConnector?.getStatus()
      },
      connectedDevices: this.getConnectedDeviceCount(),
      fortinetEcosystem: {
        fortigate: this.integrations.fortigateIntegration?.getStatus()?.isConnected || false,
        fortimanager: this.integrations.fmgDirectConnector?.getStatus()?.isConnected || false,
        fortianalyzer: this.integrations.fazDirectConnector?.getStatus()?.isConnected || false
      },
      lastHealthCheck: Date.now()
    };
  }

  /**
   * Handle initialization error
   * @param {Error} error - Initialization error
   */
  async handleInitializationError(error) {
    const errorMessage = `❌ **보안 시스템 초기화 실패**
🚨 Error: ${error.message}
🕐 Time: ${new Date().toLocaleString('ko-KR')}
🔧 시스템 관리자 확인 필요`;

    if (this.integrations.slackHandler) {
      try {
        await this.integrations.slackHandler.sendMessage('일반', errorMessage);
        await this.integrations.slackHandler.sendMessage('splunk', errorMessage);
      } catch (notificationError) {
        console.error('에러 알림 발송 실패:', notificationError);
      }
    }
  }

  /**
   * Get connected device count
   */
  getConnectedDeviceCount() {
    return this.integrations.fortigateIntegration?.deviceConnections?.size || 0;
  }

  /**
   * Manual security event injection (for testing)
   * @param {Object} testEvent - Test security event
   */
  async injectTestEvent(testEvent) {
    if (this.integrations.securityProcessor) {
      this.integrations.securityProcessor.addEvent(testEvent);
      console.log('🧪 테스트 보안 이벤트 주입됨');
    }
  }
}

// Export for use in other modules
export default SplunkFortinetEcosystemApp;

// Auto-initialize if running directly
if (typeof window === 'undefined' && typeof importScripts === 'undefined') {
  // Node.js or Worker environment - auto start
  const app = new SplunkFortinetEcosystemApp();
  app.initialize().catch(console.error);
}