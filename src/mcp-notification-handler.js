/**
 * MCP Notification Handler
 * Integrates with Slack MCP tools for automated notifications
 */

// Import the notification system
// (In actual deployment, would use proper imports)

/**
 * MCP Slack Notification Handler Class
 * Manages all Slack notifications through MCP protocol
 */
class MCPSlackHandler {
  constructor() {
    this.channels = {
      'planka-alerts': 'C09D1LW9X3R',
      'ems': 'C09DAJ6QDU3',
      '배포': 'C09DDFCK8TV', 
      '일반': 'C09DEUR4G4A',
      'splunk': 'C09DGE44XL6',
      'blacklist': 'C09E2N1T0GJ',
      'safework': 'C09EBJMS8DN',
      'mcp': 'C09HECF0R5F'
    };
    
    this.errorPatterns = [
      'ERROR', 'FATAL', 'Exception', 'CRITICAL',
      'deployment failed', 'build failed', 'test failed'
    ];
  }

  /**
   * Send message using MCP Slack tools
   * @param {string} channelName - Channel name or ID
   * @param {string} message - Message content
   */
  async sendMessage(channelName, message) {
    try {
      const channelId = this.channels[channelName] || channelName;
      
      // Using MCP Slack tool directly
      const result = await this.mcpSlackPost(channelId, message);
      
      console.log(`✅ MCP Slack message sent to ${channelName}`);
      return result;
    } catch (error) {
      console.error(`❌ MCP Slack error for ${channelName}:`, error);
      // Fallback to general channel
      if (channelName !== '일반') {
        return await this.sendMessage('일반', `⚠️ Failed to send to #${channelName}: ${message}`);
      }
      throw error;
    }
  }

  /**
   * MCP Slack Post wrapper (would be actual MCP call)
   * @param {string} channelId - Channel ID
   * @param {string} text - Message text
   */
  async mcpSlackPost(channelId, text) {
    // In actual implementation, this would be:
    // return await mcp_slack_slack_post_message({ channel_id: channelId, text });
    
    // For now, simulate the call
    return {
      ok: true,
      channel: channelId,
      message: text,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Send error log notification with Grafana integration
   * @param {Array} errors - Error log entries
   * @param {string} projectName - Project name
   */
  async notifyErrorLogs(errors, projectName = 'system') {
    if (!errors || errors.length === 0) return;

    const errorCount = errors.length;
    const criticalErrors = errors.filter(error => 
      this.errorPatterns.some(pattern => 
        error.message?.toLowerCase().includes(pattern.toLowerCase())
      )
    );

    // Deployment channel notification
    const deployMessage = `🚨 ${projectName}: ${errorCount} errors detected in logs
📊 Grafana: https://grafana.jclee.me/explore`;
    
    await this.sendMessage('배포', deployMessage);

    // Critical error notification to general
    if (criticalErrors.length > 0) {
      const criticalMessage = `❌ CRITICAL: ${criticalErrors.length} critical errors in ${projectName}
🔍 Immediate attention required`;
      
      await this.sendMessage('일반', criticalMessage);
    }

    // Project-specific channel if exists
    if (this.channels[projectName]) {
      const projectMessage = `⚠️ ${errorCount} errors detected
🔗 View logs: https://grafana.jclee.me/explore?query={job="${projectName}"}`;
      
      await this.sendMessage(projectName, projectMessage);
    }
  }

  /**
   * Deployment notification
   * @param {string} project - Project name
   * @param {string} status - success/failed
   * @param {Object} details - Deployment details
   */
  async notifyDeployment(project, status, details = {}) {
    const emoji = status === 'success' ? '✅' : '❌';
    const timestamp = new Date().toLocaleString('ko-KR');
    
    let message = `${emoji} **${project}** deployment ${status}
🕐 ${timestamp}`;

    if (details.commit) {
      message += `\n📝 Commit: ${details.commit.substring(0, 8)}`;
    }
    
    if (details.duration) {
      message += `\n⏱️ Duration: ${details.duration}`;
    }

    if (status === 'failed' && details.error) {
      message += `\n🔥 Error: ${details.error}`;
    }

    if (details.url) {
      message += `\n🔗 ${details.url}`;
    }

    // Send to deployment channel
    await this.sendMessage('배포', message);

    // Send to project-specific channel
    if (this.channels[project]) {
      await this.sendMessage(project, message);
    }

    // If failed, also notify general channel
    if (status === 'failed') {
      await this.sendMessage('일반', `🚨 **${project}** deployment failed - requires attention`);
    }
  }

  /**
   * GitHub Actions notification
   * @param {string} repo - Repository name
   * @param {string} workflow - Workflow name
   * @param {string} status - Status
   * @param {Object} details - Additional details
   */
  async notifyGitHubAction(repo, workflow, status, details = {}) {
    const emoji = status === 'success' ? '✅' : status === 'failure' ? '❌' : '⏳';
    
    let message = `${emoji} **${repo}** - ${workflow} ${status}`;
    
    if (details.branch) {
      message += `\n🌿 Branch: ${details.branch}`;
    }
    
    if (details.commit) {
      message += `\n📝 ${details.commit}`;
    }

    if (details.runUrl) {
      message += `\n🔗 View run: ${details.runUrl}`;
    }

    await this.sendMessage('배포', message);
  }

  /**
   * System health notification
   * @param {string} service - Service name
   * @param {string} status - Health status
   * @param {Object} metrics - Service metrics
   */
  async notifySystemHealth(service, status, metrics = {}) {
    const emoji = status === 'healthy' ? '💚' : status === 'warning' ? '🟡' : '🔴';
    
    let message = `${emoji} **${service}** health: ${status}`;
    
    if (metrics.uptime) {
      message += `\n⏱️ Uptime: ${metrics.uptime}`;
    }
    
    if (metrics.memory) {
      message += `\n🧠 Memory: ${metrics.memory}`;
    }
    
    if (metrics.cpu) {
      message += `\n⚡ CPU: ${metrics.cpu}`;
    }

    // Send to appropriate channel based on severity
    const channel = status === 'critical' ? '일반' : 'mcp';
    await this.sendMessage(channel, message);
  }

  /**
   * Create project error channel if needed
   * @param {string} projectName - Project name
   */
  async ensureProjectErrorChannel(projectName) {
    const channelName = `${projectName}-errors`;
    
    if (!this.channels[channelName]) {
      console.log(`⚠️ Consider creating #${channelName} for automated error notifications`);
      
      // In real implementation, would use MCP to create channel:
      // const result = await mcp_slack_create_channel({ name: channelName });
      // this.channels[channelName] = result.channel.id;
    }
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MCPSlackHandler;
}

// Global export for browser/worker environments
if (typeof globalThis !== 'undefined') {
  globalThis.MCPSlackHandler = MCPSlackHandler;
}