/**
 * Enhanced Slack Webhook Handler with MITRE ATT&CK Integration
 *
 * Extends base SlackWebhookHandler with:
 * - MITRE ATT&CK context enrichment
 * - Alert throttling/deduplication
 * - Rich Slack blocks formatting
 * - Threat intelligence links
 *
 * Phase 2.3 - Advanced Slack Notifications
 */

import https from 'https';
import url from 'url';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class SlackWebhookHandlerEnhanced {
  constructor(webhookUrl = null) {
    this.webhookUrl = webhookUrl || process.env.SLACK_WEBHOOK_URL;
    this.enabled = !!this.webhookUrl;

    // Alert throttling configuration
    this.throttleWindow = 300000; // 5 minutes
    this.alertCache = new Map(); // { alertKey: lastSentTimestamp }

    // Load MITRE lookup table
    this.mitreLookup = this.loadMITRELookup();

    // Start cleanup interval (every 10 minutes)
    this.startCleanupInterval();
  }

  /**
   * Load MITRE ATT&CK lookup table from CSV
   */
  loadMITRELookup() {
    try {
      const lookupPath = path.join(__dirname, '../../lookups/fortinet_mitre_mapping.csv');
      const content = fs.readFileSync(lookupPath, 'utf-8');
      const lines = content.trim().split('\n');
      const headers = lines[0].split(',');

      const lookup = {};
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',');
        const logid = values[0];
        lookup[logid] = {
          event_type: values[1],
          tactic_id: values[2],
          tactic_name: values[3],
          technique_id: values[4],
          technique_name: values[5],
          description: values[6],
          severity: values[7]
        };
      }

      console.log(`✅ Loaded ${Object.keys(lookup).length} MITRE mappings`);
      return lookup;
    } catch (error) {
      console.error('⚠️ Failed to load MITRE lookup table:', error.message);
      return {};
    }
  }

  /**
   * Enrich event with MITRE ATT&CK context
   */
  enrichWithMITRE(logid) {
    if (!logid || !this.mitreLookup[logid]) {
      return null;
    }

    const mitre = this.mitreLookup[logid];
    return {
      tactic: mitre.tactic_name,
      tacticId: mitre.tactic_id,
      technique: mitre.technique_name,
      techniqueId: mitre.technique_id,
      description: mitre.description,
      severity: mitre.severity,
      tacticUrl: `https://attack.mitre.org/tactics/${mitre.tactic_id}/`,
      techniqueUrl: `https://attack.mitre.org/techniques/${mitre.technique_id}/`
    };
  }

  /**
   * Check if alert should be throttled
   */
  shouldThrottle(alertKey) {
    const now = Date.now();
    const lastSent = this.alertCache.get(alertKey);

    if (!lastSent) {
      return false; // First time, send
    }

    const elapsed = now - lastSent;
    if (elapsed < this.throttleWindow) {
      console.log(`🔕 Alert throttled: ${alertKey} (sent ${Math.floor(elapsed / 1000)}s ago)`);
      return true;
    }

    return false;
  }

  /**
   * Record alert sent timestamp
   */
  recordAlertSent(alertKey) {
    this.alertCache.set(alertKey, Date.now());
  }

  /**
   * Cleanup old cache entries (called every 10 minutes)
   */
  cleanupCache() {
    const now = Date.now();
    const expiredKeys = [];

    for (const [key, timestamp] of this.alertCache.entries()) {
      if (now - timestamp > this.throttleWindow * 2) {
        expiredKeys.push(key);
      }
    }

    expiredKeys.forEach(key => this.alertCache.delete(key));

    if (expiredKeys.length > 0) {
      console.log(`🧹 Cleaned ${expiredKeys.length} expired alert cache entries`);
    }
  }

  /**
   * Start cache cleanup interval
   */
  startCleanupInterval() {
    setInterval(() => this.cleanupCache(), 600000); // 10 minutes
  }

  /**
   * Send dashboard alert with MITRE context (enhanced)
   */
  async sendDashboardAlert(alert) {
    if (!this.enabled) {
      console.log('⚠️ Slack webhook not configured, skipping alert');
      return false;
    }

    const {
      message,
      severity = 'medium',
      logid = null,
      data = {},
      title = null
    } = alert;

    // Generate throttle key
    const throttleKey = `${severity}:${logid || message}`;
    if (this.shouldThrottle(throttleKey)) {
      return false; // Alert throttled
    }

    // Enrich with MITRE context
    const mitre = logid ? this.enrichWithMITRE(logid) : null;

    // Build rich Slack blocks payload
    const payload = this.buildRichPayload({
      message,
      severity,
      title,
      data,
      mitre
    });

    const success = await this.postToWebhook(payload);

    if (success) {
      this.recordAlertSent(throttleKey);
      console.log(`✅ Sent Slack alert: ${throttleKey}`);
    }

    return success;
  }

  /**
   * Build rich Slack blocks payload
   */
  buildRichPayload({ message, severity, title, data, mitre }) {
    const emoji = this.getSeverityEmoji(severity);
    const color = this.getSeverityColor(severity);

    const blocks = [];

    // Header block
    blocks.push({
      type: 'header',
      text: {
        type: 'plain_text',
        text: `${emoji} ${title || 'Fortinet Security Alert'}`,
        emoji: true
      }
    });

    // Message block
    blocks.push({
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: `*${severity.toUpperCase()} Alert*\n${message}`
      }
    });

    // MITRE ATT&CK context (if available)
    if (mitre) {
      blocks.push({
        type: 'section',
        fields: [
          {
            type: 'mrkdwn',
            text: `*MITRE Tactic*\n<${mitre.tacticUrl}|${mitre.tactic}>`
          },
          {
            type: 'mrkdwn',
            text: `*MITRE Technique*\n<${mitre.techniqueUrl}|${mitre.technique}>`
          },
          {
            type: 'mrkdwn',
            text: `*Technique ID*\n${mitre.techniqueId}`
          },
          {
            type: 'mrkdwn',
            text: `*Risk Level*\n${mitre.severity.toUpperCase()}`
          }
        ]
      });

      // MITRE description
      blocks.push({
        type: 'context',
        elements: [
          {
            type: 'mrkdwn',
            text: `_${mitre.description}_`
          }
        ]
      });
    }

    // Additional data fields
    if (Object.keys(data).length > 0) {
      const fields = Object.entries(data)
        .filter(([_, value]) => value !== undefined && value !== null)
        .slice(0, 10) // Max 10 fields for Slack blocks
        .map(([key, value]) => ({
          type: 'mrkdwn',
          text: `*${key}*\n${value}`
        }));

      if (fields.length > 0) {
        blocks.push({
          type: 'section',
          fields: fields
        });
      }
    }

    // Divider
    blocks.push({ type: 'divider' });

    // Footer context
    blocks.push({
      type: 'context',
      elements: [
        {
          type: 'mrkdwn',
          text: `🛡️ *Splunk FortiGate Dashboard* | ${new Date().toISOString()}`
        }
      ]
    });

    // Return payload with both blocks and fallback attachment
    return {
      text: `${emoji} ${title || 'Fortinet Security Alert'}`, // Fallback text
      blocks: blocks,
      attachments: [
        {
          color: color,
          footer: 'Splunk Dashboard',
          ts: Math.floor(Date.now() / 1000)
        }
      ]
    };
  }

  /**
   * Send config change alert with MITRE context
   */
  async sendConfigChangeAlert(change) {
    const { logid, admin, object, action, path } = change;

    return await this.sendDashboardAlert({
      title: '⚙️ Configuration Change Detected',
      message: `Administrator *${admin}* ${action} configuration object`,
      severity: this.getConfigChangeSeverity(action),
      logid: logid,
      data: {
        'Object': object,
        'Action': action,
        'Path': path,
        'Admin': admin,
        'Time': new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })
      }
    });
  }

  /**
   * Send critical security event alert with MITRE context
   */
  async sendCriticalEventAlert(event) {
    const { logid, severity, srcip, dstip, action, msg } = event;

    return await this.sendDashboardAlert({
      title: '🔴 Critical Security Event',
      message: msg || 'Critical security event detected',
      severity: severity || 'critical',
      logid: logid,
      data: {
        'Source IP': srcip,
        'Destination IP': dstip,
        'Action': action,
        'LogID': logid,
        'Time': new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })
      }
    });
  }

  /**
   * Send VPN change alert
   */
  async sendVPNChangeAlert(vpn) {
    const { logid, user, action, srcip, result } = vpn;

    const severity = result === 'failure' ? 'high' : 'medium';

    return await this.sendDashboardAlert({
      title: '🔐 VPN Access Event',
      message: `VPN ${action} attempt by *${user}*: ${result}`,
      severity: severity,
      logid: logid,
      data: {
        'User': user,
        'Action': action,
        'Result': result,
        'Source IP': srcip,
        'Time': new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })
      }
    });
  }

  /**
   * Send policy change alert
   */
  async sendPolicyChangeAlert(policy) {
    const { logid, policy_name, action, admin } = policy;

    return await this.sendDashboardAlert({
      title: '📋 Policy Change Detected',
      message: `Policy *${policy_name}* was ${action}`,
      severity: 'medium',
      logid: logid,
      data: {
        'Policy': policy_name,
        'Action': action,
        'Admin': admin,
        'Time': new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })
      }
    });
  }

  /**
   * Helper: Get severity emoji
   */
  getSeverityEmoji(severity) {
    const emojis = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🟢'
    };
    return emojis[severity] || '⚪';
  }

  /**
   * Helper: Get severity color (Slack attachment color)
   */
  getSeverityColor(severity) {
    const colors = {
      critical: '#DC4E41', // Red
      high: '#F8BE34',     // Orange
      medium: '#87CEEB',   // Light Blue
      low: '#53A051'       // Green
    };
    return colors[severity] || '#808080'; // Gray default
  }

  /**
   * Helper: Get config change severity
   */
  getConfigChangeSeverity(action) {
    if (action === 'deleted') return 'critical';
    if (action === 'edited') return 'high';
    return 'medium';
  }

  /**
   * Post payload to Slack webhook
   */
  postToWebhook(payload) {
    if (!this.enabled) {
      return Promise.resolve(false);
    }

    return new Promise((resolve, reject) => {
      try {
        const parsedUrl = new URL(this.webhookUrl);
        const options = {
          hostname: parsedUrl.hostname,
          path: parsedUrl.pathname + parsedUrl.search,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        };

        const req = https.request(options, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            if (res.statusCode === 200) {
              resolve(true);
            } else {
              console.error(`❌ Slack webhook error: ${res.statusCode} - ${data}`);
              resolve(false);
            }
          });
        });

        req.on('error', (error) => {
          const maskedUrl = this.webhookUrl.replace(/\/services\/.*/, '/services/***');
          console.error(`❌ Slack webhook request failed (${maskedUrl}):`, error.message);
          resolve(false);
        });

        req.write(JSON.stringify(payload));
        req.end();

      } catch (error) {
        console.error('❌ Slack webhook error:', error.message);
        resolve(false);
      }
    });
  }

  /**
   * Test webhook connection
   */
  async testConnection() {
    const payload = {
      text: '✅ Slack Webhook Test',
      blocks: [
        {
          type: 'header',
          text: {
            type: 'plain_text',
            text: '✅ Slack Integration Test',
            emoji: true
          }
        },
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: 'Splunk FortiGate Dashboard webhook is working correctly!'
          }
        },
        {
          type: 'context',
          elements: [
            {
              type: 'mrkdwn',
              text: `Test sent at: ${new Date().toISOString()}`
            }
          ]
        }
      ]
    };

    const success = await this.postToWebhook(payload);
    console.log(success ? '✅ Slack test successful' : '❌ Slack test failed');
    return success;
  }

  /**
   * Get statistics
   */
  getStats() {
    return {
      enabled: this.enabled,
      throttleWindow: this.throttleWindow,
      cachedAlerts: this.alertCache.size,
      mitreMappings: Object.keys(this.mitreLookup).length
    };
  }
}

export default SlackWebhookHandlerEnhanced;
