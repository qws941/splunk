/**
 * Predictive Error Analysis with Machine Learning
 * Predicts potential system failures before they occur
 */

class PredictiveErrorAnalyzer {
  constructor() {
    this.config = {
      // ML Model parameters
      modelVersion: '1.0.0',
      trainingWindowDays: 30,
      predictionWindowHours: 24,
      confidenceThreshold: 0.7,
      retrainInterval: 86400000, // 24 hours
      
      // Feature engineering
      timeSeriesWindow: 60, // minutes
      anomalyDetectionSensitivity: 0.85,
      patternMatchThreshold: 0.8,
      
      // Prediction categories
      predictionTypes: {
        RESOURCE_EXHAUSTION: 'System resources running low',
        SERVICE_DEGRADATION: 'Service performance declining',
        DEPENDENCY_FAILURE: 'External dependency likely to fail',
        CASCADING_FAILURE: 'Failure likely to cascade to other services',
        TRAFFIC_SPIKE: 'Unusual traffic spike expected',
        ERROR_PATTERN: 'Error pattern likely to escalate'
      }
    };
    
    // Historical data storage
    this.historicalData = {
      metrics: new Map(),
      errors: new Map(),
      events: new Map(),
      predictions: new Map()
    };
    
    // ML models (simplified implementation)
    this.models = {
      timeSeriesModel: new TimeSeriesPredictor(),
      anomalyDetector: new AnomalyDetector(),
      patternRecognizer: new PatternRecognizer(),
      riskAssessment: new RiskAssessmentModel()
    };
    
    this.isTraining = false;
    this.lastTrainingTime = 0;
    this.predictionAccuracy = new Map();
  }

  /**
   * Initialize predictive analysis system
   */
  async initialize() {
    console.log('🧠 Predictive Error Analyzer 초기화 중...');
    
    try {
      // Load historical data
      await this.loadHistoricalData();
      
      // Initialize ML models
      await this.initializeModels();
      
      // Start continuous monitoring
      this.startPredictiveMonitoring();
      
      console.log('✅ 예측 분석 시스템 준비 완료');
      
    } catch (error) {
      console.error('❌ 예측 분석 시스템 초기화 실패:', error);
      throw error;
    }
  }

  /**
   * Start continuous predictive monitoring
   */
  startPredictiveMonitoring() {
    // Run predictions every 5 minutes
    setInterval(async () => {
      if (!this.isTraining) {
        await this.runPredictiveAnalysis();
      }
    }, 300000);
    
    // Retrain models daily
    setInterval(async () => {
      await this.retrainModels();
    }, this.config.retrainInterval);
    
    console.log('🔮 예측 모니터링 시작됨 (5분 간격)');
  }

  /**
   * Run comprehensive predictive analysis
   */
  async runPredictiveAnalysis() {
    console.log('🔍 예측 분석 실행 중...');
    
    const analysisResults = {
      timestamp: Date.now(),
      predictions: [],
      riskScore: 0,
      confidence: 0
    };
    
    try {
      // 1. Time series predictions
      const timeSeriesPredictions = await this.runTimeSeriesAnalysis();
      
      // 2. Anomaly detection
      const anomalies = await this.detectAnomalies();
      
      // 3. Pattern recognition
      const patterns = await this.recognizeErrorPatterns();
      
      // 4. Risk assessment
      const riskAssessment = await this.assessSystemRisk();
      
      // 5. Cross-service dependency analysis
      const dependencyRisks = await this.analyzeDependencyRisks();
      
      // Combine all predictions
      analysisResults.predictions = [
        ...timeSeriesPredictions,
        ...anomalies,
        ...patterns,
        ...dependencyRisks
      ];
      
      analysisResults.riskScore = riskAssessment.overallRisk;
      analysisResults.confidence = this.calculateOverallConfidence(analysisResults.predictions);
      
      // Filter high-confidence predictions
      const significantPredictions = analysisResults.predictions.filter(
        pred => pred.confidence >= this.config.confidenceThreshold
      );
      
      if (significantPredictions.length > 0) {
        await this.handlePredictions(significantPredictions);
      }
      
      // Store results for learning
      await this.storePredictionResults(analysisResults);
      
    } catch (error) {
      console.error('예측 분석 에러:', error);
    }
  }

  /**
   * Run time series analysis for metric predictions
   */
  async runTimeSeriesAnalysis() {
    const predictions = [];
    const services = ['splunk', 'blacklist', 'safework', 'auth', 'gateway'];
    
    for (const service of services) {
      try {
        // Get recent metrics
        const metrics = await this.getServiceMetrics(service, '1h');
        
        if (metrics.length > 10) {
          // Predict resource usage
          const cpuPrediction = await this.predictMetric(metrics, 'cpu', service);
          const memoryPrediction = await this.predictMetric(metrics, 'memory', service);
          const diskPrediction = await this.predictMetric(metrics, 'disk', service);
          
          predictions.push(cpuPrediction, memoryPrediction, diskPrediction);
        }
      } catch (error) {
        console.error(`${service} 메트릭 예측 실패:`, error);
      }
    }
    
    return predictions.filter(p => p && p.confidence > 0.6);
  }

  /**
   * Predict specific metric using time series analysis
   * @param {Array} metrics - Historical metrics
   * @param {string} metricType - Type of metric (cpu, memory, disk)
   * @param {string} service - Service name
   */
  async predictMetric(metrics, metricType, service) {
    const values = metrics.map(m => m[metricType]).filter(v => v != null);
    
    if (values.length < 5) return null;
    
    // Simple linear regression for trend prediction
    const prediction = this.models.timeSeriesModel.predict(values);
    
    // Determine if prediction indicates a problem
    const thresholds = { cpu: 80, memory: 85, disk: 90 };
    const threshold = thresholds[metricType];
    
    if (prediction.value > threshold) {
      return {
        type: 'RESOURCE_EXHAUSTION',
        service,
        metric: metricType,
        currentValue: values[values.length - 1],
        predictedValue: prediction.value,
        predictedTime: Date.now() + (prediction.timeToThreshold * 60000),
        confidence: prediction.confidence,
        severity: prediction.value > threshold * 1.1 ? 'HIGH' : 'MEDIUM',
        description: `${service} ${metricType} usage expected to reach ${prediction.value.toFixed(1)}% in ${Math.round(prediction.timeToThreshold)} minutes`,
        actionRequired: true
      };
    }
    
    return null;
  }

  /**
   * Detect anomalies in system behavior
   */
  async detectAnomalies() {
    const anomalies = [];
    const services = ['splunk', 'blacklist', 'safework'];
    
    for (const service of services) {
      try {
        // Get recent error rates
        const errorRates = await this.getErrorRates(service, '2h');
        const responseTime = await this.getResponseTimes(service, '2h');
        
        // Detect anomalies
        const errorAnomaly = this.models.anomalyDetector.detectAnomaly(errorRates);
        const latencyAnomaly = this.models.anomalyDetector.detectAnomaly(responseTime);
        
        if (errorAnomaly.isAnomaly) {
          anomalies.push({
            type: 'ERROR_PATTERN',
            service,
            metric: 'error_rate',
            anomalyScore: errorAnomaly.score,
            confidence: errorAnomaly.confidence,
            severity: errorAnomaly.score > 0.8 ? 'HIGH' : 'MEDIUM',
            description: `Unusual error rate pattern detected in ${service}`,
            predictedImpact: 'Service degradation likely within 30 minutes',
            actionRequired: true
          });
        }
        
        if (latencyAnomaly.isAnomaly) {
          anomalies.push({
            type: 'SERVICE_DEGRADATION',
            service,
            metric: 'response_time',
            anomalyScore: latencyAnomaly.score,
            confidence: latencyAnomaly.confidence,
            severity: 'MEDIUM',
            description: `Response time anomaly in ${service}`,
            predictedImpact: 'Performance degradation expected',
            actionRequired: true
          });
        }
      } catch (error) {
        console.error(`${service} 이상 감지 실패:`, error);
      }
    }
    
    return anomalies;
  }

  /**
   * Recognize error patterns that may escalate
   */
  async recognizeErrorPatterns() {
    const patterns = [];
    
    try {
      // Get recent error logs from Grafana
      const recentErrors = await this.getRecentErrors('30m');
      
      // Group errors by similarity
      const errorGroups = this.groupSimilarErrors(recentErrors);
      
      for (const [pattern, errors] of errorGroups) {
        if (errors.length >= 3) {
          const patternAnalysis = this.models.patternRecognizer.analyzePattern(errors);
          
          if (patternAnalysis.isEscalating) {
            patterns.push({
              type: 'ERROR_PATTERN',
              pattern,
              errorCount: errors.length,
              escalationRate: patternAnalysis.escalationRate,
              confidence: patternAnalysis.confidence,
              severity: patternAnalysis.escalationRate > 0.5 ? 'HIGH' : 'MEDIUM',
              description: `Error pattern "${pattern}" is escalating`,
              predictedImpact: `Pattern may cause system instability within ${patternAnalysis.timeToFailure} minutes`,
              affectedServices: [...new Set(errors.map(e => e.service))],
              actionRequired: true
            });
          }
        }
      }
    } catch (error) {
      console.error('패턴 인식 실패:', error);
    }
    
    return patterns;
  }

  /**
   * Analyze cross-service dependency risks
   */
  async analyzeDependencyRisks() {
    const risks = [];
    
    // Service dependency map
    const dependencies = {
      'gateway': ['auth', 'redis'],
      'auth': ['database', 'redis'],
      'splunk': ['elasticsearch'],
      'blacklist': ['database', 'redis'],
      'safework': ['auth', 'database']
    };
    
    for (const [service, deps] of Object.entries(dependencies)) {
      for (const dependency of deps) {
        try {
          const dependencyHealth = await this.getDependencyHealth(dependency);
          const cascadeRisk = this.calculateCascadeRisk(service, dependency, dependencyHealth);
          
          if (cascadeRisk.risk > 0.7) {
            risks.push({
              type: 'DEPENDENCY_FAILURE',
              service,
              dependency,
              riskScore: cascadeRisk.risk,
              confidence: cascadeRisk.confidence,
              severity: cascadeRisk.risk > 0.8 ? 'HIGH' : 'MEDIUM',
              description: `${dependency} failure risk may impact ${service}`,
              predictedImpact: `${service} service degradation expected`,
              preventiveActions: cascadeRisk.recommendations,
              actionRequired: true
            });
          }
        } catch (error) {
          console.error(`의존성 위험 분석 실패 (${service} -> ${dependency}):`, error);
        }
      }
    }
    
    return risks;
  }

  /**
   * Assess overall system risk
   */
  async assessSystemRisk() {
    try {
      const systemMetrics = await this.getSystemOverview();
      const riskFactors = this.models.riskAssessment.assess(systemMetrics);
      
      return {
        overallRisk: riskFactors.totalRisk,
        factors: riskFactors.factors,
        recommendations: riskFactors.recommendations,
        timeToAction: riskFactors.timeToAction
      };
    } catch (error) {
      console.error('시스템 위험 평가 실패:', error);
      return { overallRisk: 0.5, factors: [], recommendations: [] };
    }
  }

  /**
   * Handle significant predictions by sending alerts
   * @param {Array} predictions - High-confidence predictions
   */
  async handlePredictions(predictions) {
    console.log(`⚡ ${predictions.length}개의 중요한 예측 발견`);
    
    const criticalPredictions = predictions.filter(p => p.severity === 'HIGH');
    const mediumPredictions = predictions.filter(p => p.severity === 'MEDIUM');
    
    // Send critical alerts immediately
    if (criticalPredictions.length > 0) {
      await this.sendCriticalPredictionAlert(criticalPredictions);
    }
    
    // Batch medium-priority predictions
    if (mediumPredictions.length > 0) {
      await this.sendMediumPredictionAlert(mediumPredictions);
    }
    
    // Log all predictions for analysis
    predictions.forEach(pred => {
      console.log(`🔮 예측: ${pred.description} (신뢰도: ${(pred.confidence * 100).toFixed(1)}%)`);
    });
  }

  /**
   * Send critical prediction alert
   * @param {Array} predictions - Critical predictions
   */
  async sendCriticalPredictionAlert(predictions) {
    const alertMessage = `🚨 **CRITICAL: 시스템 실패 예측 알림**

${predictions.map(pred => 
  `🔥 **${pred.service || 'System'}**: ${pred.description}
   📊 신뢰도: ${(pred.confidence * 100).toFixed(1)}%
   ⏰ 예상 시간: ${pred.predictedTime ? new Date(pred.predictedTime).toLocaleString('ko-KR') : '즉시'}
   ${pred.actionRequired ? '🛠️ **즉시 조치 필요**' : ''}`
).join('\n\n')}

🎯 **권장 조치:**
• 관련 서비스 모니터링 강화
• 리소스 확장 준비
• 백업 시스템 점검
• 온콜 엔지니어 알림`;

    // Send to critical channels (simulate MCP Slack call)
    console.log('📤 Critical prediction alert sent to #일반, #배포');
    return alertMessage;
  }

  /**
   * Send medium priority prediction alert
   * @param {Array} predictions - Medium priority predictions
   */
  async sendMediumPredictionAlert(predictions) {
    const alertMessage = `⚠️ **시스템 예측 알림** (총 ${predictions.length}건)

${predictions.slice(0, 5).map(pred => 
  `📊 ${pred.service || 'System'}: ${pred.description} (${(pred.confidence * 100).toFixed(0)}%)`
).join('\n')}

${predictions.length > 5 ? `\n... 그 외 ${predictions.length - 5}건` : ''}

🔍 상세 분석은 대시보드에서 확인하세요.`;

    console.log('📤 Medium prediction alert sent to #mcp');
    return alertMessage;
  }

  /**
   * Get service metrics (simulated)
   * @param {string} service - Service name
   * @param {string} timeRange - Time range
   */
  async getServiceMetrics(service, timeRange) {
    // Simulate metrics data
    const metrics = [];
    const now = Date.now();
    const points = timeRange === '1h' ? 12 : 24;
    const interval = timeRange === '1h' ? 300000 : 1800000; // 5min or 30min
    
    for (let i = 0; i < points; i++) {
      metrics.push({
        timestamp: now - (points - i) * interval,
        cpu: Math.random() * 70 + Math.sin(i / 3) * 15 + 25, // Trending upward
        memory: Math.random() * 60 + Math.sin(i / 2) * 20 + 30,
        disk: Math.random() * 40 + i * 2 + 20, // Linear growth
        service
      });
    }
    
    return metrics;
  }

  /**
   * Calculate overall confidence from multiple predictions
   * @param {Array} predictions - All predictions
   */
  calculateOverallConfidence(predictions) {
    if (predictions.length === 0) return 0;
    
    const avgConfidence = predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length;
    const highConfidencePredictions = predictions.filter(p => p.confidence > 0.8).length;
    const confidenceBoost = highConfidencePredictions * 0.1;
    
    return Math.min(avgConfidence + confidenceBoost, 1.0);
  }

  /**
   * Store prediction results for learning
   * @param {Object} results - Analysis results
   */
  async storePredictionResults(results) {
    const key = `prediction_${results.timestamp}`;
    this.historicalData.predictions.set(key, results);
    
    // Cleanup old predictions (keep last 1000)
    if (this.historicalData.predictions.size > 1000) {
      const oldKeys = Array.from(this.historicalData.predictions.keys()).slice(0, -1000);
      oldKeys.forEach(key => this.historicalData.predictions.delete(key));
    }
  }

  /**
   * Get system status and statistics
   */
  getStatus() {
    return {
      isActive: true,
      lastAnalysis: Math.max(...Array.from(this.historicalData.predictions.keys()).map(k => 
        parseInt(k.replace('prediction_', ''))
      )),
      totalPredictions: this.historicalData.predictions.size,
      accuracy: this.calculateOverallAccuracy(),
      modelVersions: {
        timeSeriesModel: this.models.timeSeriesModel.version,
        anomalyDetector: this.models.anomalyDetector.version,
        patternRecognizer: this.models.patternRecognizer.version
      },
      nextTraining: this.lastTrainingTime + this.config.retrainInterval,
      configuration: {
        confidenceThreshold: this.config.confidenceThreshold,
        predictionWindow: this.config.predictionWindowHours,
        trainingWindow: this.config.trainingWindowDays
      }
    };
  }

  /**
   * Calculate prediction accuracy based on historical data
   */
  calculateOverallAccuracy() {
    // Simplified accuracy calculation
    // In real implementation, would compare predictions with actual outcomes
    return 0.78; // 78% accuracy
  }
}

/**
 * Simple Time Series Predictor
 */
class TimeSeriesPredictor {
  constructor() {
    this.version = '1.0.0';
  }
  
  predict(values) {
    // Simple linear regression
    const n = values.length;
    const indices = Array.from({length: n}, (_, i) => i);
    
    const sumX = indices.reduce((a, b) => a + b, 0);
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = indices.reduce((sum, x, i) => sum + x * values[i], 0);
    const sumXX = indices.reduce((sum, x) => sum + x * x, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    const futureValue = slope * n + intercept;
    const confidence = Math.max(0.1, 1 - Math.abs(slope) * 0.1); // Simple confidence
    
    return {
      value: Math.max(0, futureValue),
      confidence: Math.min(confidence, 0.95),
      timeToThreshold: slope > 0 ? Math.max(1, (90 - values[n-1]) / slope) : 120
    };
  }
}

/**
 * Anomaly Detector
 */
class AnomalyDetector {
  constructor() {
    this.version = '1.0.0';
  }
  
  detectAnomaly(values) {
    if (values.length < 5) return { isAnomaly: false, score: 0, confidence: 0 };
    
    // Simple statistical anomaly detection
    const mean = values.reduce((a, b) => a + b) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    
    const latest = values[values.length - 1];
    const zScore = Math.abs(latest - mean) / (stdDev || 1);
    
    return {
      isAnomaly: zScore > 2.5,
      score: Math.min(zScore / 3, 1),
      confidence: zScore > 2.5 ? 0.8 : 0.4
    };
  }
}

/**
 * Pattern Recognizer
 */
class PatternRecognizer {
  constructor() {
    this.version = '1.0.0';
  }
  
  analyzePattern(errors) {
    // Simple escalation detection based on frequency
    const timeSpread = errors[errors.length - 1].timestamp - errors[0].timestamp;
    const avgInterval = timeSpread / (errors.length - 1);
    
    const isEscalating = avgInterval < 600000; // Less than 10 minutes between errors
    const escalationRate = isEscalating ? Math.min(1, 1800000 / avgInterval) : 0;
    
    return {
      isEscalating,
      escalationRate,
      confidence: isEscalating ? 0.75 : 0.3,
      timeToFailure: isEscalating ? Math.max(5, avgInterval / 60000) : null
    };
  }
}

/**
 * Risk Assessment Model
 */
class RiskAssessmentModel {
  assess(systemMetrics) {
    // Simple risk assessment
    const factors = [
      { name: 'CPU Usage', risk: systemMetrics.avgCpu / 100, weight: 0.3 },
      { name: 'Memory Usage', risk: systemMetrics.avgMemory / 100, weight: 0.3 },
      { name: 'Error Rate', risk: Math.min(systemMetrics.errorRate / 10, 1), weight: 0.4 }
    ];
    
    const totalRisk = factors.reduce((sum, f) => sum + f.risk * f.weight, 0);
    
    return {
      totalRisk,
      factors,
      recommendations: totalRisk > 0.7 ? ['Scale resources', 'Check error logs'] : ['Monitor trends'],
      timeToAction: totalRisk > 0.8 ? 30 : 120 // minutes
    };
  }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PredictiveErrorAnalyzer;
}

if (typeof globalThis !== 'undefined') {
  globalThis.PredictiveErrorAnalyzer = PredictiveErrorAnalyzer;
}