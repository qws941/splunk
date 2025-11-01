# 📊 GitHub 검증 결과 - FortiGate 7.4 로그 구조

> **Wazuh FortiGate Decoder**에서 실제 로그 예제 확인

---

## ✅ GitHub에서 확인된 실제 로그 예제

### 출처
- **Repository**: wazuh/wazuh-ruleset
- **File**: decoders/0100-fortigate_decoders.xml
- **URL**: https://github.com/wazuh/wazuh-ruleset/blob/master/decoders/0100-fortigate_decoders.xml

---

## 🔍 확인된 실제 FortiGate 로그

### 1. logid=0100044546 (설정 속성 변경)

```
date=2016-06-16 time=08:41:14 devname=Mobipay_Firewall devid=FGTXXXX9999999999 
logid=0100044546 type=event subtype=system level=information vd="root" 
logdesc="Attribute configured" user="a@b.com.na" ui="GUI(10.42.8.253)" 
action=Edit cfgtid=2162733 cfgpath="log.threat-weight" 
cfgattr="failed-connection[low->medium]" msg="Edit log.threat-weight"
```

**핵심 필드**:
- ✅ `type=event` - 이벤트 로그
- ✅ `subtype=system` - 시스템 서브타입  
- ✅ `logid=0100044546` - 설정 속성 변경
- ✅ `cfgpath="log.threat-weight"` - 설정 경로
- ✅ `cfgattr="failed-connection[low->medium]"` - 변경 내용 (이전->이후)
- ✅ `user="a@b.com.na"` - 관리자
- ✅ `action=Edit` - 작업 유형
- ✅ `logdesc="Attribute configured"` - 로그 설명

---

## ✅ v2 대시보드 검증

### 검색 쿼리 검증

**v2 대시보드 쿼리**:
```spl
index=fw type=event subtype=system (logid=0100044546 OR logid=0100044547 OR cfgpath=*)
```

**GitHub 로그와 비교**:
- ✅ `type=event` - 일치
- ✅ `subtype=system` - 일치
- ✅ `logid=0100044546` - 일치
- ✅ `cfgpath=*` - 일치 (cfgpath="log.threat-weight" 캡처)

### 필드 매핑 검증

**v2 대시보드 eval 로직**:
```spl
| eval 설명 = coalesce(logdesc, msg, cfgpath, "Configuration change")
```

**GitHub 로그 필드**:
- ✅ `logdesc="Attribute configured"` - 우선순위 1
- ✅ `msg="Edit log.threat-weight"` - 우선순위 2
- ✅ `cfgpath="log.threat-weight"` - 우선순위 3

→ **완벽하게 일치**

---

## 🔍 추가 확인 사항

### Splunk Connect for Syslog 검증

**출처**: splunk/splunk-connect-for-syslog
**파일**: tests/test_fortinet_ngfw.py

**확인된 패턴**:
```python
'{{ mark }} {{ bsd }} fortigate date={{ date }} time={{ time }} 
devname={{ host }} devid=FGT60D4614044725 logid=0100040704 
type=event subtype=system level=notice vd=root 
logdesc="System performance statistics" action="perf-stats" 
cpu=2 mem=35 totalsession=61'
```

**검증 결과**:
- ✅ `type=event subtype=system` - Splunk 공식 파서도 동일 패턴 사용
- ✅ `logid=` 형식 - 일치
- ✅ `logdesc=` 필드 - 일치

---

## ⚠️ 주의사항: cfgpath 경로 패턴

### GitHub에서 확인된 cfgpath 예시

**1. 시스템 설정**:
```
cfgpath="log.threat-weight"
cfgpath="log.memory.filter"
```

**2. 방화벽 객체** (예상 패턴):
```
cfgpath="firewall.policy"
cfgpath="firewall.address"
cfgpath="firewall.addrgrp"
cfgpath="firewall.service"
cfgpath="firewall.servicegrp"
```

**v2 대시보드 정규식**:
```spl
match(cfgpath, "firewall\.policy")
match(cfgpath, "firewall\.address")
match(cfgpath, "firewall\.service")
```

→ 점(.) 이스케이프 **정확함** ✅

---

## 📊 검증 결론

### ✅ 올바르게 구현된 항목

1. ✅ **Event System 필터**: `type=event subtype=system` (GitHub 예제와 100% 일치)
2. ✅ **LogID 사용**: `logid=0100044546` (Wazuh 예제 일치)
3. ✅ **필드 우선순위**: `coalesce(logdesc, msg, cfgpath)` (GitHub 로그 구조와 일치)
4. ✅ **정규식 이스케이프**: `firewall\.policy` (올바른 패턴)
5. ✅ **cfgpath 필드**: GitHub 예제에서 확인됨

### ⚠️ 실제 테스트 필요

GitHub에서는 `cfgpath="log.*"` 예제만 확인되고, `firewall.policy`, `firewall.address` 등은 예제가 없습니다.

**권장 사항**:
1. 실제 Splunk에서 `index=fw type=event subtype=system cfgpath=*` 쿼리 실행
2. cfgpath 값 통계 확인:
   ```spl
   index=fw earliest=-7d type=event subtype=system cfgpath=*
   | stats count by cfgpath
   | sort -count
   ```
3. 실제 cfgpath 값에 따라 대시보드 쿼리 미세 조정

---

## 🎯 최종 결론

**v2 대시보드는 GitHub 검증 결과 구조적으로 정확함** ✅

- GitHub Wazuh 디코더: `type=event subtype=system logid=0100044546 cfgpath=*`
- Splunk 공식 파서: `type=event subtype=system`
- v2 대시보드: `type=event subtype=system (logid=0100044546 OR cfgpath=*)`

→ **완벽하게 일치**

**다음 단계**: 실제 Splunk 환경에서 테스트 쿼리 실행 및 결과 확인

---

**검증 날짜**: 2025-10-28
**검증 출처**: GitHub (wazuh-ruleset, splunk-connect-for-syslog)
**결과**: ✅ 구조적으로 정확함
**권장**: 실제 환경 테스트 필요
