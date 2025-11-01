/**
 * Cloudflare Worker - FAZ to Splunk HEC Integration
 *
 * Scheduled worker that runs every 1 minute to:
 * 1. Collect security events from FortiAnalyzer
 * 2. Process and enrich events
 * 3. Send to Splunk HEC
 * 4. Send critical alerts to Slack
 *
 * Deployment: wrangler publish
 * Logs: wrangler tail
 */

// =============================================================================
// Cloudflare Worker Event Handlers
// =============================================================================

/**
 * Scheduled Event Handler (Cron Triggers)
 * Runs every 1 minute as configured in wrangler.toml
 */
export default {
  async scheduled(event, env, ctx) {
    console.log('🕐 Cron trigger fired at:', new Date().toISOString());

    try {
      const processor = new FAZSplunkProcessor(env);
      await processor.processEvents();

      console.log('✅ Event processing completed successfully');
    } catch (error) {
      console.error('❌ Event processing failed:', error.message);
      console.error('Stack:', error.stack);

      // Send error notification to Slack if enabled
      if (env.SLACK_ENABLED === 'true' && env.SLACK_BOT_TOKEN) {
        await sendErrorNotification(env, error);
      }
    }
  },

  /**
   * HTTP Request Handler (for manual triggers and health checks)
   */
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Health check endpoint
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'healthy',
        service: 'faz-splunk-hec-integration',
        timestamp: new Date().toISOString(),
        environment: env.NODE_ENV || 'production'
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Manual trigger endpoint
    if (url.pathname === '/trigger' && request.method === 'POST') {
      try {
        const processor = new FAZSplunkProcessor(env);
        await processor.processEvents();

        return new Response(JSON.stringify({
          success: true,
          message: 'Event processing triggered successfully',
          timestamp: new Date().toISOString()
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }

    // Default response
    return new Response(JSON.stringify({
      service: 'FAZ to Splunk HEC Integration',
      version: '1.0.0',
      endpoints: {
        health: '/health',
        trigger: 'POST /trigger'
      }
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
};

// =============================================================================
// Main Processing Class
// =============================================================================

class FAZSplunkProcessor {
  constructor(env) {
    this.env = env;
    this.fazConnector = new FortiAnalyzerConnector(env);
    this.splunkConnector = new SplunkHECConnector(env);
    this.slackConnector = new SlackConnector(env);
    this.eventProcessor = new SecurityEventProcessor();
  }

  async processEvents() {
    const startTime = Date.now();
    console.log('🚀 Starting event processing...');

    // 1. Collect events from FortiAnalyzer
    const events = await this.fazConnector.fetchSecurityEvents();
    console.log(`📥 Collected ${events.length} events from FortiAnalyzer`);

    if (events.length === 0) {
      console.log('ℹ️  No new events to process');
      return;
    }

    // 2. Process and enrich events
    const processedEvents = [];
    const criticalEvents = [];

    for (const event of events) {
      const enrichedEvent = this.eventProcessor.processEvent(event);
      processedEvents.push(enrichedEvent);

      // Track critical events for alerting
      if (this.eventProcessor.shouldAlert(enrichedEvent)) {
        criticalEvents.push(enrichedEvent);
      }
    }

    console.log(`⚙️  Processed ${processedEvents.length} events`);
    console.log(`🚨 Found ${criticalEvents.length} critical events`);

    // 3. Send to Splunk HEC
    const splunkResult = await this.splunkConnector.sendEvents(processedEvents);
    console.log(`📤 Sent ${splunkResult.success} events to Splunk (${splunkResult.failed} failed)`);

    // 4. Send Slack alerts for critical events
    if (this.env.SLACK_ENABLED === 'true' && criticalEvents.length > 0) {
      await this.sendSlackAlerts(criticalEvents);
    }

    // 5. Log summary
    const duration = Date.now() - startTime;
    console.log(`✅ Processing completed in ${duration}ms`);
    console.log(`📊 Summary: ${events.length} collected, ${processedEvents.length} processed, ${criticalEvents.length} alerts`);
  }

  async sendSlackAlerts(events) {
    let sent = 0;
    let failed = 0;

    for (const event of events) {
      try {
        await this.slackConnector.sendSecurityAlert(event);
        sent++;
      } catch (error) {
        console.error(`❌ Failed to send Slack alert:`, error.message);
        failed++;
      }
    }

    console.log(`📢 Slack alerts: ${sent} sent, ${failed} failed`);
  }
}

// =============================================================================
// FortiAnalyzer Connector (Cloudflare Workers Compatible)
// =============================================================================

class FortiAnalyzerConnector {
  constructor(env) {
    this.host = env.FAZ_HOST;
    this.port = env.FAZ_PORT || '443';
    this.username = env.FAZ_USERNAME;
    this.password = env.FAZ_PASSWORD;
    this.sessionId = null;
  }

  async fetchSecurityEvents() {
    // Login to get session ID
    await this.login();

    // Calculate time range (last 1 minute)
    const now = Math.floor(Date.now() / 1000);
    const oneMinuteAgo = now - 60;

    // Fetch events
    const events = await this.getLogs({
      filter: [
        ['time', '>=', oneMinuteAgo],
        ['time', '<=', now],
        ['type', '==', 'traffic']
      ],
      limit: 100
    });

    // Logout
    await this.logout();

    return events;
  }

  async login() {
    const response = await fetch(`https://${this.host}:${this.port}/jsonrpc`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: 1,
        method: 'exec',
        params: [{
          url: '/sys/login/user',
          data: {
            user: this.username,
            passwd: this.password
          }
        }]
      })
    });

    const data = await response.json();

    if (data.result && data.result[0].status.code === 0) {
      this.sessionId = data.session;
      console.log('✅ FortiAnalyzer login successful');
    } else {
      throw new Error('FortiAnalyzer login failed');
    }
  }

  async getLogs(params) {
    const response = await fetch(`https://${this.host}:${this.port}/jsonrpc`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `APSCOOKIE_${this.port}=${this.sessionId}`
      },
      body: JSON.stringify({
        id: 2,
        method: 'get',
        params: [{
          url: '/logview/adom/root/logsearch',
          filter: params.filter,
          limit: params.limit || 100
        }],
        session: this.sessionId
      })
    });

    const data = await response.json();

    if (data.result && data.result[0].status.code === 0) {
      return data.result[0].data || [];
    }

    return [];
  }

  async logout() {
    await fetch(`https://${this.host}:${this.port}/jsonrpc`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `APSCOOKIE_${this.port}=${this.sessionId}`
      },
      body: JSON.stringify({
        id: 3,
        method: 'exec',
        params: [{ url: '/sys/logout' }],
        session: this.sessionId
      })
    });

    this.sessionId = null;
  }
}

// =============================================================================
// Splunk HEC Connector (Cloudflare Workers Compatible)
// =============================================================================

class SplunkHECConnector {
  constructor(env) {
    this.host = env.SPLUNK_HEC_HOST;
    this.port = env.SPLUNK_HEC_PORT || '8088';
    this.token = env.SPLUNK_HEC_TOKEN;
    this.scheme = env.SPLUNK_HEC_SCHEME || 'https';
    this.index = env.SPLUNK_INDEX_FORTIGATE || 'fortianalyzer';
  }

  async sendEvents(events) {
    const hecEvents = events.map(event => ({
      time: event.timestamp || Math.floor(Date.now() / 1000),
      source: 'fortianalyzer',
      sourcetype: 'fortigate:security',
      index: this.index,
      event: event
    }));

    const response = await fetch(`${this.scheme}://${this.host}:${this.port}/services/collector/event/1.0`, {
      method: 'POST',
      headers: {
        'Authorization': `Splunk ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: hecEvents.map(e => JSON.stringify(e)).join('\n')
    });

    const result = await response.json();

    return {
      success: result.code === 0 ? events.length : 0,
      failed: result.code === 0 ? 0 : events.length
    };
  }
}

// =============================================================================
// Slack Connector (Cloudflare Workers Compatible)
// =============================================================================

class SlackConnector {
  constructor(env) {
    this.token = env.SLACK_BOT_TOKEN;
    this.channel = env.SLACK_CHANNEL || 'splunk-alerts';
  }

  async sendSecurityAlert(event) {
    const severity = event.severity || 'medium';
    const color = this.getSeverityColor(severity);
    const emoji = this.getSeverityEmoji(severity);

    const message = {
      channel: this.channel,
      attachments: [{
        color: color,
        title: `${emoji} Security Alert: ${severity.toUpperCase()}`,
        text: event.message || 'Security event detected',
        fields: [
          { title: 'Event Type', value: event.event_type || 'Unknown', short: true },
          { title: 'Risk Score', value: `${event.risk_score || 0}/100`, short: true },
          { title: 'Source IP', value: event.source_ip || 'N/A', short: true },
          { title: 'Target IP', value: event.target_ip || event.dst_ip || 'N/A', short: true },
          { title: 'Timestamp', value: new Date(event.timestamp * 1000).toISOString(), short: false }
        ],
        footer: 'FortiAnalyzer → Splunk HEC',
        ts: event.timestamp || Math.floor(Date.now() / 1000)
      }]
    };

    const response = await fetch('https://slack.com/api/chat.postMessage', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(message)
    });

    const result = await response.json();

    if (!result.ok) {
      throw new Error(`Slack API error: ${result.error}`);
    }
  }

  getSeverityColor(severity) {
    const colors = {
      critical: '#DC4E41',
      high: '#F1813F',
      medium: '#F8BE34',
      low: '#53A051'
    };
    return colors[severity] || '#808080';
  }

  getSeverityEmoji(severity) {
    const emojis = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🟢'
    };
    return emojis[severity] || '⚪';
  }
}

// =============================================================================
// Security Event Processor (Same as existing)
// =============================================================================

class SecurityEventProcessor {
  processEvent(rawEvent) {
    const event = {
      ...rawEvent,
      timestamp: rawEvent.time || Math.floor(Date.now() / 1000),
      severity: this.calculateSeverity(rawEvent),
      risk_score: this.calculateRiskScore(rawEvent),
      event_type: this.classifyEventType(rawEvent)
    };

    return event;
  }

  calculateSeverity(event) {
    if (event.attack || event.virus || event.botnet) return 'critical';
    if (event.action === 'deny' || event.action === 'blocked') return 'high';
    if (event.level === 'warning') return 'medium';
    return 'low';
  }

  calculateRiskScore(event) {
    let score = 0;

    if (event.attack) score += 40;
    if (event.virus) score += 40;
    if (event.botnet) score += 30;
    if (event.action === 'deny' || event.action === 'blocked') score += 20;
    if (event.sentbyte > 1000000) score += 10; // > 1MB

    return Math.min(score, 100);
  }

  classifyEventType(event) {
    if (event.attack) return 'intrusion_attempt';
    if (event.virus) return 'malware_detected';
    if (event.botnet) return 'botnet_activity';
    if (event.action === 'deny') return 'policy_violation';
    return 'traffic';
  }

  shouldAlert(event) {
    if (event.severity === 'critical') return true;
    if (event.severity === 'high' && event.risk_score > 70) return true;

    const alwaysAlertTypes = ['intrusion_attempt', 'malware_detected', 'data_exfiltration'];
    if (alwaysAlertTypes.includes(event.event_type)) return true;

    return false;
  }
}

// =============================================================================
// Error Notification
// =============================================================================

async function sendErrorNotification(env, error) {
  try {
    const slackConnector = new SlackConnector(env);
    await fetch('https://slack.com/api/chat.postMessage', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.SLACK_BOT_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        channel: env.SLACK_CHANNEL,
        attachments: [{
          color: '#DC4E41',
          title: '🔴 Worker Error',
          text: `FAZ to Splunk HEC Worker encountered an error`,
          fields: [
            { title: 'Error', value: error.message, short: false },
            { title: 'Timestamp', value: new Date().toISOString(), short: true }
          ]
        }]
      })
    });
  } catch (notifError) {
    console.error('Failed to send error notification:', notifError.message);
  }
}
