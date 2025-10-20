/**
 * Slack Connector
 *
 * Domain: Integration
 * Purpose: Send security alerts to Slack channels
 */

import https from 'https';

class SlackConnector {
  constructor() {
    this.botToken = process.env.SLACK_BOT_TOKEN;
    this.channel = process.env.SLACK_CHANNEL || 'splunk-alerts';
    this.enabled = process.env.SLACK_ENABLED === 'true';
    this.hostname = 'slack.com';
  }

  /**
   * Initialize Slack connector
   */
  async initialize() {
    if (!this.enabled) {
      console.log('⚠️  Slack integration disabled');
      return;
    }

    if (!this.botToken) {
      console.error('❌ SLACK_BOT_TOKEN not configured');
      this.enabled = false;
      return;
    }

    console.log(`✅ Slack connector initialized (channel: ${this.channel})`);
  }

  /**
   * Send message to Slack channel
   * @param {string} channel - Channel name (optional, uses default if not provided)
   * @param {string} message - Message text (supports Markdown)
   */
  async sendMessage(channel = null, message) {
    if (!this.enabled) {
      console.log('⚠️  Slack disabled, message not sent');
      return false;
    }

    const targetChannel = channel || this.channel;

    try {
      const payload = {
        channel: targetChannel,
        text: message,
        mrkdwn: true
      };

      const response = await this.postToSlack('/api/chat.postMessage', payload);

      if (response.ok) {
        console.log(`📢 Slack message sent to #${targetChannel}`);
        return true;
      } else {
        console.error(`❌ Slack API error: ${response.error}`);
        return false;
      }

    } catch (error) {
      console.error('❌ Failed to send Slack message:', error.message);
      return false;
    }
  }

  /**
   * Send security alert to Slack
   * @param {Object} event - Security event object
   */
  async sendSecurityAlert(event) {
    const emoji = this.getSeverityEmoji(event.severity);
    const color = this.getSeverityColor(event.severity);

    const message = {
      channel: this.channel,
      attachments: [
        {
          color: color,
          title: `${emoji} Security Alert: ${event.severity.toUpperCase()}`,
          fields: [
            {
              title: 'Event Type',
              value: event.event_type || 'Unknown',
              short: true
            },
            {
              title: 'Risk Score',
              value: `${event.risk_score || 0}/100`,
              short: true
            },
            {
              title: 'Source IP',
              value: event.source_ip || 'N/A',
              short: true
            },
            {
              title: 'Target IP',
              value: event.target_ip || event.dst_ip || 'N/A',
              short: true
            },
            {
              title: 'Attack Name',
              value: event.attack_name || 'N/A',
              short: false
            },
            {
              title: 'Time',
              value: new Date(event.processed_at).toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }),
              short: false
            }
          ],
          footer: 'FortiAnalyzer → Splunk HEC',
          ts: Math.floor(event.processed_at / 1000)
        }
      ]
    };

    try {
      const response = await this.postToSlack('/api/chat.postMessage', message);

      if (response.ok) {
        console.log(`📢 Security alert sent to Slack (#${this.channel})`);
        return true;
      } else {
        console.error(`❌ Slack API error: ${response.error}`);
        return false;
      }

    } catch (error) {
      console.error('❌ Failed to send security alert:', error.message);
      return false;
    }
  }

  /**
   * Post data to Slack API
   * @param {string} path - API endpoint path
   * @param {Object} data - Payload data
   * @returns {Promise<Object>} API response
   */
  postToSlack(path, data) {
    return new Promise((resolve, reject) => {
      const payload = JSON.stringify(data);

      const options = {
        hostname: this.hostname,
        path: path,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          'Authorization': `Bearer ${this.botToken}`
        }
      };

      const req = https.request(options, (res) => {
        let responseData = '';

        res.on('data', (chunk) => {
          responseData += chunk;
        });

        res.on('end', () => {
          try {
            const response = JSON.parse(responseData);
            resolve(response);
          } catch (error) {
            reject(new Error(`Failed to parse Slack response: ${error.message}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      req.write(payload);
      req.end();
    });
  }

  /**
   * Get emoji for severity level
   * @param {string} severity - Severity level
   * @returns {string} Emoji
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
   * Get color code for severity level
   * @param {string} severity - Severity level
   * @returns {string} Hex color code
   */
  getSeverityColor(severity) {
    const colors = {
      critical: '#FF0000',  // Red
      high: '#FF8800',      // Orange
      medium: '#FFDD00',    // Yellow
      low: '#00AA00'        // Green
    };
    return colors[severity] || '#CCCCCC';
  }

  /**
   * Get connector status
   * @returns {Object} Status information
   */
  getStatus() {
    return {
      enabled: this.enabled,
      channel: this.channel,
      configured: !!this.botToken
    };
  }
}

export default SlackConnector;
