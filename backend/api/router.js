/**
 * API Router for Dashboard Backend
 *
 * REST API Endpoints:
 * - GET  /api/events - Get recent security events
 * - GET  /api/stats - Get statistics
 * - GET  /api/correlation - Get correlation analysis results
 * - GET  /api/alerts - Get active alerts
 * - POST /api/alerts/:id/acknowledge - Acknowledge alert
 * - GET  /api/threats - Get threat intelligence data
 */

export class APIRouter {
  constructor(services, wsServer) {
    this.services = services;
    this.wsServer = wsServer;
  }

  async route(req, res, url) {
    const path = url.pathname;
    const method = req.method;

    // Parse request body for POST/PUT
    let body = null;
    if (method === 'POST' || method === 'PUT') {
      body = await this.parseBody(req);
    }

    // Route mapping
    const routes = {
      'GET /api/events': () => this.getEvents(req, res, url),
      'GET /api/stats': () => this.getStats(req, res),
      'GET /api/correlation': () => this.getCorrelation(req, res, url),
      'GET /api/alerts': () => this.getAlerts(req, res),
      'POST /api/alerts/acknowledge': () => this.acknowledgeAlert(req, res, body),
      'GET /api/threats': () => this.getThreats(req, res),
      'GET /api/dashboards': () => this.getDashboards(req, res),
      'GET /api/slack/test': () => this.testSlack(req, res)
    };

    const routeKey = `${method} ${path}`;
    const handler = routes[routeKey];

    if (handler) {
      return await handler();
    }

    // 404 Not Found
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'API endpoint not found', path }));
  }

  async parseBody(req) {
    return new Promise((resolve, reject) => {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          resolve(body ? JSON.parse(body) : {});
        } catch (error) {
          reject(new Error('Invalid JSON'));
        }
      });
      req.on('error', reject);
    });
  }

  async getEvents(req, res, url) {
    try {
      const params = url.searchParams;
      const limit = parseInt(params.get('limit') || '100');
      const timeRange = params.get('timeRange') || '-1h';
      const severity = params.get('severity');

      const events = await this.services.faz.getSecurityEvents({
        timeRange,
        limit
      });

      // Filter by severity if specified
      const filtered = severity
        ? events.filter(e => e.severity === severity)
        : events;

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: true,
        count: filtered.length,
        timeRange,
        events: filtered
      }));
    } catch (error) {
      console.error('❌ getEvents error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: error.message }));
    }
  }

  async getStats(req, res) {
    try {
      const processorStats = this.services.processor.getStats();
      const fazStatus = this.services.faz.getStatus();

      const stats = {
        success: true,
        timestamp: new Date().toISOString(),
        processor: processorStats,
        connections: {
          fortianalyzer: fazStatus.authenticated || false,
          splunk: true,
          slack: this.services.slack.getStatus()?.connected || false,
          websocket: this.wsServer?.getConnectionCount() || 0
        }
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(stats));
    } catch (error) {
      console.error('❌ getStats error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: error.message }));
    }
  }

  async getCorrelation(req, res, url) {
    try {
      const params = url.searchParams;
      const timeRange = params.get('timeRange') || '-24h';

      // Mock correlation data (실제로는 Splunk query 결과)
      const correlationData = {
        success: true,
        timeRange,
        rules: [
          {
            id: 'rule_1',
            name: 'Multi-Factor Threat Score',
            triggered: 15,
            avgScore: 82.5,
            topIPs: ['192.168.1.100', '10.0.0.50'],
            trend: 'increasing'
          },
          {
            id: 'rule_2',
            name: 'Repeated High-Risk Events',
            triggered: 8,
            avgScore: 75.3,
            topIPs: ['172.16.0.25'],
            trend: 'stable'
          },
          {
            id: 'rule_3',
            name: 'Weak Signal Combination',
            triggered: 12,
            avgScore: 68.7,
            topIPs: ['192.168.10.5', '192.168.10.8'],
            trend: 'decreasing'
          }
        ],
        summary: {
          totalTriggered: 35,
          avgCorrelationScore: 75.5,
          criticalAlerts: 5,
          autoBlocked: 3
        }
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(correlationData));
    } catch (error) {
      console.error('❌ getCorrelation error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: error.message }));
    }
  }

  async getAlerts(req, res) {
    try {
      // Mock alerts data
      const alerts = {
        success: true,
        count: 3,
        alerts: [
          {
            id: 'alert_001',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            severity: 'critical',
            type: 'correlation',
            rule: 'Multi-Factor Threat Score',
            score: 95,
            sourceIP: '192.168.1.100',
            status: 'active',
            action: 'AUTO_BLOCK'
          },
          {
            id: 'alert_002',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            severity: 'high',
            type: 'intrusion',
            rule: 'Geo + Attack Pattern',
            score: 88,
            sourceIP: '10.0.0.50',
            status: 'acknowledged',
            action: 'REVIEW_AND_BLOCK'
          },
          {
            id: 'alert_003',
            timestamp: new Date(Date.now() - 10800000).toISOString(),
            severity: 'medium',
            type: 'anomaly',
            rule: 'Time-Based Anomaly',
            score: 72,
            sourceIP: '172.16.0.25',
            status: 'active',
            action: 'MONITOR'
          }
        ]
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(alerts));
    } catch (error) {
      console.error('❌ getAlerts error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: error.message }));
    }
  }

  async acknowledgeAlert(req, res, body) {
    try {
      const { alertId, acknowledgedBy, comment } = body;

      if (!alertId) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: 'alertId required' }));
        return;
      }

      console.log(`✅ Alert ${alertId} acknowledged by ${acknowledgedBy || 'unknown'}`);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: true,
        alertId,
        acknowledgedAt: new Date().toISOString(),
        acknowledgedBy,
        comment
      }));
    } catch (error) {
      console.error('❌ acknowledgeAlert error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: error.message }));
    }
  }

  async getThreats(req, res) {
    try {
      // Mock threat intelligence data
      const threats = {
        success: true,
        timestamp: new Date().toISOString(),
        topThreats: [
          {
            ip: '192.168.1.100',
            country: 'CN',
            abuseScore: 95,
            attackTypes: ['SQL Injection', 'Port Scan'],
            firstSeen: new Date(Date.now() - 86400000).toISOString(),
            lastSeen: new Date().toISOString(),
            eventCount: 245
          },
          {
            ip: '10.0.0.50',
            country: 'RU',
            abuseScore: 88,
            attackTypes: ['Brute Force'],
            firstSeen: new Date(Date.now() - 172800000).toISOString(),
            lastSeen: new Date(Date.now() - 3600000).toISOString(),
            eventCount: 128
          }
        ],
        geoDistribution: {
          CN: 245,
          RU: 128,
          VN: 67,
          BR: 45,
          IN: 32
        },
        attackTypes: {
          'SQL Injection': 156,
          'Port Scan': 123,
          'Brute Force': 98,
          'XSS': 45,
          'CSRF': 23
        }
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(threats));
    } catch (error) {
      console.error('❌ getThreats error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: error.message }));
    }
  }

  async getDashboards(req, res) {
    try {
      const dashboards = {
        success: true,
        dashboards: [
          {
            id: 'security',
            name: 'Security Overview',
            description: 'Real-time security monitoring and threat detection',
            widgets: 8
          },
          {
            id: 'correlation',
            name: 'Correlation Analysis',
            description: 'Advanced correlation rules and pattern detection',
            widgets: 6
          },
          {
            id: 'threats',
            name: 'Threat Intelligence',
            description: 'Threat intelligence and geolocation analysis',
            widgets: 5
          },
          {
            id: 'performance',
            name: 'System Performance',
            description: 'System health and performance metrics',
            widgets: 4
          }
        ]
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(dashboards));
    } catch (error) {
      console.error('❌ getDashboards error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: error.message }));
    }
  }

  async testSlack(req, res) {
    try {
      await this.services.slack.sendMessage('Test message from React Dashboard API');

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: true,
        message: 'Slack test message sent'
      }));
    } catch (error) {
      console.error('❌ testSlack error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: error.message }));
    }
  }
}
