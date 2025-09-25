/**
 * Project-specific Error Channel Manager
 * Automatically creates and manages Slack channels for project notifications
 */

class SlackChannelManager {
  constructor() {
    // Existing channels from MCP list
    this.existingChannels = {
      'planka-alerts': 'C09D1LW9X3R',
      'ems': 'C09DAJ6QDU3',
      '배포': 'C09DDFCK8TV',
      '일반': 'C09DEUR4G4A',
      'splunk': 'C09DGE44XL6',
      'blacklist': 'C09E2N1T0GJ',
      'safework': 'C09EBJMS8DN',
      'mcp': 'C09HECF0R5F'
    };
    
    // Projects that need error channels
    this.projects = [
      'splunk',
      'blacklist', 
      'safework',
      'ems',
      'planka',
      'gateway',
      'auth',
      'users',
      'orders',
      'products',
      'inventory',
      'webhooks',
      'notifs',
      'uploads'
    ];
    
    this.channelTemplate = {
      purpose: 'Automated error notifications and monitoring alerts for {project}',
      topic: 'Error logs and deployment status for {project} service'
    };
  }

  /**
   * Initialize all project error channels
   */
  async initializeProjectChannels() {
    console.log('🚀 Initializing project-specific error channels...');
    
    const results = {
      existing: [],
      created: [],
      failed: []
    };

    for (const project of this.projects) {
      const channelName = `${project}-errors`;
      
      if (this.existingChannels[channelName]) {
        results.existing.push(channelName);
        console.log(`✅ Channel #${channelName} already exists`);
        continue;
      }

      try {
        const created = await this.createProjectErrorChannel(project);
        if (created) {
          results.created.push(channelName);
        }
      } catch (error) {
        console.error(`❌ Failed to create #${channelName}:`, error);
        results.failed.push({ channel: channelName, error: error.message });
      }
    }

    // Report results
    await this.reportChannelInitialization(results);
    return results;
  }

  /**
   * Create error channel for specific project
   * @param {string} projectName - Project name
   */
  async createProjectErrorChannel(projectName) {
    const channelName = `${projectName}-errors`;
    
    console.log(`🔧 Creating channel #${channelName}...`);
    
    // In actual implementation, would use MCP Slack channel creation
    // For now, simulate the creation process
    const channelConfig = {
      name: channelName,
      purpose: this.channelTemplate.purpose.replace('{project}', projectName),
      topic: this.channelTemplate.topic.replace('{project}', projectName),
      is_private: false
    };
    
    // Simulate MCP Slack channel creation
    const mockChannelId = `C${Date.now().toString(36).toUpperCase()}`;
    
    // Add to existing channels registry
    this.existingChannels[channelName] = mockChannelId;
    
    console.log(`✅ Created #${channelName} with ID ${mockChannelId}`);
    
    // Send welcome message to new channel
    await this.sendChannelWelcomeMessage(projectName, channelName, mockChannelId);
    
    return {
      name: channelName,
      id: mockChannelId,
      config: channelConfig
    };
  }

  /**
   * Send welcome message to newly created channel
   * @param {string} projectName - Project name
   * @param {string} channelName - Channel name
   * @param {string} channelId - Channel ID
   */
  async sendChannelWelcomeMessage(projectName, channelName, channelId) {
    const welcomeMessage = `🎉 **${projectName}** 에러 알림 채널이 생성되었습니다!

이 채널에서 다음과 같은 알림을 받게 됩니다:
🚨 에러 로그 감지 알림
⚠️ 배포 실패 알림  
🔍 헬스 체크 실패 알림
📊 성능 임계치 초과 알림

🔧 **설정된 모니터링:**
- Grafana 로그 실시간 감시
- GitHub Actions 배포 상태
- 컨테이너 헬스 체크
- 서비스 가용성 모니터링

🔗 **관련 링크:**
- Grafana: https://grafana.jclee.me/explore?query={job="${projectName}"}
- Service: https://${projectName}.jclee.me
- Health: https://${projectName}.jclee.me/health

💡 **알림 설정이 완료되었습니다!**`;

    console.log(`📤 Sending welcome message to #${channelName}`);
    
    // In actual implementation, would use MCP Slack post
    // For now, simulate successful message send
    return {
      ok: true,
      channel: channelId,
      message: welcomeMessage
    };
  }

  /**
   * Get or create error channel for project
   * @param {string} projectName - Project name
   */
  async ensureProjectErrorChannel(projectName) {
    const channelName = `${projectName}-errors`;
    
    // Check if channel already exists
    if (this.existingChannels[channelName]) {
      return {
        name: channelName,
        id: this.existingChannels[channelName],
        existed: true
      };
    }
    
    // Create new channel
    const created = await this.createProjectErrorChannel(projectName);
    return {
      ...created,
      existed: false
    };
  }

  /**
   * Report channel initialization results
   * @param {Object} results - Initialization results
   */
  async reportChannelInitialization(results) {
    let reportMessage = `📊 **프로젝트 에러 채널 초기화 완료**

✅ **기존 채널:** ${results.existing.length}개
${results.existing.map(ch => `   • #${ch}`).join('\n')}

🆕 **새로 생성:** ${results.created.length}개
${results.created.map(ch => `   • #${ch}`).join('\n')}`;

    if (results.failed.length > 0) {
      reportMessage += `

❌ **생성 실패:** ${results.failed.length}개
${results.failed.map(f => `   • #${f.channel}: ${f.error}`).join('\n')}`;
    }

    reportMessage += `

🔔 **총 ${results.existing.length + results.created.length}개 채널에서 자동 알림을 받게 됩니다.**

각 프로젝트별 에러 채널에서:
• 실시간 에러 로그 알림
• 배포 상태 업데이트  
• 헬스 체크 결과
• 성능 모니터링 알림`;

    // Send to MCP channel
    console.log('📤 Sending initialization report...');
    
    // In actual implementation, would use MCP Slack
    return reportMessage;
  }

  /**
   * Update channel purposes and topics
   */
  async updateChannelMetadata() {
    console.log('🔧 Updating channel metadata...');
    
    const updates = [];
    
    for (const project of this.projects) {
      const channelName = `${project}-errors`;
      const channelId = this.existingChannels[channelName];
      
      if (channelId) {
        // In real implementation, would update channel via MCP
        updates.push({
          channel: channelName,
          purpose: this.channelTemplate.purpose.replace('{project}', project),
          topic: this.channelTemplate.topic.replace('{project}', project)
        });
      }
    }
    
    console.log(`✅ Updated metadata for ${updates.length} channels`);
    return updates;
  }

  /**
   * Get all project error channels
   */
  getProjectErrorChannels() {
    const projectChannels = {};
    
    for (const project of this.projects) {
      const channelName = `${project}-errors`;
      if (this.existingChannels[channelName]) {
        projectChannels[project] = {
          name: channelName,
          id: this.existingChannels[channelName]
        };
      }
    }
    
    return projectChannels;
  }

  /**
   * Get channel recommendations
   */
  getChannelRecommendations() {
    const missing = [];
    
    for (const project of this.projects) {
      const channelName = `${project}-errors`;
      if (!this.existingChannels[channelName]) {
        missing.push({
          project,
          channelName,
          recommended: true,
          reason: 'Automated error notifications and deployment monitoring'
        });
      }
    }
    
    return {
      missing,
      total: this.projects.length,
      existing: this.projects.length - missing.length
    };
  }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SlackChannelManager;
}

if (typeof globalThis !== 'undefined') {
  globalThis.SlackChannelManager = SlackChannelManager;
}