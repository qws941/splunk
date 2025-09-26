# 🛡️ Fortinet 방화벽 정책 확인 도구

FortiManager를 통해 관리되는 80+ FortiGate 장비의 방화벽 정책을 실시간으로 확인할 수 있는 웹 기반 도구입니다.

## ✨ 주요 기능

### 🔍 정책 확인 기능
- **출발지 → 목적지 트래픽 분석**: IP 주소와 포트를 입력하여 허용/차단 여부 확인
- **실시간 정책 평가**: FortiGate의 정책 평가 순서를 정확히 반영
- **다중 장비 지원**: 80+ FortiGate 장비 전체 또는 특정 장비 선택
- **Multi-VDOM 지원**: 가상 도메인별 정책 확인

### 🌐 사용자 인터페이스
- **직관적인 웹 인터페이스**: 모바일 친화적 반응형 디자인
- **실시간 결과 표시**: 정책 매칭 결과와 상세 정보 제공
- **시각적 피드백**: 허용/차단 상태를 색상과 아이콘으로 구분

### 🔧 고급 기능
- **주소 객체 해석**: FortiGate 주소 객체 자동 확인
- **서비스 객체 해석**: 포트/프로토콜 서비스 객체 자동 확인
- **정책 상세 정보**: 매칭된 정책의 모든 설정값 표시
- **실시간 장비 상태**: 연결된 FortiGate 장비 상태 확인

## 🚀 시작하기

### 전제 조건
```bash
# Node.js 18+ 필요
node --version

# FortiManager 접근 권한
# - FortiManager 호스트: fortimanager.jclee.me
# - API 접근 권한이 있는 관리자 계정
```

### 설치 및 실행
```bash
# 의존성 설치
npm install

# 환경 변수 설정
export FMG_HOST=fortimanager.jclee.me
export FMG_USERNAME=admin
export FMG_PASSWORD=your_password
export FMG_ADOM=Global

# 정책 확인 서버 실행
npm run policy-server

# 개발 모드 (자동 재시작)
npm run policy-server:dev
```

### 웹 인터페이스 접근
```
브라우저에서 열기: http://localhost:3001
```

## 🎯 사용 방법

### 1. 기본 정책 확인
```
1. 출발지 IP 주소 입력 (예: 192.168.1.100)
2. 목적지 IP 주소 입력 (예: 10.0.0.100)
3. 프로토콜 선택 (TCP/UDP/ICMP/Any)
4. 포트 번호 입력 (예: 80, 443, 22)
5. "정책 확인" 버튼 클릭
```

### 2. 고급 옵션 사용
```
- 장비 선택: 특정 FortiGate 장비만 확인
- VDOM 선택: 가상 도메인별 정책 확인
- 서비스 객체: HTTP, HTTPS, SSH 등 미리 정의된 서비스
- 모든 매칭 정책 표시: 첫 번째 매칭 정책뿐만 아니라 모든 관련 정책
```

### 3. 결과 해석
```yaml
허용 결과 (✅):
  - 초록색 표시
  - 매칭된 정책 정보 표시
  - 정책 ID, 이름, 설정값 상세 정보

차단 결과 (❌):
  - 빨간색 표시
  - 차단 이유 (명시적 차단 또는 기본 거부)
  - 관련 정책 정보 (있는 경우)
```

## 🏗️ 아키텍처

### 시스템 구성
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Web Browser       │    │  Policy Server      │    │  FortiManager       │
│  (React Frontend)   │◄──►│  (Node.js/Express)  │◄──►│  (JSON-RPC API)     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FortiGate Devices (80+)                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐       ┌─────────┐  ┌─────────┐     │
│  │   FG1   │  │   FG2   │  │   FG3   │  ...  │  FG79   │  │  FG80+  │     │
│  └─────────┘  └─────────┘  └─────────┘       └─────────┘  └─────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 데이터 흐름
```
1. 사용자 입력 → 웹 인터페이스
2. 웹 인터페이스 → Policy Server API
3. Policy Server → FortiManager JSON-RPC
4. FortiManager → 정책 데이터 조회
5. Policy Server → 정책 평가 엔진
6. 결과 반환 → 웹 인터페이스 표시
```

## 📊 API 엔드포인트

### 정책 확인 API
```http
POST /api/policy/verify
Content-Type: application/json

{
  "sourceIP": "192.168.1.100",
  "destIP": "10.0.0.100",
  "protocol": "TCP",
  "port": 80,
  "service": "HTTP",
  "device": "FortiGate-80E",
  "vdom": "root"
}
```

### 응답 예시
```json
{
  "matches": true,
  "policy": {
    "id": 15,
    "name": "Allow_Web_Access",
    "action": "accept",
    "srcaddr": ["Internal_Network"],
    "dstaddr": ["DMZ_Servers"],
    "service": ["HTTP", "HTTPS"],
    "device": "FortiGate-80E",
    "vdom": "root"
  },
  "result": "ALLOW",
  "evaluation": {
    "sourceIP": "192.168.1.100",
    "destIP": "10.0.0.100",
    "port": 80,
    "protocol": "TCP",
    "matchedSrcAddr": ["Internal_Network"],
    "matchedDstAddr": ["DMZ_Servers"],
    "matchedService": ["HTTP"]
  }
}
```

### 장비 목록 API
```http
GET /api/fortimanager/devices
```

### 정책 상세 API
```http
GET /api/policy/123?device=FortiGate-80E&vdom=root
```

## 🔧 설정

### 환경 변수
```bash
# FortiManager 연결 설정
FMG_HOST=fortimanager.jclee.me       # FortiManager 호스트
FMG_PORT=443                         # HTTPS 포트
FMG_USERNAME=admin                   # 관리자 사용자명
FMG_PASSWORD=fortinet               # 관리자 비밀번호
FMG_ADOM=Global                     # Administrative Domain

# 서버 설정
PORT=3001                           # 웹 서버 포트
NODE_ENV=production                 # 운영/개발 모드
```

### FortiManager 권한 요구사항
```yaml
필요 권한:
  - Read-only access to Policy & Object configurations
  - Device management read access
  - ADOM access (Global 또는 specific)

API 접근:
  - JSON-RPC 2.0 지원
  - /jsonrpc endpoint 접근 권한
  - Policy Manager (/pm/config/) 읽기 권한
  - Device Manager (/dvmdb/) 읽기 권한
```

## 🛡️ 보안 고려사항

### 인증 및 권한
- FortiManager와의 연결에 HTTPS/TLS 사용
- 관리자 계정 정보는 환경변수로 관리
- API 키 또는 토큰 기반 인증 권장

### 네트워크 보안
- FortiManager 관리 네트워크와의 직접 연결 필요
- 방화벽 규칙: Policy Server → FortiManager (TCP/443)
- 웹 인터페이스 접근 제한 권장

### 데이터 보안
- 정책 정보는 메모리에서만 처리 (영구 저장하지 않음)
- 민감한 네트워크 정보 로깅 제한
- RBAC 기반 접근 제어 구현 권장

## 🔄 통합 연동

### Splunk 연동
```javascript
// 정책 확인 결과를 Splunk으로 전송
const verificationEvent = {
  timestamp: Date.now(),
  source_ip: sourceIP,
  dest_ip: destIP,
  result: result.result,
  policy_id: result.policy?.id,
  user: req.user || 'anonymous'
};

// Splunk HEC로 전송
await splunkConnector.sendEvent('policy_verification', verificationEvent);
```

### Slack 알림 연동
```javascript
// 중요 정책 확인시 Slack 알림
if (result.result === 'BLOCK' && isProductionTraffic(sourceIP, destIP)) {
  await slackHandler.sendAlert({
    channel: '#security-alerts',
    message: `🚫 Production traffic blocked: ${sourceIP} → ${destIP}:${port}`,
    policy: result.policy
  });
}
```

## 📈 모니터링 및 로깅

### 실시간 메트릭
```yaml
제공 메트릭:
  - 시간당 정책 확인 요청 수
  - 허용/차단 비율
  - 응답 시간 통계
  - FortiManager 연결 상태
  - 오류율 및 유형별 분석
```

### 로그 수집
```yaml
로그 카테고리:
  - 정책 확인 요청/응답
  - FortiManager API 호출
  - 사용자 활동 (익명화)
  - 시스템 오류 및 경고
  - 성능 메트릭
```

## 🚀 배포

### Docker 배포
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY src/ ./src/
EXPOSE 3001
CMD ["npm", "run", "policy-server"]
```

### 운영 환경 설정
```yaml
# docker-compose.yml
version: '3.8'
services:
  policy-verification:
    build: .
    ports:
      - "3001:3001"
    environment:
      - FMG_HOST=fortimanager.jclee.me
      - FMG_USERNAME=${FMG_USERNAME}
      - FMG_PASSWORD=${FMG_PASSWORD}
      - FMG_ADOM=Global
    restart: unless-stopped
    networks:
      - fortinet-management
```

## 🧪 테스트

### 단위 테스트
```bash
# 정책 평가 로직 테스트
npm test

# 특정 테스트 실행
node --test src/tests/policy-evaluation.test.js
```

### 통합 테스트
```bash
# FortiManager 연결 테스트
npm run test:integration

# API 엔드포인트 테스트
npm run test:api
```

## 📞 지원 및 문의

### 기술 지원
- **시스템 관리자**: jclee@company.com
- **보안 팀**: security@company.com
- **네트워크 팀**: network@company.com

### 문제 해결
```bash
# 로그 확인
npm run policy-server 2>&1 | tee policy-server.log

# FortiManager 연결 테스트
curl -X POST http://localhost:3001/api/fortimanager/test

# 서버 상태 확인
curl http://localhost:3001/health
```

---

**📝 이 도구는 FortiManager API를 직접 활용하여 실시간 정책 확인 기능을 제공합니다.**
**🔒 보안이 중요한 환경에서는 적절한 접근 제어와 모니터링을 구성하시기 바랍니다.**