# 🔄 GitHub Default Branch 변경 가이드

## 1. GitHub 웹사이트에서 Default Branch 변경

### 단계별 진행
1. **GitHub Repository 접속**
   - URL: https://github.com/qws941/splunk

2. **Settings 탭 이동**
   - Repository 페이지에서 **Settings** 클릭

3. **Branches 섹션 접속**
   - 왼쪽 메뉴에서 **Branches** 클릭

4. **Default Branch 변경**
   - "Default branch" 섹션에서 연필 아이콘 클릭
   - 드롭다운에서 **master** 선택
   - **Update** 클릭
   - 확인 대화상자에서 **I understand, update the default branch** 클릭

## 2. 변경 확인 방법

### Repository 기본 브랜치 확인
- Repository 메인 페이지에서 브랜치 드롭다운이 **master** 를 가리키는지 확인

### Git clone 테스트
```bash
# 새로운 클론 시 master 브랜치가 기본으로 체크아웃되는지 확인
git clone https://github.com/qws941/splunk.git test-clone
cd test-clone
git branch  # master 브랜치여야 함
```

## 3. GitHub Actions 워크플로우 업데이트

### .github/workflows/deploy.yml 수정 필요
```yaml
# 기존 main 브랜치 트리거를 master로 변경
on:
  push:
    branches: [master]  # main → master로 변경
  pull_request:
    branches: [master]  # main → master로 변경
```

## 4. 변경 완료 후 할 일

1. **main 브랜치 삭제** (로컬 및 원격)
2. **모든 팀원에게 알림**
3. **CI/CD 설정 업데이트**
4. **문서 업데이트**

## ⚠️ 주의사항

- Default branch 변경 후에는 모든 새로운 Pull Request가 master로 향함
- 기존 main 브랜치를 참조하는 모든 스크립트/설정 업데이트 필요
- 팀원들은 로컬 repository를 다시 설정해야 할 수 있음

## 🔗 참고 링크

- [GitHub Default Branch 변경 공식 문서](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/changing-the-default-branch)
- [Repository Settings](https://github.com/qws941/splunk/settings/branches)