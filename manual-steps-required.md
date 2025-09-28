# ⚠️ 수동 설정 필요: GitHub Default Branch 변경

## 🔧 GitHub 웹사이트에서 수행할 작업

GitHub Repository에서 Default Branch를 **main**에서 **master**로 변경해야 합니다.

### 1. GitHub 설정 변경
1. **Repository 접속**: https://github.com/qws941/splunk
2. **Settings** → **Branches** 이동
3. **Default branch** 섹션에서 연필 아이콘 클릭
4. **master** 브랜치 선택
5. **Update** 클릭 및 확인

### 2. 변경 완료 후 실행할 명령어

GitHub에서 default branch 변경 완료 후 아래 명령어 실행:

```bash
# main 브랜치 삭제 (로컬)
git branch -d main

# main 브랜치 삭제 (원격)
git push origin --delete main

# 로컬 master 브랜치가 origin/master를 추적하는지 확인
git branch -vv

# 성공 확인
git branch -a
```

## ✅ 현재 완료된 작업

- ✅ master 브랜치 생성 및 푸시 완료
- ✅ GitHub Actions 워크플로우 master 브랜치로 업데이트
- ✅ 모든 코드 및 설정이 master 브랜치에 준비됨

## 🎯 결과 확인

변경 완료 후 다음을 확인하세요:

1. **Repository 메인 페이지**에서 기본 브랜치가 **master**인지 확인
2. **새로운 clone 시 master 브랜치가 체크아웃**되는지 확인
3. **GitHub Actions가 master 브랜치 push 시 트리거**되는지 확인

## 📋 체크리스트

- [ ] GitHub에서 Default branch를 master로 변경
- [ ] `git branch -d main` 실행
- [ ] `git push origin --delete main` 실행
- [ ] 새로운 clone 테스트
- [ ] GitHub Actions 동작 확인

## 🚨 주의사항

**반드시 GitHub 웹사이트에서 Default branch 변경을 먼저 수행한 후** main 브랜치를 삭제하세요. 순서를 바꾸면 Repository 접근에 문제가 발생할 수 있습니다.