#!/usr/bin/env node

/**
 * FortiAnalyzer Native REST API Test
 */

import FortiAnalyzerDirectConnector from './domains/integration/fortianalyzer-direct-connector.js';

async function testNativeConnection() {
  console.log('🔌 FortiAnalyzer Native REST API 연결 테스트...\n');

  const connector = new FortiAnalyzerDirectConnector();

  try {
    // 1. FAZ 인증
    console.log('1️⃣ FortiAnalyzer 인증...');
    await connector.initialize();

    // 2. 보안 이벤트 가져오기 (REST API)
    console.log('\n2️⃣ 보안 이벤트 가져오기 (REST API)...');
    const result = await connector.getSecurityEvents({ limit: 10 });

    if (result.success) {
      console.log(`✅ 이벤트 ${result.events.length}개 수신`);
      console.log('\n샘플 이벤트:');
      console.log(JSON.stringify(result.events[0], null, 2));
    }

    // 3. 상태 확인
    console.log('\n3️⃣ 연결 상태:');
    const status = connector.getStatus();
    console.log(JSON.stringify(status, null, 2));

    console.log('\n✅ Native REST API 연결 성공!');
    console.log('UDP Syslog 대신 REST API로 데이터 수신 가능');

  } catch (error) {
    console.error('\n❌ 연결 실패:', error.message);
    console.log('\n환경 변수 확인:');
    console.log('- FAZ_HOST:', process.env.FAZ_HOST || '미설정');
    console.log('- FAZ_API_TOKEN:', process.env.FAZ_API_TOKEN ? '설정됨' : '미설정');
  }
}

// 실행
testNativeConnection();
