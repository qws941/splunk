#!/usr/bin/env node
/**
 * Deploy Splunk Dashboards via REST API
 *
 * Usage: node scripts/deploy-dashboards.js
 *
 * Environment Variables:
 * - SPLUNK_HOST: Splunk server hostname (default: splunk.jclee.me)
 * - SPLUNK_PORT: Splunk management port (default: 8089)
 * - SPLUNK_USERNAME: Splunk admin username
 * - SPLUNK_PASSWORD: Splunk admin password
 * - SPLUNK_APP: Target app (default: search)
 */

import fs from 'fs';
import path from 'path';
import https from 'https';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const config = {
  host: process.env.SPLUNK_HOST || 'splunk.jclee.me',
  port: parseInt(process.env.SPLUNK_PORT) || 8089,
  username: process.env.SPLUNK_USERNAME || 'admin',
  password: process.env.SPLUNK_PASSWORD,
  app: process.env.SPLUNK_APP || 'search',
  scheme: 'https'
};

// Dashboard directory
const dashboardDir = path.join(__dirname, '..', 'dashboards');

// Dashboard files
const dashboards = [
  { id: 'fortigate-security-overview', name: 'FortiGate Security Overview' },
  { id: 'threat-intelligence', name: 'Threat Intelligence Dashboard' },
  { id: 'traffic-analysis', name: 'Network Traffic Analysis' },
  { id: 'performance-monitoring', name: 'FortiGate Performance Monitoring' },
  { id: 'fortinet-config-management-final', name: 'Fortinet 설정 관리 (PRD - Proxy Slack 통합)' }
];

/**
 * Deploy dashboard to Splunk via REST API
 */
async function deployDashboard(dashboardId, dashboardName, xmlContent) {
  return new Promise((resolve, reject) => {
    // Encode credentials
    const auth = Buffer.from(`${config.username}:${config.password}`).toString('base64');

    // Prepare POST data
    const postData = new URLSearchParams({
      'name': dashboardId,
      'eai:data': xmlContent
    }).toString();

    const options = {
      hostname: config.host,
      port: config.port,
      path: `/servicesNS/nobody/${config.app}/data/ui/views`,
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(postData)
      },
      rejectUnauthorized: false // Accept self-signed certificates
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode === 201 || res.statusCode === 200) {
          resolve({
            success: true,
            statusCode: res.statusCode,
            message: `Dashboard deployed: ${dashboardName}`
          });
        } else if (res.statusCode === 409) {
          // Dashboard already exists, try to update
          updateDashboard(dashboardId, dashboardName, xmlContent)
            .then(resolve)
            .catch(reject);
        } else {
          reject({
            success: false,
            statusCode: res.statusCode,
            message: `Failed to deploy dashboard: ${data}`
          });
        }
      });
    });

    req.on('error', (error) => {
      reject({
        success: false,
        error: error.message
      });
    });

    req.write(postData);
    req.end();
  });
}

/**
 * Update existing dashboard
 */
async function updateDashboard(dashboardId, dashboardName, xmlContent) {
  return new Promise((resolve, reject) => {
    const auth = Buffer.from(`${config.username}:${config.password}`).toString('base64');

    const postData = new URLSearchParams({
      'eai:data': xmlContent
    }).toString();

    const options = {
      hostname: config.host,
      port: config.port,
      path: `/servicesNS/nobody/${config.app}/data/ui/views/${dashboardId}`,
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(postData)
      },
      rejectUnauthorized: false
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve({
            success: true,
            statusCode: res.statusCode,
            message: `Dashboard updated: ${dashboardName}`
          });
        } else {
          reject({
            success: false,
            statusCode: res.statusCode,
            message: `Failed to update dashboard: ${data}`
          });
        }
      });
    });

    req.on('error', (error) => {
      reject({
        success: false,
        error: error.message
      });
    });

    req.write(postData);
    req.end();
  });
}

/**
 * Main deployment function
 */
async function main() {
  console.log('🚀 Deploying Splunk Dashboards via REST API...\n');

  // Check password
  if (!config.password) {
    console.error('❌ SPLUNK_PASSWORD environment variable not set');
    console.error('   Set it in .env or export SPLUNK_PASSWORD=your_password\n');
    process.exit(1);
  }

  console.log(`📡 Target: ${config.scheme}://${config.host}:${config.port}`);
  console.log(`📦 App: ${config.app}`);
  console.log(`👤 User: ${config.username}\n`);

  let deployed = 0;
  let failed = 0;

  // Deploy each dashboard
  for (const dashboard of dashboards) {
    try {
      const filepath = path.join(dashboardDir, `${dashboard.id}.xml`);

      if (!fs.existsSync(filepath)) {
        console.error(`⚠️  File not found: ${dashboard.id}.xml (run export-dashboards.js first)`);
        failed++;
        continue;
      }

      const xmlContent = fs.readFileSync(filepath, 'utf8');

      console.log(`📊 Deploying: ${dashboard.name}...`);

      const result = await deployDashboard(dashboard.id, dashboard.name, xmlContent);

      if (result.success) {
        console.log(`✅ ${result.message}\n`);
        deployed++;
      } else {
        console.error(`❌ ${result.message}\n`);
        failed++;
      }

    } catch (error) {
      console.error(`❌ Error deploying ${dashboard.name}:`, error.message || error);
      failed++;
    }
  }

  console.log('\n📊 Deployment Summary:');
  console.log(`   ✅ Deployed: ${deployed}`);
  console.log(`   ❌ Failed: ${failed}`);
  console.log(`   📁 Total: ${dashboards.length}\n`);

  if (deployed > 0) {
    console.log('🌐 Access dashboards at:');
    console.log(`   https://${config.host}/app/${config.app}/dashboards\n`);

    dashboards.forEach(d => {
      console.log(`   - ${d.name}:`);
      console.log(`     https://${config.host}/app/${config.app}/${d.id}\n`);
    });
  }

  process.exit(failed > 0 ? 1 : 0);
}

// Run
main().catch(error => {
  console.error('❌ Deployment failed:', error);
  process.exit(1);
});
