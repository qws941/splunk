# 배포 옵션 요약 - 3가지 방법

**목적**: 로컬 테스트 및 에어갭 배포를 위한 모든 옵션 비교

**상황**: 알림 설정 버그 수정 완료 → 로컬에서 검증 → 에어갭 배포

---

## 🎯 Quick Decision Guide

```
사용 목적이 무엇인가요?

├─ 빠른 로컬 테스트 (5분)
│  → Option 1: Bash Script (QUICK-TEST.sh)
│
├─ 인프라 코드 관리 (GitOps)
│  → Option 2: Terraform (선언적)
│
└─ 전체 배포 자동화 (플러그인 + 설정)
   → Option 3: Ansible (절차적)
```

---

## Option 1: Bash Script (권장 - 로컬 테스트)

### ✅ 장점
- ✨ **가장 빠름** (1개 명령어로 완료)
- ✨ 외부 도구 불필요 (bash + curl만)
- ✨ 에러 처리 자동화
- ✨ 즉시 결과 확인 (40초 대기)

### ❌ 단점
- 재사용성 낮음 (로컬 환경만)
- 상태 관리 없음
- 롤백 수동

### 📋 사용 방법

```bash
# 1. HEC 토큰 설정 (Splunk Web UI에서 생성)
export SPLUNK_HEC_TOKEN="your-token-here"

# 2. 실행
./scripts/QUICK-TEST.sh

# 3. 결과 확인 (자동)
# ✅ Test data sent: 9 events
# ✅ Data indexed: 9 events
# ⏳ Alert executions: 3+ (expected: 3+)
```

### 📁 관련 파일
- `scripts/QUICK-TEST.sh` - 원클릭 자동화 스크립트
- `scripts/generate-alert-test-data.js` - 테스트 데이터 생성기
- `docs/LOCAL-ALERT-TEST-GUIDE.md` - 상세 가이드 (수동 단계)

---

## Option 2: Terraform (권장 - 운영 환경)

### ✅ 장점
- ✨ **선언적** (원하는 상태만 정의)
- ✨ 상태 관리 (terraform.tfstate)
- ✨ 변경 미리보기 (terraform plan)
- ✨ 롤백 쉬움 (terraform destroy)
- ✨ GitOps 워크플로우
- ✨ 여러 환경 관리 (dev/staging/prod)

### ❌ 단점
- Provider 설치 필요 (에어갭: 수동)
- HCL 문법 학습 필요
- 플러그인 설치 불가 (Splunk 리소스만)

### 📋 사용 방법

```bash
cd terraform

# 1. 변수 파일 생성
cp variables.tfvars.example terraform.tfvars
vim terraform.tfvars  # Splunk/Slack 정보 입력

# 2. 초기화
terraform init

# 3. 변경 사항 미리보기
terraform plan

# 4. 배포
terraform apply

# 5. HEC 토큰 확인
terraform output hec_token
```

### 📁 관련 파일
- `terraform/splunk-alerts.tf` - 메인 설정 (HEC + 3개 알림)
- `terraform/variables.tfvars.example` - 변수 템플릿
- `docs/AUTOMATION-DEPLOYMENT-GUIDE.md` - Terraform 상세 가이드

---

## Option 3: Ansible (권장 - 에어갭 환경)

### ✅ 장점
- ✨ **End-to-end 자동화** (플러그인 + HEC + 알림)
- ✨ 에어갭 지원 강력 (Provider 불필요)
- ✨ YAML 문법 (직관적)
- ✨ 복잡한 로직 지원 (조건문, 반복문)
- ✨ 기존 Ansible 인프라 활용

### ❌ 단점
- 절차적 (순서 중요)
- 상태 관리 없음 (멱등성은 보장)
- 변경 미리보기 제한적 (--check)

### 📋 사용 방법

```bash
cd ansible

# 1. 인벤토리 파일 생성
cp inventory.ini.example inventory.ini
vim inventory.ini  # Splunk 서버 정보 입력

# 2. 플러그인 파일 준비 (에어갭)
# /tmp/에 3개 플러그인 .tgz 파일 복사

# 3. Dry-run 테스트
ansible-playbook -i inventory.ini deploy-alerts.yml --check

# 4. 배포 실행
ansible-playbook -i inventory.ini deploy-alerts.yml

# 5. 검증 자동 실행 (3개 알림 확인)
```

### 📁 관련 파일
- `ansible/deploy-alerts.yml` - 메인 Playbook (6단계 배포)
- `ansible/inventory.ini.example` - 인벤토리 템플릿
- `docs/AUTOMATION-DEPLOYMENT-GUIDE.md` - Ansible 상세 가이드

---

## 📊 비교표

| 항목 | Bash Script | Terraform | Ansible |
|------|-------------|-----------|---------|
| **실행 시간** | ⚡ 5분 | ⏱️ 10분 | ⏱️ 15분 |
| **사전 준비** | HEC 토큰만 | terraform init | 플러그인 복사 |
| **학습 곡선** | ✅ 낮음 | ⚠️ 중간 (HCL) | ✅ 낮음 (YAML) |
| **에어갭 지원** | ✅ 완벽 | ⚠️ Provider 수동 | ✅ 완벽 |
| **상태 관리** | ❌ 없음 | ✅ tfstate | ❌ 없음 |
| **롤백** | ❌ 수동 | ✅ destroy | ⚠️ 수동 |
| **플러그인 설치** | ❌ 불가 | ❌ 불가 | ✅ 가능 |
| **HEC 생성** | ❌ 수동 | ✅ 자동 | ✅ 자동 |
| **알림 등록** | ❌ 수동 | ✅ 자동 | ✅ 자동 |
| **검증 자동화** | ✅ 6단계 | ⚠️ output만 | ✅ assert |
| **재사용성** | ❌ 로컬만 | ✅ 높음 | ✅ 높음 |
| **GitOps** | ❌ 불가 | ✅ 완벽 | ⚠️ 가능 |

---

## 🎯 사용 시나리오별 권장

### 시나리오 1: 로컬에서 빠른 테스트

**목적**: 수정된 알림이 작동하는지 5분 내 확인

**권장**: ✅ **Bash Script (QUICK-TEST.sh)**

**이유**:
- 1개 명령어로 완료
- HEC 토큰만 있으면 즉시 실행
- 자동 검증 (데이터 전송 → 인덱싱 → 알림 실행)

```bash
export SPLUNK_HEC_TOKEN="your-token"
./scripts/QUICK-TEST.sh
```

---

### 시나리오 2: 에어갭 환경 배포 (플러그인 포함)

**목적**: 인터넷 없는 환경에 처음부터 전체 배포

**권장**: ✅ **Ansible (deploy-alerts.yml)**

**이유**:
- 플러그인 3개 자동 설치
- HEC + 알림 + 인덱스 전부 생성
- USB로 파일만 전송하면 끝

```bash
# 1. USB에 준비
tar czf splunk-deployment.tar.gz ansible/ plugins/

# 2. 에어갭에서 배포
ansible-playbook -i inventory.ini deploy-alerts.yml
```

---

### 시나리오 3: 여러 환경 관리 (dev/staging/prod)

**목적**: 동일한 알림 설정을 3개 환경에 일관되게 배포

**권장**: ✅ **Terraform (splunk-alerts.tf)**

**이유**:
- Workspace로 환경 분리
- terraform.tfvars만 교체
- 변경 사항 추적 (terraform plan)

```bash
# Dev 환경
terraform workspace select dev
terraform apply -var-file=dev.tfvars

# Prod 환경
terraform workspace select prod
terraform apply -var-file=prod.tfvars
```

---

### 시나리오 4: GitOps 워크플로우 (CI/CD)

**목적**: Git push → 자동 배포 (GitHub Actions)

**권장**: ✅ **Terraform + Git**

**이유**:
- 코드로 인프라 관리
- Pull Request로 변경 검토
- terraform plan으로 diff 확인

```yaml
# .github/workflows/deploy.yml
- name: Terraform Apply
  run: terraform apply -auto-approve
```

---

### 시나리오 5: 복잡한 배포 로직 (조건문, 반복문)

**목적**: Splunk 버전에 따라 다른 설정 적용

**권장**: ✅ **Ansible (조건 분기)**

**이유**:
- Jinja2 템플릿으로 조건문
- when 절로 작업 선택
- 반복문으로 여러 서버 처리

```yaml
- name: Deploy alert
  when: splunk_version is version('9.0', '>=')
  ...
```

---

## 🔄 조합 사용 (Best Practice)

### 권장 조합: Terraform + Ansible

```
Terraform (Splunk 리소스 관리)
  ├─ HEC 토큰 생성
  ├─ 알림 등록
  └─ 인덱스 생성

Ansible (시스템 설정)
  ├─ 플러그인 설치
  ├─ Splunk 재시작
  └─ 검증 테스트
```

**실행 순서**:
```bash
# 1. Ansible로 플러그인 설치
ansible-playbook -i inventory.ini deploy-alerts.yml --tags plugins

# 2. Terraform으로 리소스 생성
cd terraform && terraform apply

# 3. Ansible로 검증
ansible-playbook -i inventory.ini deploy-alerts.yml --tags verify
```

---

## 📁 파일 구조 요약

```
/home/jclee/app/splunk/
├── scripts/
│   ├── QUICK-TEST.sh                    # Bash 자동화 (로컬 테스트)
│   ├── generate-alert-test-data.js      # 테스트 데이터 생성
│   └── diagnose-alerts-not-working.sh   # 진단 스크립트
│
├── terraform/
│   ├── splunk-alerts.tf                 # Terraform 메인 설정
│   └── variables.tfvars.example         # 변수 템플릿
│
├── ansible/
│   ├── deploy-alerts.yml                # Ansible Playbook
│   └── inventory.ini.example            # 인벤토리 템플릿
│
├── docs/
│   ├── LOCAL-ALERT-TEST-GUIDE.md        # 로컬 테스트 가이드 (수동)
│   ├── AUTOMATION-DEPLOYMENT-GUIDE.md   # Terraform/Ansible 가이드
│   ├── DEPLOYMENT-OPTIONS-SUMMARY.md    # 이 문서
│   └── ALERT-BUG-FIXED.md               # 버그 수정 내역
│
└── configs/
    └── savedsearches-fortigate-alerts.conf  # 수정된 알림 설정
```

---

## ✅ 다음 단계 체크리스트

### 로컬 테스트 (현재)

- [ ] HEC 토큰 생성 (Splunk Web UI)
- [ ] Option 선택:
  - [ ] **Bash**: `./scripts/QUICK-TEST.sh`
  - [ ] **Terraform**: `cd terraform && terraform apply`
  - [ ] **Ansible**: `ansible-playbook -i inventory.ini deploy-alerts.yml`
- [ ] 알림 작동 확인 (Slack 또는 Splunk 로그)
- [ ] 문제 발생 시: `./scripts/diagnose-alerts-not-working.sh`

### 에어갭 배포 (다음)

- [ ] 파일 준비 (USB)
  - [ ] 플러그인 3개 (.tgz)
  - [ ] Ansible playbook 또는 Terraform 설정
  - [ ] 수정된 savedsearches-fortigate-alerts.conf
- [ ] USB 전송
- [ ] 에어갭에서 배포 실행
- [ ] 검증 스크립트 실행

---

**작성일**: 2025-10-30
**버그 수정**: ✅ 완료 (공백 추가)
**테스트 도구**: ✅ 3가지 옵션 준비 완료
**다음 단계**: 사용자가 Option 선택 후 로컬 테스트 실행
