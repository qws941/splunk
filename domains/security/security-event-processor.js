/**
 * Security Event Processor
 *
 * Core security domain module for processing and analyzing security events
 * from FortiGate, FortiManager, and FortiAnalyzer.
 *
 * Domain: Security
 * Purpose: Real-time security event processing, correlation, and alerting
 */

/**
 * Security Event Processor Class
 */
class SecurityEventProcessor {
  constructor() {
    // Event queue for processing
    this.eventQueue = [];
    this.processedEvents = [];

    // Event statistics
    this.stats = {
      totalEvents: 0,
      criticalEvents: 0,
      highEvents: 0,
      mediumEvents: 0,
      lowEvents: 0,
      processedCount: 0,
      errorCount: 0
    };

    // Correlation rules
    this.correlationRules = new Map();

    // Integration references
    this.integrations = null;

    // Processing state
    this.isInitialized = false;
    this.isProcessing = false;
    this.processingInterval = null;

    // Configuration
    this.config = {
      batchSize: 100,
      processingInterval: 5000, // 5 seconds
      maxQueueSize: 10000,
      alertThresholds: {
        critical: 10,
        high: 50,
        medium: 100
      }
    };
  }

  /**
   * Initialize the security event processor
   * @param {Object} integrations - Integration instances (Splunk, FortiManager, etc.)
   */
  async initialize(integrations = null) {
    if (this.isInitialized) {
      console.log('⚠️ Security Event Processor already initialized');
      return;
    }

    console.log('🛡️ Initializing Security Event Processor...');

    this.integrations = integrations;

    // Start automatic processing
    this.startProcessing();

    this.isInitialized = true;
    console.log('✅ Security Event Processor initialized');
  }

  /**
   * Start automatic event processing
   */
  startProcessing() {
    if (this.isProcessing) return;

    this.processingInterval = setInterval(() => {
      this.processEventBatch();
    }, this.config.processingInterval);

    this.isProcessing = true;
    console.log('🔄 Security event processing started');
  }

  /**
   * Stop automatic event processing
   */
  stopProcessing() {
    if (this.processingInterval) {
      clearInterval(this.processingInterval);
      this.processingInterval = null;
    }
    this.isProcessing = false;
    console.log('⏹️ Security event processing stopped');
  }

  /**
   * Add a single security event to the queue
   * @param {Object} event - Security event object
   */
  addEvent(event) {
    if (!event) return;

    // Enrich event with metadata
    const enrichedEvent = this.enrichEvent(event);

    // Check queue size
    if (this.eventQueue.length >= this.config.maxQueueSize) {
      console.warn('⚠️ Event queue full, dropping oldest events');
      this.eventQueue.splice(0, this.config.batchSize);
    }

    this.eventQueue.push(enrichedEvent);
    this.stats.totalEvents++;

    // Update severity counters
    this.updateSeverityStats(enrichedEvent);
  }

  /**
   * Add multiple security events to the queue
   * @param {Array} events - Array of security event objects
   */
  addEvents(events) {
    if (!Array.isArray(events)) return;

    events.forEach(event => this.addEvent(event));
    console.log(`📥 Added ${events.length} events to queue (Total: ${this.eventQueue.length})`);
  }

  /**
   * Enrich event with additional metadata
   * @param {Object} event - Raw event
   * @returns {Object} Enriched event
   */
  enrichEvent(event) {
    return {
      ...event,
      processed_at: Date.now(),
      event_id: this.generateEventId(),
      severity: event.severity || this.determineSeverity(event),
      risk_score: this.calculateRiskScore(event)
    };
  }

  /**
   * Determine event severity based on content
   * @param {Object} event - Event object
   * @returns {string} Severity level
   */
  determineSeverity(event) {
    // Basic severity determination logic
    if (event.riskLevel === 'CRITICAL' || event.priority === 'critical') {
      return 'critical';
    } else if (event.riskLevel === 'HIGH' || event.priority === 'high') {
      return 'high';
    } else if (event.riskLevel === 'MEDIUM' || event.priority === 'medium') {
      return 'medium';
    }
    return 'low';
  }

  /**
   * Calculate risk score for event
   * @param {Object} event - Event object
   * @returns {number} Risk score (0-100)
   */
  calculateRiskScore(event) {
    let score = 0;

    // Severity-based scoring
    if (event.severity === 'critical') score += 40;
    else if (event.severity === 'high') score += 30;
    else if (event.severity === 'medium') score += 20;
    else score += 10;

    // Event type scoring
    if (event.event_type === 'intrusion_attempt') score += 30;
    else if (event.event_type === 'malware_detected') score += 25;
    else if (event.event_type === 'policy_violation') score += 20;

    // Source reputation (if available)
    if (event.source_reputation === 'malicious') score += 20;

    return Math.min(score, 100);
  }

  /**
   * Update severity statistics
   * @param {Object} event - Event with severity
   */
  updateSeverityStats(event) {
    switch (event.severity) {
      case 'critical':
        this.stats.criticalEvents++;
        break;
      case 'high':
        this.stats.highEvents++;
        break;
      case 'medium':
        this.stats.mediumEvents++;
        break;
      default:
        this.stats.lowEvents++;
    }
  }

  /**
   * Process a batch of events
   */
  async processEventBatch() {
    if (this.eventQueue.length === 0) return;

    const batchSize = Math.min(this.config.batchSize, this.eventQueue.length);
    const batch = this.eventQueue.splice(0, batchSize);

    try {
      // Process each event in the batch
      for (const event of batch) {
        await this.processEvent(event);
      }

      this.stats.processedCount += batch.length;
      console.log(`✅ Processed ${batch.length} events (Queue: ${this.eventQueue.length})`);
    } catch (error) {
      console.error('❌ Batch processing error:', error);
      this.stats.errorCount++;
    }
  }

  /**
   * Process a single security event
   * @param {Object} event - Security event to process
   */
  async processEvent(event) {
    try {
      // Apply correlation rules
      const correlatedEvents = this.correlateEvent(event);

      // Check if event triggers alerts
      if (this.shouldAlert(event)) {
        await this.triggerAlert(event);
      }

      // Send to Splunk (if integration available)
      if (this.integrations?.splunkConnector) {
        await this.sendToSplunk(event);
      }

      // Store in processed events history
      this.processedEvents.push({
        ...event,
        correlated_events: correlatedEvents,
        processed: true
      });

      // Maintain processed events size
      if (this.processedEvents.length > 1000) {
        this.processedEvents.splice(0, 100);
      }
    } catch (error) {
      console.error('❌ Event processing error:', error);
      throw error;
    }
  }

  /**
   * Correlate event with other events
   * @param {Object} event - Event to correlate
   * @returns {Array} Correlated events
   */
  correlateEvent(event) {
    const correlated = [];

    // Check correlation rules
    for (const [ruleId, rule] of this.correlationRules) {
      const matches = this.processedEvents.filter(prevEvent => {
        return this.matchesCorrelationRule(event, prevEvent, rule);
      });

      if (matches.length > 0) {
        correlated.push(...matches);
      }
    }

    return correlated;
  }

  /**
   * Check if two events match a correlation rule
   * @param {Object} event1 - First event
   * @param {Object} event2 - Second event
   * @param {Object} rule - Correlation rule
   * @returns {boolean} True if events correlate
   */
  matchesCorrelationRule(event1, event2, rule) {
    // Time window check
    const timeDiff = Math.abs(event1.processed_at - event2.processed_at);
    if (timeDiff > rule.correlation_window) return false;

    // Event type matching
    if (rule.event_types) {
      if (!rule.event_types.includes(event1.event_type) ||
          !rule.event_types.includes(event2.event_type)) {
        return false;
      }
    }

    // Source IP matching (if specified)
    if (rule.match_source_ip && event1.source_ip !== event2.source_ip) {
      return false;
    }

    return true;
  }

  /**
   * Configure correlation rules
   * @param {Object} rules - Correlation rules configuration
   */
  configureCorrelationRules(rules) {
    if (!rules) return;

    Object.entries(rules).forEach(([ruleId, rule]) => {
      this.correlationRules.set(ruleId, rule);
    });

    console.log(`📋 Configured ${this.correlationRules.size} correlation rules`);
  }

  /**
   * Check if event should trigger an alert
   * @param {Object} event - Event to check
   * @returns {boolean} True if should alert
   */
  shouldAlert(event) {
    // Critical events always alert
    if (event.severity === 'critical') return true;

    // High severity with high risk score
    if (event.severity === 'high' && event.risk_score > 70) return true;

    // Specific event types always alert
    const alwaysAlertTypes = ['intrusion_attempt', 'malware_detected', 'data_exfiltration'];
    if (alwaysAlertTypes.includes(event.event_type)) return true;

    return false;
  }

  /**
   * Trigger security alert
   * @param {Object} event - Event that triggered alert
   */
  async triggerAlert(event) {
    console.log(`🚨 SECURITY ALERT: ${event.severity.toUpperCase()}`);
    console.log(`   Event Type: ${event.event_type}`);
    console.log(`   Risk Score: ${event.risk_score}`);
    console.log(`   Source: ${event.source_system || 'FortiAnalyzer'}`);

    // Send to Slack (if integration available)
    if (this.integrations?.slackConnector) {
      try {
        await this.integrations.slackConnector.sendSecurityAlert(event);
      } catch (error) {
        console.error('❌ Failed to send Slack alert:', error.message);
      }
    }
  }

  /**
   * Format alert message for Slack
   * @param {Object} event - Event to format
   * @returns {string} Formatted alert message
   */
  formatAlertMessage(event) {
    const emoji = event.severity === 'critical' ? '🔴' : '⚠️';
    return `${emoji} **Security Alert: ${event.severity.toUpperCase()}**

**Event Type**: ${event.event_type}
**Risk Score**: ${event.risk_score}/100
**Source System**: ${event.source_system || 'Unknown'}
**Time**: ${new Date(event.processed_at).toLocaleString()}

**Details**: ${JSON.stringify(event.details || {}, null, 2)}`;
  }

  /**
   * Send event to Splunk HEC
   * @param {Object} event - Event to send
   */
  async sendToSplunk(event) {
    try {
      if (!this.integrations?.splunkConnector) return;

      await this.integrations.splunkConnector.sendEvent({
        sourcetype: event.source_system || 'security:event',
        index: 'fortianalyzer',
        event: {
          ...event,
          timestamp: event.processed_at
        }
      });
    } catch (error) {
      console.error('❌ Failed to send event to Splunk:', error);
    }
  }

  /**
   * Generate unique event ID
   * @returns {string} Unique event ID
   */
  generateEventId() {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get processor status
   * @returns {Object} Status information
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      isProcessing: this.isProcessing,
      queueSize: this.eventQueue.length,
      stats: this.stats,
      correlationRules: this.correlationRules.size
    };
  }

  /**
   * Get current statistics
   * @returns {Object} Statistics
   */
  getStats() {
    return {
      ...this.stats,
      queueSize: this.eventQueue.length,
      processedHistorySize: this.processedEvents.length
    };
  }

  /**
   * Clear event queue and reset statistics
   */
  reset() {
    this.eventQueue = [];
    this.processedEvents = [];
    this.stats = {
      totalEvents: 0,
      criticalEvents: 0,
      highEvents: 0,
      mediumEvents: 0,
      lowEvents: 0,
      processedCount: 0,
      errorCount: 0
    };
    console.log('🔄 Security Event Processor reset');
  }

  /**
   * Shutdown processor
   */
  async shutdown() {
    console.log('⏹️ Shutting down Security Event Processor...');

    this.stopProcessing();

    // Process remaining events
    if (this.eventQueue.length > 0) {
      console.log(`📤 Processing ${this.eventQueue.length} remaining events...`);
      await this.processEventBatch();
    }

    this.isInitialized = false;
    console.log('✅ Security Event Processor shutdown complete');
  }
}

// Export the class
export default SecurityEventProcessor;
