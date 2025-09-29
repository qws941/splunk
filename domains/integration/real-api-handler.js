/**
 * Real API Handler - Production Ready Implementation
 * Removes all mocks and implements actual API calls with robust error handling
 */

import { CircuitBreakerManager } from '../defense/circuit-breaker.js';
import { logger } from '../monitoring/production-logger.js';

export class RealAPIHandler {
  constructor() {
    this.retryConfig = {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 10000,
      backoffFactor: 2
    };

    this.timeouts = {
      connection: 30000,   // 30 seconds
      request: 60000,     // 60 seconds
      longOperation: 300000 // 5 minutes for large queries
    };

    // Initialize circuit breaker manager for resilient API calls
    this.circuitManager = new CircuitBreakerManager();

    // Create child logger for API operations
    this.logger = logger.child({ component: 'RealAPIHandler' });

    this.logger.info('RealAPIHandler initialized with circuit breaker protection');
  }

  /**
   * Make HTTP request with circuit breaker protection and retry logic
   */
  async makeHttpRequest(url, options = {}, retryCount = 0) {
    const {
      method = 'GET',
      headers = {},
      body = null,
      timeout = this.timeouts.request,
      validateResponse = true,
      serviceName = this.getServiceNameFromURL(url)
    } = options;

    // Use circuit breaker for resilient API calls
    return this.circuitManager.execute(
      serviceName,
      async () => {
        const startTime = Date.now();
        try {
          this.logger.debug(`API request starting`, {
            method, url, attempt: retryCount + 1, serviceName
          });

          // Create AbortController for timeout
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), timeout);

          const response = await fetch(url, {
            method,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
              'User-Agent': 'Splunk-FortiNet-Integration/2.0',
              ...headers
            },
            body: body ? JSON.stringify(body) : null,
            signal: controller.signal
          });

          clearTimeout(timeoutId);
          const responseTime = Date.now() - startTime;

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const data = await response.json();

          if (validateResponse && this.hasAPIError(data)) {
            throw new Error(`API Error: ${this.extractErrorMessage(data)}`);
          }

          // Log successful API call
          this.logger.logAPICall(method, url, response.status, responseTime);

          return data;

        } catch (error) {
          const responseTime = Date.now() - startTime;
          this.logger.logAPICall(method, url, null, responseTime, error);

          // Retry logic for recoverable errors
          if (this.isRetryableError(error) && retryCount < this.retryConfig.maxRetries) {
            const delay = this.calculateRetryDelay(retryCount);
            this.logger.warn(`Retrying API call`, {
              method, url, error: error.message, retryIn: delay, attempt: retryCount + 1
            });

            await this.sleep(delay);
            return this.makeHttpRequest(url, { ...options, serviceName }, retryCount + 1);
          }

          throw error;
        }
      },
      async (reason) => {
        // Circuit breaker fallback with proper logging
        this.logger.logCircuitBreaker(serviceName, 'OPEN', 'fallback_triggered', { reason });
        return { error: `Service ${serviceName} temporarily unavailable: ${reason}` };
      },
      {
        failureThreshold: 5,
        recoveryTimeout: 30000,
        timeout: timeout
      }
    );
  }

  /**
   * Make FortiManager JSON-RPC call
   */
  async makeFortiManagerCall(baseURL, sessionId, method, url, params = {}) {
    const rpcRequest = {
      id: Date.now(),
      method: method,
      params: [{
        url: url,
        session: sessionId,
        ...params
      }]
    };

    const response = await this.makeHttpRequest(`${baseURL}/jsonrpc`, {
      method: 'POST',
      body: rpcRequest,
      timeout: this.timeouts.longOperation
    });

    if (response.error) {
      throw new Error(`FortiManager Error: ${response.error.message || 'Unknown error'}`);
    }

    return response;
  }

  /**
   * Make FortiAnalyzer REST API call
   */
  async makeFortiAnalyzerCall(baseURL, accessToken, endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const fullURL = `${baseURL}${endpoint}${queryString ? '?' + queryString : ''}`;

    return this.makeHttpRequest(fullURL, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json'
      },
      timeout: this.timeouts.longOperation
    });
  }

  /**
   * Make Splunk HEC call
   */
  async makeSplunkHECCall(baseURL, token, events) {
    const hecURL = `${baseURL}/services/collector/event`;

    // Format events for HEC
    const formattedEvents = Array.isArray(events) ? events : [events];
    const body = formattedEvents.map(event => ({
      time: event.time || Math.floor(Date.now() / 1000),
      source: event.source || 'fortimanager',
      sourcetype: event.sourcetype || 'fortigate:traffic',
      index: event.index || 'security',
      event: event.event || event
    }));

    return this.makeHttpRequest(hecURL, {
      method: 'POST',
      headers: {
        'Authorization': `Splunk ${token}`,
        'Content-Type': 'application/json'
      },
      body: body.length === 1 ? body[0] : body
    });
  }

  /**
   * Check if error has API-specific error indicators
   */
  hasAPIError(data) {
    return (
      data.error ||
      (data.result && data.result[0] && data.result[0].status && data.result[0].status.code !== 0) ||
      (data.status && data.status !== 'success')
    );
  }

  /**
   * Extract error message from API response
   */
  extractErrorMessage(data) {
    if (data.error) {
      return data.error.message || data.error.data || 'Unknown API error';
    }

    if (data.result && data.result[0] && data.result[0].status) {
      return data.result[0].status.message || `Error code: ${data.result[0].status.code}`;
    }

    return 'Unknown error occurred';
  }

  /**
   * Determine if error is retryable
   */
  isRetryableError(error) {
    // Network errors, timeouts, and temporary server errors are retryable
    return (
      error.name === 'AbortError' ||           // Timeout
      error.message.includes('ECONNRESET') ||  // Connection reset
      error.message.includes('ENOTFOUND') ||   // DNS resolution
      error.message.includes('ECONNREFUSED') || // Connection refused
      error.message.includes('500') ||         // Internal server error
      error.message.includes('502') ||         // Bad gateway
      error.message.includes('503') ||         // Service unavailable
      error.message.includes('504')            // Gateway timeout
    );
  }

  /**
   * Calculate retry delay with exponential backoff
   */
  calculateRetryDelay(retryCount) {
    const delay = Math.min(
      this.retryConfig.baseDelay * Math.pow(this.retryConfig.backoffFactor, retryCount),
      this.retryConfig.maxDelay
    );

    // Add jitter to prevent thundering herd
    return delay + Math.random() * 1000;
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Validate environment variables
   */
  validateEnvironment(requiredVars) {
    const missing = [];

    for (const varName of requiredVars) {
      if (!process.env[varName]) {
        missing.push(varName);
      }
    }

    if (missing.length > 0) {
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
  }

  /**
   * Test network connectivity
   */
  async testConnectivity(url, timeout = 10000) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        method: 'HEAD',
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  /**
   * Extract service name from URL for circuit breaker identification
   */
  getServiceNameFromURL(url) {
    try {
      const parsedURL = new URL(url);
      const hostname = parsedURL.hostname;

      // Map hostnames to service names
      if (hostname.includes('fortimanager') || hostname === process.env.FMG_HOST) {
        return 'fortimanager';
      } else if (hostname.includes('fortianalyzer') || hostname === process.env.FAZ_HOST) {
        return 'fortianalyzer';
      } else if (hostname.includes('splunk') || hostname === process.env.SPLUNK_HEC_HOST) {
        return 'splunk-hec';
      } else {
        return `service-${hostname.replace(/\./g, '-')}`;
      }
    } catch (error) {
      return 'unknown-service';
    }
  }

  /**
   * Get circuit breaker status for monitoring
   */
  getCircuitBreakerStatus() {
    return this.circuitManager.getSystemHealth();
  }
}

export default RealAPIHandler;