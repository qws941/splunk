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

/**
 * Main Application Class
 */
/**
 * Splunk-FortiGate Security Integration App
 */
class SplunkFortiGateSecurityApp {
  constructor() {
    // Import all security modules
    this.FortigateSplunkIntegration = null;
    this.SplunkAPIConnector = null;
    this.SecurityEventProcessor = null;
    this.MCPSlackHandler = null;
    
    // System state
    this.isInitialized = false;
    this.startTime = new Date();
    
    // Integration instances
    this.integrations = {
      fortigateIntegration: null,
      splunkConnector: null,
      securityProcessor: null,
      slackHandler: null
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

    console.log('🚀 Splunk-FortiGate 보안 통합 시스템 초기화...');

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
      
      // 6. Start security monitoring
      console.log('🔄 Step 5: 보안 모니터링 시작...');
      await this.startSecurityMonitoring();
      
      // 7. Send startup notification
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
   * Start security monitoring
   */
  async startSecurityMonitoring() {
    // Set up event flow: FortiGate → Security Processor → Splunk + Slack
    
    // Connect FortiGate events to security processor
    if (this.integrations.fortigateIntegration && this.integrations.securityProcessor) {
      // Override the original event processing to use security processor
      const originalProcessEvents = this.integrations.fortigateIntegration.processSecurityEvents.bind(
        this.integrations.fortigateIntegration
      );
      
      this.integrations.fortigateIntegration.processSecurityEvents = async (events) => {
        // Send events to security processor instead of direct processing
        if (events.length > 0) {
          this.integrations.securityProcessor.addEvents(events);
          this.systemMetrics.totalSecurityEvents += events.length;
          this.systemMetrics.lastEventProcessed = Date.now();
        }
      };
      
      console.log('🔗 FortiGate → 보안 프로세서 연결 완료');
    }
    
    // Start monitoring dashboard sync
    this.startDashboardSync();
    
    console.log('👁️ 실시간 보안 모니터링 시작됨');
  }

  /**
   * Start dashboard synchronization
   */
  startDashboardSync() {
    // Update security dashboard every 5 minutes
    setInterval(async () => {
      try {
        await this.updateSecurityDashboard();
      } catch (error) {
        console.error('대시보드 업데이트 실패:', error);
      }
    }, 300000); // 5 minutes
  }

  /**
   * Update security dashboard
   */
  async updateSecurityDashboard() {
    if (!this.integrations.splunkConnector) return;
    
    try {
      // Get system metrics from Splunk
      const metrics = await this.integrations.splunkConnector.getSystemMetrics();
      
      // Update dashboard with latest security metrics
      const dashboardXML = this.generateSecurityDashboardXML(metrics);
      
      await this.integrations.splunkConnector.createSecurityDashboard(
        'fortigate_security_realtime',
        dashboardXML
      );
      
      console.log('📊 보안 대시보드 업데이트 완료');
      
    } catch (error) {
      console.error('대시보드 업데이트 에러:', error);
    }
  }

  /**
   * Generate security dashboard XML
   * @param {Object} metrics - System metrics
   */
  generateSecurityDashboardXML(metrics) {
    return `
<dashboard version="1.1">
  <label>FortiGate Real-time Security Dashboard</label>
  <description>실시간 보안 위협 모니터링 및 분석</description>
  
  <row>
    <panel>
      <title>보안 이벤트 현황</title>
      <single>
        <search>
          <query>index=fortigate_security earliest=-1h | stats count</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">none</option>
        <option name="colorBy">trend</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
      </single>
    </panel>
    
    <panel>
      <title>중요 보안 알림</title>
      <single>
        <search>
          <query>index=fortigate_security riskLevel=CRITICAL earliest=-1h | stats count</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">none</option>
        <option name="colorBy">value</option>
      </single>
    </panel>
    
    <panel>
      <title>차단된 위협</title>
      <single>
        <search>
          <query>index=fortigate_security action=blocked earliest=-1h | stats count</query>
          <refresh>30s</refresh>
        </search>
      </single>
    </panel>
  </row>
  
  <row>
    <panel>
      <title>상위 공격 소스 IP</title>
      <table>
        <search>
          <query>
            index=fortigate_security riskLevel=CRITICAL OR riskLevel=HIGH earliest=-4h 
            | stats count by source_ip, geoData.country 
            | sort -count | head 10
          </query>
          <refresh>60s</refresh>
        </search>
      </table>
    </panel>
    
    <panel>
      <title>보안 이벤트 타입별 분포</title>
      <chart>
        <search>
          <query>
            index=fortigate_security earliest=-4h 
            | stats count by type 
            | sort -count
          </query>
          <refresh>60s</refresh>
        </search>
        <option name="charting.chart">pie</option>
      </chart>
    </panel>
  </row>
  
  <row>
    <panel>
      <title>실시간 보안 이벤트 타임라인</title>
      <chart>
        <search>
          <query>
            index=fortigate_security earliest=-2h 
            | timechart span=5m count by riskLevel
          </query>
          <refresh>30s</refresh>
        </search>
        <option name="charting.chart">area</option>
        <option name="charting.axisTitleY.text">이벤트 수</option>
      </chart>
    </panel>
  </row>
  
  <row>
    <panel>
      <title>FortiGate 디바이스별 보안 상태</title>
      <table>
        <search>
          <query>
            index=fortigate_security earliest=-1h 
            | stats count as total_events, 
              sum(eval(if(riskLevel="CRITICAL",1,0))) as critical_events,
              sum(eval(if(riskLevel="HIGH",1,0))) as high_events
              by device 
            | eval risk_percentage=round((critical_events+high_events)*100/total_events,2)
            | sort -risk_percentage
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
    
    const startupMessage = `🚀 **Splunk-FortiGate 보안 시스템 가동**

✅ **시스템 상태**: 정상 가동 중
📊 **연동 현황**:
  • Splunk Enterprise 연결: ✅
  • FortiGate 다중방화벽: ✅ (${this.getConnectedDeviceCount()}대)
  • 보안 이벤트 프로세서: ✅
  • MCP Slack 알림: ✅

🔥 **모니터링 대상**:
  • FortiGate-Main (192.168.1.1)
  • FortiGate-DMZ (192.168.1.2)  
  • FortiGate-Branch (10.0.1.1)

🛡️ **보안 기능**:
  • 실시간 위협 탐지 및 분석
  • 지능형 보안 이벤트 상관분석
  • 자동 보안 알림 (CRITICAL/HIGH 우선)
  • Splunk 대시보드 실시간 동기화

⏰ **시작 시간**: ${this.startTime.toLocaleString('ko-KR')}

🎯 **보안 모니터링이 시작되었습니다!**`;

    // Send to security channels
    if (this.integrations.slackHandler) {
      await this.integrations.slackHandler.sendMessage('splunk', startupMessage);
      await this.integrations.slackHandler.sendMessage('safework', '🛡️ Splunk-FortiGate 보안 시스템 가동 시작');
    }
  }

  /**
   * Handle system shutdown
   */
  async shutdown() {
    console.log('⏹️ 보안 시스템 종료 중...');
    
    // Send shutdown notification
    if (this.integrations.slackHandler) {
      await this.integrations.slackHandler.sendMessage('splunk', 
        '⏹️ Splunk-FortiGate 보안 시스템 정상 종료');
    }
    
    this.isInitialized = false;
  }

  /**
   * Get system status
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      startTime: this.startTime,
      uptime: Date.now() - this.startTime.getTime(),
      systemMetrics: this.systemMetrics,
      integrations: {
        splunkConnector: this.integrations.splunkConnector?.getStatus(),
        fortigateIntegration: this.integrations.fortigateIntegration?.getStatus(),
        securityProcessor: this.integrations.securityProcessor?.getStatus()
      },
      connectedDevices: this.getConnectedDeviceCount(),
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
export default SplunkFortiGateSecurityApp;

// Auto-initialize if running directly
if (typeof window === 'undefined' && typeof importScripts === 'undefined') {
  // Node.js or Worker environment - auto start
  const app = new SplunkFortiGateSecurityApp();
  app.initialize().catch(console.error);
}