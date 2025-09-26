/**
 * Policy Verification Web Server
 * Serves the policy verification web interface and API endpoints
 */

import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import FortiManagerDirectConnector from './fortimanager-direct-connector.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class PolicyVerificationServer {
  constructor(port = 3001) {
    this.app = express();
    this.port = port;
    this.fmgConnector = null;

    this.setupMiddleware();
    this.setupRoutes();
  }

  /**
   * Setup Express middleware
   */
  setupMiddleware() {
    // JSON parser
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // CORS for development
    this.app.use((req, res, next) => {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');

      if (req.method === 'OPTIONS') {
        res.sendStatus(200);
      } else {
        next();
      }
    });

    // Request logging
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
      next();
    });
  }

  /**
   * Setup API routes
   */
  setupRoutes() {
    // Serve the policy verification web page
    this.app.get('/', (req, res) => {
      res.sendFile(path.join(__dirname, 'policy-verification-web.html'));
    });

    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        fmgConnected: this.fmgConnector?.isConnected || false
      });
    });

    // Get managed devices
    this.app.get('/api/fortimanager/devices', async (req, res) => {
      try {
        if (!this.fmgConnector) {
          return res.status(503).json({ error: 'FortiManager connector not initialized' });
        }

        const devices = await this.fmgConnector.getManagedDevices();
        res.json(devices);
      } catch (error) {
        console.error('❌ Failed to get devices:', error);
        res.status(500).json({ error: error.message });
      }
    });

    // Policy verification endpoint
    this.app.post('/api/policy/verify', async (req, res) => {
      try {
        const { sourceIP, destIP, protocol, port, service, device, vdom } = req.body;

        // Validate input
        if (!sourceIP || !destIP) {
          return res.status(400).json({
            error: 'Source IP and Destination IP are required'
          });
        }

        if (!this.fmgConnector || !this.fmgConnector.isConnected) {
          return res.status(503).json({
            error: 'FortiManager connector not connected'
          });
        }

        console.log(`🔍 Policy verification request: ${sourceIP} → ${destIP}:${port}/${protocol}`);

        // Perform policy evaluation
        const result = await this.fmgConnector.evaluatePolicyMatch(
          sourceIP,
          destIP,
          service || 'any',
          port || 80,
          protocol || 'TCP',
          device,
          vdom || 'root'
        );

        // Log the verification for audit
        console.log(`✅ Policy verification completed: ${result.result} - ${result.matches ? `Policy ${result.policy.id}` : 'No match'}`);

        res.json(result);

      } catch (error) {
        console.error('❌ Policy verification failed:', error);
        res.status(500).json({
          error: 'Policy verification failed',
          details: error.message
        });
      }
    });

    // Get policy details
    this.app.get('/api/policy/:policyId', async (req, res) => {
      try {
        const { policyId } = req.params;
        const { device, vdom = 'root' } = req.query;

        if (!this.fmgConnector) {
          return res.status(503).json({ error: 'FortiManager connector not initialized' });
        }

        // Query specific policy
        const policies = await this.fmgConnector.queryPoliciesForVerification(device, vdom);
        const policy = policies.find(p => p.policyid.toString() === policyId);

        if (!policy) {
          return res.status(404).json({ error: 'Policy not found' });
        }

        res.json(policy);
      } catch (error) {
        console.error('❌ Failed to get policy details:', error);
        res.status(500).json({ error: error.message });
      }
    });

    // Test connectivity to FortiManager
    this.app.post('/api/fortimanager/test', async (req, res) => {
      try {
        if (!this.fmgConnector) {
          return res.status(503).json({ error: 'FortiManager connector not initialized' });
        }

        // Test authentication
        await this.fmgConnector.authenticate();

        res.json({
          status: 'success',
          message: 'FortiManager connection test successful',
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        console.error('❌ FortiManager connectivity test failed:', error);
        res.status(500).json({
          error: 'Connectivity test failed',
          details: error.message
        });
      }
    });

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({ error: 'Endpoint not found' });
    });

    // Error handler
    this.app.use((error, req, res, next) => {
      console.error('❌ Server error:', error);
      res.status(500).json({
        error: 'Internal server error',
        details: error.message
      });
    });
  }

  /**
   * Initialize FortiManager connector
   */
  async initializeFortiManager() {
    try {
      console.log('🏢 Initializing FortiManager connector...');
      this.fmgConnector = new FortiManagerDirectConnector();
      await this.fmgConnector.initialize();
      console.log('✅ FortiManager connector initialized');
    } catch (error) {
      console.error('❌ Failed to initialize FortiManager connector:', error);
      // Continue without FMG connector - show error in UI
    }
  }

  /**
   * Start the web server
   */
  async start() {
    try {
      // Initialize FortiManager connector first
      await this.initializeFortiManager();

      // Start web server
      this.server = this.app.listen(this.port, () => {
        console.log('🌐 Policy Verification Server started');
        console.log(`📱 Web Interface: http://localhost:${this.port}`);
        console.log(`🔧 API Base URL: http://localhost:${this.port}/api`);
        console.log(`🛡️ FortiManager Connected: ${this.fmgConnector?.isConnected || false}`);
      });

      // Graceful shutdown
      process.on('SIGTERM', () => this.shutdown());
      process.on('SIGINT', () => this.shutdown());

    } catch (error) {
      console.error('❌ Failed to start server:', error);
      throw error;
    }
  }

  /**
   * Shutdown the server
   */
  async shutdown() {
    console.log('⏹️ Shutting down Policy Verification Server...');

    if (this.server) {
      this.server.close(() => {
        console.log('✅ Web server closed');
      });
    }

    if (this.fmgConnector) {
      this.fmgConnector.disconnect();
      console.log('✅ FortiManager connector disconnected');
    }

    process.exit(0);
  }

  /**
   * Get server status
   */
  getStatus() {
    return {
      running: !!this.server,
      port: this.port,
      fmgConnected: this.fmgConnector?.isConnected || false,
      startTime: this.startTime || null
    };
  }
}

// Export for use as module or run standalone
export default PolicyVerificationServer;

// Run standalone if this is the main module
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const server = new PolicyVerificationServer();
  server.start().catch(error => {
    console.error('💥 Server startup failed:', error);
    process.exit(1);
  });
}