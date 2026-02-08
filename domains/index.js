/**
 * Barrel exports for DDD domain modules.
 *
 * Usage:
 *   import { CircuitBreaker, SplunkAPIConnector } from './domains/index.js';
 */

export { default as CircuitBreaker } from './defense/circuit-breaker.js';
export { default as FortiAnalyzerDirectConnector } from './integration/fortianalyzer-direct-connector.js';
export { default as SlackConnector } from './integration/slack-connector.js';
export { default as SlackWebhookHandler } from './integration/slack-webhook-handler.js';
export { default as SplunkAPIConnector } from './integration/splunk-api-connector.js';
export { default as SplunkDashboards } from './integration/splunk-dashboards.js';
export { default as SplunkQueries } from './integration/splunk-queries.js';
export { default as SplunkRestClient } from './integration/splunk-rest-client.js';
export { default as SecurityEventProcessor } from './security/security-event-processor.js';
