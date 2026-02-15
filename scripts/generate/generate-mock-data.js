#!/usr/bin/env node
/**
 * Mock Data Generator for Splunk Dashboards
 *
 * Generates realistic FortiAnalyzer security events for testing Splunk dashboards
 * in air-gapped environments without real FortiAnalyzer connection.
 *
 * Usage:
 *   node scripts/generate-mock-data.js --count=1000 --send
 *   node scripts/generate-mock-data.js --count=500 --output=mock-events.json
 */

import https from 'https';
import { randomInt, randomBytes } from 'crypto';

// =============================================================================
// Configuration
// =============================================================================

const config = {
  splunkHecHost: process.env.SPLUNK_HEC_HOST || 'splunk.jclee.me',
  splunkHecPort: process.env.SPLUNK_HEC_PORT || '8088',
  splunkHecToken: process.env.SPLUNK_HEC_TOKEN || 'your_token_here',
  splunkIndex: process.env.SPLUNK_INDEX_FORTIGATE || 'fortianalyzer',
  eventCount: 1000,
  sendToSplunk: false,
  outputFile: null
};

// Parse command line arguments
process.argv.slice(2).forEach(arg => {
  if (arg.startsWith('--count=')) {
    config.eventCount = parseInt(arg.split('=')[1]);
  } else if (arg === '--send') {
    config.sendToSplunk = true;
  } else if (arg.startsWith('--output=')) {
    config.outputFile = arg.split('=')[1];
  }
});

// =============================================================================
// Mock Data Templates
// =============================================================================

const MOCK_DATA = {
  // Source IPs (attackers)
  sourceIPs: [
    '45.142.212.61', '185.220.101.45', '91.203.5.165', '103.253.145.28',
    '194.180.48.103', '23.129.64.216', '178.128.90.45', '159.89.133.74',
    '167.99.83.205', '142.93.126.155', '188.166.11.87', '165.232.84.226',
    '68.183.44.143', '206.189.156.99', '157.245.108.125', '134.209.24.42',
    '139.59.173.67', '143.198.109.233', '161.35.219.74', '147.182.131.69'
  ],

  // Target IPs (internal network)
  targetIPs: [
    '10.0.1.100', '10.0.1.105', '10.0.1.110', '10.0.1.115', '10.0.1.120',
    '10.0.2.50', '10.0.2.55', '10.0.2.60', '10.0.3.30', '10.0.3.35',
    '192.168.1.10', '192.168.1.20', '192.168.1.30', '192.168.2.40', '192.168.2.50'
  ],

  // Attack names (IPS signatures)
  attacks: [
    'SQL.Injection.Attempt',
    'XSS.Cross.Site.Scripting',
    'Remote.Code.Execution.Attempt',
    'Directory.Traversal.Attack',
    'Command.Injection',
    'LDAP.Injection',
    'XML.External.Entity.Attack',
    'Server.Side.Request.Forgery',
    'Brute.Force.Login.Attempt',
    'DDoS.Flood.Attack',
    'Port.Scan.Detected',
    'Malicious.File.Upload',
    'Buffer.Overflow.Attempt',
    'Privilege.Escalation',
    'Suspicious.PowerShell.Execution'
  ],

  // Malware families
  malware: [
    'Trojan.Generic.KD.12345',
    'Ransomware.WannaCry',
    'Backdoor.Agent.XYZ',
    'Worm.Conficker.B',
    'Trojan.Emotet',
    'Rootkit.TDSS',
    'Spyware.KeyLogger',
    'Adware.BrowserModifier',
    'Trojan.Banker.Zeus',
    'RAT.DarkComet'
  ],

  // Botnet names
  botnets: [
    'Mirai', 'Emotet', 'Zeus', 'Necurs', 'Gameover', 'Conficker',
    'Dridex', 'TrickBot', 'Qakbot', 'IcedID'
  ],

  // WebFilter categories
  webCategories: [
    'Malicious.Websites', 'Phishing', 'Spam.URLs', 'Adult.Content',
    'Gambling', 'Illegal.Downloads', 'Proxy.Avoidance', 'Hacking',
    'Malware.Distribution', 'Command.and.Control'
  ],

  // Applications
  applications: [
    'HTTP', 'HTTPS', 'SSH', 'FTP', 'SMTP', 'DNS', 'MySQL', 'PostgreSQL',
    'RDP', 'SMB', 'Telnet', 'SNMP', 'Redis', 'MongoDB', 'Elasticsearch'
  ],

  // Protocols
  protocols: ['TCP', 'UDP', 'ICMP', 'GRE'],

  // Services (ports)
  services: [
    { name: 'HTTP', port: 80 },
    { name: 'HTTPS', port: 443 },
    { name: 'SSH', port: 22 },
    { name: 'FTP', port: 21 },
    { name: 'SMTP', port: 25 },
    { name: 'DNS', port: 53 },
    { name: 'MySQL', port: 3306 },
    { name: 'PostgreSQL', port: 5432 },
    { name: 'RDP', port: 3389 },
    { name: 'SMB', port: 445 }
  ],

  // Countries
  countries: [
    'China', 'Russia', 'United States', 'Brazil', 'India', 'Germany',
    'France', 'United Kingdom', 'Netherlands', 'Ukraine', 'Vietnam',
    'South Korea', 'Japan', 'Canada', 'Australia'
  ],

  // Device names
  devices: [
    'FortiGate-DC1', 'FortiGate-DC2', 'FortiGate-Branch1',
    'FortiGate-Branch2', 'FortiGate-DMZ', 'FortiGate-HQ'
  ],

  // Actions
  actions: ['blocked', 'denied', 'dropped', 'allowed', 'monitored']
};

// =============================================================================
// Event Generators
// =============================================================================

function randomElement(array) {
  return array[randomInt(array.length)];
}

function randomTimestamp(hoursAgo = 24) {
  const now = Math.floor(Date.now() / 1000);
  const offset = randomInt(hoursAgo * 3600);
  return now - offset;
}

function generateSecurityEvent() {
  const severity = randomElement(['critical', 'high', 'medium', 'low']);
  const action = severity === 'critical' || severity === 'high'
    ? 'blocked'
    : randomElement(MOCK_DATA.actions);

  const srcIP = randomElement(MOCK_DATA.sourceIPs);
  const dstIP = randomElement(MOCK_DATA.targetIPs);
  const attack = randomElement(MOCK_DATA.attacks);
  const service = randomElement(MOCK_DATA.services);

  return {
    timestamp: randomTimestamp(24),
    time: randomTimestamp(24),
    type: 'traffic',
    subtype: 'forward',
    level: severity === 'critical' ? 'alert' : 'warning',
    severity: severity,
    vd: 'root',
    srcip: srcIP,
    src_ip: srcIP,
    srcport: randomInt(50000) + 10000,
    dstip: dstIP,
    dst_ip: dstIP,
    target_ip: dstIP,
    dstport: service.port,
    service: service.name,
    proto: randomElement(MOCK_DATA.protocols),
    action: action,
    policyid: randomInt(100) + 1,
    policyname: `Policy_${randomInt(50) + 1}`,
    sessionid: randomInt(1000000),
    attack: attack,
    attack_name: attack,
    attack_id: randomInt(50000),
    sensor: 'IPS_Sensor_1',
    ref: `https://fortiguard.com/encyclopedia/ips/${randomInt(50000)}`,
    msg: `${attack} detected from ${srcIP} to ${dstIP}`,
    srcintf: 'port1',
    dstintf: 'port2',
    srcintfrole: 'wan',
    dstintfrole: 'lan',
    srccountry: randomElement(MOCK_DATA.countries),
    dstcountry: 'South Korea',
    app: randomElement(MOCK_DATA.applications),
    apprisk: severity === 'critical' ? 'critical' : severity,
    appcat: 'Network.Service',
    sentbyte: randomInt(100000),
    rcvdbyte: randomInt(100000),
    sentpkt: randomInt(1000),
    rcvdpkt: randomInt(1000),
    duration: randomInt(3600),
    device: randomElement(MOCK_DATA.devices),
    devid: `FG${randomInt(9000) + 1000}`,
    event_type: 'intrusion_attempt',
    risk_score: severity === 'critical' ? randomInt(30) + 70 : randomInt(50) + 20,
    source_type: 'fortianalyzer',
    sourcetype: 'fortigate:security',
    index: config.splunkIndex
  };
}

function generateMalwareEvent() {
  const malware = randomElement(MOCK_DATA.malware);
  const srcIP = randomElement(MOCK_DATA.targetIPs); // Internal host infected
  const dstIP = randomElement(MOCK_DATA.sourceIPs); // External C&C

  return {
    timestamp: randomTimestamp(24),
    time: randomTimestamp(24),
    type: 'utm',
    subtype: 'virus',
    level: 'alert',
    severity: 'critical',
    vd: 'root',
    srcip: srcIP,
    src_ip: srcIP,
    srcport: randomInt(50000) + 10000,
    dstip: dstIP,
    dst_ip: dstIP,
    target_ip: dstIP,
    dstport: randomInt(10000),
    service: 'HTTP',
    proto: 'TCP',
    action: 'blocked',
    virus: malware,
    virus_name: malware,
    dtype: 'Virus',
    analyticscksum: randomBytes(16).toString('hex'),
    analyticssubmit: 'false',
    msg: `Virus detected: ${malware}`,
    srcintf: 'port2',
    dstintf: 'port1',
    srcintfrole: 'lan',
    dstintfrole: 'wan',
    device: randomElement(MOCK_DATA.devices),
    devid: `FG${randomInt(9000) + 1000}`,
    event_type: 'malware_detected',
    risk_score: randomInt(30) + 70,
    source_type: 'fortianalyzer',
    sourcetype: 'fortigate:security',
    index: config.splunkIndex
  };
}

function generateBotnetEvent() {
  const botnet = randomElement(MOCK_DATA.botnets);
  const srcIP = randomElement(MOCK_DATA.targetIPs); // Internal bot
  const dstIP = randomElement(MOCK_DATA.sourceIPs); // C&C server

  return {
    timestamp: randomTimestamp(24),
    time: randomTimestamp(24),
    type: 'utm',
    subtype: 'ips',
    level: 'alert',
    severity: 'critical',
    vd: 'root',
    srcip: srcIP,
    src_ip: srcIP,
    srcport: randomInt(50000) + 10000,
    dstip: dstIP,
    dst_ip: dstIP,
    target_ip: dstIP,
    dstport: randomElement([80, 443, 8080, 8443]),
    service: 'HTTPS',
    proto: 'TCP',
    action: 'blocked',
    attack: `${botnet}.Command.and.Control`,
    attack_name: `${botnet}.Command.and.Control`,
    botnet: botnet,
    botnet_name: botnet,
    category: 'botnet',
    msg: `Botnet C&C communication detected: ${botnet}`,
    srcintf: 'port2',
    dstintf: 'port1',
    srcintfrole: 'lan',
    dstintfrole: 'wan',
    device: randomElement(MOCK_DATA.devices),
    devid: `FG${randomInt(9000) + 1000}`,
    event_type: 'botnet_activity',
    risk_score: randomInt(30) + 70,
    source_type: 'fortianalyzer',
    sourcetype: 'fortigate:security',
    index: config.splunkIndex
  };
}

function generateWebFilterEvent() {
  const category = randomElement(MOCK_DATA.webCategories);
  const srcIP = randomElement(MOCK_DATA.targetIPs);

  return {
    timestamp: randomTimestamp(24),
    time: randomTimestamp(24),
    type: 'utm',
    subtype: 'webfilter',
    level: 'warning',
    severity: 'medium',
    vd: 'root',
    srcip: srcIP,
    src_ip: srcIP,
    srcport: randomInt(50000) + 10000,
    dstip: randomElement(MOCK_DATA.sourceIPs),
    dstport: 443,
    service: 'HTTPS',
    proto: 'TCP',
    action: 'blocked',
    hostname: `malicious-site-${randomInt(1000)}.com`,
    url: `https://malicious-site-${randomInt(1000)}.com/path`,
    category: category,
    catdesc: category,
    msg: `WebFilter blocked: ${category}`,
    srcintf: 'port2',
    dstintf: 'port1',
    srcintfrole: 'lan',
    dstintfrole: 'wan',
    device: randomElement(MOCK_DATA.devices),
    devid: `FG${randomInt(9000) + 1000}`,
    event_type: 'web_threat',
    risk_score: randomInt(40) + 30,
    source_type: 'fortianalyzer',
    sourcetype: 'fortigate:security',
    index: config.splunkIndex
  };
}

function generateTrafficEvent() {
  const service = randomElement(MOCK_DATA.services);
  const srcIP = randomElement(MOCK_DATA.targetIPs);
  const dstIP = Math.random() > 0.5
    ? randomElement(MOCK_DATA.sourceIPs)
    : randomElement(MOCK_DATA.targetIPs);

  return {
    timestamp: randomTimestamp(24),
    time: randomTimestamp(24),
    type: 'traffic',
    subtype: 'forward',
    level: 'notice',
    severity: 'low',
    vd: 'root',
    srcip: srcIP,
    src_ip: srcIP,
    srcport: randomInt(50000) + 10000,
    dstip: dstIP,
    dst_ip: dstIP,
    dstport: service.port,
    service: service.name,
    proto: randomElement(['TCP', 'UDP']),
    action: 'allowed',
    policyid: randomInt(100) + 1,
    policyname: `Policy_${randomInt(50) + 1}`,
    sessionid: randomInt(1000000),
    app: randomElement(MOCK_DATA.applications),
    appcat: 'Network.Service',
    sentbyte: randomInt(10000000),
    rcvdbyte: randomInt(10000000),
    sentpkt: randomInt(10000),
    rcvdpkt: randomInt(10000),
    duration: randomInt(7200),
    srcintf: Math.random() > 0.5 ? 'port1' : 'port2',
    dstintf: Math.random() > 0.5 ? 'port1' : 'port2',
    device: randomElement(MOCK_DATA.devices),
    devid: `FG${randomInt(9000) + 1000}`,
    event_type: 'traffic',
    risk_score: randomInt(20),
    source_type: 'fortianalyzer',
    sourcetype: 'fortigate:security',
    index: config.splunkIndex
  };
}

function generateDeviceStatusEvent() {
  const device = randomElement(MOCK_DATA.devices);

  return {
    timestamp: randomTimestamp(1),
    time: randomTimestamp(1),
    type: 'event',
    subtype: 'system',
    level: 'information',
    severity: 'info',
    name: device,
    ip: `10.0.0.${randomInt(200) + 1}`,
    conn_status: 1, // Connected
    conf_status: 1, // In sync
    os_ver: `v7.${randomInt(5)}.${randomInt(10)}`,
    cpu: randomInt(80),
    memory: randomInt(80),
    disk: randomInt(80),
    sessions: randomInt(50000),
    latency: randomInt(100),
    device: device,
    devid: `FG${randomInt(9000) + 1000}`,
    event_type: 'device_status',
    source_type: 'fortimanager',
    sourcetype: 'fortimanager:device_status',
    index: config.splunkIndex
  };
}

// =============================================================================
// Main Generator
// =============================================================================

function generateMockEvents(count) {
  const events = [];

  for (let i = 0; i < count; i++) {
    const eventType = randomInt(100);

    let event;
    if (eventType < 40) {
      // 40% security events
      event = generateSecurityEvent();
    } else if (eventType < 50) {
      // 10% malware events
      event = generateMalwareEvent();
    } else if (eventType < 60) {
      // 10% botnet events
      event = generateBotnetEvent();
    } else if (eventType < 70) {
      // 10% webfilter events
      event = generateWebFilterEvent();
    } else if (eventType < 95) {
      // 25% traffic events
      event = generateTrafficEvent();
    } else {
      // 5% device status events
      event = generateDeviceStatusEvent();
    }

    events.push(event);
  }

  return events;
}

// =============================================================================
// Splunk HEC Sender
// =============================================================================

async function sendToSplunkHEC(events) {
  return new Promise((resolve, reject) => {
    const hecEvents = events.map(event => JSON.stringify({
      time: event.timestamp || event.time,
      source: 'mock-data-generator',
      sourcetype: event.sourcetype || 'fortigate:security',
      index: event.index || config.splunkIndex,
      event: event
    })).join('\n');

    const options = {
      hostname: config.splunkHecHost,
      port: config.splunkHecPort,
      path: '/services/collector/event/1.0',
      method: 'POST',
      headers: {
        'Authorization': `Splunk ${config.splunkHecToken}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(hecEvents)
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
          resolve({ success: true, data: JSON.parse(data) });
        } else {
          reject(new Error(`HEC returned status ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(hecEvents);
    req.end();
  });
}

// =============================================================================
// Main Execution
// =============================================================================

async function main() {
  console.log('🎲 Mock Data Generator for Splunk Dashboards');
  console.log('='.repeat(60));
  console.log(`📊 Generating ${config.eventCount} events...`);

  const events = generateMockEvents(config.eventCount);

  // Calculate statistics
  const stats = {
    security: events.filter(e => e.event_type === 'intrusion_attempt').length,
    malware: events.filter(e => e.event_type === 'malware_detected').length,
    botnet: events.filter(e => e.event_type === 'botnet_activity').length,
    webfilter: events.filter(e => e.event_type === 'web_threat').length,
    traffic: events.filter(e => e.event_type === 'traffic').length,
    device: events.filter(e => e.event_type === 'device_status').length,
    critical: events.filter(e => e.severity === 'critical').length,
    high: events.filter(e => e.severity === 'high').length,
    medium: events.filter(e => e.severity === 'medium').length,
    low: events.filter(e => e.severity === 'low').length
  };

  console.log('\n📈 Event Statistics:');
  console.log(`   Security Events: ${stats.security}`);
  console.log(`   Malware Events: ${stats.malware}`);
  console.log(`   Botnet Events: ${stats.botnet}`);
  console.log(`   WebFilter Events: ${stats.webfilter}`);
  console.log(`   Traffic Events: ${stats.traffic}`);
  console.log(`   Device Status: ${stats.device}`);
  console.log('\n🎯 Severity Distribution:');
  console.log(`   Critical: ${stats.critical}`);
  console.log(`   High: ${stats.high}`);
  console.log(`   Medium: ${stats.medium}`);
  console.log(`   Low: ${stats.low}`);

  // Save to file
  if (config.outputFile) {
    const fs = await import('fs');
    fs.writeFileSync(config.outputFile, JSON.stringify(events, null, 2));
    console.log(`\n💾 Events saved to: ${config.outputFile}`);
  }

  // Send to Splunk HEC
  if (config.sendToSplunk) {
    console.log(`\n🚀 Sending events to Splunk HEC...`);
    console.log(`   Host: ${config.splunkHecHost}:${config.splunkHecPort}`);
    console.log(`   Index: ${config.splunkIndex}`);

    try {
      // Send in batches of 100
      const batchSize = 100;
      let sent = 0;

      for (let i = 0; i < events.length; i += batchSize) {
        const batch = events.slice(i, i + batchSize);
        await sendToSplunkHEC(batch);
        sent += batch.length;
        console.log(`   Sent ${sent}/${events.length} events...`);
      }

      console.log('✅ All events sent successfully!');
      console.log(`\n🔍 Verify in Splunk:`);
      console.log(`   index=${config.splunkIndex} | head 100`);
    } catch (error) {
      console.error('❌ Failed to send events:', error.message);
      process.exit(1);
    }
  }

  console.log('\n✅ Mock data generation complete!');
}

main().catch(error => {
  console.error('❌ Error:', error.message);
  process.exit(1);
});
