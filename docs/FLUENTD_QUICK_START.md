# 🚀 Fluentd-HEC Quick Start Guide

**Architecture**: FortiGate → FortiAnalyzer → Fluentd → Splunk HEC

**Setup Time**: 10분 (자동화됨)

---

## 📋 사전 요구사항

1. ✅ Docker & Docker Compose 설치됨
2. ✅ Splunk HEC 토큰 생성됨
3. ✅ FortiAnalyzer 관리자 접근 가능
4. ✅ 방화벽 규칙: FAZ → Fluentd (UDP 514), Fluentd → Splunk (TCP 8088)

---

## ⚡ 30초 자동 배포

### 1️⃣ 환경 변수 설정

```bash
cd /home/jclee/app/splunk

# .env 파일 복사 (처음만)
cp .env.example .env

# 필수 변수 수정 (vi 또는 nano)
vi .env
```

**필수 변수**:
```bash
SPLUNK_HEC_HOST=splunk.jclee.me
SPLUNK_HEC_TOKEN=00000000-0000-0000-0000-000000000000
SPLUNK_INDEX_FORTIGATE=fortianalyzer
```

### 2️⃣ 자동 배포 실행

```bash
./scripts/deploy-fluentd-hec.sh
```

**이 스크립트가 자동으로**:
- ✅ Fluentd 컨테이너 배포 (splunk-hec plugin 설치)
- ✅ Syslog 포트 오픈 (UDP 514, TCP 6514)
- ✅ Splunk HEC 연결 테스트
- ✅ FortiAnalyzer 설정 파일 생성 (복붙 전용)

### 3️⃣ FortiAnalyzer 설정 (1분)

스크립트가 생성한 `faz-fluentd-config-*.txt` 파일 열기:

```bash
cat faz-fluentd-config-$(ls -t faz-fluentd-config-*.txt | head -1)
```

**"1단계" 섹션 복붙** → FortiAnalyzer CLI에 붙여넣기:

```bash
# SSH로 FAZ 접속
ssh admin@<FAZ_IP>

# 설정 파일의 "1단계" 명령어 복붙
config system log-forward
    edit "fluentd-syslog"
        set server-ip "172.28.32.x"  # Fluentd 서버 IP
        set server-port 514
        set protocol udp
        set log-type traffic utm event
        set status enable
    next
end
```

### 4️⃣ 데이터 확인 (1-2분 후)

**Splunk Web Search**:
```spl
index=fortianalyzer sourcetype=fortianalyzer:fluentd earliest=-5m
| head 100
| table _time, devname, logid, type, subtype, srcip, dstip
```

---

## ✅ 완료!

**예상 결과**:
- FortiAnalyzer 로그가 Fluentd 경유하여 Splunk에 전송됨
- 레이턴시: 5-10초 (Fluentd 버퍼 flush 간격)
- Sourcetype: `fortianalyzer:fluentd`

---

## 🔍 모니터링

### Fluentd 상태 확인

```bash
# 컨테이너 로그 (실시간)
docker logs -f fluentd-faz-hec

# Fluentd 모니터링 API
curl http://localhost:24220/api/plugins.json | jq .

# Buffer 상태
docker exec fluentd-faz-hec ls -lh /var/log/fluentd/buffer/splunk_hec/
```

### Prometheus 메트릭

```bash
curl http://localhost:24231/metrics
```

**Grafana 대시보드**: http://grafana.jclee.me (자동 수집됨)

---

## 🛠️ 트러블슈팅

### 문제 1: 로그가 Splunk에 안 들어옴

**확인 순서**:
```bash
# 1. Fluentd 컨테이너 실행 중?
docker ps | grep fluentd-faz-hec

# 2. Fluentd 로그 확인
docker logs fluentd-faz-hec --tail 50

# 3. Buffer에 데이터 쌓이는지 확인
docker exec fluentd-faz-hec ls -lh /var/log/fluentd/buffer/splunk_hec/

# 4. Splunk HEC 연결 테스트
curl -k https://splunk.jclee.me:8088/services/collector/event \
  -H "Authorization: Splunk ${SPLUNK_HEC_TOKEN}" \
  -d '{"event":"test","sourcetype":"test"}'
```

### 문제 2: FortiAnalyzer에서 Fluentd로 안 보냄

**FortiAnalyzer CLI 확인**:
```bash
# Syslog 전송 상태
diagnose test application logfwd

# 큐 상태 (0에 가까워야 정상)
diagnose log-forward queue-status

# 최근 전송 로그
diagnose log-forward logfwd-log list | tail -20
```

### 문제 3: Fluentd 파싱 실패

**로그에서 parsing error 찾기**:
```bash
docker logs fluentd-faz-hec 2>&1 | grep -i "error\|failed"
```

**해결**: `configs/fluentd/fluent.conf`의 정규식 수정

### 문제 4: Buffer가 계속 쌓임

**원인**: Splunk HEC 접근 불가 또는 토큰 오류

**확인**:
```bash
# Fluentd에서 Splunk HEC 연결 테스트
docker exec fluentd-faz-hec curl -k \
  -H "Authorization: Splunk ${SPLUNK_HEC_TOKEN}" \
  -d '{"event":"test"}' \
  https://splunk.jclee.me:8088/services/collector/event
```

---

## 🔧 고급 설정

### GeoIP 추가 (선택적)

`configs/fluentd/fluent.conf`에 추가:

```ruby
<filter fortianalyzer.**>
  @type geoip
  geoip_lookup_keys srcip,dstip
  <record>
    src_country ${city.country.iso_code["srcip"]}
    src_city ${city.city.name["srcip"]}
    dst_country ${city.country.iso_code["dstip"]}
    dst_city ${city.city.name["dstip"]}
  </record>
</filter>
```

**재시작**:
```bash
docker restart fluentd-faz-hec
```

### Debug 로그 수집 제외

`configs/fluentd/fluent.conf`에 추가:

```ruby
<filter fortianalyzer.**>
  @type grep
  <exclude>
    key level
    pattern /^debug$/
  </exclude>
</filter>
```

### Traffic 로그 샘플링 (10%)

```ruby
<filter fortianalyzer.*.traffic>
  @type sampling
  sample_rate 10
</filter>
```

---

## 📊 아키텍처 비교

| 특징 | Direct FAZ HEC | **Fluentd-HEC (현재)** |
|------|----------------|------------------------|
| 설정 복잡도 | ⭐⭐⭐⭐⭐ 매우 간단 | ⭐⭐⭐ 보통 |
| 추가 인프라 | 없음 (FAZ 내장) | Fluentd 컨테이너 필요 |
| 레이턴시 | < 1초 | 5-10초 |
| 로그 변환 | 제한적 | **무제한** ✅ |
| 여러 목적지 | 단일 (Splunk만) | **다중 가능** ✅ |
| 커스텀 필드 | 불가 | **가능** ✅ |
| 비용 | $0 | VM/컨테이너 비용 |

**선택 이유**: 로그 변환 및 다중 목적지 전송 필요 시 Fluentd-HEC 사용

---

## 📝 다음 단계

1. **대시보드 배포**:
   ```bash
   # Splunk Web UI → Dashboards → Create → Dashboard Studio → Source
   # 붙여넣기: configs/dashboards/studio-production/*.json
   ```

2. **알림 설정**:
   ```bash
   # configs/savedsearches-fortigate-alerts.conf를 Splunk에 배포
   cp configs/savedsearches-fortigate-alerts.conf \
      /opt/splunk/etc/apps/search/local/
   ```

3. **Grafana 연동** (자동):
   - Prometheus가 http://localhost:24231/metrics에서 자동 수집
   - Loki가 docker logs에서 자동 수집
   - Grafana 대시보드: http://grafana.jclee.me

---

**Setup Time**: 10분
**Maintenance**: 월 1회 (Fluentd plugin 업데이트)
**Performance**: 5-10초 레이턴시, 100 events/batch
**Reliability**: Buffer + Retry (10 attempts, exponential backoff)

**문서**:
- 상세 비교: `docs/FLUENTD_HEC_EVALUATION.md`
- Config 파일: `configs/fluentd/fluent.conf`
- Compose 파일: `docker-compose-fluentd.yml`

**Support**: Docker logs 확인 → 설정 파일의 트러블슈팅 섹션 참고
