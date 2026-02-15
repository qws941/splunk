#!/usr/bin/env node
/**
 * Deploy Current Splunk Dashboards (configs/dashboards/) via REST API
 *
 * Usage: node scripts/deploy-current-dashboards.js
 *
 * Environment Variables:
 * - SPLUNK_HOST: Splunk server hostname (default: localhost)
 * - SPLUNK_PORT: Splunk management port (default: 8089)
 * - SPLUNK_USERNAME: Splunk admin username (default: admin)
 * - SPLUNK_PASSWORD: Splunk admin password (required)
 * - SPLUNK_APP: Target app (default: search)
 */

import fs from 'fs';
import path from 'path';
import https from 'https';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env file
const envPath = path.join(__dirname, '../.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf-8');
  envContent.split('\n').forEach(line => {
    const match = line.match(/^([^=]+)=(.*)$/);
    if (match && !process.env[match[1]]) {
      process.env[match[1]] = match[2].trim();
    }
  });
}

// Configuration
const config = {
  host: process.env.SPLUNK_HOST || 'localhost',
  port: parseInt(process.env.SPLUNK_PORT) || 8089,
  username: process.env.SPLUNK_USERNAME || 'admin',
  password: process.env.SPLUNK_PASSWORD,
  app: process.env.SPLUNK_APP || 'search',
  scheme: 'https'
};

// Dashboard directory
const dashboardDir = path.join(__dirname, '..', 'configs', 'dashboards');

// Dashboard files to deploy
const dashboards = [
  {
    file: 'correlation-analysis.xml',
    id: 'correlation_analysis',
    name: 'FortiGate Correlation Analysis'
  },
  {
    file: 'fortigate-operations.xml',
    id: 'fortigate_operations',
    name: 'FortiGate Operations Dashboard'
  },
  {
    file: 'slack-test-simple.xml',
    id: 'slack_test_simple',
    name: 'Slack Alert Test (Simple)'
  },
  {
    file: 'slack-toggle.json',
    id: 'slack_toggle',
    name: '🔔 Slack 알림 제어',
    isStudio: true
  },
  {
    file: 'fortinet-management-dashboard.json',
    id: 'fortinet_management',
    name: '🛡️ Fortinet Device Management + Slack Control',
    isStudio: true
  },
  {
    file: 'fortigate-operations-unified.json',
    id: 'fortigate_operations_unified',
    name: '🛡️ FortiGate Operations + Slack Control',
    isStudio: true
  }
];

/**
 * Deploy dashboard to Splunk via REST API
 */
async function deployDashboard(dashboardId, dashboardName, content, isStudio = false) {
  return new Promise((resolve, reject) => {
    // Encode credentials
    const auth = Buffer.from(`${config.username}:${config.password}`).toString('base64');

    let postData, contentType, apiPath;

    if (isStudio) {
      // Dashboard Studio uses different API
      apiPath = `/servicesNS/nobody/${config.app}/data/ui/views`;
      postData = new URLSearchParams({
        'name': dashboardId,
        'eai:type': 'views',
        'eai:data': content,
        'eai:acl.sharing': 'app',
        'eai:acl.app': config.app
      }).toString();
      contentType = 'application/x-www-form-urlencoded';
    } else {
      // Classic XML dashboard
      apiPath = `/servicesNS/nobody/${config.app}/data/ui/views`;
      postData = new URLSearchParams({
        'name': dashboardId,
        'eai:data': content,
        'eai:acl.sharing': 'app',
        'eai:acl.app': config.app
      }).toString();
      contentType = 'application/x-www-form-urlencoded';
    }

    const options = {
      hostname: config.host,
      port: config.port,
      path: apiPath,
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': contentType,
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
            message: `Dashboard deployed: ${dashboardName}`,
            created: true
          });
        } else if (res.statusCode === 409) {
          // Dashboard already exists, try to update
          updateDashboard(dashboardId, dashboardName, content, isStudio)
            .then(resolve)
            .catch(reject);
        } else {
          reject({
            success: false,
            statusCode: res.statusCode,
            message: `Failed to deploy dashboard: ${data.substring(0, 200)}`
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
async function updateDashboard(dashboardId, dashboardName, content, isStudio = false) {
  return new Promise((resolve, reject) => {
    const auth = Buffer.from(`${config.username}:${config.password}`).toString('base64');

    const postData = new URLSearchParams({
      'eai:data': content
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
            message: `Dashboard updated: ${dashboardName}`,
            created: false
          });
        } else {
          reject({
            success: false,
            statusCode: res.statusCode,
            message: `Failed to update dashboard: ${data.substring(0, 200)}`
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
 * Validate dashboard file (XML or JSON)
 */
function validateDashboard(filepath) {
  try {
    const content = fs.readFileSync(filepath, 'utf8');

    // Check if JSON (Dashboard Studio)
    if (filepath.endsWith('.json')) {
      try {
        const jsonData = JSON.parse(content);

        // Basic Dashboard Studio validation
        if (!jsonData.visualizations || !jsonData.dataSources) {
          return { valid: false, error: 'Not a valid Dashboard Studio JSON (missing visualizations or dataSources)' };
        }

        return { valid: true, content, isStudio: true };
      } catch (e) {
        return { valid: false, error: `Invalid JSON: ${e.message}` };
      }
    }

    // Basic XML validation
    if (!content.includes('<form') && !content.includes('<dashboard')) {
      return { valid: false, error: 'Not a valid Splunk dashboard XML (missing <form> or <dashboard> tag)' };
    }

    // Check for common XML errors
    const openTags = content.match(/<[^/][^>]*>/g) || [];
    const closeTags = content.match(/<\/[^>]+>/g) || [];

    if (openTags.length === 0) {
      return { valid: false, error: 'No opening tags found' };
    }

    return { valid: true, content, isStudio: false };
  } catch (error) {
    return { valid: false, error: error.message };
  }
}

/**
 * Main deployment function
 */
async function main() {
  console.log('🚀 대시보드 현행화 (Splunk REST API 배포)\n');
  console.log('─'.repeat(60));

  // Check password
  if (!config.password) {
    console.error('❌ SPLUNK_PASSWORD 환경 변수가 설정되지 않았습니다.');
    console.error('   .env 파일에 추가하거나:');
    console.error('   export SPLUNK_PASSWORD=your_password\n');
    process.exit(1);
  }

  console.log(`📡 Target: ${config.scheme}://${config.host}:${config.port}`);
  console.log(`📦 App: ${config.app}`);
  console.log(`👤 User: ${config.username}`);
  console.log(`📂 Source: configs/dashboards/`);
  console.log('─'.repeat(60));
  console.log('');

  let deployed = 0;
  let updated = 0;
  let failed = 0;

  // Deploy each dashboard
  for (const dashboard of dashboards) {
    try {
      const filepath = path.join(dashboardDir, dashboard.file);

      console.log(`📊 ${dashboard.name}`);
      console.log(`   File: ${dashboard.file}`);

      // Check file exists
      if (!fs.existsSync(filepath)) {
        console.error(`   ❌ 파일을 찾을 수 없습니다: ${dashboard.file}\n`);
        failed++;
        continue;
      }

      // Validate dashboard file
      const fileType = filepath.endsWith('.json') ? 'JSON' : 'XML';
      console.log(`   🔍 ${fileType} 검증 중...`);
      const validation = validateDashboard(filepath);

      if (!validation.valid) {
        console.error(`   ❌ ${fileType} 검증 실패: ${validation.error}\n`);
        failed++;
        continue;
      }

      console.log(`   ✅ ${fileType} 유효함 (${Math.round(validation.content.length / 1024)}KB)`);

      // Deploy
      console.log(`   📤 배포 중...`);
      const result = await deployDashboard(dashboard.id, dashboard.name, validation.content, dashboard.isStudio || false);

      if (result.success) {
        if (result.created) {
          console.log(`   ✅ 새로 생성됨`);
          deployed++;
        } else {
          console.log(`   ✅ 업데이트됨`);
          updated++;
        }
        console.log(`   🔗 URL: https://${config.host}/app/${config.app}/${dashboard.id}`);
      } else {
        console.log(`   ❌ 실패: ${result.message}`);
        failed++;
      }

      console.log('');

    } catch (error) {
      console.error(`   ❌ 오류: ${error.message || error.error || JSON.stringify(error)}\n`);
      failed++;
    }
  }

  // Summary
  console.log('─'.repeat(60));
  console.log('📊 배포 결과:');
  console.log(`   ✅ 새로 생성: ${deployed}`);
  console.log(`   🔄 업데이트: ${updated}`);
  console.log(`   ❌ 실패: ${failed}`);
  console.log(`   📁 전체: ${dashboards.length}`);
  console.log('─'.repeat(60));

  if (deployed + updated > 0) {
    console.log('\n🌐 대시보드 접근:');
    console.log(`   https://${config.host}/app/${config.app}/dashboards\n`);
    console.log('📌 배포된 대시보드:');

    dashboards.forEach(d => {
      console.log(`   • ${d.name}`);
      console.log(`     https://${config.host}/app/${config.app}/${d.id}\n`);
    });
  }

  process.exit(failed > 0 ? 1 : 0);
}

// Run
main().catch(error => {
  console.error('❌배포 실패:', error);
  process.exit(1);
});
