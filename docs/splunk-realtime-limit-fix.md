# Real-time Search Limit 늘리기 (임시 해결책)

## ⚠️ 주의사항
- 이건 **임시 방편**입니다
- 근본 원인(불필요한 검색)을 해결하는 게 우선!
- 리소스 부족하면 Splunk 전체가 느려질 수 있음

## 🔧 설정 방법

### 1. limits.conf 파일 수정

**파일 위치**:
```
/opt/splunk/etc/system/local/limits.conf
```

### 2. 다음 내용 추가

```ini
[realtime]
# 기본값: max_searches_per_cpu = 1 (CPU 70개면 70개 제한)
# 변경: max_searches_per_cpu = 2 (CPU 70개면 140개 허용)
max_searches_per_cpu = 2

# 또는 절대 숫자로 지정
max_searches = 140
```

### 3. Splunk 재시작

```bash
/opt/splunk/bin/splunk restart
```

## ✅ 효과

- Real-time 검색 한계: 70 → 140
- 경고 사라짐
- **하지만 CPU/메모리 더 쓰게 됨!**

## 🎯 권장 해결책 (근본 치료)

1. **Real-time → Scheduled 전환**
   - 5분마다 실행으로 바꿔도 대부분 OK

2. **불필요한 검색 비활성화**
   - 66,763번 스킵 = 죽은 검색

3. **검색 통합**
   - 비슷한 검색 여러 개 → 1개로 합치기

## 📊 현재 상황

```
현재: 70/70 Real-time 검색 (포화)
목표: 30-40개 이하 (여유 있게)
```

---

**급하면 limits.conf 수정 → Splunk 재시작**
**근본 해결하려면 → 불필요한 검색 계속 비활성화**
