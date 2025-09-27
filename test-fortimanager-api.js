#!/usr/bin/env node

/**
 * FortiManager JSON-RPC API 실제 연결 테스트
 * 실제 FMG 서버가 있을 때만 동작
 */

import https from 'https';

const FMG_CONFIG = {
  host: process.env.FMG_HOST || 'fortimanager.jclee.me',
  port: process.env.FMG_PORT || 443,
  username: process.env.FMG_USERNAME || 'admin',
  password: process.env.FMG_PASSWORD || 'fortinet',
  timeout: 10000
};

/**
 * FortiManager JSON-RPC API 호출 함수
 */
async function callFortiManagerAPI(method, url, data = null, sessionId = null) {
  return new Promise((resolve, reject) => {
    const payload = {
      id: Math.floor(Math.random() * 1000),
      method: method,
      params: [{
        url: url,
        ...(data && { data: data })
      }],
      ...(sessionId && { session: sessionId })
    };

    const postData = JSON.stringify(payload);

    const options = {
      hostname: FMG_CONFIG.host,
      port: FMG_CONFIG.port,
      path: '/jsonrpc',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      rejectUnauthorized: false // FortiManager는 보통 자체 서명 인증서 사용
    };

    const req = https.request(options, (res) => {
      let responseData = '';

      res.on('data', (chunk) => {
        responseData += chunk;
      });

      res.on('end', () => {
        try {
          const jsonResponse = JSON.parse(responseData);
          resolve(jsonResponse);
        } catch (error) {
          reject(new Error(`JSON 파싱 오류: ${error.message}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error('API 호출 타임아웃'));
    });

    req.setTimeout(FMG_CONFIG.timeout);
    req.write(postData);
    req.end();
  });
}

/**
 * FortiManager 로그인 테스트
 */
async function testLogin() {
  console.log('🔐 FortiManager 로그인 테스트 중...');
  console.log(`📡 연결 대상: ${FMG_CONFIG.host}:${FMG_CONFIG.port}`);

  try {
    const response = await callFortiManagerAPI('exec', 'sys/login/user', {
      user: FMG_CONFIG.username,
      passwd: FMG_CONFIG.password
    });

    if (response.result && response.result[0] && response.result[0].status && response.result[0].status.code === 0) {
      console.log('✅ 로그인 성공!');
      console.log(`🎟️ 세션 ID: ${response.session}`);
      return response.session;
    } else {
      console.log('❌ 로그인 실패');
      console.log('📄 응답:', JSON.stringify(response, null, 2));
      return null;
    }
  } catch (error) {
    console.log('❌ 연결 오류:', error.message);
    return null;
  }
}

/**
 * 시스템 상태 조회 테스트
 */
async function testSystemStatus(sessionId) {
  console.log('\n📊 시스템 상태 조회 테스트 중...');

  try {
    const response = await callFortiManagerAPI('get', 'sys/status', null, sessionId);

    if (response.result && response.result[0] && response.result[0].status && response.result[0].status.code === 0) {
      const data = response.result[0].data;
      console.log('✅ 시스템 상태 조회 성공!');
      console.log(`📦 버전: ${data.Version || 'N/A'}`);
      console.log(`🏷️ 호스트명: ${data.Hostname || 'N/A'}`);
      console.log(`🔢 시리얼: ${data.Serial || 'N/A'}`);
      return true;
    } else {
      console.log('❌ 시스템 상태 조회 실패');
      console.log('📄 응답:', JSON.stringify(response, null, 2));
      return false;
    }
  } catch (error) {
    console.log('❌ 시스템 상태 조회 오류:', error.message);
    return false;
  }
}

/**
 * 관리 장비 목록 조회 테스트
 */
async function testDeviceList(sessionId) {
  console.log('\n🖥️ 관리 장비 목록 조회 테스트 중...');

  try {
    const response = await callFortiManagerAPI('get', 'dvmdb/device', null, sessionId);

    if (response.result && response.result[0] && response.result[0].status && response.result[0].status.code === 0) {
      const devices = response.result[0].data;
      console.log(`✅ 장비 목록 조회 성공! (총 ${devices.length}개 장비)`);

      devices.slice(0, 5).forEach((device, index) => {
        console.log(`📱 장비 ${index + 1}: ${device.name} (${device.ip}) - ${device.conn_status}`);
      });

      if (devices.length > 5) {
        console.log(`   ... 외 ${devices.length - 5}개 장비`);
      }

      return devices.length;
    } else {
      console.log('❌ 장비 목록 조회 실패');
      console.log('📄 응답:', JSON.stringify(response, null, 2));
      return 0;
    }
  } catch (error) {
    console.log('❌ 장비 목록 조회 오류:', error.message);
    return 0;
  }
}

/**
 * 정책 패키지 조회 테스트
 */
async function testPolicyPackages(sessionId) {
  console.log('\n📋 정책 패키지 조회 테스트 중...');

  try {
    const response = await callFortiManagerAPI('get', 'pm/pkg/adom/Global', null, sessionId);

    if (response.result && response.result[0] && response.result[0].status && response.result[0].status.code === 0) {
      const packages = response.result[0].data;
      console.log(`✅ 정책 패키지 조회 성공! (총 ${packages.length}개 패키지)`);

      packages.slice(0, 3).forEach((pkg, index) => {
        console.log(`📦 패키지 ${index + 1}: ${pkg.name} (타입: ${pkg.type || 'N/A'})`);
      });

      return packages.length;
    } else {
      console.log('❌ 정책 패키지 조회 실패');
      console.log('📄 응답:', JSON.stringify(response, null, 2));
      return 0;
    }
  } catch (error) {
    console.log('❌ 정책 패키지 조회 오류:', error.message);
    return 0;
  }
}

/**
 * 로그아웃 테스트
 */
async function testLogout(sessionId) {
  console.log('\n🚪 로그아웃 테스트 중...');

  try {
    const response = await callFortiManagerAPI('exec', 'sys/logout', null, sessionId);
    console.log('✅ 로그아웃 완료');
    return true;
  } catch (error) {
    console.log('❌ 로그아웃 오류:', error.message);
    return false;
  }
}

/**
 * 메인 테스트 실행 함수
 */
async function runTests() {
  console.log('🧪 FortiManager JSON-RPC API 실제 연결 테스트 시작\n');
  console.log('=' .repeat(60));

  // 1. 로그인 테스트
  const sessionId = await testLogin();
  if (!sessionId) {
    console.log('\n❌ 로그인에 실패하여 테스트를 중단합니다.');
    console.log('\n💡 해결 방법:');
    console.log('   1. FMG_HOST 환경변수 확인 (현재: ' + FMG_CONFIG.host + ')');
    console.log('   2. FMG_USERNAME/FMG_PASSWORD 환경변수 확인');
    console.log('   3. FortiManager 서버가 실행 중인지 확인');
    console.log('   4. 네트워크 연결 및 방화벽 설정 확인');
    return false;
  }

  let successCount = 1; // 로그인 성공

  // 2. 시스템 상태 조회
  if (await testSystemStatus(sessionId)) successCount++;

  // 3. 관리 장비 목록 조회
  const deviceCount = await testDeviceList(sessionId);
  if (deviceCount > 0) successCount++;

  // 4. 정책 패키지 조회
  const packageCount = await testPolicyPackages(sessionId);
  if (packageCount > 0) successCount++;

  // 5. 로그아웃
  if (await testLogout(sessionId)) successCount++;

  // 결과 요약
  console.log('\n' + '=' .repeat(60));
  console.log('📊 테스트 결과 요약:');
  console.log(`✅ 성공한 테스트: ${successCount}/5`);
  console.log(`📱 관리 장비 수: ${deviceCount}개`);
  console.log(`📦 정책 패키지 수: ${packageCount}개`);

  if (successCount === 5) {
    console.log('\n🎉 모든 테스트 성공! FortiManager API 연동이 완전히 작동합니다.');
    return true;
  } else {
    console.log('\n⚠️  일부 테스트 실패. 부분적으로 작동합니다.');
    return false;
  }
}

// 스크립트가 직접 실행될 때만 테스트 실행
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests().catch(console.error);
}

export { callFortiManagerAPI, testLogin, testSystemStatus, testDeviceList };