/**
 * Splunk Dashboard with MCP Slack Notification Integration
 * Main entry point for the notification system
 */

// Import notification modules
import { MCPSlackHandler } from './mcp-notification-handler.js';
import { GrafanaLogMonitor } from './grafana-monitor.js';
import { DeploymentNotifier } from './deployment-notifier.js';
import { SlackChannelManager } from './channel-manager.js';

/**
 * Main Application Class
 */
class SplunkNotificationApp {
  constructor() {
    this.slackHandler = new MCPSlackHandler();
    this.grafanaMonitor = new GrafanaLogMonitor();
    this.deploymentNotifier = new DeploymentNotifier();
    this.channelManager = new SlackChannelManager();
    
    this.isInitialized = false;
    this.startTime = new Date();
  }

  /**
   * Initialize the notification system
   */
  async initialize() {
    if (this.isInitialized) {
      console.log('⚠️ System already initialized');
      return;
    }

    console.log('🚀 Initializing Splunk MCP Slack Notification System...');

    try {
      // 1. Initialize project error channels
      console.log('📋 Step 1: Initializing project error channels...');
      const channelResults = await this.channelManager.initializeProjectChannels();
      
      // 2. Start Grafana monitoring
      console.log('📊 Step 2: Starting Grafana log monitoring...');
      await this.grafanaMonitor.startMonitoring();
      
      // 3. Send startup notification
      console.log('📤 Step 3: Sending startup notifications...');
      await this.sendStartupNotifications(channelResults);
      
      this.isInitialized = true;
      console.log('✅ Notification system initialized successfully!');
      
    } catch (error) {
      console.error('❌ Initialization failed:', error);
      await this.handleInitializationError(error);
      throw error;
    }
  }

  /**
   * Send startup notifications
   * @param {Object} channelResults - Channel initialization results
   */
  async sendStartupNotifications(channelResults) {
    const startupMessage = `🚀 **Splunk MCP 알림 시스템 시작**

✅ 시스템 상태: 정상 가동
📊 Grafana 모니터링: 활성화
🔔 프로젝트 채널: ${channelResults.existing.length + channelResults.created.length}개
⏰ 시작 시간: ${this.startTime.toLocaleString('ko-KR')}

🔧 **활성화된 기능:**
• 실시간 에러 로그 감지
• 자동 배포 상태 알림
• GitHub Actions 연동
• 헬스 체크 모니터링
• 프로젝트별 개별 채널 알림

📊 **모니터링 대상:**
${this.channelManager.projects.map(p => `• ${p}.jclee.me`).join('\n')}

🎯 **알림이 준비되었습니다!**`;

    // Send to main channels
    await this.slackHandler.sendMessage('mcp', startupMessage);
    await this.slackHandler.sendMessage('배포', '✅ 자동 배포 알림 시스템 활성화');
  }

  /**
   * Handle GitHub webhook requests
   * @param {Object} payload - Webhook payload
   * @param {string} eventType - Event type header
   */
  async handleWebhook(payload, eventType) {
    console.log(`📥 Received ${eventType} webhook`);
    
    try {
      switch (eventType) {
        case 'push':
          await this.deploymentNotifier.handleGitHubWebhook(payload);
          break;
          
        case 'workflow_run':
          await this.deploymentNotifier.handleWorkflowEvent(payload);
          break;
          
        case 'deployment_status':
          await this.handleDeploymentStatusWebhook(payload);
          break;
          
        default:
          console.log(`ℹ️ Unhandled webhook type: ${eventType}`);
      }
    } catch (error) {
      console.error(`❌ Webhook handling error:`, error);
      await this.slackHandler.sendMessage('mcp', 
        `🚨 Webhook 처리 에러: ${eventType} - ${error.message}`);
    }
  }

  /**
   * Handle deployment status webhook
   * @param {Object} payload - Deployment status payload
   */
  async handleDeploymentStatusWebhook(payload) {
    const { deployment, deployment_status, repository } = payload;
    const projectName = repository.name;
    const status = deployment_status.state;
    
    console.log(`🔄 Deployment status: ${projectName} - ${status}`);
    
    const emoji = status === 'success' ? '✅' : status === 'failure' ? '❌' : '⏳';
    const message = `${emoji} **${projectName}** deployment ${status}
🔗 Environment: ${deployment.environment}
📝 ${deployment_status.description || 'No description'}`;

    await this.slackHandler.sendMessage('배포', message);
  }

  /**
   * Manual error log check
   * @param {string} projectName - Optional project name filter
   */
  async checkErrorLogs(projectName = null) {
    console.log(`🔍 Manual error log check${projectName ? ` for ${projectName}` : ''}...`);
    
    try {
      const query = projectName ? 
        `{job="${projectName}"} |= "ERROR" [15m]` : 
        '{job=~".*"} |= "ERROR" [15m]';
        
      const errors = await this.grafanaMonitor.queryGrafana(query, 50);
      
      if (errors.length > 0) {
        await this.grafanaMonitor.processErrors(errors, false);
        return { found: true, count: errors.length };
      } else {
        await this.slackHandler.sendMessage('mcp', 
          `✅ ${projectName || 'All services'}: No errors in last 15 minutes`);
        return { found: false, count: 0 };
      }
    } catch (error) {
      console.error('Manual error check failed:', error);
      return { found: false, count: 0, error: error.message };
    }
  }

  /**
   * Send test notification
   * @param {string} channelName - Target channel
   * @param {string} testType - Type of test
   */
  async sendTestNotification(channelName = 'mcp', testType = 'basic') {
    const testMessages = {
      basic: '🧪 MCP Slack 연동 테스트',
      deployment: '🚀 배포 알림 테스트 - 시스템 정상 작동',
      error: '⚠️ 에러 로그 감지 테스트 - 모니터링 활성화',
      health: '💚 헬스 체크 테스트 - 모든 서비스 정상'
    };
    
    const message = testMessages[testType] || testMessages.basic;
    const timestamp = new Date().toLocaleString('ko-KR');
    
    return await this.slackHandler.sendMessage(channelName, 
      `${message}\n🕐 ${timestamp}`);
  }

  /**
   * Get system status
   */
  getStatus() {
    return {
      initialized: this.isInitialized,
      startTime: this.startTime,
      uptime: Date.now() - this.startTime.getTime(),
      grafanaMonitoring: this.grafanaMonitor.getStatus(),
      deploymentNotifier: this.deploymentNotifier.getStatus(),
      projectChannels: this.channelManager.getProjectErrorChannels(),
      channelRecommendations: this.channelManager.getChannelRecommendations()
    };
  }

  /**
   * Shutdown the notification system
   */
  async shutdown() {
    console.log('⏹️ Shutting down notification system...');
    
    // Stop monitoring
    await this.grafanaMonitor.stopMonitoring();
    
    // Send shutdown notification
    await this.slackHandler.sendMessage('mcp', 
      '⏹️ Splunk MCP 알림 시스템 종료');
    
    this.isInitialized = false;
  }

  /**
   * Handle initialization error
   * @param {Error} error - Initialization error
   */
  async handleInitializationError(error) {
    const errorMessage = `❌ **시스템 초기화 실패**
🚨 Error: ${error.message}
🕐 Time: ${new Date().toLocaleString('ko-KR')}
🔧 Manual intervention required`;

    try {
      await this.slackHandler.sendMessage('mcp', errorMessage);
    } catch (notificationError) {
      console.error('Failed to send error notification:', notificationError);
    }
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SplunkNotificationApp;
}

// Global export for browser/worker environments
if (typeof globalThis !== 'undefined') {
  globalThis.SplunkNotificationApp = SplunkNotificationApp;
}

// Auto-initialize if running directly
if (typeof window === 'undefined' && typeof importScripts === 'undefined') {
  // Node.js or Worker environment - auto start
  const app = new SplunkNotificationApp();
  app.initialize().catch(console.error);
}