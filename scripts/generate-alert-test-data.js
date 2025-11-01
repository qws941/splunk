#!/usr/bin/env node
/**
 * Generate Test Data for FortiGate Real-time Alerts
 *
 * Generates FortiGate system events that trigger the 3 production alerts:
 * 1. FortiGate_Config_Change_Alert (logid=0100044546/7)
 * 2. FortiGate_Critical_Event_Alert (level=critical)
 * 3. FortiGate_HA_Event_Alert (logid=0103*)
 *
 * Usage:
 *   # Send to local Splunk HEC (localhost:8088)
 *   node scripts/generate-alert-test-data.js --send
 *
 *   # Save to file
 *   node scripts/generate-alert-test-data.js --output=test-events.json
 *
 *   # Generate specific event types
 *   node scripts/generate-alert-test-data.js --type=config --send
 *   node scripts/generate-alert-test-data.js --type=critical --send
 *   node scripts/generate-alert-test-data.js --type=ha --send
 */

import https from 'https';
import { randomInt } from 'crypto';

// =============================================================================
// Configuration
// =============================================================================

const config = {
  splunkHecHost: process.env.SPLUNK_HEC_HOST || 'localhost',
  splunkHecPort: process.env.SPLUNK_HEC_PORT || '8088',
  splunkHecToken: process.env.SPLUNK_HEC_TOKEN || 'your_token_here',
  splunkIndex: 'fortianalyzer', // Must match alert config
  eventType: 'all', // all, config, critical, ha
  sendToSplunk: false,
  outputFile: null
};

// Parse arguments
process.argv.slice(2).forEach(arg => {
  if (arg === '--send') {
    config.sendToSplunk = true;
  } else if (arg.startsWith('--output=')) {
    config.outputFile = arg.split('=')[1];
  } else if (arg.startsWith('--type=')) {
    config.eventType = arg.split('=')[1];
  } else if (arg.startsWith('--token=')) {
    config.splunkHecToken = arg.split('=')[1];
  }
});

// =============================================================================
// Event Generators
// =============================================================================

function randomElement(array) {
  return array[randomInt(array.length)];
}

function randomTimestamp() {
  // Recent timestamp (last 30 seconds for real-time alert window)
  const now = Math.floor(Date.now() / 1000);
  return now - randomInt(30);
}

/**
 * Generate FortiGate Configuration Change Event
 * Triggers: FortiGate_Config_Change_Alert
 */
function generateConfigChangeEvent() {
  const logid = randomElement(['0100044546', '0100044547']); // CLI or GUI
  const accessMethod = logid === '0100044546' ? 'CLI' : 'GUI';

  const cfgPaths = [
    'firewall.policy.edit.1',
    'firewall.address.edit.Server-1',
    'firewall.service.custom.HTTP-8080',
    'system.interface.edit.port1',
    'router.static.edit.1',
    'vpn.ipsec.phase1-interface.edit.VPN-1'
  ];

  const cfgObjects = [
    'policy-1', 'policy-2', 'Server-1', 'WebServer', 'port1', 'port2',
    'VPN-1', 'route-1', 'HTTP-8080'
  ];

  const actions = ['add', 'edit', 'delete', 'set'];
  const users = ['admin', 'fwadmin', 'operator', 'john.doe'];

  const cfgpath = randomElement(cfgPaths);
  const cfgobj = randomElement(cfgObjects);
  const action = randomElement(actions);
  const user = randomElement(users);

  const cfgattr = `srcintf=port1 dstintf=port2 srcaddr=LAN_SUBNET dstaddr=Internet service=HTTP action=accept`;

  return {
    time: randomTimestamp(),
    type: 'event',
    subtype: 'system',
    level: 'notice',
    logid: logid,
    devname: randomElement(['FGT-HQ-01', 'FGT-HQ-02', 'FGT-Branch-01']),
    vd: 'root',
    user: user,
    ui: accessMethod,
    action: action,
    cfgpath: cfgpath,
    cfgobj: cfgobj,
    cfgattr: cfgattr,
    msg: `Configuration changed: ${action} ${cfgpath} ${cfgobj}`,
    logdesc: `Admin ${user} modified configuration via ${accessMethod}`,
    devid: `FGT${randomInt(9000) + 1000}`,
    sourcetype: 'fortigate:event',
    index: config.splunkIndex
  };
}

/**
 * Generate FortiGate Critical System Event
 * Triggers: FortiGate_Critical_Event_Alert
 */
function generateCriticalEvent() {
  const criticalEvents = [
    {
      logid: '0104032001',
      msg: 'Memory usage high: 92%',
      logdesc: 'System memory usage exceeded threshold'
    },
    {
      logid: '0104032002',
      msg: 'CPU usage critical: 95%',
      logdesc: 'System CPU usage exceeded threshold'
    },
    {
      logid: '0104043523',
      msg: 'Disk full: 98% used',
      logdesc: 'System disk usage critical'
    },
    {
      logid: '0104043524',
      msg: 'HA sync failed',
      logdesc: 'High Availability synchronization failed'
    },
    {
      logid: '0104010003',
      msg: 'System reboot initiated',
      logdesc: 'FortiGate system is rebooting'
    },
    {
      logid: '0104010004',
      msg: 'Service daemon crashed',
      logdesc: 'Critical system daemon unexpectedly terminated'
    }
  ];

  const event = randomElement(criticalEvents);

  return {
    time: randomTimestamp(),
    type: 'event',
    subtype: 'system',
    level: 'critical',
    logid: event.logid,
    devname: randomElement(['FGT-HQ-01', 'FGT-HQ-02', 'FGT-Branch-01']),
    vd: 'root',
    msg: event.msg,
    logdesc: event.logdesc,
    devid: `FGT${randomInt(9000) + 1000}`,
    sourcetype: 'fortigate:event',
    index: config.splunkIndex
  };
}

/**
 * Generate FortiGate HA Event
 * Triggers: FortiGate_HA_Event_Alert
 */
function generateHAEvent() {
  const haEvents = [
    {
      logid: '0103008001',
      level: 'critical',
      msg: 'HA failover occurred',
      logdesc: 'High Availability failover from primary to secondary'
    },
    {
      logid: '0103008002',
      level: 'critical',
      msg: 'HA member disconnected',
      logdesc: 'HA cluster member lost connection'
    },
    {
      logid: '0103008003',
      level: 'warning',
      msg: 'HA sync status changed',
      logdesc: 'HA synchronization status changed'
    },
    {
      logid: '0103008010',
      level: 'error',
      msg: 'HA configuration mismatch',
      logdesc: 'HA members have different configurations'
    }
  ];

  const event = randomElement(haEvents);

  return {
    time: randomTimestamp(),
    type: 'event',
    subtype: 'system',
    level: event.level,
    logid: event.logid,
    devname: randomElement(['FGT-HA-01', 'FGT-HA-02']),
    vd: 'root',
    msg: event.msg,
    logdesc: event.logdesc,
    ha_group: randomInt(10) + 1,
    ha_priority: randomInt(255),
    devid: `FGT${randomInt(9000) + 1000}`,
    sourcetype: 'fortigate:event',
    index: config.splunkIndex
  };
}

// =============================================================================
// Splunk HEC Sender
// =============================================================================

async function sendToSplunkHEC(events) {
  return new Promise((resolve, reject) => {
    const hecEvents = events.map(event => JSON.stringify({
      time: event.time,
      source: 'alert-test-generator',
      sourcetype: event.sourcetype || 'fortigate:event',
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
      res.on('data', (chunk) => { data += chunk; });
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
  console.log('🔔 FortiGate Alert Test Data Generator');
  console.log('='.repeat(60));

  const events = [];

  // Generate events based on type
  if (config.eventType === 'all' || config.eventType === 'config') {
    console.log('📝 Generating Config Change events...');
    for (let i = 0; i < 3; i++) {
      events.push(generateConfigChangeEvent());
    }
  }

  if (config.eventType === 'all' || config.eventType === 'critical') {
    console.log('🚨 Generating Critical Event events...');
    for (let i = 0; i < 3; i++) {
      events.push(generateCriticalEvent());
    }
  }

  if (config.eventType === 'all' || config.eventType === 'ha') {
    console.log('🔴 Generating HA Event events...');
    for (let i = 0; i < 3; i++) {
      events.push(generateHAEvent());
    }
  }

  console.log(`\n✅ Generated ${events.length} test events`);

  // Save to file
  if (config.outputFile) {
    const fs = await import('fs');
    fs.writeFileSync(config.outputFile, JSON.stringify(events, null, 2));
    console.log(`💾 Events saved to: ${config.outputFile}`);
  }

  // Send to Splunk HEC
  if (config.sendToSplunk) {
    console.log(`\n🚀 Sending to Splunk HEC...`);
    console.log(`   Host: ${config.splunkHecHost}:${config.splunkHecPort}`);
    console.log(`   Index: ${config.splunkIndex}`);

    try {
      const result = await sendToSplunkHEC(events);
      console.log('✅ Events sent successfully!');
      console.log(`\n🔍 Verify in Splunk:`);
      console.log(`   index=${config.splunkIndex} sourcetype=fortigate:event earliest=-1m | head 20`);
      console.log(`\n⏳ Wait 30 seconds, then check Slack channel for alert notifications`);
    } catch (error) {
      console.error('❌ Failed to send events:', error.message);
      console.error('\n💡 Troubleshooting:');
      console.error('   1. Check HEC token: Settings → Data inputs → HTTP Event Collector');
      console.error('   2. Verify HEC is enabled: Settings → Data inputs → HTTP Event Collector → Global Settings');
      console.error('   3. Check container port: docker port splunk-test 8088');
      process.exit(1);
    }
  }

  if (!config.sendToSplunk && !config.outputFile) {
    console.log('\n💡 Preview of first event:');
    console.log(JSON.stringify(events[0], null, 2));
    console.log('\n📌 Usage:');
    console.log('   --send              Send to Splunk HEC');
    console.log('   --output=file.json  Save to file');
    console.log('   --type=config       Generate only config change events');
    console.log('   --type=critical     Generate only critical events');
    console.log('   --type=ha           Generate only HA events');
    console.log('   --token=YOUR_TOKEN  Set HEC token');
  }
}

main().catch(error => {
  console.error('❌ Error:', error.message);
  process.exit(1);
});
