#!/usr/bin/env node
/**
 * Export Splunk Dashboards to Individual XML Files
 *
 * Usage: node scripts/export-dashboards.js
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import SplunkDashboards from '../domains/integration/splunk-dashboards.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Output directory
const outputDir = path.join(__dirname, '..', 'dashboards');

// Create output directory if it doesn't exist
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Initialize dashboard generator
const dashboardsLib = new SplunkDashboards();

// Dashboard definitions
const dashboards = [
  {
    id: 'fortigate-security-overview',
    name: 'FortiGate Security Overview',
    method: 'getSecurityOverviewDashboard'
  },
  {
    id: 'threat-intelligence',
    name: 'Threat Intelligence Dashboard',
    method: 'getThreatIntelDashboard'
  },
  {
    id: 'traffic-analysis',
    name: 'Network Traffic Analysis',
    method: 'getTrafficAnalysisDashboard'
  },
  {
    id: 'performance-monitoring',
    name: 'FortiGate Performance Monitoring',
    method: 'getPerformanceDashboard'
  }
];

console.log('📊 Exporting Splunk Dashboards to XML...\n');

// Export each dashboard
let exported = 0;
dashboards.forEach(dashboard => {
  try {
    // Get dashboard XML
    const xml = dashboardsLib[dashboard.method]();

    // Write to file
    const filename = `${dashboard.id}.xml`;
    const filepath = path.join(outputDir, filename);
    fs.writeFileSync(filepath, xml, 'utf8');

    console.log(`✅ ${dashboard.name}`);
    console.log(`   → ${filename}\n`);

    exported++;
  } catch (error) {
    console.error(`❌ Failed to export ${dashboard.name}:`, error.message);
  }
});

console.log(`\n✅ Exported ${exported}/${dashboards.length} dashboards to ${outputDir}/\n`);
console.log('📁 Files created:');
dashboards.forEach(d => {
  const filepath = path.join(outputDir, `${d.id}.xml`);
  if (fs.existsSync(filepath)) {
    const stats = fs.statSync(filepath);
    console.log(`   - ${d.id}.xml (${(stats.size / 1024).toFixed(1)} KB)`);
  }
});

console.log('\n🚀 Next steps:');
console.log('   1. Review XML files in dashboards/ directory');
console.log('   2. Run: node scripts/deploy-dashboards.js (deploy to Splunk)');
console.log('   3. Or manually upload to splunk.jclee.me Web UI\n');
