/**
 * Slack Webhook Handler
 * Domain: Integration
 * Purpose: Send alerts from Splunk dashboard to Slack via Webhook
 */

import https from 'https';

class SlackWebhookHandler {
  constructor(webhookUrl = null) {
    this.webhookUrl = webhookUrl || process.env.SLACK_WEBHOOK_URL;
    this.enabled = !!this.webhookUrl;
  }

  /**
   * Set Slack Webhook URL
   * @param {string} webhookUrl - Slack Webhook URL
   */
  setWebhookUrl(webhookUrl) {
    this.webhookUrl = webhookUrl;
    this.enabled = !!this.webhookUrl;
  }

  /**
   * Send dashboard alert to Slack
   * @param {Object} alert - Alert data
   * @param {string} alert.message - Alert message
   * @param {string} alert.severity - Severity level (critical/high/medium/low)
   * @param {Object} alert.data - Additional data (optional)
   * @returns {Promise<boolean>} Success status
   */
  async sendDashboardAlert(alert) {
    if (!this.enabled) {
      console.log('⚠️  Slack Webhook not configured');
      return false;
    }

    const { message, severity = 'medium', data = {} } = alert;

    const color = this.getSeverityColor(severity);
    const emoji = this.getSeverityEmoji(severity);
    const icon = this.getSeverityIcon(severity);

    // Slack message payload
    const payload = {
      text: `${emoji} *Fortinet Dashboard Alert*`,
      attachments: [
        {
          color: color,
          title: `${icon} ${severity.toUpperCase()} Alert`,
          text: message,
          fields: this.buildFields(data),
          footer: 'Splunk Dashboard',
          footer_icon: 'https://www.splunk.com/content/dam/splunk2/images/icons/favicons/favicon.ico',
          ts: Math.floor(Date.now() / 1000)
        }
      ]
    };

    try {
      const response = await this.postToWebhook(payload);
      console.log(`📢 Slack alert sent: ${severity} - ${message}`);
      return response;
    } catch (error) {
      console.error('❌ Failed to send Slack alert:', error.message);
      return false;
    }
  }

  /**
   * Send configuration change alert
   * @param {Object} change - Configuration change data
   */
  async sendConfigChangeAlert(change) {
    const {
      device,
      user,
      changeType,
      category,
      objectName,
      value,
      timestamp
    } = change;

    const message = `설정 변경 감지: ${device}`;
    const severity = this.getChangeSeverity(category, changeType);

    const data = {
      '장비': device,
      '관리자': user,
      '작업유형': changeType,
      '설정분류': category,
      '객체명': objectName,
      '설정값': value,
      '시간': timestamp
    };

    return await this.sendDashboardAlert({ message, severity, data });
  }

  /**
   * Send critical event alert
   * @param {Object} event - Critical event data
   */
  async sendCriticalEventAlert(event) {
    const {
      device,
      eventCategory,
      eventType,
      message: eventMsg,
      timestamp
    } = event;

    const message = `🚨 CRITICAL 이벤트: ${device} - ${eventCategory}`;
    const severity = 'critical';

    const data = {
      '장비': device,
      '이벤트분류': eventCategory,
      '유형': eventType,
      '메시지': eventMsg,
      '시간': timestamp
    };

    return await this.sendDashboardAlert({ message, severity, data });
  }

  /**
   * Send VPN change alert
   * @param {Object} vpn - VPN change data
   */
  async sendVPNChangeAlert(vpn) {
    const {
      device,
      user,
      vpnType,
      vpnName,
      action,
      attribute,
      value,
      timestamp
    } = vpn;

    const message = `VPN 설정 변경: ${device} - ${vpnType}`;
    const severity = 'high';

    const data = {
      '장비': device,
      '관리자': user,
      'VPN유형': vpnType,
      'VPN명': vpnName,
      '작업': action,
      '속성': attribute,
      '값': value,
      '시간': timestamp
    };

    return await this.sendDashboardAlert({ message, severity, data });
  }

  /**
   * Send firewall policy change alert
   * @param {Object} policy - Policy change data
   */
  async sendPolicyChangeAlert(policy) {
    const {
      device,
      user,
      action,
      policyName,
      changeDetails,
      timestamp
    } = policy;

    const message = `방화벽 정책 변경: ${device} - ${policyName}`;
    const severity = 'high';

    const data = {
      '장비': device,
      '관리자': user,
      '작업': action,
      '정책명': policyName,
      '변경내용': changeDetails,
      '시간': timestamp
    };

    return await this.sendDashboardAlert({ message, severity, data });
  }

  /**
   * Build Slack message fields from data object
   * @param {Object} data - Data object
   * @returns {Array} Slack fields array
   */
  buildFields(data) {
    return Object.entries(data)
      .filter(([_, value]) => value !== undefined && value !== null && value !== '-')
      .map(([key, value]) => ({
        title: key,
        value: String(value),
        short: key !== '메시지' && key !== '변경내용' && key !== '설정값'
      }));
  }

  /**
   * Post data to Slack Webhook
   * @param {Object} payload - Slack message payload
   * @returns {Promise<boolean>} Success status
   */
  postToWebhook(payload) {
    return new Promise((resolve, reject) => {
      const url = new URL(this.webhookUrl);
      const postData = JSON.stringify(payload);

      const options = {
        hostname: url.hostname,
        path: url.pathname + url.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData)
        }
      };

      const req = https.request(options, (res) => {
        let responseData = '';

        res.on('data', (chunk) => {
          responseData += chunk;
        });

        res.on('end', () => {
          if (res.statusCode === 200) {
            resolve(true);
          } else {
            reject(new Error(`Slack API returned ${res.statusCode}: ${responseData}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      req.write(postData);
      req.end();
    });
  }

  /**
   * Get severity emoji
   * @param {string} severity - Severity level
   * @returns {string} Emoji
   */
  getSeverityEmoji(severity) {
    const emojis = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🟢',
      info: '🔵'
    };
    return emojis[severity] || '⚪';
  }

  /**
   * Get severity icon
   * @param {string} severity - Severity level
   * @returns {string} Icon
   */
  getSeverityIcon(severity) {
    const icons = {
      critical: '🚨',
      high: '⚠️',
      medium: '📢',
      low: 'ℹ️',
      info: '💬'
    };
    return icons[severity] || '📝';
  }

  /**
   * Get severity color
   * @param {string} severity - Severity level
   * @returns {string} Hex color code
   */
  getSeverityColor(severity) {
    const colors = {
      critical: '#DC4E41',  // Red
      high: '#F8BE34',      // Orange
      medium: '#87CEEB',    // Sky Blue
      low: '#53A051',       // Green
      info: '#6C757D'       // Gray
    };
    return colors[severity] || '#CCCCCC';
  }

  /**
   * Determine severity based on change category and type
   * @param {string} category - Configuration category
   * @param {string} changeType - Change type
   * @returns {string} Severity level
   */
  getChangeSeverity(category, changeType) {
    // Critical categories
    if (['방화벽 정책', 'IPSec VPN', 'SSL VPN', '관리자'].includes(category)) {
      return changeType === '삭제' ? 'critical' : 'high';
    }

    // Important categories
    if (['주소 객체', '주소 그룹', '서비스 객체', '인터페이스'].includes(category)) {
      return changeType === '삭제' ? 'high' : 'medium';
    }

    // Other categories
    return 'medium';
  }

  /**
   * Test Slack webhook connectivity
   * @returns {Promise<boolean>} Connection status
   */
  async testConnection() {
    if (!this.enabled) {
      console.log('❌ Slack Webhook URL not configured');
      return false;
    }

    const testPayload = {
      text: '✅ Slack Webhook 연결 테스트 성공',
      attachments: [
        {
          color: '#53A051',
          title: 'Connection Test',
          text: 'Splunk Dashboard → Slack 연동이 정상적으로 작동합니다.',
          footer: 'Splunk Dashboard Alert System',
          ts: Math.floor(Date.now() / 1000)
        }
      ]
    };

    try {
      await this.postToWebhook(testPayload);
      console.log('✅ Slack webhook connection test passed');
      return true;
    } catch (error) {
      console.error('❌ Slack webhook connection test failed:', error.message);
      return false;
    }
  }

  /**
   * Get handler status
   * @returns {Object} Status information
   */
  getStatus() {
    return {
      enabled: this.enabled,
      webhookUrl: this.webhookUrl ? this.maskWebhookUrl(this.webhookUrl) : null,
      configured: !!this.webhookUrl
    };
  }

  /**
   * Mask webhook URL for security
   * @param {string} url - Webhook URL
   * @returns {string} Masked URL
   */
  maskWebhookUrl(url) {
    try {
      const urlObj = new URL(url);
      const pathParts = urlObj.pathname.split('/');
      const maskedPath = pathParts.map((part, index) =>
        index >= pathParts.length - 1 ? '***' : part
      ).join('/');
      return `${urlObj.protocol}//${urlObj.hostname}${maskedPath}`;
    } catch {
      return '*** (invalid URL)';
    }
  }
}

export default SlackWebhookHandler;
