/**
 * Policy Verification Demo Script
 * Shows how the policy verification system works with sample scenarios
 */

import PolicyVerificationServer from './policy-verification-server.js';

class PolicyVerificationDemo {
  constructor() {
    this.server = new PolicyVerificationServer(3001);
    this.testScenarios = [
      {
        name: "Web Server Access",
        description: "Internal user accessing external web server",
        sourceIP: "192.168.1.100",
        destIP: "1.1.1.1",
        protocol: "TCP",
        port: 80,
        service: "HTTP"
      },
      {
        name: "SSH Access",
        description: "Admin accessing internal server via SSH",
        sourceIP: "192.168.10.50",
        destIP: "172.16.1.100",
        protocol: "TCP",
        port: 22,
        service: "SSH"
      },
      {
        name: "Database Access",
        description: "Application server connecting to database",
        sourceIP: "10.0.1.50",
        destIP: "10.0.2.100",
        protocol: "TCP",
        port: 3306,
        service: "MYSQL"
      },
      {
        name: "DNS Query",
        description: "Client making DNS query",
        sourceIP: "192.168.1.200",
        destIP: "8.8.8.8",
        protocol: "UDP",
        port: 53,
        service: "DNS"
      },
      {
        name: "Blocked Traffic",
        description: "Potentially blocked traffic from external to internal",
        sourceIP: "203.0.113.100",
        destIP: "192.168.1.10",
        protocol: "TCP",
        port: 445,
        service: "SMB"
      }
    ];
  }

  /**
   * Run policy verification demo
   */
  async runDemo() {
    console.log('🛡️ FortiNet Policy Verification Demo');
    console.log('=====================================\n');

    console.log('🏢 Demo Environment:');
    console.log('- 80+ FortiGate devices managed by FortiManager');
    console.log('- Multiple VDOMs and security policies');
    console.log('- Real-time policy evaluation\n');

    // Initialize FortiManager connector (with mock data for demo)
    console.log('🔧 Initializing demo environment...');
    await this.server.initializeFortiManager();
    console.log('✅ Demo environment ready\n');

    // Run test scenarios
    console.log('🧪 Running Policy Verification Scenarios');
    console.log('==========================================\n');

    for (let i = 0; i < this.testScenarios.length; i++) {
      const scenario = this.testScenarios[i];
      console.log(`Scenario ${i + 1}: ${scenario.name}`);
      console.log(`Description: ${scenario.description}`);
      console.log(`Traffic: ${scenario.sourceIP} → ${scenario.destIP}:${scenario.port}/${scenario.protocol}`);

      try {
        const result = await this.server.fmgConnector.evaluatePolicyMatch(
          scenario.sourceIP,
          scenario.destIP,
          scenario.service,
          scenario.port,
          scenario.protocol
        );

        console.log(`Result: ${this.getResultDisplay(result.result)}`);

        if (result.matches && result.policy) {
          console.log(`Policy: ${result.policy.name} (ID: ${result.policy.id})`);
          console.log(`Action: ${result.policy.action}`);
        } else {
          console.log(`Reason: ${result.evaluation.reason}`);
        }

        console.log('─'.repeat(50) + '\n');
      } catch (error) {
        console.log(`❌ Error: ${error.message}\n`);
      }
    }

    // Show summary
    this.showDemoSummary();
  }

  /**
   * Get colored result display
   */
  getResultDisplay(result) {
    return result === 'ALLOW' ? '✅ ALLOW' : '❌ BLOCK';
  }

  /**
   * Show demo summary and next steps
   */
  showDemoSummary() {
    console.log('📊 Demo Summary');
    console.log('================');
    console.log('✅ Policy verification system demonstrates:');
    console.log('   • Real-time policy evaluation');
    console.log('   • Multi-device and multi-VDOM support');
    console.log('   • Accurate source/destination matching');
    console.log('   • Service and port resolution');
    console.log('   • Default deny behavior\n');

    console.log('🌐 Web Interface Features:');
    console.log('   • User-friendly input forms');
    console.log('   • Real-time validation');
    console.log('   • Detailed result display');
    console.log('   • Mobile-responsive design');
    console.log('   • Advanced filtering options\n');

    console.log('🔧 Production Setup:');
    console.log('   1. Configure FortiManager credentials');
    console.log('   2. Set up proper RBAC permissions');
    console.log('   3. Configure HTTPS/TLS for security');
    console.log('   4. Integrate with existing SIEM (Splunk)');
    console.log('   5. Set up monitoring and alerting\n');

    console.log('🚀 Next Steps:');
    console.log('   • Start the web server: npm run policy-server');
    console.log('   • Open browser: http://localhost:3001');
    console.log('   • Test with your network scenarios');
    console.log('   • Review detailed documentation\n');

    console.log('📞 Support:');
    console.log('   • Technical documentation: POLICY_VERIFICATION_README.md');
    console.log('   • API reference: /api/policy/verify endpoint');
    console.log('   • Integration guide: Splunk and Slack connectivity\n');
  }

  /**
   * Show network topology example
   */
  showNetworkTopology() {
    console.log('🌐 Sample Network Topology');
    console.log('==========================');
    console.log('');
    console.log('Internet');
    console.log('    │');
    console.log('┌───▼────────────────────┐');
    console.log('│  FortiGate Cluster     │ ← 80+ devices managed');
    console.log('│  (Edge Firewalls)      │   by FortiManager');
    console.log('└───┬────────────────────┘');
    console.log('    │');
    console.log('┌───▼────┬─────────┬─────────┐');
    console.log('│ DMZ    │ Internal │ Server  │');
    console.log('│ Zone   │ Network  │ Zone    │');
    console.log('│192.0.2.│192.168.1.│10.0.0.  │');
    console.log('│/24     │/24       │/24      │');
    console.log('└────────┴─────────┴─────────┘');
    console.log('');
    console.log('Policy verification checks traffic flow');
    console.log('between any source and destination across');
    console.log('all zones and VDOMs.\n');
  }
}

// Run demo if called directly
if (process.argv[1].endsWith('policy-verification-demo.js')) {
  const demo = new PolicyVerificationDemo();

  console.log('Select demo mode:');
  console.log('1. Full demo with scenarios');
  console.log('2. Network topology display');
  console.log('3. Quick API test\n');

  const mode = process.argv[2] || '1';

  switch (mode) {
    case '1':
      demo.runDemo().catch(error => {
        console.error('❌ Demo failed:', error);
        process.exit(1);
      });
      break;
    case '2':
      demo.showNetworkTopology();
      break;
    case '3':
      console.log('🧪 Quick API Test');
      console.log('Start server: npm run policy-server');
      console.log('Test command: curl -X POST http://localhost:3001/api/policy/verify -H "Content-Type: application/json" -d \'{"sourceIP":"192.168.1.100","destIP":"10.0.0.100","protocol":"TCP","port":80}\'');
      break;
    default:
      console.log('Invalid mode. Use 1, 2, or 3.');
      process.exit(1);
  }
}

export default PolicyVerificationDemo;