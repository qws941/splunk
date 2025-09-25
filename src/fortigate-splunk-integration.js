/**
 * FortiGate-Splunk Integration Module
 * Handles multiple FortiGate devices and real-time security event processing
 */

class FortigateSplunkIntegration {
  constructor() {
    this.fortigateDevices = [
      {
        name: 'FortiGate-Main',
        ip: '192.168.1.1',
        port: 443,
        apiKey: process.env.FORTIGATE_API_KEY_MAIN || 'demo-key-main',
        vdoms: ['root', 'dmz', 'internal'],
        priority: 'critical',
        zones: ['internal', 'dmz', 'external']
      },
      {
        name: 'FortiGate-DMZ',
        ip: '192.168.1.2', 
        port: 443,
        apiKey: process.env.FORTIGATE_API_KEY_DMZ || 'demo-key-dmz',
        vdoms: ['root', 'dmz'],
        priority: 'high',
        zones: ['dmz', 'external']
      },
      {
        name: 'FortiGate-Branch',
        ip: '10.0.1.1',
        port: 443,
        apiKey: process.env.FORTIGATE_API_KEY_BRANCH || 'demo-key-branch',
        vdoms: ['root'],
        priority: 'medium',
        zones: ['internal', 'external']
      }
    ];

    this.deviceConnections = new Map();
    this.eventBuffer = [];
    this.isMonitoring = false;
    this.pollInterval = 30000; // 30 seconds
    this.lastPollTime = new Map();
    
    // Security event types to monitor
    this.monitoringTypes = {
      ips: {
        endpoint: '/api/v2/log/ips',
        priority: 90,
        filters: ['attack', 'anomaly', 'signature']
      },
      traffic: {
        endpoint: '/api/v2/log/traffic', 
        priority: 60,
        filters: ['denied', 'blocked']
      },
      auth: {
        endpoint: '/api/v2/log/auth',
        priority: 70,
        filters: ['failed', 'locked']
      },
      vpn: {
        endpoint: '/api/v2/log/vpn',
        priority: 65,
        filters: ['tunnel-down', 'auth-failed']
      },
      malware: {
        endpoint: '/api/v2/log/av',
        priority: 95,
        filters: ['infected', 'blocked']
      }
    };
  }

  /**
   * Initialize FortiGate integration system
   */
  async initialize() {
    console.log('🔥 Initializing FortiGate-Splunk integration...');
    
    try {
      // Test connections to all devices
      for (const device of this.fortigateDevices) {
        await this.testDeviceConnection(device);
      }
      
      console.log(`✅ Connected to ${this.deviceConnections.size} FortiGate devices`);
      
      // Start monitoring if initialization successful
      await this.startSecurityMonitoring();
      
    } catch (error) {
      console.error('❌ FortiGate integration initialization failed:', error);
      throw error;
    }
  }

  /**
   * Test connection to FortiGate device
   * @param {Object} device - Device configuration
   */
  async testDeviceConnection(device) {
    try {
      console.log(`🔍 Testing connection to ${device.name} (${device.ip})`);
      
      // In actual implementation, would make real API call
      const connectionTest = await this.makeFortiGateAPICall(device, '/api/v2/cmdb/system/status');
      
      if (connectionTest.success) {
        this.deviceConnections.set(device.name, {
          ...device,
          status: 'connected',
          lastSeen: Date.now(),
          version: connectionTest.data?.version || 'unknown'
        });
        
        console.log(`✅ ${device.name} connected successfully`);
      } else {
        throw new Error(`Connection failed: ${connectionTest.error}`);
      }
      
    } catch (error) {
      console.error(`❌ Failed to connect to ${device.name}:`, error.message);
      
      // Add as disconnected for monitoring
      this.deviceConnections.set(device.name, {
        ...device,
        status: 'disconnected',
        lastError: error.message,
        lastSeen: Date.now()
      });
    }
  }

  /**
   * Make API call to FortiGate device
   * @param {Object} device - Device configuration
   * @param {string} endpoint - API endpoint
   * @param {Object} params - Query parameters
   */
  async makeFortiGateAPICall(device, endpoint, params = {}) {
    try {
      const url = `https://${device.ip}:${device.port}${endpoint}`;
      const queryParams = new URLSearchParams({
        access_token: device.apiKey,
        vdom: device.vdoms[0], // Default to first VDOM
        ...params
      });

      // Simulate API call for demo
      console.log(`📡 API Call: ${device.name}${endpoint}`);
      
      // Mock successful response
      return {
        success: true,
        data: {
          version: '7.4.1',
          status: 'online',
          results: []
        }
      };
      
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Start security event monitoring
   */
  async startSecurityMonitoring() {
    if (this.isMonitoring) {
      console.log('⚠️ Security monitoring already running');
      return;
    }

    console.log('👁️ Starting FortiGate security monitoring...');
    this.isMonitoring = true;
    
    // Initialize last poll times
    for (const device of this.fortigateDevices) {
      this.lastPollTime.set(device.name, Date.now());
    }
    
    // Start monitoring loop
    this.monitoringLoop();
  }

  /**
   * Security monitoring loop
   */
  async monitoringLoop() {
    while (this.isMonitoring) {
      try {
        await this.pollSecurityEvents();
        await this.sleep(this.pollInterval);
      } catch (error) {
        console.error('❌ Monitoring loop error:', error);
        await this.sleep(10000); // Shorter retry interval
      }
    }
  }

  /**
   * Poll security events from all devices
   */
  async pollSecurityEvents() {
    console.log('🔍 Polling security events from FortiGate devices...');
    
    const allEvents = [];
    const now = Date.now();
    
    // Poll each device
    for (const device of this.fortigateDevices) {
      const deviceConnection = this.deviceConnections.get(device.name);
      
      if (!deviceConnection || deviceConnection.status !== 'connected') {
        console.warn(`⚠️ Skipping ${device.name} - not connected`);
        continue;
      }
      
      try {
        const deviceEvents = await this.pollDeviceEvents(device);
        allEvents.push(...deviceEvents);
        
        // Update last seen
        deviceConnection.lastSeen = now;
        
      } catch (error) {
        console.error(`❌ Failed to poll ${device.name}:`, error);
        deviceConnection.status = 'error';
        deviceConnection.lastError = error.message;
      }
    }
    
    // Process collected events
    if (allEvents.length > 0) {
      console.log(`📊 Collected ${allEvents.length} security events`);
      await this.processSecurityEvents(allEvents);
    }
  }

  /**
   * Poll security events from single device
   * @param {Object} device - Device configuration
   */
  async pollDeviceEvents(device) {
    const events = [];
    const lastPoll = this.lastPollTime.get(device.name);
    const timeFilter = Math.floor((Date.now() - lastPoll) / 1000); // seconds
    
    // Poll each event type
    for (const [eventType, config] of Object.entries(this.monitoringTypes)) {
      try {
        const eventData = await this.makeFortiGateAPICall(device, config.endpoint, {
          since: timeFilter,
          count: 100
        });
        
        if (eventData.success && eventData.data.results) {
          // Transform FortiGate logs to standardized format
          const transformedEvents = eventData.data.results.map(log => ({
            id: `${device.name}-${eventType}-${Date.now()}-${Math.random().toString(36)}`,
            timestamp: Date.now(),
            device: device.name,
            deviceIP: device.ip,
            type: eventType,
            priority: config.priority,
            sourceIP: log.srcip || 'unknown',
            targetIP: log.dstip || 'unknown',
            sourcePort: log.srcport || 0,
            targetPort: log.dstport || 0,
            protocol: log.proto || 'unknown',
            action: log.action || 'unknown',
            severity: this.determineSeverity(log, eventType),
            message: log.msg || log.logdesc || 'Security event detected',
            vdom: log.vd || device.vdoms[0],
            policyId: log.policyid || 0,
            service: log.service || 'unknown',
            app: log.app || 'unknown',
            rawLog: log
          }));
          
          events.push(...transformedEvents);
        }
      } catch (error) {
        console.error(`❌ Failed to poll ${eventType} events from ${device.name}:`, error);
      }
    }
    
    this.lastPollTime.set(device.name, Date.now());
    return events;
  }

  /**
   * Determine event severity based on log data
   * @param {Object} log - Raw FortiGate log
   * @param {string} eventType - Event type
   */
  determineSeverity(log, eventType) {
    // Critical severity conditions
    if (eventType === 'malware' || 
        (log.attack && log.attack.includes('critical')) ||
        (log.severity && parseInt(log.severity) >= 8)) {
      return 'CRITICAL';
    }
    
    // High severity conditions  
    if (eventType === 'ips' || 
        (log.attack && log.attack.includes('high')) ||
        (log.severity && parseInt(log.severity) >= 6)) {
      return 'HIGH';
    }
    
    // Medium severity
    if (log.severity && parseInt(log.severity) >= 4) {
      return 'MEDIUM';
    }
    
    return 'LOW';
  }

  /**
   * Process collected security events
   * @param {Array} events - Security events
   */
  async processSecurityEvents(events) {
    if (events.length === 0) return;
    
    console.log(`🛡️ Processing ${events.length} security events`);
    
    // Add to buffer for batch processing
    this.eventBuffer.push(...events);
    
    // Process high priority events immediately
    const criticalEvents = events.filter(e => e.severity === 'CRITICAL');
    const highEvents = events.filter(e => e.severity === 'HIGH');
    
    if (criticalEvents.length > 0) {
      console.log(`🚨 ${criticalEvents.length} CRITICAL events detected`);
      // These would be sent immediately to security processor
    }
    
    if (highEvents.length > 0) {
      console.log(`🔴 ${highEvents.length} HIGH severity events detected`);
    }
    
    // Trigger batch processing if buffer is full
    if (this.eventBuffer.length >= 100) {
      await this.flushEventBuffer();
    }
  }

  /**
   * Flush event buffer to security processor
   */
  async flushEventBuffer() {
    if (this.eventBuffer.length === 0) return;
    
    console.log(`📤 Flushing ${this.eventBuffer.length} events to security processor`);
    
    const events = [...this.eventBuffer];
    this.eventBuffer = [];
    
    // This would normally be sent to the security event processor
    // For now, just log the summary
    const summary = this.generateEventSummary(events);
    console.log('📊 Event Summary:', summary);
    
    return events;
  }

  /**
   * Generate event summary statistics
   * @param {Array} events - Events to summarize
   */
  generateEventSummary(events) {
    const summary = {
      total: events.length,
      byDevice: {},
      bySeverity: {},
      byType: {},
      timeRange: {
        start: Math.min(...events.map(e => e.timestamp)),
        end: Math.max(...events.map(e => e.timestamp))
      }
    };
    
    events.forEach(event => {
      // By device
      summary.byDevice[event.device] = (summary.byDevice[event.device] || 0) + 1;
      
      // By severity
      summary.bySeverity[event.severity] = (summary.bySeverity[event.severity] || 0) + 1;
      
      // By type
      summary.byType[event.type] = (summary.byType[event.type] || 0) + 1;
    });
    
    return summary;
  }

  /**
   * Stop security monitoring
   */
  stopSecurityMonitoring() {
    this.isMonitoring = false;
    console.log('⏹️ FortiGate security monitoring stopped');
  }

  /**
   * Get system status
   */
  getStatus() {
    const connectedDevices = Array.from(this.deviceConnections.values())
      .filter(device => device.status === 'connected');
    
    return {
      isMonitoring: this.isMonitoring,
      totalDevices: this.fortigateDevices.length,
      connectedDevices: connectedDevices.length,
      deviceStatus: Array.from(this.deviceConnections.entries()).map(([name, device]) => ({
        name,
        status: device.status,
        lastSeen: device.lastSeen,
        ip: device.ip
      })),
      eventBufferSize: this.eventBuffer.length,
      monitoringTypes: Object.keys(this.monitoringTypes),
      lastPoll: Math.max(...Array.from(this.lastPollTime.values()))
    };
  }

  /**
   * Get device connection info
   * @param {string} deviceName - Device name
   */
  getDeviceInfo(deviceName) {
    return this.deviceConnections.get(deviceName);
  }

  /**
   * Sleep utility
   * @param {number} ms - Milliseconds to sleep
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export
export default FortigateSplunkIntegration;