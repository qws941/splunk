# 🏢 Splunk 중심 Fortinet 통합 시스템 요구사항 명세서

## 📋 **시스템 개요**

### 보유 장비 현황
- **FMG** (FortiManager): 중앙 정책 관리
- **FAZ** (FortiAnalyzer): 로그 분석 및 보고
- **FortiGate**: 보안 게이트웨이 (Multiple)
- **Splunk**: SIEM 플랫폼 (통합 허브)

### 통합 목표
- Splunk를 중심으로 한 통합 보안 운영센터 구축
- 실시간 위협 탐지 및 자동 대응
- 통합 대시보드를 통한 360도 보안 가시성
- 정책 변경 및 설정 감사 자동화

---

## 🌐 **통신 요구사항**

### 1. **네트워크 연결 요구사항**

#### **FortiManager ↔ Splunk**
```
Protocol: HTTPS/JSON-RPC
Port: 443
Authentication: Username/Password + Session Token
API Endpoints:
  - /jsonrpc (JSON-RPC 2.0)
  - /sys/login/user (Authentication)
  - /pm/config/ (Policy Management)
  - /dvmdb/ (Device Management)
Connection Method: REST API Polling
Polling Interval: 60초 (정책 변경)
```

#### **FortiAnalyzer ↔ Splunk**
```
Protocol: HTTPS/REST API
Port: 443
Authentication: API Token
API Endpoints:
  - /api/v2/cmdb/system/admin (Auth)
  - /api/v2/log/ (Log Data)
  - /api/v2/report/ (Reports)
Connection Method: REST API + Log Forwarding
Data Transfer: JSON Format
Polling Interval: 300초 (분석 데이터)
```

#### **FortiGate ↔ Splunk**
```
Protocol: HTTPS/REST API + Syslog
Port: 443 (API), 514 (Syslog)
Authentication: API Token
API Endpoints:
  - /api/v2/log/ (Security Logs)
  - /api/v2/monitor/ (System Status)
Connection Method: Hybrid (API + Syslog)
Polling Interval: 30초 (보안 이벤트)
```

---

## 📊 **데이터 수집 명세**

### **FortiManager 데이터**
```javascript
데이터 카테고리: {
  policy_changes: {
    수집주기: "1분",
    우선순위: "높음",
    Splunk_Index: "fortimanager_policy",
    필드: ["policyid", "name", "action", "srcaddr", "dstaddr", "service"]
  },
  config_changes: {
    수집주기: "5분",
    우선순위: "중간",
    Splunk_Index: "fortimanager_config",
    필드: ["revision", "created_by", "timestamp", "device"]
  },
  admin_activities: {
    수집주기: "1분",
    우선순위: "높음",
    Splunk_Index: "fortimanager_admin",
    필드: ["user", "action", "result", "timestamp"]
  }
}
```

### **FortiAnalyzer 데이터**
```javascript
데이터 카테고리: {
  security_analytics: {
    수집주기: "5분",
    우선순위: "높음",
    Splunk_Index: "fortianalyzer_security",
    필드: ["threat_type", "severity", "source_ip", "target_ip", "analysis_result"]
  },
  traffic_analytics: {
    수집주기: "10분",
    우선순위: "중간",
    Splunk_Index: "fortianalyzer_traffic",
    필드: ["bandwidth", "top_applications", "top_users", "anomalies"]
  },
  compliance_reports: {
    수집주기: "1시간",
    우선순위: "낮음",
    Splunk_Index: "fortianalyzer_compliance",
    필드: ["report_type", "compliance_status", "violations"]
  }
}
```

---

## 🏗️ **시스템 아키텍처**

### **통합 아키텍처 구성도**
```
┌─────────────────────────────────────────────────────────┐
│                    Splunk SIEM Hub                     │
├─────────────────┬─────────────────┬─────────────────────┤
│  FMG Connector  │  FAZ Connector  │ FortiGate Connector │
├─────────────────┼─────────────────┼─────────────────────┤
│ • Policy Mgmt   │ • Log Analysis  │ • Real-time Events  │
│ • Config Audit  │ • Threat Intel  │ • Security Logs     │
│ • Admin Audit   │ • Compliance    │ • Traffic Logs      │
└─────────────────┴─────────────────┴─────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│FortiManager │  │FortiAnalyzer│  │ FortiGate   │
│   (FMG)     │  │    (FAZ)    │  │ Multi-Device│
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## 📁 **구현 모듈 구조**

```
src/
├── connectors/
│   ├── fortimanager-splunk-connector.js     # FMG 연동
│   ├── fortianalyzer-splunk-connector.js    # FAZ 연동
│   └── fortigate-splunk-integration.js      # FortiGate 연동 (기존)
├── processors/
│   ├── security-event-processor.js          # 보안 이벤트 처리 (기존)
│   ├── policy-change-processor.js           # 정책 변경 처리
│   └── compliance-processor.js              # 컴플라이언스 처리
├── analytics/
│   ├── threat-correlation-engine.js         # 위협 상관분석
│   ├── anomaly-detection.js                 # 이상 탐지
│   └── risk-scoring.js                      # 위험 점수 산출
├── automation/
│   ├── soar-workflows.js                    # SOAR 워크플로우
│   ├── auto-response.js                     # 자동 대응
│   └── policy-automation.js                 # 정책 자동화
└── dashboards/
    ├── executive-dashboard.js               # 경영진 대시보드
    ├── soc-dashboard.js                     # SOC 대시보드
    └── compliance-dashboard.js              # 컴플라이언스 대시보드
```

---

## 🔒 **보안 요구사항**

### **인증 및 권한**
- **FMG**: Username/Password + Session Management
- **FAZ**: API Token + Role-based Access
- **FortiGate**: API Token + RBAC
- **Splunk**: App Token + Index Permissions

### **네트워크 보안**
- **전송 암호화**: HTTPS/TLS 1.2+
- **API 인증**: Certificate-based Authentication
- **방화벽 규칙**: 필요한 포트만 개방 (443, 514)
- **네트워크 분할**: Management vs Data Networks

---

## ⚡ **성능 요구사항**

### **처리 성능**
- **이벤트 처리량**: 10,000 EPS (Events Per Second)
- **API 호출 제한**: FMG/FAZ 각 60 requests/minute
- **데이터 지연시간**: < 30초 (실시간 이벤트)
- **대시보드 로딩**: < 5초

### **저장 용량**
```
Splunk Indexes:
  - fortigate_security: 10GB/day
  - fortimanager_policy: 1GB/day
  - fortianalyzer_security: 5GB/day
  - Total Retention: 90 days
  - Total Storage: ~1.5TB
```

---

## 📊 **통합 대시보드 요구사항**

### **Executive Dashboard**
- 전체 보안 상태 (Green/Yellow/Red)
- 일일 보안 이벤트 수
- 정책 변경 현황
- 컴플라이언스 점수
- 위험 점수 트렌드
- **업데이트**: 실시간 (5분)

### **SOC Dashboard**
- 실시간 위협 맵
- 상위 공격자 IP
- 차단된 위협 수
- 정책 적용 현황
- 장비별 상태
- **업데이트**: 실시간 (30초)

### **Compliance Dashboard**
- 정책 준수율
- 설정 변경 감사
- 관리자 활동 로그
- 규정 위반 사항
- **업데이트**: 1시간

---

## 🚨 **알림 및 자동화**

### **Slack 알림 채널**
```
Critical Alerts → #security-critical
  - CRITICAL 등급 위협, 정책 위반 (즉시)

Warning Alerts → #security-warnings
  - HIGH 등급 위협, 설정 변경 (5분 집계)

Info Alerts → #security-info
  - 시스템 상태, 정기 리포트 (1시간 집계)
```

### **자동 대응 레벨**
- **Level 1**: 알려진 악성 IP 자동 차단 (<30초)
- **Level 2**: 의심 활동 격리 후 승인 (<5분)
- **Level 3**: 복잡한 위협은 SOC 팀 에스컬레이션

---

## 🚀 **구현 단계**

### **Phase 1: 기반 구축 (4주)**
- [x] FortiGate-Splunk 연동 (완료)
- [ ] FMG-Splunk 커넥터 개발
- [ ] FAZ-Splunk 커넥터 개발

### **Phase 2: 통합 및 분석 (6주)**
- [ ] 통합 이벤트 프로세서
- [ ] 위협 상관분석 엔진
- [ ] 통합 대시보드 구축

### **Phase 3: 자동화 (4주)**
- [ ] SOAR 워크플로우
- [ ] 자동 대응 시스템
- [ ] 정책 자동화

### **Phase 4: 최적화 (2주)**
- [ ] 성능 튜닝
- [ ] 고가용성 구성
- [ ] 운영 자동화

---

## 📈 **핵심 KPI**

### **보안 지표**
- 평균 위협 탐지 시간 (MTTD): < 5분
- 평균 대응 시간 (MTTR): < 30분
- 오탐률 (False Positive): < 5%
- 시스템 가동률: > 99.9%

### **운영 지표**
- 정책 배포 시간: < 10분
- 컴플라이언스 점수: > 95%
- 관리자 생산성 향상: 40%
- 수동 작업 감소: 60%

---

**📝 이 명세서는 Splunk를 중심으로 한 완전한 Fortinet 생태계 통합을 위한 모든 요구사항을 정의합니다.**