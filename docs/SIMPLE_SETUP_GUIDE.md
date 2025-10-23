# 🚀 FortiAnalyzer → Splunk 초간단 설정 가이드

> **목표**: Splunk 설정 최소화, FAZ는 신경 안 쓰고 로그만 보내기

---

## 📋 선택: 방법 하나만 고르기

### ❓ 어떤 방식을 선택해야 할까?

| 상황 | 권장 방법 | 이유 |
|------|----------|------|
| **FAZ가 이미 Syslog 보내고 있음** | 방법 3 (Syslog) ⭐ | Splunk 설정만 하면 끝 |
| **FAZ 설정 못 건드림** | 방법 1 (Node.js) | FAZ API로 읽어와서 전송 |
| **FAZ 7.4+ 있고 HEC 설정 가능** | 방법 2 (FAZ HEC) | FAZ에서 직접 HEC로 전송 |

**대부분의 경우**: **방법 3 (Syslog) 추천** ✅

---

## 🎯 방법 3: Syslog (가장 간단) ⭐

### Splunk 설정 (5분)

#### 1. Syslog Input 추가

```bash
# Splunk Web UI
Settings → Data Inputs → UDP → New Local UDP

Port: 514 (또는 5514)
Source type: fortinet:fortigate:syslog
Index: fw
```

**또는 CLI로 설정**:

```bash
# /opt/splunk/etc/system/local/inputs.conf
[udp://514]
sourcetype = fortinet:fortigate:syslog
index = fw
connection_host = ip
no_appending_timestamp = true
```

#### 2. Splunk 재시작

```bash
sudo /opt/splunk/bin/splunk restart
```

#### 3. 끝! 🎉

FortiAnalyzer에서 Syslog만 보내면 자동으로 `index=fw`에 저장됩니다.

---

### FAZ 설정 (1분)

FortiAnalyzer에서 Syslog Forwarding만 켜면 됩니다:

```
System Settings → Advanced → Log Forwarding → Settings

[✓] Enable Forwarding
Server: <Splunk IP>
Port: 514
Protocol: UDP
```

**설정 파일**: `configs/fortigate-syslog.conf` 참고

---

### 대시보드 배포

```bash
# Splunk Web UI에서 업로드
Settings → User interface → Views → Import from XML

파일: configs/dashboards/correlation-analysis-syslog.xml
```

**완료!** ✅

---

## 🔧 방법 1: Node.js HEC (FAZ 설정 못 건드릴 때)

### Splunk 설정 (3분)

#### 1. HEC 토큰 생성

```bash
# Splunk Web UI
Settings → Data Inputs → HTTP Event Collector → New Token

Name: fortianalyzer-hec
Source type: _json
Index: fortigate_security
```

**토큰 복사**: `xxxx-xxxx-xxxx-xxxx`

#### 2. HEC 활성화

```bash
# Settings → Data Inputs → HTTP Event Collector → Global Settings
[✓] All Tokens: Enabled
[✓] Enable SSL: Yes
HTTP Port Number: 8088
```

#### 3. 끝! 🎉

---

### Node.js 클라이언트 실행

```bash
# .env 파일 설정
cp .env.example .env

# 필수 변수만 설정
FAZ_HOST=your-faz.example.com
FAZ_USERNAME=admin
FAZ_PASSWORD=your_password

SPLUNK_HEC_HOST=your-splunk.example.com
SPLUNK_HEC_TOKEN=xxxx-xxxx-xxxx-xxxx

# 실행
npm start
```

**또는 Cloudflare Workers**:

```bash
npm run deploy:worker
```

---

### 대시보드 배포

```bash
파일: configs/dashboards/correlation-analysis-hec.xml
```

---

## ⚡ 방법 2: FAZ HEC Direct (FAZ 7.4+만 가능)

### Splunk 설정

**방법 1과 동일** (HEC 토큰 생성)

---

### FAZ 설정

```
System Settings → Advanced → Log Forwarding → Settings

[✓] Enable Forwarding
Type: HEC
Server: <Splunk IP>:8088
Token: <HEC Token>
Index: fw
```

**설정 파일**: `configs/fortianalyzer-hec-direct.conf` 참고

---

### 대시보드 배포

```bash
파일: configs/dashboards/correlation-analysis-faz.xml
```

---

## 🎯 요약: 진짜 간단한 버전

### Splunk 쪽 (한 번만)

**Syslog 방식**:
```bash
1. Settings → Data Inputs → UDP → Port 514
2. Index: fw
3. 끝
```

**HEC 방식**:
```bash
1. Settings → Data Inputs → HEC → New Token
2. Index: fortigate_security (또는 fw)
3. 토큰 복사
4. 끝
```

### FAZ 쪽 (30초)

**Syslog 방식**:
```
Log Forwarding 켜기 → Splunk IP:514 입력 → 끝
```

**HEC 방식**:
```
Log Forwarding 켜기 → Splunk IP:8088 + Token → 끝
```

---

## 🚨 Splunk 쪽 추가 작업이 필요 없는 이유

✅ **Sourcetype 자동 인식**: `fortinet:fortigate:syslog` 또는 `_json`
✅ **Field Extraction 자동**: Splunk가 자동으로 필드 추출
✅ **App 설치 불필요**: 기본 Splunk만으로 충분
✅ **Data Model 선택적**: correlation-rules.conf 사용 시에만 필요

---

## 📊 Correlation Rules 설정 (선택적)

**상관관계 분석이 필요한 경우에만**:

```bash
# configs/correlation-rules.conf를 Splunk에 배포
cp configs/correlation-rules.conf /opt/splunk/etc/apps/fortigate/local/savedsearches.conf

# Splunk 재시작
sudo /opt/splunk/bin/splunk restart
```

---

## 🎉 최종 정리

### 가장 쉬운 방법 (추천)

```
1. Splunk: UDP 514 Input 추가 (1분)
2. FAZ: Syslog Forwarding 켜기 (30초)
3. Dashboard: correlation-analysis-syslog.xml 업로드 (30초)

총 2분 완료! ✅
```

### Splunk에서 해야 할 것

- ✅ Input 하나 추가 (UDP 또는 HEC)
- ❌ App 설치 불필요
- ❌ Sourcetype 설정 불필요 (자동)
- ❌ Field Extraction 불필요 (자동)
- ❌ 복잡한 설정 전혀 없음!

---

**Updated**: 2025-10-22
**Recommendation**: 방법 3 (Syslog) - 가장 간단함 ⭐
