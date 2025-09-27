/**
 * Security Event Processor
 * Intelligent correlation, scoring, and threat analysis
 */

class SecurityEventProcessor {
  constructor() {
    this.eventQueue = [];
    this.correlationWindow = 300000; // 5 minutes
    this.correlatedEvents = new Map();
    this.threatIntelligence = new Map();
    this.geoLocationCache = new Map();
    
    // Correlation rules for attack pattern detection
    this.correlationRules = [
      {
        id: 'brute_force_attack',
        name: 'Brute Force Attack Detection',
        conditions: {
          eventType: 'auth',
          action: 'failed',
          threshold: 5,
          timeWindow: 300 // 5 minutes
        },
        severity: 'HIGH',
        category: 'Authentication'
      },
      {
        id: 'port_scan_detection',
        name: 'Port Scan Detection',
        conditions: {
          eventType: 'traffic',
          uniquePorts: 10,
          timeWindow: 180 // 3 minutes
        },
        severity: 'MEDIUM',
        category: 'Network'
      },
      {
        id: 'malware_outbreak',
        name: 'Malware Outbreak',
        conditions: {
          eventType: 'malware',
          threshold: 3,
          timeWindow: 600 // 10 minutes
        },
        severity: 'CRITICAL',
        category: 'Malware'
      },
      {
        id: 'lateral_movement',
        name: 'Lateral Movement Detection',
        conditions: {
          multipleTargets: 5,
          sameSource: true,
          timeWindow: 900 // 15 minutes
        },
        severity: 'HIGH',
        category: 'Advanced Threat'
      }
    ];

    // Threat intelligence sources (mock data)
    this.initializeThreatIntelligence();
    
    this.isProcessing = false;
    this.processedCount = 0;
    this.alertCount = 0;
  }

  /**
   * Initialize security event processor
   * @param {Object} integrations - Integration instances
   */
  async initialize(integrations = {}) {
    console.log('🛡️ Initializing Security Event Processor...');
    
    this.integrations = integrations;
    this.isProcessing = true;
    
    // Start processing loop
    this.startProcessing();
    
    console.log('✅ Security Event Processor initialized');
  }

  /**
   * Initialize threat intelligence data
   */
  initializeThreatIntelligence() {
    // Mock threat intelligence data
    const maliciousIPs = [
      '203.0.113.45', '192.0.2.146', '198.51.100.78',
      '10.0.0.1', '172.16.0.1', '185.220.101.42'
    ];
    
    maliciousIPs.forEach(ip => {
      this.threatIntelligence.set(ip, {
        reputation: 'malicious',
        category: 'botnet',
        confidence: 85,
        lastSeen: Date.now() - Math.random() * 86400000,
        sources: ['threat_feed_1', 'abuse_ipdb']
      });
    });
    
    console.log(`📊 Loaded ${maliciousIPs.length} threat intelligence entries`);
  }

  /**
   * Add security event to processing queue
   * @param {Object} event - Security event
   */
  addEvent(event) {
    this.eventQueue.push({
      ...event,
      receivedTime: Date.now(),
      processed: false
    });
  }

  /**
   * Add multiple events to processing queue
   * @param {Array} events - Array of security events
   */
  addEvents(events) {
    events.forEach(event => this.addEvent(event));
    console.log(`📥 Added ${events.length} events to processing queue`);
  }

  /**
   * Start event processing loop
   */
  startProcessing() {
    console.log('🔄 Starting security event processing...');
    
    setInterval(() => {
      if (this.eventQueue.length > 0) {
        this.processEventBatch();
      }
    }, 10000); // Process every 10 seconds
    
    // Correlation analysis every minute
    setInterval(() => {
      this.runCorrelationAnalysis();
    }, 60000);
  }

  /**
   * Process batch of events
   */
  async processEventBatch() {
    const batchSize = Math.min(50, this.eventQueue.length);
    const batch = this.eventQueue.splice(0, batchSize);
    
    console.log(`⚙️ Processing batch of ${batch.length} security events`);
    
    for (const event of batch) {
      try {
        await this.processSecurityEvent(event);
        this.processedCount++;
      } catch (error) {
        console.error('❌ Error processing event:', error);
      }
    }
  }

  /**
   * Process individual security event
   * @param {Object} event - Security event to process
   */
  async processSecurityEvent(event) {
    // 1. Enrich event with additional data
    const enrichedEvent = await this.enrichEvent(event);
    
    // 2. Calculate security score
    enrichedEvent.securityScore = this.calculateSecurityScore(enrichedEvent);
    
    // 3. Classify threat level
    enrichedEvent.threatLevel = this.classifyThreatLevel(enrichedEvent);
    
    // 4. Check against threat intelligence
    enrichedEvent.threatIntel = await this.checkThreatIntelligence(enrichedEvent);
    
    // 5. Store for correlation analysis
    this.storeForCorrelation(enrichedEvent);
    
    // 6. Send to Splunk if high priority
    if (enrichedEvent.securityScore >= 70 || enrichedEvent.severity === 'CRITICAL') {
      await this.sendToSplunk(enrichedEvent);
    }
    
    // 7. Generate alerts if needed
    await this.generateAlerts(enrichedEvent);
    
    return enrichedEvent;
  }

  /**
   * Enrich event with additional context
   * @param {Object} event - Original event
   */
  async enrichEvent(event) {
    const enriched = { ...event };
    
    // Add geo-location data
    if (event.sourceIP) {
      enriched.geoData = await this.getGeoLocation(event.sourceIP);
    }
    
    // Add device context
    enriched.deviceContext = this.getDeviceContext(event.device);
    
    // Add time-based context
    enriched.timeContext = this.getTimeContext(event.timestamp);
    
    // Add network zone information
    enriched.networkZone = this.determineNetworkZone(event.sourceIP, event.targetIP);
    
    return enriched;
  }

  /**
   * Calculate security score (0-100)
   * @param {Object} event - Enriched event
   */
  calculateSecurityScore(event) {
    let score = 0;
    
    // Base score by event type
    const typeScores = {
      ips: 70,
      malware: 90,
      traffic: 30,
      auth: 40,
      vpn: 35
    };
    
    score += typeScores[event.type] || 20;
    
    // Severity multiplier
    const severityMultipliers = {
      'CRITICAL': 1.5,
      'HIGH': 1.2,
      'MEDIUM': 1.0,
      'LOW': 0.7
    };
    
    score *= severityMultipliers[event.severity] || 1.0;
    
    // Threat intelligence boost
    if (event.threatIntel && event.threatIntel.reputation === 'malicious') {
      score += 30;
    }
    
    // Geographic risk (external IPs from high-risk countries)
    if (event.geoData && event.geoData.riskLevel === 'high') {
      score += 20;
    }
    
    // Time-based factors (unusual hours)
    if (event.timeContext && event.timeContext.isOutsideBusinessHours) {
      score += 10;
    }
    
    // Network zone violations
    if (event.networkZone === 'external_to_internal') {
      score += 25;
    }
    
    return Math.min(100, Math.max(0, Math.round(score)));
  }

  /**
   * Classify threat level based on multiple factors
   * @param {Object} event - Enriched event
   */
  classifyThreatLevel(event) {
    if (event.securityScore >= 90) return 'CRITICAL';
    if (event.securityScore >= 70) return 'HIGH';
    if (event.securityScore >= 50) return 'MEDIUM';
    return 'LOW';
  }

  /**
   * Check event against threat intelligence
   * @param {Object} event - Event to check
   */
  async checkThreatIntelligence(event) {
    const intel = {
      sourceIP: this.threatIntelligence.get(event.sourceIP) || null,
      targetIP: this.threatIntelligence.get(event.targetIP) || null
    };
    
    if (intel.sourceIP || intel.targetIP) {
      return {
        reputation: intel.sourceIP?.reputation || intel.targetIP?.reputation,
        confidence: Math.max(intel.sourceIP?.confidence || 0, intel.targetIP?.confidence || 0),
        category: intel.sourceIP?.category || intel.targetIP?.category
      };
    }
    
    return null;
  }

  /**
   * Get geo-location data for IP address
   * @param {string} ip - IP address
   */
  async getGeoLocation(ip) {
    // Check cache first
    if (this.geoLocationCache.has(ip)) {
      return this.geoLocationCache.get(ip);
    }
    
    // Mock geo-location data
    const mockGeoData = {
      country: this.getMockCountry(ip),
      city: 'Unknown',
      lat: 0,
      lon: 0,
      riskLevel: this.getCountryRiskLevel(ip)
    };
    
    this.geoLocationCache.set(ip, mockGeoData);
    return mockGeoData;
  }

  /**
   * Get mock country for IP (simplified)
   * @param {string} ip - IP address
   */
  getMockCountry(ip) {
    const ipHash = ip.split('.').reduce((a, b) => a + parseInt(b), 0);
    const countries = ['US', 'CN', 'RU', 'KR', 'JP', 'DE', 'UK', 'FR'];
    return countries[ipHash % countries.length];
  }

  /**
   * Get country risk level
   * @param {string} ip - IP address
   */
  getCountryRiskLevel(ip) {
    const country = this.getMockCountry(ip);
    const highRiskCountries = ['CN', 'RU', 'IR', 'KP'];
    return highRiskCountries.includes(country) ? 'high' : 'medium';
  }

  /**
   * Get device context information
   * @param {string} deviceName - Device name
   */
  getDeviceContext(deviceName) {
    const deviceProfiles = {
      'FortiGate-Main': { role: 'perimeter', criticality: 'high', zone: 'dmz' },
      'FortiGate-DMZ': { role: 'dmz', criticality: 'high', zone: 'dmz' },
      'FortiGate-Branch': { role: 'branch', criticality: 'medium', zone: 'branch' }
    };
    
    return deviceProfiles[deviceName] || { role: 'unknown', criticality: 'low', zone: 'unknown' };
  }

  /**
   * Get time-based context
   * @param {number} timestamp - Event timestamp
   */
  getTimeContext(timestamp) {
    const eventTime = new Date(timestamp);
    const hour = eventTime.getHours();
    const dayOfWeek = eventTime.getDay();
    
    return {
      hour,
      dayOfWeek,
      isWeekend: dayOfWeek === 0 || dayOfWeek === 6,
      isOutsideBusinessHours: hour < 8 || hour > 18,
      isNightTime: hour < 6 || hour > 22
    };
  }

  /**
   * Determine network zone based on IP addresses
   * @param {string} sourceIP - Source IP
   * @param {string} targetIP - Target IP
   */
  determineNetworkZone(sourceIP, targetIP) {
    const isInternal = (ip) => {
      return ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.');
    };
    
    const sourceInternal = isInternal(sourceIP);
    const targetInternal = isInternal(targetIP);
    
    if (!sourceInternal && targetInternal) return 'external_to_internal';
    if (sourceInternal && !targetInternal) return 'internal_to_external';
    if (sourceInternal && targetInternal) return 'internal_to_internal';
    return 'external_to_external';
  }

  /**
   * Store event for correlation analysis
   * @param {Object} event - Enriched event
   */
  storeForCorrelation(event) {
    const correlationKey = `${event.sourceIP}_${event.type}`;
    
    if (!this.correlatedEvents.has(correlationKey)) {
      this.correlatedEvents.set(correlationKey, []);
    }
    
    this.correlatedEvents.get(correlationKey).push(event);
    
    // Clean old events (outside correlation window)
    const cutoffTime = Date.now() - this.correlationWindow;
    const events = this.correlatedEvents.get(correlationKey);
    const recentEvents = events.filter(e => e.timestamp >= cutoffTime);
    this.correlatedEvents.set(correlationKey, recentEvents);
  }

  /**
   * Run correlation analysis
   */
  async runCorrelationAnalysis() {
    console.log('🔗 Running correlation analysis...');
    
    for (const rule of this.correlationRules) {
      const matches = await this.checkCorrelationRule(rule);
      
      if (matches.length > 0) {
        await this.generateCorrelationAlert(rule, matches);
      }
    }
  }

  /**
   * Check specific correlation rule
   * @param {Object} rule - Correlation rule
   */
  async checkCorrelationRule(rule) {
    const matches = [];
    const cutoffTime = Date.now() - (rule.conditions.timeWindow * 1000);
    
    for (const [key, events] of this.correlatedEvents.entries()) {
      const recentEvents = events.filter(e => e.timestamp >= cutoffTime);
      
      if (this.evaluateRuleConditions(rule, recentEvents)) {
        matches.push({
          correlationKey: key,
          events: recentEvents,
          count: recentEvents.length
        });
      }
    }
    
    return matches;
  }

  /**
   * Evaluate rule conditions against events
   * @param {Object} rule - Correlation rule
   * @param {Array} events - Events to evaluate
   */
  evaluateRuleConditions(rule, events) {
    const conditions = rule.conditions;
    
    // Check event type filter
    if (conditions.eventType) {
      const filteredEvents = events.filter(e => e.type === conditions.eventType);
      if (filteredEvents.length < (conditions.threshold || 1)) {
        return false;
      }
    }
    
    // Check threshold
    if (conditions.threshold && events.length < conditions.threshold) {
      return false;
    }
    
    // Check unique ports (for port scan detection)
    if (conditions.uniquePorts) {
      const uniquePorts = new Set(events.map(e => e.targetPort)).size;
      if (uniquePorts < conditions.uniquePorts) {
        return false;
      }
    }
    
    // Check multiple targets (for lateral movement)
    if (conditions.multipleTargets) {
      const uniqueTargets = new Set(events.map(e => e.targetIP)).size;
      if (uniqueTargets < conditions.multipleTargets) {
        return false;
      }
    }
    
    return true;
  }

  /**
   * Generate correlation alert
   * @param {Object} rule - Triggered rule
   * @param {Array} matches - Matched event groups
   */
  async generateCorrelationAlert(rule, matches) {
    console.log(`🚨 Correlation alert: ${rule.name} (${matches.length} matches)`);
    
    for (const match of matches) {
      const alert = {
        id: `correlation_${rule.id}_${Date.now()}`,
        type: 'correlation',
        ruleName: rule.name,
        ruleId: rule.id,
        severity: rule.severity,
        category: rule.category,
        eventCount: match.count,
        correlationKey: match.correlationKey,
        events: match.events,
        timestamp: Date.now(),
        description: `${rule.name} detected: ${match.count} related events`
      };
      
      await this.generateAlerts(alert);
      this.alertCount++;
    }
  }

  /**
   * Send event to Splunk
   * @param {Object} event - Processed event
   */
  async sendToSplunk(event) {
    try {
      if (this.integrations.splunkConnector) {
        await this.integrations.splunkConnector.ingestSecurityEvents([event]);
      }
    } catch (error) {
      console.error('❌ Failed to send event to Splunk:', error);
    }
  }

  /**
   * Generate security alerts
   * @param {Object} event - Event or correlation alert
   */
  async generateAlerts(event) {
    // Send to Slack for high-priority events
    if (event.threatLevel === 'CRITICAL' || event.severity === 'CRITICAL') {
      await this.sendSlackAlert(event);
    }
    
    // Log alert
    console.log(`🚨 Security Alert [${event.severity || event.threatLevel}]: ${event.message || event.description}`);
  }

  /**
   * Send alert to Slack
   * @param {Object} event - Alert event
   */
  async sendSlackAlert(event) {
    try {
      if (this.integrations.slackHandler) {
        await this.integrations.slackHandler.sendSecurityAlert(event);
      }
    } catch (error) {
      console.error('❌ Failed to send Slack alert:', error);
    }
  }

  /**
   * Get processor status
   */
  getStatus() {
    return {
      isProcessing: this.isProcessing,
      queueLength: this.eventQueue.length,
      processedCount: this.processedCount,
      alertCount: this.alertCount,
      correlationEntries: this.correlatedEvents.size,
      threatIntelEntries: this.threatIntelligence.size,
      activeRules: this.correlationRules.length,
      lastProcessed: Date.now()
    };
  }

  /**
   * Stop processing
   */
  stop() {
    this.isProcessing = false;
    console.log('⏹️ Security Event Processor stopped');
  }
}

// Export
export default SecurityEventProcessor;