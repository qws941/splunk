# Web UI에서 Slack 알림 테스트 (CLI 없음)

## 1단계: 데이터 확인 (30초)

### Splunk Web → Search & Reporting

```spl
index=fortianalyzer sourcetype=fw_log | head 10
```

**Enter 실행**

- 결과 있음 ✅ → 다음 단계
- 결과 없음 ❌ → FortiAnalyzer UDP 5140 확인 필요

---

## 2단계: Slack 테스트 (30초)

### 같은 검색창에 입력:

```spl
| makeresults | eval message="테스트" | sendalert slack param.channel="#splunk-alerts" param.message=message
```

**Enter 실행**

→ **Slack 채널 확인!** 메시지 왔으면 ✅ 성공

---

## 3단계: 알림 수동 실행 (1분)

### Settings → Searches, reports, and alerts

1. `FAZ_Critical_Alerts` 찾기
2. **▶️ Run** 클릭 (우측)
3. 실행 완료 기다리기
4. **Slack 채널 확인**

→ 메시지 왔으면 ✅ 알림 작동!

---

## 4단계: 알림 자동 실행 켜기 (10초)

### 같은 화면에서:

1. `FAZ_Critical_Alerts` → **Edit**
2. **Enable** 체크박스 ✅
3. **Save**

→ 이제 5분마다 자동 실행됨

---

## 5단계: 발송 내역 확인 (30초)

### Search & Reporting 검색창:

```spl
index=_audit action="alert_fired" | head 10
```

**Enter 실행**

→ 발송 내역 보이면 ✅ 정상 작동

---

## 끝!

**전체 5분 소요**
- 데이터 확인 30초
- Slack 테스트 30초  
- 수동 실행 1분
- 자동 켜기 10초
- 내역 확인 30초

**이제 알림이 자동으로 Slack에 갑니다!**
