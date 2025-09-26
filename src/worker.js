/**
 * Cloudflare Worker Entry Point
 * Serves the Fortinet Policy Verification web interface
 */

// Import the HTML content directly
const htmlContent = `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🛡️ Fortinet 방화벽 정책 확인</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
      color: #ffffff;
      min-height: 100vh;
      padding: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .container {
      max-width: 800px;
      margin: 0 auto;
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-radius: 20px;
      padding: 40px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
      text-align: center;
    }

    .header h1 {
      font-size: 2.5rem;
      margin-bottom: 20px;
      text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }

    .description {
      font-size: 1.2rem;
      opacity: 0.9;
      margin-bottom: 30px;
      line-height: 1.6;
    }

    .features {
      text-align: left;
      margin: 30px 0;
    }

    .features h3 {
      color: #4fc3f7;
      margin-bottom: 15px;
    }

    .features ul {
      list-style: none;
      padding: 0;
    }

    .features li {
      margin: 10px 0;
      padding-left: 30px;
      position: relative;
    }

    .features li:before {
      content: '✅';
      position: absolute;
      left: 0;
    }

    .setup-info {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 15px;
      padding: 25px;
      margin: 30px 0;
      text-align: left;
    }

    .setup-info h3 {
      color: #4fc3f7;
      margin-bottom: 15px;
    }

    .code-block {
      background: rgba(0, 0, 0, 0.3);
      border-radius: 8px;
      padding: 15px;
      font-family: monospace;
      font-size: 0.9rem;
      margin: 10px 0;
      white-space: pre-wrap;
    }

    .github-link {
      display: inline-block;
      background: linear-gradient(45deg, #4fc3f7, #29b6f6);
      color: white;
      text-decoration: none;
      padding: 15px 30px;
      border-radius: 50px;
      font-weight: 600;
      transition: transform 0.3s ease;
    }

    .github-link:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 20px rgba(79, 195, 247, 0.3);
    }

    .status {
      margin-top: 20px;
      padding: 15px;
      background: rgba(76, 175, 80, 0.2);
      border: 1px solid #4caf50;
      border-radius: 10px;
    }

    @media (max-width: 768px) {
      .container {
        margin: 20px;
        padding: 30px 20px;
      }

      .header h1 {
        font-size: 2rem;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🛡️ Fortinet 방화벽 정책 확인 시스템</h1>
      <p class="description">
        FortiManager를 통해 관리되는 80+ FortiGate 장비의<br>
        방화벽 정책을 실시간으로 확인할 수 있는 웹 기반 도구
      </p>
    </div>

    <div class="features">
      <h3>🎯 핵심 기능</h3>
      <ul>
        <li>출발지 → 목적지 트래픽 분석</li>
        <li>실시간 허용/차단 여부 확인</li>
        <li>다중 FortiGate 장비 지원 (80+)</li>
        <li>Multi-VDOM 환경 지원</li>
        <li>정책 상세 정보 표시</li>
        <li>모바일 친화적 웹 인터페이스</li>
      </ul>
    </div>

    <div class="setup-info">
      <h3>🚀 시스템 구성</h3>
      <p>이 시스템은 다음과 같이 구성되어 있습니다:</p>
      <ul>
        <li><strong>웹 인터페이스</strong>: 사용자 친화적 정책 확인 도구</li>
        <li><strong>Policy Server</strong>: Express.js 기반 RESTful API</li>
        <li><strong>FortiManager 연동</strong>: JSON-RPC 직접 연결</li>
        <li><strong>Splunk 통합</strong>: 중앙화된 보안 이벤트 처리</li>
      </ul>
    </div>

    <div class="setup-info">
      <h3>🔧 로컬 실행 방법</h3>
      <div class="code-block"># 저장소 클론
git clone https://github.com/qws941/splunk.git
cd splunk

# 의존성 설치
npm install

# 환경 변수 설정
export FMG_HOST=fortimanager.jclee.me
export FMG_USERNAME=admin
export FMG_PASSWORD=your_password

# 정책 확인 서버 실행
npm run policy-server

# 웹 브라우저에서 접속
# http://localhost:3001</div>
    </div>

    <div class="setup-info">
      <h3>📊 API 사용 예시</h3>
      <div class="code-block"># 정책 확인 API
curl -X POST http://localhost:3001/api/policy/verify \\
  -H "Content-Type: application/json" \\
  -d '{
    "sourceIP": "192.168.1.100",
    "destIP": "10.0.0.100",
    "protocol": "TCP",
    "port": 80
  }'</div>
    </div>

    <div class="status">
      <strong>✅ 시스템 상태:</strong> 정책 확인 시스템이 성공적으로 구현되었습니다!<br>
      완전한 기능을 사용하려면 위의 설정 과정을 따라 로컬 서버를 실행하세요.
    </div>

    <div style="margin-top: 30px;">
      <a href="https://github.com/qws941/splunk" class="github-link" target="_blank">
        📚 GitHub 저장소 방문
      </a>
    </div>

    <div style="margin-top: 30px; font-size: 0.9rem; opacity: 0.8;">
      <p>🔒 보안이 중요한 환경에서는 적절한 접근 제어와 모니터링을 구성하시기 바랍니다.</p>
      <p>📞 지원이 필요하시면 GitHub Issues를 이용해 주세요.</p>
    </div>
  </div>
</body>
</html>`;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Handle different routes
    if (url.pathname === '/' || url.pathname === '/index.html') {
      return new Response(htmlContent, {
        headers: {
          'Content-Type': 'text/html;charset=UTF-8',
          'Cache-Control': 'public, max-age=3600',
        },
      });
    }

    // Health check endpoint
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'healthy',
        message: 'Fortinet Policy Verification System - Static Web Interface',
        timestamp: new Date().toISOString(),
        note: 'For full functionality, run the Node.js server locally'
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
        },
      });
    }

    // API information endpoint
    if (url.pathname.startsWith('/api')) {
      return new Response(JSON.stringify({
        message: 'API endpoints are available when running the local server',
        setup: 'Run: npm run policy-server',
        endpoints: [
          'POST /api/policy/verify - Policy verification',
          'GET /api/fortimanager/devices - Device list',
          'GET /health - Server status'
        ]
      }), {
        headers: {
          'Content-Type': 'application/json',
        },
      });
    }

    // 404 for other routes
    return new Response('Page not found', { status: 404 });
  },
};