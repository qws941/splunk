/**
 * AI-Powered Alert Classification System
 * Uses machine learning to intelligently classify and prioritize alerts
 */

class AIAlertClassifier {
  constructor() {
    this.config = {
      // Classification thresholds
      criticalThreshold: 0.8,
      warningThreshold: 0.6,
      infoThreshold: 0.3,
      
      // ML model parameters
      learningRate: 0.01,
      maxFeatures: 1000,
      trainingWindowSize: 10000,
      
      // Alert patterns database
      knownPatterns: new Map(),
      alertHistory: [],
      
      // Cloudflare AI integration
      cloudflareAccountId: process.env.CLOUDFLARE_ACCOUNT_ID,
      cloudflareApiToken: process.env.CLOUDFLARE_API_TOKEN
    };
    
    this.alertClassifications = {
      CRITICAL: {
        level: 5,
        emoji: '🚨',
        channels: ['일반', '배포'],
        autoAction: 'immediate_notification',
        escalation: true
      },
      HIGH: {
        level: 4,
        emoji: '🔥',
        channels: ['배포'],
        autoAction: 'priority_notification',
        escalation: false
      },
      MEDIUM: {
        level: 3,
        emoji: '⚠️',
        channels: ['mcp'],
        autoAction: 'standard_notification',
        escalation: false
      },
      LOW: {
        level: 2,
        emoji: '📊',
        channels: ['mcp'],
        autoAction: 'batch_notification',
        escalation: false
      },
      INFO: {
        level: 1,
        emoji: 'ℹ️',
        channels: [],
        autoAction: 'log_only',
        escalation: false
      }
    };
    
    // Initialize feature extractors
    this.featureExtractors = {
      textLength: (text) => text.length,
      errorKeywords: this.extractErrorKeywords.bind(this),
      severity: this.extractSeverityScore.bind(this),
      frequency: this.calculateFrequency.bind(this),
      timeContext: this.extractTimeContext.bind(this),
      serviceContext: this.extractServiceContext.bind(this)
    };
    
    this.isModelTrained = false;
  }

  /**
   * Classify alert using AI analysis
   * @param {Object} alert - Alert object
   * @returns {Object} Classification result
   */
  async classifyAlert(alert) {
    console.log(`🤖 AI 알림 분류 시작: ${alert.message?.substring(0, 50)}...`);
    
    try {
      // Extract features
      const features = await this.extractFeatures(alert);
      
      // Use Cloudflare AI for advanced classification
      const aiClassification = await this.getCloudflareAIClassification(alert, features);
      
      // Combine rule-based and AI classification
      const finalClassification = await this.combineClassifications(alert, features, aiClassification);
      
      // Learn from classification
      await this.updateLearningModel(alert, finalClassification);
      
      console.log(`✅ 분류 완료: ${finalClassification.level} (신뢰도: ${finalClassification.confidence})`);
      
      return finalClassification;
      
    } catch (error) {
      console.error('AI 분류 에러:', error);
      return this.fallbackClassification(alert);
    }
  }

  /**
   * Extract features from alert
   * @param {Object} alert - Alert object
   */
  async extractFeatures(alert) {
    const features = {};
    
    // Basic text features
    features.textLength = alert.message?.length || 0;
    features.hasStackTrace = /^\s+at\s/.test(alert.message || '');
    features.hasTimestamp = /\d{4}-\d{2}-\d{2}/.test(alert.message || '');
    
    // Error keywords extraction
    features.errorKeywords = this.extractErrorKeywords(alert.message || '');
    features.severityScore = this.extractSeverityScore(alert.message || '');
    
    // Context features
    features.serviceName = alert.service || 'unknown';
    features.environment = alert.environment || 'production';
    features.timestamp = alert.timestamp || Date.now();
    
    // Frequency features
    features.frequency = await this.calculateFrequency(alert);
    features.isRecurring = features.frequency > 3;
    
    // Time context
    features.timeContext = this.extractTimeContext(alert.timestamp);
    features.isBusinessHours = features.timeContext.isBusinessHours;
    
    // Service health context
    features.serviceHealth = await this.getServiceHealthScore(alert.service);
    
    return features;
  }

  /**
   * Use Cloudflare AI for advanced text classification
   * @param {Object} alert - Alert object
   * @param {Object} features - Extracted features
   */
  async getCloudflareAIClassification(alert, features) {
    try {
      // Prepare prompt for AI classification
      const classificationPrompt = `
Classify this system alert for severity and priority:

Alert Message: "${alert.message}"
Service: ${features.serviceName}
Environment: ${features.environment}
Error Keywords: ${features.errorKeywords.join(', ')}
Frequency: ${features.frequency} occurrences
Is Recurring: ${features.isRecurring}
Business Hours: ${features.isBusinessHours}

Classification Categories:
- CRITICAL: System down, data loss, security breach
- HIGH: Service degraded, user impact, deployment issues
- MEDIUM: Performance issues, minor errors, warnings
- LOW: Info messages, debug logs, maintenance notices

Respond with JSON: {"level": "CRITICAL|HIGH|MEDIUM|LOW", "confidence": 0.0-1.0, "reasoning": "explanation"}`;

      // Call Cloudflare AI (simulated for now)
      const aiResponse = await this.callCloudflareAI(classificationPrompt);
      
      return aiResponse || this.fallbackAIClassification(features);
      
    } catch (error) {
      console.error('Cloudflare AI 분류 실패:', error);
      return this.fallbackAIClassification(features);
    }
  }

  /**
   * Call Cloudflare AI API (simulated)
   * @param {string} prompt - Classification prompt
   */
  async callCloudflareAI(prompt) {
    // In real implementation, would call:
    // const response = await fetch(`https://api.cloudflare.com/client/v4/accounts/${this.config.cloudflareAccountId}/ai/run/@cf/meta/llama-2-7b-chat-int8`, {
    //   method: 'POST',
    //   headers: {
    //     'Authorization': `Bearer ${this.config.cloudflareApiToken}`,
    //     'Content-Type': 'application/json'
    //   },
    //   body: JSON.stringify({
    //     messages: [{ role: 'user', content: prompt }]
    //   })
    // });
    
    // For now, simulate intelligent classification
    const mockResponse = this.simulateAIClassification(prompt);
    return mockResponse;
  }

  /**
   * Simulate AI classification (for testing)
   * @param {string} prompt - Classification prompt
   */
  simulateAIClassification(prompt) {
    const text = prompt.toLowerCase();
    
    if (text.includes('critical') || text.includes('fatal') || text.includes('down')) {
      return { level: 'CRITICAL', confidence: 0.95, reasoning: 'System critical error detected' };
    } else if (text.includes('error') || text.includes('failed') || text.includes('exception')) {
      return { level: 'HIGH', confidence: 0.85, reasoning: 'Error condition detected' };
    } else if (text.includes('warning') || text.includes('degraded')) {
      return { level: 'MEDIUM', confidence: 0.75, reasoning: 'Warning condition detected' };
    } else {
      return { level: 'LOW', confidence: 0.65, reasoning: 'Info or debug message' };
    }
  }

  /**
   * Combine rule-based and AI classifications
   * @param {Object} alert - Original alert
   * @param {Object} features - Extracted features
   * @param {Object} aiClassification - AI classification result
   */
  async combineClassifications(alert, features, aiClassification) {
    const ruleBasedScore = this.getRuleBasedScore(features);
    const aiScore = this.convertLevelToScore(aiClassification.level);
    
    // Weighted combination (70% AI, 30% rules)
    const combinedScore = (aiScore * 0.7) + (ruleBasedScore * 0.3);
    const finalLevel = this.convertScoreToLevel(combinedScore);
    
    // Apply business logic adjustments
    const adjustedClassification = this.applyBusinessRules(finalLevel, features, alert);
    
    return {
      level: adjustedClassification.level,
      priority: adjustedClassification.priority,
      confidence: aiClassification.confidence * 0.8 + 0.2, // Slight confidence adjustment
      reasoning: aiClassification.reasoning,
      features: features,
      aiScore: aiScore,
      ruleScore: ruleBasedScore,
      combinedScore: combinedScore,
      autoActions: this.alertClassifications[adjustedClassification.level].autoAction,
      channels: this.alertClassifications[adjustedClassification.level].channels,
      escalation: this.alertClassifications[adjustedClassification.level].escalation,
      timestamp: Date.now()
    };
  }

  /**
   * Extract error keywords and weight them
   * @param {string} text - Alert text
   */
  extractErrorKeywords(text) {
    const keywords = {
      critical: ['fatal', 'critical', 'emergency', 'panic', 'crash', 'down', 'outage'],
      high: ['error', 'exception', 'failed', 'failure', 'timeout', 'refused', 'denied'],
      medium: ['warning', 'warn', 'degraded', 'slow', 'retry', 'reconnect'],
      low: ['info', 'debug', 'trace', 'notice', 'success', 'completed']
    };
    
    const found = [];
    const lowerText = text.toLowerCase();
    
    for (const [level, words] of Object.entries(keywords)) {
      for (const word of words) {
        if (lowerText.includes(word)) {
          found.push({ word, level, weight: this.getKeywordWeight(word) });
        }
      }
    }
    
    return found;
  }

  /**
   * Calculate keyword weight
   * @param {string} keyword - Keyword to weight
   */
  getKeywordWeight(keyword) {
    const weights = {
      'fatal': 1.0, 'critical': 1.0, 'crash': 0.9, 'down': 0.9,
      'error': 0.8, 'exception': 0.8, 'failed': 0.7, 'failure': 0.7,
      'warning': 0.5, 'warn': 0.5, 'degraded': 0.6,
      'info': 0.2, 'debug': 0.1, 'trace': 0.1
    };
    return weights[keyword] || 0.5;
  }

  /**
   * Extract severity score from text
   * @param {string} text - Alert text
   */
  extractSeverityScore(text) {
    const keywords = this.extractErrorKeywords(text);
    if (keywords.length === 0) return 0.3;
    
    const maxWeight = Math.max(...keywords.map(k => k.weight));
    const avgWeight = keywords.reduce((sum, k) => sum + k.weight, 0) / keywords.length;
    
    return (maxWeight * 0.7) + (avgWeight * 0.3);
  }

  /**
   * Calculate alert frequency
   * @param {Object} alert - Alert object
   */
  async calculateFrequency(alert) {
    const timeWindow = 3600000; // 1 hour
    const now = Date.now();
    const similarAlerts = this.alertHistory.filter(histAlert => 
      histAlert.service === alert.service &&
      histAlert.message?.substring(0, 100) === alert.message?.substring(0, 100) &&
      (now - histAlert.timestamp) < timeWindow
    );
    
    return similarAlerts.length;
  }

  /**
   * Extract time context
   * @param {number} timestamp - Alert timestamp
   */
  extractTimeContext(timestamp) {
    const date = new Date(timestamp);
    const hour = date.getHours();
    const dayOfWeek = date.getDay();
    
    return {
      hour,
      dayOfWeek,
      isBusinessHours: hour >= 9 && hour <= 18 && dayOfWeek >= 1 && dayOfWeek <= 5,
      isWeekend: dayOfWeek === 0 || dayOfWeek === 6,
      isNightTime: hour >= 22 || hour <= 6
    };
  }

  /**
   * Extract service context
   * @param {Object} alert - Alert object
   */
  extractServiceContext(alert) {
    const criticalServices = ['auth', 'gateway', 'payment', 'database'];
    const isCriticalService = criticalServices.includes(alert.service);
    
    return {
      isCritical: isCriticalService,
      serviceType: this.getServiceType(alert.service),
      dependencies: this.getServiceDependencies(alert.service)
    };
  }

  /**
   * Get service health score
   * @param {string} serviceName - Service name
   */
  async getServiceHealthScore(serviceName) {
    // Simulate health check
    const healthScores = {
      'auth': 0.95,
      'gateway': 0.92,
      'splunk': 0.88,
      'blacklist': 0.94,
      'safework': 0.91
    };
    
    return healthScores[serviceName] || 0.85;
  }

  /**
   * Update learning model with new classification
   * @param {Object} alert - Original alert
   * @param {Object} classification - Final classification
   */
  async updateLearningModel(alert, classification) {
    // Store classification result for learning
    this.alertHistory.push({
      alert,
      classification,
      timestamp: Date.now()
    });
    
    // Trim history to manageable size
    if (this.alertHistory.length > this.config.trainingWindowSize) {
      this.alertHistory = this.alertHistory.slice(-this.config.trainingWindowSize);
    }
    
    // Update pattern recognition
    const pattern = this.generatePattern(alert);
    if (!this.config.knownPatterns.has(pattern)) {
      this.config.knownPatterns.set(pattern, []);
    }
    this.config.knownPatterns.get(pattern).push(classification);
  }

  /**
   * Generate pattern signature for alert
   * @param {Object} alert - Alert object
   */
  generatePattern(alert) {
    const signature = [
      alert.service || 'unknown',
      alert.message?.substring(0, 50).replace(/\d+/g, 'N') || '',
      alert.level || 'info'
    ].join('|');
    
    return signature;
  }

  /**
   * Get service type classification
   * @param {string} serviceName - Service name
   */
  getServiceType(serviceName) {
    const types = {
      'auth': 'security',
      'gateway': 'infrastructure', 
      'database': 'data',
      'payment': 'business',
      'monitoring': 'ops'
    };
    return types[serviceName] || 'general';
  }

  /**
   * Get service dependencies
   * @param {string} serviceName - Service name
   */
  getServiceDependencies(serviceName) {
    const dependencies = {
      'auth': ['database', 'redis'],
      'gateway': ['auth', 'services'],
      'payment': ['auth', 'database', 'external-api']
    };
    return dependencies[serviceName] || [];
  }

  /**
   * Apply business rules to classification
   * @param {string} level - Initial classification level
   * @param {Object} features - Alert features
   * @param {Object} alert - Original alert
   */
  applyBusinessRules(level, features, alert) {
    let adjustedLevel = level;
    let priority = this.alertClassifications[level].level;
    
    // Escalate critical services
    if (features.serviceContext?.isCritical && level === 'HIGH') {
      adjustedLevel = 'CRITICAL';
      priority = this.alertClassifications.CRITICAL.level;
    }
    
    // De-escalate during maintenance windows
    if (this.isMaintenanceWindow()) {
      if (adjustedLevel === 'HIGH') adjustedLevel = 'MEDIUM';
      if (adjustedLevel === 'MEDIUM') adjustedLevel = 'LOW';
    }
    
    // Escalate recurring issues
    if (features.frequency > 5 && adjustedLevel === 'MEDIUM') {
      adjustedLevel = 'HIGH';
    }
    
    return { level: adjustedLevel, priority };
  }

  /**
   * Check if currently in maintenance window
   */
  isMaintenanceWindow() {
    const now = new Date();
    const hour = now.getHours();
    // Maintenance window: 2-4 AM
    return hour >= 2 && hour <= 4;
  }

  /**
   * Convert level to numerical score
   * @param {string} level - Classification level
   */
  convertLevelToScore(level) {
    const scores = { 'CRITICAL': 1.0, 'HIGH': 0.75, 'MEDIUM': 0.5, 'LOW': 0.25, 'INFO': 0.0 };
    return scores[level] || 0.5;
  }

  /**
   * Convert numerical score to level
   * @param {number} score - Numerical score
   */
  convertScoreToLevel(score) {
    if (score >= 0.8) return 'CRITICAL';
    if (score >= 0.6) return 'HIGH';
    if (score >= 0.4) return 'MEDIUM';
    if (score >= 0.2) return 'LOW';
    return 'INFO';
  }

  /**
   * Get rule-based classification score
   * @param {Object} features - Alert features
   */
  getRuleBasedScore(features) {
    let score = 0.3; // Base score
    
    // Severity keywords
    if (features.errorKeywords.length > 0) {
      const maxWeight = Math.max(...features.errorKeywords.map(k => k.weight));
      score = Math.max(score, maxWeight);
    }
    
    // Critical service bonus
    if (features.serviceContext?.isCritical) {
      score += 0.2;
    }
    
    // Frequency penalty/bonus
    if (features.frequency > 5) {
      score += 0.15; // Recurring issue
    }
    
    // Business hours adjustment
    if (features.isBusinessHours) {
      score += 0.1;
    }
    
    return Math.min(score, 1.0);
  }

  /**
   * Fallback classification when AI fails
   * @param {Object} alert - Alert object
   */
  fallbackClassification(alert) {
    const message = (alert.message || '').toLowerCase();
    
    if (message.includes('critical') || message.includes('fatal')) {
      return { level: 'CRITICAL', confidence: 0.8, reasoning: 'Rule-based fallback' };
    } else if (message.includes('error') || message.includes('failed')) {
      return { level: 'HIGH', confidence: 0.7, reasoning: 'Rule-based fallback' };
    } else {
      return { level: 'MEDIUM', confidence: 0.6, reasoning: 'Rule-based fallback' };
    }
  }

  /**
   * Fallback AI classification
   * @param {Object} features - Alert features
   */
  fallbackAIClassification(features) {
    const score = this.getRuleBasedScore(features);
    const level = this.convertScoreToLevel(score);
    
    return {
      level,
      confidence: 0.6,
      reasoning: 'Fallback rule-based classification'
    };
  }

  /**
   * Get classification statistics
   */
  getStatistics() {
    const stats = {
      totalAlerts: this.alertHistory.length,
      classifications: { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 },
      averageConfidence: 0,
      topPatterns: []
    };
    
    // Calculate classification distribution
    this.alertHistory.forEach(entry => {
      const level = entry.classification.level;
      stats.classifications[level]++;
      stats.averageConfidence += entry.classification.confidence;
    });
    
    if (this.alertHistory.length > 0) {
      stats.averageConfidence /= this.alertHistory.length;
    }
    
    // Top patterns
    const patternCounts = new Map();
    this.config.knownPatterns.forEach((classifications, pattern) => {
      patternCounts.set(pattern, classifications.length);
    });
    
    stats.topPatterns = Array.from(patternCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
    
    return stats;
  }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AIAlertClassifier;
}

if (typeof globalThis !== 'undefined') {
  globalThis.AIAlertClassifier = AIAlertClassifier;
}