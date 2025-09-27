#!/usr/bin/env node

/**
 * FortiAnalyzer 실제 연동 가능성 테스트
 * 실제 FAZ 서버와 Splunk HEC 연동 테스트
 */

import https from 'https';
import http from 'http';
import net from 'net';

const FAZ_CONFIG = {
  host: process.env.FAZ_HOST || 'fortianalyzer.jclee.me',
  port: process.env.FAZ_PORT || 443,
  username: process.env.FAZ_USERNAME || 'admin',
  password: process.env.FAZ_PASSWORD || 'fortinet'
};

const SPLUNK_CONFIG = {
  host: process.env.SPLUNK_HEC_HOST || 'splunk.jclee.me',
  port: process.env.SPLUNK_HEC_PORT || 8088,
  token: process.env.SPLUNK_HEC_TOKEN || 'test-token'
};

/**
 * FortiAnalyzer REST API 호출 테스트
 */
async function testFortiAnalyzerConnection() {
  console.log('🔍 FortiAnalyzer REST API 연결 테스트 중...');
  console.log(`📡 연결 대상: ${FAZ_CONFIG.host}:${FAZ_CONFIG.port}`);

  return new Promise((resolve) => {
    const auth = Buffer.from(`${FAZ_CONFIG.username}:${FAZ_CONFIG.password}`).toString('base64');

    const options = {
      hostname: FAZ_CONFIG.host,
      port: FAZ_CONFIG.port,
      path: '/api/v2/cmdb/system/status',
      method: 'GET',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/json'
      },
      rejectUnauthorized: false,
      timeout: 10000
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✅ FortiAnalyzer 연결 성공!');
          try {
            const response = JSON.parse(data);
            console.log(`📦 버전: ${response.version || 'N/A'}`);
            console.log(`🏷️ 호스트명: ${response.hostname || 'N/A'}`);
            resolve(true);
          } catch (error) {
            console.log('✅ 연결 성공 (응답 파싱 오류)');
            resolve(true);
          }
        } else {
          console.log(`❌ FortiAnalyzer 연결 실패 (HTTP ${res.statusCode})`);
          resolve(false);
        }
      });
    });

    req.on('error', (error) => {
      console.log('❌ FortiAnalyzer 연결 오류:', error.message);
      resolve(false);
    });

    req.on('timeout', () => {
      req.destroy();
      console.log('❌ FortiAnalyzer 연결 타임아웃');
      resolve(false);
    });

    req.setTimeout(10000);
    req.end();
  });
}

/**
 * Splunk HEC 연결 테스트
 */
async function testSplunkHECConnection() {
  console.log('\n💧 Splunk HEC 연결 테스트 중...');
  console.log(`📡 연결 대상: ${SPLUNK_CONFIG.host}:${SPLUNK_CONFIG.port}`);

  return new Promise((resolve) => {
    const testEvent = {
      event: 'FortiAnalyzer integration test',
      source: 'fortianalyzer:test',
      sourcetype: 'fortianalyzer:integration',
      index: 'main',
      time: Math.floor(Date.now() / 1000),
      host: 'integration-test'
    };

    const postData = JSON.stringify(testEvent);

    const options = {
      hostname: SPLUNK_CONFIG.host,
      port: SPLUNK_CONFIG.port,
      path: '/services/collector',
      method: 'POST',
      headers: {
        'Authorization': `Splunk ${SPLUNK_CONFIG.token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      rejectUnauthorized: false,
      timeout: 10000
    };

    const protocol = SPLUNK_CONFIG.port === 8088 ? https : http;
    const req = protocol.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✅ Splunk HEC 연결 성공!');
          console.log('📤 테스트 이벤트 전송 완료');
          resolve(true);
        } else {
          console.log(`❌ Splunk HEC 연결 실패 (HTTP ${res.statusCode})`);
          console.log('📄 응답:', data);
          resolve(false);
        }
      });
    });

    req.on('error', (error) => {
      console.log('❌ Splunk HEC 연결 오류:', error.message);
      resolve(false);
    });

    req.on('timeout', () => {
      req.destroy();
      console.log('❌ Splunk HEC 연결 타임아웃');
      resolve(false);
    });

    req.setTimeout(10000);
    req.write(postData);
    req.end();
  });
}

/**
 * 모의 FortiGate 로그 데이터 생성
 */
function generateMockFortiGateLog() {
  const timestamp = new Date().toISOString();
  const mockLog = {
    time: timestamp,
    devname: 'FortiGate-Main-01',
    devid: 'FGT60E1234567890',
    logid: '0000000013',
    type: 'traffic',
    subtype: 'forward',
    level: 'notice',
    vd: 'root',
    eventtime: Math.floor(Date.now() / 1000),
    srcip: '192.168.1.100',
    srcport: 54321,
    srcintf: 'internal',
    srcintfrole: 'lan',
    dstip: '203.0.113.50',
    dstport: 443,
    dstintf: 'wan1',
    dstintfrole: 'wan',
    policyid: 1001,
    policytype: 'policy',
    service: 'HTTPS',
    proto: 6,
    action: 'accept',
    policyname: 'Allow_HTTPS_Outbound',
    duration: 120,
    sentbyte: 2048,
    rcvdbyte: 8192,
    sentpkt: 15,
    rcvdpkt: 12,
    appcat: 'unscanned'
  };

  return {
    event: mockLog,
    source: 'fortianalyzer',
    sourcetype: 'fortigate_traffic',
    index: 'security',
    time: Math.floor(Date.now() / 1000),
    host: 'fortianalyzer.jclee.me'
  };
}

/**
 * 모의 로그 데이터 Splunk 전송 테스트
 */
async function testLogDataTransmission() {
  console.log('\n📊 모의 FortiGate 로그 데이터 전송 테스트 중...');

  const mockEvent = generateMockFortiGateLog();
  const postData = JSON.stringify(mockEvent);

  return new Promise((resolve) => {
    const options = {
      hostname: SPLUNK_CONFIG.host,
      port: SPLUNK_CONFIG.port,
      path: '/services/collector',
      method: 'POST',
      headers: {
        'Authorization': `Splunk ${SPLUNK_CONFIG.token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      rejectUnauthorized: false,
      timeout: 10000
    };

    const protocol = SPLUNK_CONFIG.port === 8088 ? https : http;
    const req = protocol.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✅ 모의 로그 데이터 전송 성공!');
          console.log('📤 전송된 이벤트:');
          console.log(`   - 소스 IP: ${mockEvent.event.srcip}`);
          console.log(`   - 목적지 IP: ${mockEvent.event.dstip}`);
          console.log(`   - 정책 ID: ${mockEvent.event.policyid}`);
          console.log(`   - 액션: ${mockEvent.event.action}`);
          resolve(true);
        } else {
          console.log(`❌ 모의 로그 데이터 전송 실패 (HTTP ${res.statusCode})`);
          resolve(false);
        }
      });
    });

    req.on('error', (error) => {
      console.log('❌ 로그 데이터 전송 오류:', error.message);
      resolve(false);
    });

    req.on('timeout', () => {
      req.destroy();
      console.log('❌ 로그 데이터 전송 타임아웃');
      resolve(false);
    });

    req.setTimeout(10000);
    req.write(postData);
    req.end();
  });
}

/**
 * 네트워크 연결성 테스트
 */
async function testNetworkConnectivity() {
  console.log('\n🌐 네트워크 연결성 테스트 중...');

  const testConnections = [
    { name: 'FortiAnalyzer', host: FAZ_CONFIG.host, port: FAZ_CONFIG.port },
    { name: 'Splunk HEC', host: SPLUNK_CONFIG.host, port: SPLUNK_CONFIG.port }
  ];

  const results = [];

  for (const conn of testConnections) {
    const result = await new Promise((resolve) => {
      const startTime = Date.now();
      const socket = new net.Socket();

      socket.setTimeout(5000);

      socket.connect(conn.port, conn.host, () => {
        const latency = Date.now() - startTime;
        console.log(`✅ ${conn.name} 연결 성공 (지연시간: ${latency}ms)`);
        socket.destroy();
        resolve({ name: conn.name, success: true, latency });
      });

      socket.on('error', (error) => {
        console.log(`❌ ${conn.name} 연결 실패: ${error.message}`);
        resolve({ name: conn.name, success: false, error: error.message });
      });

      socket.on('timeout', () => {
        console.log(`❌ ${conn.name} 연결 타임아웃`);
        socket.destroy();
        resolve({ name: conn.name, success: false, error: 'timeout' });
      });
    });

    results.push(result);
  }

  return results;
}

/**
 * 메인 테스트 실행 함수
 */
async function runIntegrationTests() {
  console.log('🧪 FortiAnalyzer-Splunk 통합 연동 테스트 시작\n');
  console.log('=' .repeat(60));

  let successCount = 0;
  const totalTests = 4;

  // 1. 네트워크 연결성 테스트
  const networkResults = await testNetworkConnectivity();
  const networkSuccess = networkResults.every(r => r.success);
  if (networkSuccess) successCount++;

  // 2. FortiAnalyzer 연결 테스트
  if (await testFortiAnalyzerConnection()) successCount++;

  // 3. Splunk HEC 연결 테스트
  if (await testSplunkHECConnection()) successCount++;

  // 4. 로그 데이터 전송 테스트
  if (await testLogDataTransmission()) successCount++;

  // 결과 요약
  console.log('\n' + '=' .repeat(60));
  console.log('📊 통합 테스트 결과 요약:');
  console.log(`✅ 성공한 테스트: ${successCount}/${totalTests}`);

  console.log('\n💡 실제 연동을 위한 환경 설정:');
  console.log('   FAZ_HOST=' + FAZ_CONFIG.host);
  console.log('   FAZ_USERNAME=' + FAZ_CONFIG.username);
  console.log('   SPLUNK_HEC_HOST=' + SPLUNK_CONFIG.host);
  console.log('   SPLUNK_HEC_TOKEN=' + SPLUNK_CONFIG.token);

  if (successCount === totalTests) {
    console.log('\n🎉 모든 통합 테스트 성공! 실제 환경에서 완전히 동작할 수 있습니다.');
  } else if (successCount >= 2) {
    console.log('\n⚠️ 부분적 성공. 환경 설정 후 완전 동작 가능합니다.');
  } else {
    console.log('\n❌ 대부분의 테스트 실패. 환경 설정이 필요합니다.');
  }

  return successCount;
}

// 스크립트가 직접 실행될 때만 테스트 실행
if (import.meta.url === `file://${process.argv[1]}`) {
  runIntegrationTests().catch(console.error);
}

export { testFortiAnalyzerConnection, testSplunkHECConnection, generateMockFortiGateLog };