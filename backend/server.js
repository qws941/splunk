/**
 * Backend API Server for FortiAnalyzer-Splunk React Dashboard
 *
 * Features:
 * - REST API endpoints for dashboard data
 * - WebSocket for real-time event streaming
 * - Zero external dependencies (Node.js built-ins only)
 */

import http from 'http';
import { URL } from 'url';
import { WebSocketServer } from './websocket/websocket-server.js';
import { APIRouter } from './api/router.js';
import FortiAnalyzerDirectConnector from '../domains/integration/fortianalyzer-direct-connector.js';
import SplunkHECConnector from '../domains/integration/splunk-api-connector.js';
import SlackConnector from '../domains/integration/slack-connector.js';
import SecurityEventProcessor from '../domains/security/security-event-processor.js';

class DashboardAPIServer {
  constructor() {
    this.port = process.env.API_PORT || 3001;
    this.server = null;
    this.wsServer = null;
    this.router = null;

    // Service instances
    this.services = {
      faz: new FortiAnalyzerDirectConnector(),
      splunk: new SplunkHECConnector(),
      slack: new SlackConnector(),
      processor: new SecurityEventProcessor()
    };

    // Metrics
    this.metrics = {
      requests: 0,
      wsConnections: 0,
      errors: 0,
      startTime: Date.now()
    };
  }

  async initialize() {
    console.log('🚀 Initializing Dashboard API Server...\n');

    // Initialize services
    await this.initializeServices();

    // Create HTTP server
    this.server = http.createServer((req, res) => this.handleRequest(req, res));

    // Create WebSocket server
    this.wsServer = new WebSocketServer(this.server);
    this.wsServer.initialize(this.services);

    // Initialize router
    this.router = new APIRouter(this.services, this.wsServer);

    // Start listening
    this.server.listen(this.port, () => {
      console.log(`✅ Dashboard API Server listening on port ${this.port}`);
      console.log(`   REST API: http://localhost:${this.port}/api`);
      console.log(`   WebSocket: ws://localhost:${this.port}`);
      console.log(`   Health: http://localhost:${this.port}/health\n`);
    });

    // Start event polling
    this.startEventPolling();
  }

  async initializeServices() {
    console.log('🔌 Initializing services...');

    try {
      await this.services.faz.initialize();
      console.log('  ✓ FortiAnalyzer connected');

      await this.services.splunk.initialize();
      console.log('  ✓ Splunk HEC connected');

      await this.services.slack.initialize();
      console.log('  ✓ Slack connected');

      await this.services.processor.initialize({
        splunkConnector: this.services.splunk,
        slackConnector: this.services.slack
      });
      console.log('  ✓ Security Event Processor initialized\n');
    } catch (error) {
      console.error('❌ Service initialization failed:', error.message);
      throw error;
    }
  }

  async handleRequest(req, res) {
    this.metrics.requests++;

    // Enable CORS
    const allowedOrigin = process.env.CORS_ORIGIN || '*';
    res.setHeader('Access-Control-Allow-Origin', allowedOrigin);
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
      res.writeHead(200);
      res.end();
      return;
    }

    const url = new URL(req.url, `http://${req.headers.host}`);

    try {
      // Health check endpoint
      if (url.pathname === '/health') {
        return this.handleHealthCheck(req, res);
      }

      // Metrics endpoint
      if (url.pathname === '/metrics') {
        return this.handleMetrics(req, res);
      }

      // API routes
      if (url.pathname.startsWith('/api/')) {
        return await this.router.route(req, res, url);
      }

      // 404 Not Found
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not Found', path: url.pathname }));

    } catch (error) {
      this.metrics.errors++;
      console.error('❌ Request error:', error);

      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        error: 'Internal Server Error',
        message: error.message
      }));
    }
  }

  handleHealthCheck(req, res) {
    const uptime = Math.floor((Date.now() - this.metrics.startTime) / 1000);

    const health = {
      status: 'healthy',
      service: 'dashboard-api-server',
      version: '2.0.0',
      uptime_seconds: uptime,
      timestamp: new Date().toISOString(),
      components: {
        fortianalyzer: {
          connected: this.services.faz.getStatus()?.authenticated || false,
          status: this.services.faz.getStatus()?.authenticated ? 'healthy' : 'degraded'
        },
        splunk: {
          connected: true,
          status: 'healthy'
        },
        slack: {
          connected: this.services.slack.getStatus()?.connected || false,
          status: this.services.slack.getStatus()?.connected ? 'healthy' : 'degraded'
        },
        websocket: {
          connections: this.wsServer?.getConnectionCount() || 0,
          status: 'healthy'
        }
      },
      metrics: {
        total_requests: this.metrics.requests,
        ws_connections: this.wsServer?.getConnectionCount() || 0,
        errors: this.metrics.errors,
        processed_events: this.services.processor.getStats()?.processedCount || 0
      }
    };

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(health, null, 2));
  }

  handleMetrics(req, res) {
    const uptime = Math.floor((Date.now() - this.metrics.startTime) / 1000);
    const stats = this.services.processor.getStats();

    const metrics = [
      '# HELP dashboard_api_uptime_seconds Service uptime',
      '# TYPE dashboard_api_uptime_seconds gauge',
      `dashboard_api_uptime_seconds ${uptime}`,
      '',
      '# HELP dashboard_api_requests_total Total HTTP requests',
      '# TYPE dashboard_api_requests_total counter',
      `dashboard_api_requests_total ${this.metrics.requests}`,
      '',
      '# HELP dashboard_api_errors_total Total errors',
      '# TYPE dashboard_api_errors_total counter',
      `dashboard_api_errors_total ${this.metrics.errors}`,
      '',
      '# HELP dashboard_ws_connections Current WebSocket connections',
      '# TYPE dashboard_ws_connections gauge',
      `dashboard_ws_connections ${this.wsServer?.getConnectionCount() || 0}`,
      '',
      '# HELP dashboard_processed_events_total Total processed events',
      '# TYPE dashboard_processed_events_total counter',
      `dashboard_processed_events_total ${stats?.processedCount || 0}`,
      ''
    ].join('\n');

    res.writeHead(200, { 'Content-Type': 'text/plain; version=0.0.4' });
    res.end(metrics);
  }

  startEventPolling() {
    console.log('⏰ Starting event polling (60s interval)...\n');

    setInterval(async () => {
      try {
        const events = await this.services.faz.getSecurityEvents({
          timeRange: '-5m',
          limit: 100
        });

        if (events && events.length > 0) {
          console.log(`📥 Received ${events.length} events`);

          // Process events
          for (const event of events) {
            await this.services.processor.processEvent(event);
          }

          // Broadcast to WebSocket clients
          if (this.wsServer) {
            this.wsServer.broadcast({
              type: 'events',
              data: events,
              timestamp: new Date().toISOString()
            });
          }
        }
      } catch (error) {
        console.error('❌ Event polling error:', error.message);
      }
    }, 60000);
  }

  async shutdown() {
    console.log('\n👋 Shutting down server...');

    if (this.wsServer) {
      this.wsServer.close();
    }

    if (this.server) {
      this.server.close();
    }

    console.log('✅ Server shutdown complete');
  }
}

// Main execution
async function main() {
  const server = new DashboardAPIServer();

  try {
    await server.initialize();
  } catch (error) {
    console.error('❌ Server startup failed:', error);
    process.exit(1);
  }

  // Graceful shutdown
  process.on('SIGINT', async () => {
    await server.shutdown();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await server.shutdown();
    process.exit(0);
  });
}

main();
