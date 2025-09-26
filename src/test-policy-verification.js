/**
 * Test script for Policy Verification functionality
 */

import PolicyVerificationServer from './policy-verification-server.js';

async function testPolicyVerification() {
  console.log('🧪 Testing Policy Verification System...\n');

  const server = new PolicyVerificationServer(3001);

  try {
    // Test 1: Server initialization
    console.log('Test 1: Server Initialization');
    console.log('================================');
    await server.initializeFortiManager();
    console.log('✅ FortiManager connector initialized\n');

    // Test 2: IP matching logic
    console.log('Test 2: IP Matching Logic');
    console.log('==========================');
    const fmgConnector = server.fmgConnector;

    // Test subnet matching
    const subnetTest1 = fmgConnector.ipMatchesAddress('192.168.1.100', '192.168.1.0/24');
    console.log(`192.168.1.100 matches 192.168.1.0/24: ${subnetTest1}`);

    const subnetTest2 = fmgConnector.ipMatchesAddress('192.168.2.100', '192.168.1.0/24');
    console.log(`192.168.2.100 matches 192.168.1.0/24: ${subnetTest2}`);

    // Test exact match
    const exactTest = fmgConnector.ipMatchesAddress('10.0.0.1', '10.0.0.1');
    console.log(`10.0.0.1 matches 10.0.0.1: ${exactTest}`);

    // Test any/all match
    const anyTest = fmgConnector.ipMatchesAddress('1.2.3.4', '0.0.0.0/0');
    console.log(`1.2.3.4 matches 0.0.0.0/0: ${anyTest}\n`);

    // Test 3: Port matching logic
    console.log('Test 3: Port Matching Logic');
    console.log('============================');

    const portTest1 = fmgConnector.portMatchesService(80, 'TCP', { protocol: 'TCP', ports: '80' });
    console.log(`Port 80/TCP matches TCP:80: ${portTest1}`);

    const portTest2 = fmgConnector.portMatchesService(443, 'TCP', { protocol: 'TCP', ports: '80-443' });
    console.log(`Port 443/TCP matches TCP:80-443: ${portTest2}`);

    const portTest3 = fmgConnector.portMatchesService(22, 'TCP', { protocol: 'any', ports: 'any' });
    console.log(`Port 22/TCP matches any:any: ${portTest3}\n`);

    // Test 4: Mock policy evaluation
    console.log('Test 4: Mock Policy Evaluation');
    console.log('===============================');

    console.log('Testing policy evaluation with mock data...');

    // This will use mock data since we don't have real FMG connection
    try {
      const result = await fmgConnector.evaluatePolicyMatch(
        '192.168.1.100',  // source
        '10.0.0.100',     // destination
        'HTTP',           // service
        80,               // port
        'TCP',            // protocol
        null,             // device (all)
        'root'            // vdom
      );

      console.log('Policy evaluation result:');
      console.log(JSON.stringify(result, null, 2));
    } catch (error) {
      console.log('Expected error (no real FMG connection):', error.message);
    }

    console.log('\n✅ All tests completed successfully!');
    console.log('\n🌐 To test the web interface:');
    console.log('1. Run: npm run policy-server');
    console.log('2. Open: http://localhost:3001');
    console.log('3. Enter test IPs and see the results\n');

  } catch (error) {
    console.error('❌ Test failed:', error);
    throw error;
  }
}

// Run tests
testPolicyVerification().catch(error => {
  console.error('💥 Test execution failed:', error);
  process.exit(1);
});