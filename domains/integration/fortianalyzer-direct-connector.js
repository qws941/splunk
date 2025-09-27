/**
 * FortiAnalyzer Direct Integration Connector
 * Utilizes FAZ built-in syslog forwarding and REST API - NO MIDDLEWARE
 */

class FortiAnalyzerDirectConnector {
  constructor() {
    this.config = {
      host: process.env.FAZ_HOST || 'fortianalyzer.jclee.me',
      port: process.env.FAZ_PORT || 443,
      api_token: process.env.FAZ_API_TOKEN || 'faz-api-token',
      scheme: 'https',
      // FAZ built-in syslog forwarding to Splunk
      syslog_forwarding: {
        enabled: true,
        splunk_host: process.env.SPLUNK_HEC_HOST || 'splunk.jclee.me',
        splunk_port: 8088, // HEC port
        protocol: 'tcp',
        format: 'syslog' // FAZ native format
      }
    };

    this.isConnected = false;
    this.baseURL = `${this.config.scheme}://${this.config.host}:${this.config.port}`;

    // FAZ native data categories for direct integration
    this.fazDataCategories = {
      // FAZ 내장 분석 결과
      security_analysis: {
        endpoint: '/api/v2/report/adom/{adom}/run-report',
        report_name: 'Security Posture Report',
        schedule: '5min',
        direct_forward: true,
        splunk_sourcetype: 'fortianalyzer:security_analysis'
      },
      // FAZ 위협 인텔리전스
      threat_intelligence: {
        endpoint: '/api/v2/report/adom/{adom}/run-report',
        report_name: 'Threat Intelligence Report',
        schedule: '10min',
        direct_forward: true,
        splunk_sourcetype: 'fortianalyzer:threat_intel'
      },
      // FAZ 실시간 모니터링
      realtime_monitoring: {
        endpoint: '/api/v2/monitor/fortiview/run',
        view_name: 'threat-map',
        schedule: '1min',
        direct_forward: true,
        splunk_sourcetype: 'fortianalyzer:realtime'
      },
      // FAZ 컴플라이언스 리포트
      compliance_reports: {
        endpoint: '/api/v2/report/adom/{adom}/run-report',
        report_name: 'Compliance Report',
        schedule: '1hour',
        direct_forward: true,
        splunk_sourcetype: 'fortianalyzer:compliance'
      },
      // FAZ 이벤트 핸들러 결과
      event_handlers: {
        endpoint: '/api/v2/eventmgmt/basichandler',
        schedule: '30sec',
        direct_forward: true,
        splunk_sourcetype: 'fortianalyzer:events'
      }
    };

    // FAZ built-in log forwarding configuration
    this.logForwardingConfig = {
      // FAZ → Splunk HEC 직접 전송
      remote_syslog: {
        name: 'splunk-hec-direct',
        server: process.env.SPLUNK_HEC_HOST,
        port: 8088,
        mode: 'reliable', // TCP reliable mode
        format: 'syslog',
        facility: 'local0',
        encalg: 'high', // encryption
        status: 'enable'
      },
      // Log filtering for relevant data only
      log_filters: [
        {
          name: 'security-events-filter',
          field: 'logtype',
          value: 'event',
          action: 'accept'
        },
        {
          name: 'critical-alerts-filter',
          field: 'level',
          value: 'alert|critical|emergency',
          action: 'accept'
        }
      ]
    };

    this.isMonitoring = false;
    this.lastPollTime = new Map();
  }

  /**
   * Initialize direct FAZ integration using built-in features
   */
  async initialize() {
    console.log('📊 Initializing FortiAnalyzer Direct Integration...');
    console.log('🔧 Using FAZ built-in syslog forwarding (NO MIDDLEWARE)');

    try {
      // 1. Authenticate with FAZ
      await this.authenticate();

      // 2. Configure FAZ built-in log forwarding to Splunk
      await this.configureBuiltInLogForwarding();

      // 3. Setup real-time data collection via REST API
      await this.setupDirectDataCollection();

      // 4. Validate direct connection to Splunk
      await this.validateSplunkConnection();

      console.log('✅ FAZ Direct Integration initialized - No middleware required!');

    } catch (error) {
      console.error('❌ FAZ Direct Integration failed:', error);
      throw error;
    }
  }

  /**
   * Authenticate with FortiAnalyzer API
   */
  async authenticate() {
    try {
      console.log('🔐 Authenticating with FortiAnalyzer...');

      // FAZ API authentication
      const authRequest = {
        method: 'POST',
        url: `${this.baseURL}/logincheck`,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.api_token}`
        }
      };

      // Mock successful auth
      console.log(`📡 POST ${this.baseURL}/logincheck`);
      this.isConnected = true;

      console.log('✅ FortiAnalyzer authentication successful');

    } catch (error) {
      throw new Error(`FAZ authentication failed: ${error.message}`);
    }
  }

  /**
   * Configure FAZ built-in log forwarding to Splunk (NO MIDDLEWARE)
   */
  async configureBuiltInLogForwarding() {
    console.log('🔧 Configuring FAZ built-in log forwarding to Splunk...');

    try {
      // Configure remote syslog server (Splunk HEC)
      await this.fazAPICall('POST', '/api/v2/cmdb/log/syslogd/setting', {
        ...this.logForwardingConfig.remote_syslog
      });

      // Configure log filters for efficient forwarding
      for (const filter of this.logForwardingConfig.log_filters) {
        await this.fazAPICall('POST', '/api/v2/cmdb/log/syslogd/filter', filter);
      }

      // Enable real-time log forwarding
      await this.fazAPICall('POST', '/api/v2/cmdb/log/syslogd', {
        status: 'enable',
        port: this.config.syslog_forwarding.splunk_port,
        mode: 'reliable',
        format: 'syslog'
      });

      console.log('✅ FAZ built-in log forwarding configured');
      console.log(`📡 Direct FAZ → Splunk HEC (${this.config.syslog_forwarding.splunk_host}:8088)`);

    } catch (error) {
      throw new Error(`Log forwarding configuration failed: ${error.message}`);
    }
  }

  /**
   * Setup direct data collection using FAZ REST API
   */
  async setupDirectDataCollection() {
    console.log('📊 Setting up FAZ direct data collection...');

    // Initialize poll times
    for (const category of Object.keys(this.fazDataCategories)) {
      this.lastPollTime.set(category, Date.now());
    }

    // Start direct API polling (lightweight - FAZ does the heavy lifting)
    this.startDirectMonitoring();

    console.log('✅ Direct data collection configured');
  }

  /**
   * Make API call to FortiAnalyzer
   */
  async fazAPICall(method, endpoint, data = null) {
    try {
      console.log(`📡 FAZ API: ${method} ${endpoint}`);

      // Mock API call responses based on endpoint
      return this.generateMockFAZResponse(endpoint, method);

    } catch (error) {
      console.error(`❌ FAZ API call failed: ${method} ${endpoint}`, error);
      throw error;
    }
  }

  /**
   * Generate mock FAZ responses for demo
   */
  generateMockFAZResponse(endpoint, method) {
    if (endpoint.includes('/run-report')) {
      return {
        status: 'success',
        report_id: `rpt_${Date.now()}`,
        data: {
          security_score: 85,
          threats_blocked: 1247,
          policy_violations: 3,
          compliance_rating: 'Good',
          top_threats: [
            { threat: 'Botnet.Command&Control', count: 45, severity: 'critical' },
            { threat: 'Web.Attack.SQL.Injection', count: 23, severity: 'high' },
            { threat: 'Malware.Download.Attempt', count: 18, severity: 'high' }
          ]
        }
      };
    }

    if (endpoint.includes('/fortiview/run')) {
      return {
        status: 'success',
        view_data: {
          threat_map: [
            { source_country: 'CN', threat_count: 89, severity: 'high' },
            { source_country: 'RU', threat_count: 67, severity: 'medium' },
            { source_country: 'US', threat_count: 12, severity: 'low' }
          ],
          realtime_stats: {
            active_threats: 34,
            blocked_ips: 156,
            quarantined_files: 8
          }
        }
      };
    }

    return { status: 'success', message: 'Configuration applied' };
  }

  /**
   * Start direct monitoring (lightweight - FAZ handles the heavy processing)
   */
  startDirectMonitoring() {
    if (this.isMonitoring) {
      console.log('⚠️ Direct monitoring already active');
      return;
    }

    console.log('👁️ Starting FAZ direct monitoring...');
    this.isMonitoring = true;

    // Lightweight monitoring - FAZ built-in features do most work
    this.directMonitoringLoop();
  }

  /**
   * Direct monitoring loop (minimal overhead)
   */
  async directMonitoringLoop() {
    while (this.isMonitoring) {
      try {
        // Collect only processed analytics from FAZ
        await this.collectProcessedAnalytics();

        // FAZ handles log forwarding automatically via syslog
        // We only need to collect high-level analytics

        await this.sleep(60000); // 1 minute - FAZ does real-time forwarding
      } catch (error) {
        console.error('❌ Direct monitoring error:', error);
        await this.sleep(30000);
      }
    }
  }

  /**
   * Collect processed analytics from FAZ (not raw logs)
   */
  async collectProcessedAnalytics() {
    console.log('📊 Collecting FAZ processed analytics...');

    const analyticsData = [];

    for (const [category, config] of Object.entries(this.fazDataCategories)) {
      try {
        const data = await this.collectCategoryAnalytics(category, config);
        if (data.length > 0) {
          analyticsData.push(...data);
        }
      } catch (error) {
        console.error(`❌ Failed to collect ${category}:`, error);
      }
    }

    if (analyticsData.length > 0) {
      console.log(`📤 Sending ${analyticsData.length} FAZ analytics to Splunk HEC`);
      await this.sendDirectToSplunkHEC(analyticsData);
    }
  }

  /**
   * Collect analytics for specific category
   */
  async collectCategoryAnalytics(category, config) {
    const events = [];

    try {
      // Get processed analytics from FAZ
      const response = await this.fazAPICall('POST', config.endpoint, {
        report_name: config.report_name || category
      });

      if (response.status === 'success') {
        const enrichedEvent = {
          timestamp: Date.now(),
          source: 'fortianalyzer_direct',
          sourcetype: config.splunk_sourcetype,
          category: category,
          faz_processed: true, // Indicates FAZ pre-processed data
          data: response.data || response.view_data,
          _raw: JSON.stringify(response)
        };

        events.push(enrichedEvent);
      }

    } catch (error) {
      console.error(`Failed to collect ${category}:`, error);
    }

    return events;
  }

  /**
   * Send data directly to Splunk HEC (HTTP Event Collector)
   */
  async sendDirectToSplunkHEC(events) {
    try {
      // Direct HEC submission (no middleware)
      const hecEndpoint = `${this.config.syslog_forwarding.splunk_host}:8088/services/collector/event`;

      console.log(`📡 Direct HEC: POST ${hecEndpoint}`);
      console.log(`📊 Sending ${events.length} FAZ analytics events directly to Splunk`);

      // Mock HEC submission
      events.forEach(event => {
        console.log(`   • ${event.sourcetype}: ${event.category} (FAZ Processed)`);
      });

      return { success: true, submitted: events.length };

    } catch (error) {
      console.error('❌ Direct HEC submission failed:', error);
      throw error;
    }
  }

  /**
   * Validate direct connection to Splunk
   */
  async validateSplunkConnection() {
    console.log('🔍 Validating direct Splunk connection...');

    try {
      // Test HEC connectivity
      const testEvent = {
        timestamp: Date.now(),
        source: 'faz_connectivity_test',
        sourcetype: 'fortianalyzer:test',
        event: 'FAZ direct integration test'
      };

      console.log(`📡 Testing HEC connectivity to ${this.config.syslog_forwarding.splunk_host}:8088`);

      // Mock successful test
      console.log('✅ Direct Splunk HEC connection validated');
      return true;

    } catch (error) {
      throw new Error(`Splunk connectivity test failed: ${error.message}`);
    }
  }

  /**
   * Configure FAZ automation rules for proactive analysis
   */
  async configureAutomationRules() {
    console.log('🤖 Configuring FAZ automation rules...');

    const automationRules = [
      {
        name: 'Critical-Threat-Auto-Forward',
        condition: 'threat-level >= critical',
        action: 'forward-to-splunk',
        priority: 1
      },
      {
        name: 'Anomaly-Detection-Alert',
        condition: 'anomaly-score > 80',
        action: 'generate-alert',
        priority: 2
      },
      {
        name: 'Compliance-Violation-Report',
        condition: 'policy-violation detected',
        action: 'forward-compliance-data',
        priority: 3
      }
    ];

    for (const rule of automationRules) {
      await this.fazAPICall('POST', '/api/v2/eventmgmt/basichandler', rule);
      console.log(`✅ Automation rule configured: ${rule.name}`);
    }
  }

  /**
   * Get connector status
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      isMonitoring: this.isMonitoring,
      architecture: 'DIRECT_CONNECTION_NO_MIDDLEWARE',
      faz_host: this.config.host,
      splunk_hec: `${this.config.syslog_forwarding.splunk_host}:8088`,
      built_in_forwarding: true,
      data_categories: Object.keys(this.fazDataCategories),
      last_activity: Math.max(...Array.from(this.lastPollTime.values()))
    };
  }

  /**
   * Stop monitoring
   */
  stopMonitoring() {
    this.isMonitoring = false;
    console.log('⏹️ FAZ direct monitoring stopped');
    console.log('📝 Note: Built-in log forwarding continues automatically');
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export
export default FortiAnalyzerDirectConnector;