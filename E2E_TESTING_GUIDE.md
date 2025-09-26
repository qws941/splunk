# 🧪 E2E Testing Guide - Playwright

## 📋 개요

이 프로젝트는 **Playwright**를 사용한 포괄적인 End-to-End (E2E) 테스트를 제공합니다. Fortinet 정책 확인 시스템의 모든 기능을 자동으로 테스트하고 검증합니다.

## 🎯 테스트 범위

### 1. **기능 테스트** (`fortinet-policy-verification.spec.js`)
- ✅ 메인 페이지 로드 및 요소 검증
- ✅ GitHub 저장소 링크 기능
- ✅ 시스템 구성 정보 표시
- ✅ 로컬 설정 가이드 확인
- ✅ API 사용 예시 표시
- ✅ 시스템 상태 정보
- ✅ 모바일 반응형 디자인
- ✅ 보안 헤더 및 메타 태그
- ✅ CSS 스타일링 검증
- ✅ 네비게이션 및 스크롤 동작

### 2. **API 테스트** (`fortinet-policy-verification.spec.js`)
- ✅ `/health` 엔드포인트 상태 확인
- ✅ `/api/test` API 정보 엔드포인트
- ✅ 루트 경로 (`/`) HTML 응답
- ✅ `/index.html` 경로 동작
- ✅ 404 오류 처리

### 3. **시각적 회귀 테스트** (`visual-regression.spec.js`)
- 📸 데스크톱 뷰포트 스크린샷
- 📸 모바일 뷰포트 스크린샷
- 📸 태블릿 뷰포트 스크린샷
- 📸 개별 섹션 스크린샷
- 📸 다크 모드 호환성
- 📸 인쇄 미디어 테스트
- 📸 호버 상태 테스트
- 📸 고대비 접근성 테스트
- 📸 컴포넌트 수준 시각적 테스트

### 4. **크로스 브라우저 호환성**
- 🌐 Chromium (Chrome/Edge)
- 🌐 Firefox
- 🌐 WebKit (Safari)
- 📱 Mobile Chrome (Pixel 5)
- 📱 Mobile Safari (iPhone 12)

### 5. **성능 및 접근성 테스트**
- ⚡ 페이지 로딩 시간 측정
- ♿ 접근성 요소 검증
- ⌨️ 키보드 네비게이션 테스트

## 🚀 테스트 실행 방법

### 로컬 환경에서 실행

```bash
# 전체 E2E 테스트 실행
npm run test:e2e

# 특정 브라우저에서 실행
npm run test:e2e -- --project=chromium
npm run test:e2e -- --project=firefox
npm run test:e2e -- --project=webkit

# 시각적 모드로 실행 (브라우저 창 표시)
npm run test:e2e:headed

# 디버그 모드로 실행
npm run test:e2e:debug

# UI 모드로 실행 (인터랙티브)
npm run test:e2e:ui

# 테스트 리포트 보기
npm run test:e2e:report
```

### 특정 테스트 실행

```bash
# 특정 테스트 파일 실행
npm run test:e2e tests/e2e/fortinet-policy-verification.spec.js

# 특정 테스트 케이스 실행 (grep 패턴)
npm run test:e2e -- -g "should load main page"

# API 테스트만 실행
npm run test:e2e -- -g "API Endpoints"

# 시각적 테스트만 실행
npm run test:e2e tests/e2e/visual-regression.spec.js

# 시각적 스크린샷 업데이트
npm run test:e2e tests/e2e/visual-regression.spec.js --update-snapshots
```

## 🔧 GitHub Actions 통합

### 자동 실행 트리거
- ✅ `main`, `develop` 브랜치 push
- ✅ Pull Request 생성
- ✅ 수동 워크플로우 실행
- ✅ 매일 자동 실행 (오전 2시 UTC)

### 워크플로우 구성
1. **기본 E2E 테스트** (`.github/workflows/e2e-tests.yml`)
2. **시각적 회귀 테스트**
3. **크로스 브라우저 테스트** (Matrix Strategy)
4. **성능 테스트**
5. **테스트 결과 요약**

### 배포 통합
- ✅ 배포 워크플로우에 중요 E2E 테스트 포함
- ✅ 배포 후 자동 검증
- ✅ 실패 시 배포 중단

## 📊 테스트 결과 및 아티팩트

### 생성되는 아티팩트
- 📄 **HTML 테스트 리포트**: 상세한 테스트 결과
- 📸 **스크린샷**: 실패한 테스트의 스크린샷
- 🎬 **비디오**: 실패한 테스트의 동작 영상
- 🔍 **트레이스**: 디버깅용 상세 실행 로그
- 📈 **성능 메트릭**: 페이지 로딩 시간 등

### GitHub Actions에서 결과 확인
1. **Actions** 탭 → **E2E Tests with Playwright** 워크플로우 선택
2. **Artifacts** 섹션에서 다운로드:
   - `playwright-report`: HTML 테스트 리포트
   - `playwright-screenshots`: 스크린샷 모음
   - `visual-regression-results`: 시각적 테스트 결과

## 🐛 문제 해결

### 일반적인 오류

1. **브라우저 설치 오류**
   ```bash
   npx playwright install --with-deps
   ```

2. **시각적 테스트 실패 (스크린샷 차이)**
   ```bash
   # 기준 스크린샷 업데이트
   npm run test:e2e tests/e2e/visual-regression.spec.js --update-snapshots
   ```

3. **네트워크 타임아웃**
   - `playwright.config.js`에서 `timeout` 값 조정
   - 테스트에서 `waitForLoadState('networkidle')` 사용

4. **CI 환경에서 실패**
   - 시스템 의존성 확인: `npx playwright install-deps`
   - 헤드리스 모드 확인

### 로그 및 디버깅

```bash
# 상세 로그와 함께 실행
DEBUG=pw:api npm run test:e2e

# 특정 테스트 디버그
npm run test:e2e:debug -- -g "specific test name"

# 트레이스 뷰어로 실패 분석
npx playwright show-trace test-results/path-to-trace.zip
```

## 📈 성능 기준

### 기대되는 성능 메트릭
- ✅ 페이지 로딩 시간: < 3초
- ✅ API 응답 시간: < 1초
- ✅ 시각적 완성도: 100% 픽셀 일치

### 접근성 기준
- ✅ 키보드 네비게이션 지원
- ✅ 적절한 헤딩 구조 (h1, h3)
- ✅ 대체 텍스트 (alt 속성)
- ✅ 고대비 모드 지원

## 🔄 지속적인 개선

### 테스트 추가 가이드라인
1. **새로운 기능 개발 시**: 해당 기능의 E2E 테스트 추가
2. **UI 변경 시**: 시각적 회귀 테스트 기준 스크린샷 업데이트
3. **API 변경 시**: API 테스트 케이스 업데이트
4. **버그 수정 시**: 재현 가능한 테스트 케이스 추가

### 모니터링
- 📊 매일 자동 실행으로 지속적 품질 확인
- 🚨 실패 시 GitHub Issues 자동 생성 (설정 필요)
- 📈 테스트 실행 시간 및 성공률 모니터링

---

## 🎯 테스트 커버리지

현재 E2E 테스트가 다음 기능들을 포괄적으로 검증합니다:

- **✅ 웹 인터페이스**: 완전한 UI/UX 테스트
- **✅ API 엔드포인트**: 모든 REST API 검증
- **✅ 반응형 디자인**: 다양한 디바이스 지원
- **✅ 크로스 브라우저**: 주요 브라우저 호환성
- **✅ 접근성**: WCAG 가이드라인 준수
- **✅ 성능**: 로딩 시간 및 반응성
- **✅ 시각적 일관성**: 픽셀 단위 정확도

**🛡️ 프로덕션 준비 완료: Fortinet 정책 확인 시스템이 모든 테스트를 통과했습니다!**