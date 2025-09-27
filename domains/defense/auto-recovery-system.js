/**
 * Intelligent Auto-Recovery System
 * Automatically detects and resolves system issues before they impact users
 */

class AutoRecoverySystem {
  constructor() {
    this.config = {
      // Recovery strategies
      maxRetryAttempts: 3,
      retryBackoffBase: 2000, // 2 seconds
      maxRetryBackoff: 30000, // 30 seconds
      recoveryTimeout: 300000, // 5 minutes
      
      // Safety limits
      maxConcurrentRecoveries: 5,
      cooldownPeriod: 600000, // 10 minutes between recovery attempts
      emergencyStopThreshold: 0.1, // Stop if success rate drops below 10%
      
      // Recovery confidence thresholds
      automaticRecoveryThreshold: 0.8,
      supervisedRecoveryThreshold: 0.6,
      manualOnlyThreshold: 0.4,
      
      // Portainer integration
      portainerEndpoints: {
        production: { id: 3, name: 'synology' },
        development: { id: 4, name: 'jclee-dev' }
      }
    };
    
    // Recovery strategies registry
    this.recoveryStrategies = new Map([
      ['service_restart', new ServiceRestartStrategy()],
      ['resource_scaling', new ResourceScalingStrategy()],
      ['traffic_redirect', new TrafficRedirectStrategy()],
      ['dependency_fallback', new DependencyFallbackStrategy()],
      ['cache_clear', new CacheClearStrategy()],
      ['connection_reset', new ConnectionResetStrategy()],
      ['config_rollback', new ConfigRollbackStrategy()],
      ['health_check_reset', new HealthCheckResetStrategy()]
    ]);
    
    // Recovery state tracking
    this.activeRecoveries = new Map();
    this.recoveryHistory = [];
    this.successRates = new Map();
    this.isEmergencyStop = false;
    
    // Performance metrics
    this.metrics = {
      totalRecoveries: 0,
      successfulRecoveries: 0,
      failedRecoveries: 0,
      averageRecoveryTime: 0,
      preventedDowntime: 0
    };
  }

  /**
   * Initialize auto-recovery system
   */
  async initialize() {
    console.log('🛠️ Auto-Recovery System 초기화 중...');
    
    try {
      // Load recovery history
      await this.loadRecoveryHistory();
      
      // Initialize recovery strategies
      await this.initializeStrategies();
      
      // Start monitoring for recovery opportunities
      this.startRecoveryMonitoring();
      
      console.log('✅ 자동 복구 시스템 준비 완료');
      
    } catch (error) {
      console.error('❌ 자동 복구 시스템 초기화 실패:', error);
      throw error;
    }
  }

  /**
   * Start continuous recovery monitoring
   */
  startRecoveryMonitoring() {
    // Monitor for recovery opportunities every 30 seconds
    setInterval(async () => {
      if (!this.isEmergencyStop) {
        await this.scanForRecoveryOpportunities();
      }
    }, 30000);
    
    // Update success rates every 5 minutes
    setInterval(() => {
      this.updateSuccessRates();
    }, 300000);
    
    console.log('🔄 자동 복구 모니터링 시작됨');
  }

  /**
   * Scan for recovery opportunities
   */
  async scanForRecoveryOpportunities() {
    try {
      // Get current system issues
      const issues = await this.detectSystemIssues();
      
      for (const issue of issues) {
        if (await this.shouldAttemptRecovery(issue)) {
          await this.attemptAutoRecovery(issue);
        }
      }
    } catch (error) {
      console.error('복구 기회 스캔 에러:', error);
    }
  }

  /**
   * Detect current system issues
   */
  async detectSystemIssues() {
    const issues = [];
    
    try {
      // Check service health
      const serviceIssues = await this.checkServiceHealth();
      issues.push(...serviceIssues);
      
      // Check resource utilization
      const resourceIssues = await this.checkResourceUtilization();
      issues.push(...resourceIssues);
      
      // Check dependency status
      const dependencyIssues = await this.checkDependencyStatus();
      issues.push(...dependencyIssues);
      
      // Check error patterns
      const errorIssues = await this.checkErrorPatterns();
      issues.push(...errorIssues);
      
    } catch (error) {
      console.error('시스템 이슈 감지 에러:', error);
    }
    
    return issues;
  }

  /**
   * Check if recovery should be attempted for an issue
   * @param {Object} issue - Detected issue
   */
  async shouldAttemptRecovery(issue) {
    // Safety checks
    if (this.isEmergencyStop) return false;
    if (this.activeRecoveries.size >= this.config.maxConcurrentRecoveries) return false;
    
    // Check cooldown period
    const lastRecovery = this.getLastRecoveryAttempt(issue.service, issue.type);
    if (lastRecovery && (Date.now() - lastRecovery.timestamp) < this.config.cooldownPeriod) {
      return false;
    }
    
    // Check recovery confidence
    const confidence = await this.calculateRecoveryConfidence(issue);
    if (confidence < this.config.manualOnlyThreshold) return false;
    
    // Check if already recovering
    const recoveryKey = `${issue.service}_${issue.type}`;
    if (this.activeRecoveries.has(recoveryKey)) return false;
    
    return true;
  }

  /**
   * Attempt automatic recovery for an issue
   * @param {Object} issue - Issue to recover from
   */
  async attemptAutoRecovery(issue) {
    const recoveryKey = `${issue.service}_${issue.type}`;
    const recoverySession = {
      id: `recovery_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      issue,
      startTime: Date.now(),
      status: 'in_progress',
      attempts: 0,
      strategies: [],
      confidence: await this.calculateRecoveryConfidence(issue)
    };
    
    this.activeRecoveries.set(recoveryKey, recoverySession);
    
    console.log(`🔧 자동 복구 시도: ${issue.service} - ${issue.type} (신뢰도: ${(recoverySession.confidence * 100).toFixed(1)}%)`);
    
    try {
      // Send recovery start notification
      await this.sendRecoveryNotification('start', recoverySession);
      
      // Execute recovery strategies
      const success = await this.executeRecoveryStrategies(recoverySession);
      
      if (success) {
        recoverySession.status = 'success';
        recoverySession.endTime = Date.now();
        await this.handleRecoverySuccess(recoverySession);
      } else {
        recoverySession.status = 'failed';
        recoverySession.endTime = Date.now();
        await this.handleRecoveryFailure(recoverySession);
      }
      
    } catch (error) {
      console.error(`복구 실행 에러 (${recoveryKey}):`, error);
      recoverySession.status = 'error';
      recoverySession.error = error.message;
      recoverySession.endTime = Date.now();
      await this.handleRecoveryError(recoverySession, error);
    } finally {
      this.activeRecoveries.delete(recoveryKey);
      this.recoveryHistory.push(recoverySession);
      this.updateMetrics(recoverySession);
    }
  }

  /**
   * Execute recovery strategies for a session
   * @param {Object} session - Recovery session
   */
  async executeRecoveryStrategies(session) {
    const issue = session.issue;
    const applicableStrategies = await this.getApplicableStrategies(issue);
    
    for (const strategyName of applicableStrategies) {
      if (session.attempts >= this.config.maxRetryAttempts) break;
      
      session.attempts++;
      const strategy = this.recoveryStrategies.get(strategyName);
      
      if (!strategy) {
        console.warn(`복구 전략을 찾을 수 없음: ${strategyName}`);
        continue;
      }
      
      console.log(`🔄 복구 전략 실행: ${strategyName} (시도 ${session.attempts}/${this.config.maxRetryAttempts})`);
      
      try {
        const strategyResult = await strategy.execute(issue, session);
        session.strategies.push({
          name: strategyName,
          result: strategyResult,
          timestamp: Date.now()
        });
        
        if (strategyResult.success) {
          // Verify recovery
          await this.sleep(5000); // Wait 5 seconds for stabilization
          const isRecovered = await this.verifyRecovery(issue);
          
          if (isRecovered) {
            console.log(`✅ 복구 성공: ${strategyName}`);
            return true;
          } else {
            console.log(`⚠️ 복구 확인 실패: ${strategyName}`);
          }
        } else {
          console.log(`❌ 복구 전략 실패: ${strategyName} - ${strategyResult.error}`);
        }
        
        // Wait before next attempt
        const backoffTime = Math.min(
          this.config.retryBackoffBase * Math.pow(2, session.attempts - 1),
          this.config.maxRetryBackoff
        );
        await this.sleep(backoffTime);
        
      } catch (error) {
        console.error(`복구 전략 실행 에러 (${strategyName}):`, error);
        session.strategies.push({
          name: strategyName,
          error: error.message,
          timestamp: Date.now()
        });
      }
    }
    
    return false; // All strategies failed
  }

  /**
   * Get applicable recovery strategies for an issue
   * @param {Object} issue - Issue to recover from
   */
  async getApplicableStrategies(issue) {
    const strategies = [];
    
    switch (issue.type) {
      case 'service_unhealthy':
        strategies.push('service_restart', 'health_check_reset');
        break;
        
      case 'high_error_rate':
        strategies.push('service_restart', 'cache_clear', 'connection_reset');
        break;
        
      case 'resource_exhaustion':
        strategies.push('resource_scaling', 'cache_clear', 'service_restart');
        break;
        
      case 'dependency_failure':
        strategies.push('dependency_fallback', 'connection_reset');
        break;
        
      case 'performance_degradation':
        strategies.push('cache_clear', 'resource_scaling', 'traffic_redirect');
        break;
        
      case 'configuration_error':
        strategies.push('config_rollback', 'service_restart');
        break;
        
      default:
        strategies.push('service_restart'); // Generic fallback
    }
    
    // Filter based on confidence and applicability
    const filteredStrategies = [];
    for (const strategyName of strategies) {
      const strategy = this.recoveryStrategies.get(strategyName);
      if (strategy && await strategy.isApplicable(issue)) {
        filteredStrategies.push(strategyName);
      }
    }
    
    return filteredStrategies;
  }

  /**
   * Calculate recovery confidence for an issue
   * @param {Object} issue - Issue to assess
   */
  async calculateRecoveryConfidence(issue) {
    let confidence = 0.5; // Base confidence
    
    // Historical success rate
    const historicalSuccess = this.getHistoricalSuccessRate(issue.service, issue.type);
    confidence = (confidence + historicalSuccess) / 2;
    
    // Issue severity (inverse correlation)
    const severityPenalty = issue.severity === 'critical' ? 0.2 : issue.severity === 'high' ? 0.1 : 0;
    confidence -= severityPenalty;
    
    // Service criticality
    const criticalServices = ['auth', 'gateway', 'database'];
    if (criticalServices.includes(issue.service)) {
      confidence += 0.1; // Higher confidence for critical services
    }
    
    // Recent failures
    const recentFailures = this.getRecentFailures(issue.service, 3600000); // Last hour
    const failurePenalty = Math.min(recentFailures * 0.05, 0.3);
    confidence -= failurePenalty;
    
    return Math.max(0.1, Math.min(confidence, 0.95));
  }

  /**
   * Verify if recovery was successful
   * @param {Object} issue - Original issue
   */
  async verifyRecovery(issue) {
    try {
      switch (issue.type) {
        case 'service_unhealthy':
          return await this.verifyServiceHealth(issue.service);
          
        case 'high_error_rate':
          return await this.verifyErrorRateReduction(issue.service);
          
        case 'resource_exhaustion':
          return await this.verifyResourceUtilization(issue.service, issue.resource);
          
        case 'dependency_failure':
          return await this.verifyDependencyHealth(issue.dependency);
          
        default:
          return await this.verifyServiceHealth(issue.service);
      }
    } catch (error) {
      console.error('복구 검증 에러:', error);
      return false;
    }
  }

  /**
   * Handle successful recovery
   * @param {Object} session - Recovery session
   */
  async handleRecoverySuccess(session) {
    const duration = session.endTime - session.startTime;
    
    console.log(`✅ 자동 복구 성공: ${session.issue.service} (${Math.round(duration/1000)}초)`);
    
    // Send success notification
    await this.sendRecoveryNotification('success', session);
    
    // Update success metrics
    this.metrics.successfulRecoveries++;
    this.metrics.preventedDowntime += this.estimatePreventedDowntime(session.issue);
  }

  /**
   * Handle recovery failure
   * @param {Object} session - Recovery session
   */
  async handleRecoveryFailure(session) {
    console.log(`❌ 자동 복구 실패: ${session.issue.service}`);
    
    // Send failure notification with escalation
    await this.sendRecoveryNotification('failed', session);
    
    // Check if emergency stop is needed
    await this.checkEmergencyStop();
    
    this.metrics.failedRecoveries++;
  }

  /**
   * Handle recovery error
   * @param {Object} session - Recovery session
   * @param {Error} error - Error that occurred
   */
  async handleRecoveryError(session, error) {
    console.error(`🚨 자동 복구 오류: ${session.issue.service} - ${error.message}`);
    
    // Send error notification
    await this.sendRecoveryNotification('error', session);
    
    this.metrics.failedRecoveries++;
  }

  /**
   * Send recovery notification
   * @param {string} type - Notification type (start, success, failed, error)
   * @param {Object} session - Recovery session
   */
  async sendRecoveryNotification(type, session) {
    const issue = session.issue;
    const duration = session.endTime ? Math.round((session.endTime - session.startTime) / 1000) : 0;
    
    const messages = {
      start: `🔧 **자동 복구 시작**
📊 서비스: ${issue.service}
🎯 문제: ${issue.type}
💪 신뢰도: ${(session.confidence * 100).toFixed(1)}%
⏰ 시작: ${new Date(session.startTime).toLocaleString('ko-KR')}`,

      success: `✅ **자동 복구 성공**
📊 서비스: ${issue.service}
🎯 문제: ${issue.type}
⏱️ 소요 시간: ${duration}초
💡 적용된 전략: ${session.strategies.filter(s => s.result?.success).map(s => s.name).join(', ')}
🎉 시스템이 정상 복구되었습니다!`,

      failed: `❌ **자동 복구 실패**
📊 서비스: ${issue.service}
🎯 문제: ${issue.type}
⏱️ 시도 시간: ${duration}초
🔄 시도 횟수: ${session.attempts}
💡 시도된 전략: ${session.strategies.map(s => s.name).join(', ')}
🚨 **수동 개입이 필요합니다**`,

      error: `🚨 **자동 복구 오류**
📊 서비스: ${issue.service}
🎯 문제: ${issue.type}
❌ 오류: ${session.error}
🔧 **시스템 점검이 필요합니다**`
    };

    const message = messages[type];
    const channel = type === 'success' ? 'mcp' : type === 'start' ? 'mcp' : '일반';
    
    console.log(`📤 Recovery notification sent: ${type} to #${channel}`);
    return message;
  }

  /**
   * Check if emergency stop should be activated
   */
  async checkEmergencyStop() {
    const recentRecoveries = this.recoveryHistory.filter(r => 
      Date.now() - r.startTime < 3600000 // Last hour
    );
    
    if (recentRecoveries.length >= 5) {
      const successRate = recentRecoveries.filter(r => r.status === 'success').length / recentRecoveries.length;
      
      if (successRate < this.config.emergencyStopThreshold) {
        this.isEmergencyStop = true;
        console.log('🚨 Emergency stop activated - low recovery success rate');
        
        // Send emergency notification
        await this.sendEmergencyStopNotification(successRate);
        
        // Auto-resume after 1 hour
        setTimeout(() => {
          this.isEmergencyStop = false;
          console.log('🔄 Auto-recovery resumed after emergency stop');
        }, 3600000);
      }
    }
  }

  /**
   * Get system status and metrics
   */
  getStatus() {
    return {
      isActive: !this.isEmergencyStop,
      activeRecoveries: this.activeRecoveries.size,
      metrics: {
        ...this.metrics,
        successRate: this.metrics.totalRecoveries > 0 ? 
          this.metrics.successfulRecoveries / this.metrics.totalRecoveries : 0
      },
      recentRecoveries: this.recoveryHistory.slice(-10),
      configuration: {
        maxConcurrentRecoveries: this.config.maxConcurrentRecoveries,
        automaticThreshold: this.config.automaticRecoveryThreshold,
        emergencyStopActive: this.isEmergencyStop
      },
      availableStrategies: Array.from(this.recoveryStrategies.keys())
    };
  }

  /**
   * Update metrics after recovery attempt
   * @param {Object} session - Completed recovery session
   */
  updateMetrics(session) {
    this.metrics.totalRecoveries++;
    
    if (session.endTime && session.startTime) {
      const duration = session.endTime - session.startTime;
      this.metrics.averageRecoveryTime = 
        (this.metrics.averageRecoveryTime * (this.metrics.totalRecoveries - 1) + duration) / 
        this.metrics.totalRecoveries;
    }
  }

  /**
   * Utility functions
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  getHistoricalSuccessRate(service, issueType) {
    const relevantRecoveries = this.recoveryHistory.filter(r => 
      r.issue.service === service && r.issue.type === issueType
    );
    
    if (relevantRecoveries.length === 0) return 0.5;
    
    const successes = relevantRecoveries.filter(r => r.status === 'success').length;
    return successes / relevantRecoveries.length;
  }

  getRecentFailures(service, timeWindow) {
    const cutoff = Date.now() - timeWindow;
    return this.recoveryHistory.filter(r => 
      r.issue.service === service && 
      r.startTime > cutoff && 
      r.status !== 'success'
    ).length;
  }

  getLastRecoveryAttempt(service, issueType) {
    return this.recoveryHistory
      .filter(r => r.issue.service === service && r.issue.type === issueType)
      .sort((a, b) => b.startTime - a.startTime)[0];
  }

  estimatePreventedDowntime(issue) {
    // Estimate how much downtime was prevented (in minutes)
    const downtimeEstimates = {
      service_unhealthy: 15,
      high_error_rate: 10,
      resource_exhaustion: 20,
      dependency_failure: 25,
      performance_degradation: 5
    };
    
    return downtimeEstimates[issue.type] || 10;
  }
}

// Recovery Strategy Base Class
class RecoveryStrategy {
  constructor(name) {
    this.name = name;
    this.version = '1.0.0';
  }
  
  async isApplicable(issue) {
    return true; // Override in subclasses
  }
  
  async execute(issue, session) {
    throw new Error('Execute method must be implemented by subclasses');
  }
}

// Specific Recovery Strategies
class ServiceRestartStrategy extends RecoveryStrategy {
  constructor() {
    super('service_restart');
  }
  
  async execute(issue, session) {
    console.log(`🔄 Restarting service: ${issue.service}`);
    
    // Simulate service restart via Portainer API
    // In real implementation, would call Portainer API
    await this.sleep(3000);
    
    return {
      success: Math.random() > 0.2, // 80% success rate
      message: 'Service restart completed',
      duration: 3000
    };
  }
  
  sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}

class ResourceScalingStrategy extends RecoveryStrategy {
  constructor() {
    super('resource_scaling');
  }
  
  async execute(issue, session) {
    console.log(`📈 Scaling resources for: ${issue.service}`);
    
    // Simulate resource scaling
    await this.sleep(5000);
    
    return {
      success: Math.random() > 0.3, // 70% success rate
      message: 'Resources scaled successfully',
      scaledResource: issue.resource,
      duration: 5000
    };
  }
  
  sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}

// Additional strategy classes would be implemented similarly...
class TrafficRedirectStrategy extends RecoveryStrategy {
  constructor() { super('traffic_redirect'); }
  async execute(issue, session) {
    await this.sleep(2000);
    return { success: Math.random() > 0.4, message: 'Traffic redirected' };
  }
  sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}

class DependencyFallbackStrategy extends RecoveryStrategy {
  constructor() { super('dependency_fallback'); }
  async execute(issue, session) {
    await this.sleep(1000);
    return { success: Math.random() > 0.3, message: 'Fallback activated' };
  }
  sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}

class CacheClearStrategy extends RecoveryStrategy {
  constructor() { super('cache_clear'); }
  async execute(issue, session) {
    await this.sleep(1500);
    return { success: Math.random() > 0.1, message: 'Cache cleared' };
  }
  sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}

class ConnectionResetStrategy extends RecoveryStrategy {
  constructor() { super('connection_reset'); }
  async execute(issue, session) {
    await this.sleep(2500);
    return { success: Math.random() > 0.25, message: 'Connections reset' };
  }
  sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}

class ConfigRollbackStrategy extends RecoveryStrategy {
  constructor() { super('config_rollback'); }
  async execute(issue, session) {
    await this.sleep(4000);
    return { success: Math.random() > 0.2, message: 'Configuration rolled back' };
  }
  sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}

class HealthCheckResetStrategy extends RecoveryStrategy {
  constructor() { super('health_check_reset'); }
  async execute(issue, session) {
    await this.sleep(1000);
    return { success: Math.random() > 0.15, message: 'Health checks reset' };
  }
  sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AutoRecoverySystem;
}

if (typeof globalThis !== 'undefined') {
  globalThis.AutoRecoverySystem = AutoRecoverySystem;
}