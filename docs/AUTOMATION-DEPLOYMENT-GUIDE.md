# 자동화 배포 가이드 (Terraform & Ansible)

**목적**: Terraform 또는 Ansible을 사용한 FortiGate 알림 자동 배포

**소요 시간**: 10-15분

---

## 🚀 Quick Start

### Option 1: Terraform (선언적 인프라)

```bash
cd /home/jclee/app/splunk/terraform

# 1. 변수 파일 생성
cp variables.tfvars.example terraform.tfvars
vim terraform.tfvars  # Splunk/Slack 정보 입력

# 2. Terraform 초기화
terraform init

# 3. 배포 계획 확인
terraform plan

# 4. 배포 실행
terraform apply

# 5. HEC 토큰 확인
terraform output hec_token
```

### Option 2: Ansible (절차적 자동화)

```bash
cd /home/jclee/app/splunk/ansible

# 1. 인벤토리 파일 생성
cp inventory.ini.example inventory.ini
vim inventory.ini  # Splunk 서버 정보 입력

# 2. 플러그인 파일 준비 (에어갭 환경)
# /tmp/에 3개 플러그인 .tgz 파일 복사
ls -lh /tmp/*tgz
# slack-notification-alert_2.3.2.tgz
# fortinet-fortigate-add-on-for-splunk_1.6.9.tgz
# splunk-common-information-model-cim_6.2.0.tgz

# 3. Dry-run 테스트
ansible-playbook -i inventory.ini deploy-alerts.yml --check

# 4. 실제 배포
ansible-playbook -i inventory.ini deploy-alerts.yml

# 5. 특정 작업만 실행 (예: 알림만 배포)
ansible-playbook -i inventory.ini deploy-alerts.yml --tags alerts
```

---

## 📋 Terraform 상세 가이드

### 1. Provider 설치

```bash
# Splunk Terraform Provider 자동 다운로드
terraform init

# Provider 버전 확인
terraform providers
```

### 2. 변수 설정 (terraform.tfvars)

```hcl
# Splunk 설정
splunk_url      = "https://localhost:8089"
splunk_username = "admin"
splunk_password = "changeme"
insecure_ssl    = true  # 로컬 테스트용 (운영 환경: false)

# Slack 설정
slack_webhook_url = "https://hooks.slack.com/services/T00/B00/xxx"
slack_channel     = "#security-firewall-alert"
```

### 3. 배포 실행

```bash
# 배포 계획 확인 (변경 사항 미리보기)
terraform plan

# 배포 실행
terraform apply

# 자동 승인 (스크립트 자동화 시)
terraform apply -auto-approve

# 특정 리소스만 배포
terraform apply -target=splunk_inputs_http_event_collector.fortigate_hec
```

### 4. 생성된 리소스 확인

```bash
# HEC 토큰 확인
terraform output hec_token

# 알림 이름 확인
terraform output alert_names

# 모든 출력 확인
terraform output
```

### 5. 변경 사항 적용

```bash
# 코드 수정 후 다시 apply
vim splunk-alerts.tf
terraform apply

# 변경 사항만 표시
terraform plan
```

### 6. 리소스 삭제

```bash
# 모든 리소스 삭제 (주의!)
terraform destroy

# 특정 리소스만 삭제
terraform destroy -target=splunk_saved_searches.config_change_alert
```

---

## 📋 Ansible 상세 가이드

### 1. 사전 준비 (에어갭 환경)

```bash
# 플러그인 파일을 Splunk 서버 /tmp/에 복사
scp plugins/*.tgz root@splunk-server:/tmp/

# 또는 USB로 전송
# 1. USB 마운트: mount /dev/sdb1 /mnt/usb
# 2. 파일 복사: cp /mnt/usb/*.tgz /tmp/
# 3. 권한 설정: chmod 644 /tmp/*.tgz
```

### 2. 인벤토리 설정 (inventory.ini)

```ini
# 로컬 Splunk (현재 시스템)
[splunk_servers]
localhost ansible_connection=local ansible_host=localhost

# 원격 Splunk 서버
[splunk_servers]
splunk.example.com ansible_host=192.168.1.100 ansible_user=root

# 여러 Splunk 서버 (분산 환경)
[splunk_servers]
splunk1.example.com ansible_host=192.168.1.101
splunk2.example.com ansible_host=192.168.1.102

[splunk_servers:vars]
splunk_home=/opt/splunk
splunk_password=changeme
```

### 3. Playbook 실행 옵션

```bash
# 전체 배포
ansible-playbook -i inventory.ini deploy-alerts.yml

# 구문 검사만 (실제 실행 안 함)
ansible-playbook -i inventory.ini deploy-alerts.yml --syntax-check

# Dry-run (변경 사항 미리보기)
ansible-playbook -i inventory.ini deploy-alerts.yml --check

# 상세 로그 출력
ansible-playbook -i inventory.ini deploy-alerts.yml -v   # 기본
ansible-playbook -i inventory.ini deploy-alerts.yml -vv  # 상세
ansible-playbook -i inventory.ini deploy-alerts.yml -vvv # 매우 상세

# 특정 단계부터 시작
ansible-playbook -i inventory.ini deploy-alerts.yml --start-at-task="Deploy Config Change Alert"

# 특정 호스트에만 실행
ansible-playbook -i inventory.ini deploy-alerts.yml --limit splunk1.example.com
```

### 4. Playbook 커스터마이징

#### 변수 재정의

```bash
# 명령줄에서 변수 재정의
ansible-playbook -i inventory.ini deploy-alerts.yml \
  -e "slack_channel=#test-alerts" \
  -e "fortigate_index=fw"
```

#### 작업 건너뛰기 (태그 사용)

```yaml
# deploy-alerts.yml 수정 (태그 추가)
tasks:
  - name: Install Slack plugin
    tags: plugins
    ...

  - name: Deploy Config Change Alert
    tags: alerts
    ...
```

```bash
# 플러그인 설치만 실행
ansible-playbook -i inventory.ini deploy-alerts.yml --tags plugins

# 알림 배포만 실행
ansible-playbook -i inventory.ini deploy-alerts.yml --tags alerts

# 특정 태그 제외
ansible-playbook -i inventory.ini deploy-alerts.yml --skip-tags plugins
```

### 5. 검증 및 테스트

```bash
# Playbook 실행 후 자동 검증
# - 플러그인 설치 확인
# - HEC 토큰 생성 확인
# - 알림 등록 확인 (3개)

# 수동 검증
ansible splunk_servers -i inventory.ini -m shell -a "ls -l /opt/splunk/etc/apps/slack_alerts"
ansible splunk_servers -i inventory.ini -m shell -a "/opt/splunk/bin/splunk list saved-search -auth admin:changeme | grep FortiGate"
```

---

## 🔧 Troubleshooting

### Terraform 문제

**문제 1: Provider 다운로드 실패 (에어갭)**
```bash
# 에러: Failed to install provider
# 해결: 수동 Provider 설치

# 1. 인터넷 연결된 시스템에서 Provider 다운로드
terraform providers mirror /tmp/terraform-providers

# 2. 에어갭 시스템에 복사
# 3. Provider 경로 지정
terraform init -plugin-dir=/tmp/terraform-providers
```

**문제 2: 인증 실패**
```bash
# 에러: 401 Unauthorized
# 해결: 변수 확인
terraform console
> var.splunk_username
> var.splunk_password

# 직접 지정
terraform apply -var="splunk_password=your_password"
```

**문제 3: 리소스 이미 존재**
```bash
# 에러: Resource already exists
# 해결: Import 기존 리소스
terraform import splunk_saved_searches.config_change_alert FortiGate_Config_Change_Alert
```

### Ansible 문제

**문제 1: 플러그인 파일 없음**
```bash
# 에러: No such file or directory: /tmp/slack-notification-alert_2.3.2.tgz
# 해결: 파일 확인
ansible splunk_servers -i inventory.ini -m shell -a "ls -lh /tmp/*.tgz"

# 파일 복사 (Playbook에 추가)
- name: Copy plugins to target
  copy:
    src: "../plugins/{{ item }}"
    dest: "/tmp/{{ item }}"
  with_items:
    - slack-notification-alert_2.3.2.tgz
    - fortinet-fortigate-add-on-for-splunk_1.6.9.tgz
```

**문제 2: Splunk 재시작 시간 초과**
```bash
# 에러: Timeout waiting for Splunk restart
# 해결: async/poll 조정 (playbook handlers 섹션)
handlers:
  - name: restart splunk
    command: "{{ splunk_home }}/bin/splunk restart"
    async: 120  # 60초 → 120초로 증가
    poll: 5
```

**문제 3: REST API 실패**
```bash
# 에러: 409 Conflict (리소스 이미 존재)
# 해결: status_code에 409 추가 (이미 추가됨)
status_code: [200, 201, 409]  # 409 = 이미 존재 (정상)
```

**문제 4: Slack Webhook 테스트**
```bash
# Ansible에서 Slack 연결 테스트
- name: Test Slack webhook
  uri:
    url: "{{ slack_webhook_url }}"
    method: POST
    body_format: json
    body:
      text: "✅ Ansible deployment test"
    status_code: 200
```

---

## 📊 비교표: Terraform vs Ansible

| 기능 | Terraform | Ansible |
|------|-----------|---------|
| **방식** | 선언적 (Declarative) | 절차적 (Procedural) |
| **상태 관리** | terraform.tfstate 파일 | 없음 (idempotent tasks) |
| **변경 감지** | terraform plan (diff) | --check (dry-run) |
| **롤백** | terraform destroy | 수동 (playbook 역순 실행) |
| **학습 곡선** | 중간 (HCL 문법) | 낮음 (YAML) |
| **에어갭 지원** | Provider 수동 설치 필요 | 기본 지원 (Python만 필요) |
| **멱등성** | 자동 (상태 기반) | 수동 (tasks에 명시) |
| **복잡한 로직** | 제한적 (for_each, count) | 강력 (Jinja2 템플릿) |
| **재사용성** | 모듈화 쉬움 | Role/Collections |

### 권장 사용 시나리오

**Terraform 사용 시**:
- ✅ Splunk 리소스만 관리 (HEC, 알림, 인덱스)
- ✅ 변경 사항 추적 중요 (terraform.tfstate)
- ✅ 여러 환경 동일 구성 (dev/staging/prod)
- ✅ GitOps 워크플로우

**Ansible 사용 시**:
- ✅ 플러그인 설치 + 설정 (end-to-end)
- ✅ 에어갭 환경 (Provider 없음)
- ✅ 복잡한 배포 로직 (조건, 반복문)
- ✅ 기존 Ansible 인프라 활용

**둘 다 사용** (권장):
- Terraform: Splunk 리소스 관리
- Ansible: 플러그인 설치 + 시스템 설정

---

## 🎯 에어갭 환경 배포 절차

### 1. 파일 준비 (인터넷 연결 시스템)

```bash
cd /home/jclee/app/splunk

# Terraform Provider (Terraform 사용 시)
terraform providers mirror /tmp/terraform-providers
tar czf terraform-providers.tar.gz /tmp/terraform-providers

# Ansible Playbook + 플러그인
tar czf splunk-deployment.tar.gz \
  ansible/ \
  terraform/ \
  plugins/*.tgz \
  configs/savedsearches-fortigate-alerts.conf \
  scripts/QUICK-TEST.sh \
  scripts/generate-alert-test-data.js
```

### 2. 파일 전송 (USB)

```bash
# USB 마운트
mount /dev/sdb1 /mnt/usb

# 파일 복사
cp splunk-deployment.tar.gz /mnt/usb/
cp terraform-providers.tar.gz /mnt/usb/  # Terraform 사용 시

# 언마운트
umount /mnt/usb
```

### 3. 에어갭 시스템에서 배포

```bash
# USB 마운트
mount /dev/sdb1 /mnt/usb

# 파일 복사
cd /home/jclee/app/splunk
tar xzf /mnt/usb/splunk-deployment.tar.gz

# Terraform 배포
cd terraform
tar xzf /mnt/usb/terraform-providers.tar.gz -C /
terraform init -plugin-dir=/tmp/terraform-providers
terraform apply -auto-approve

# 또는 Ansible 배포
cd ansible
ansible-playbook -i inventory.ini deploy-alerts.yml
```

---

## ✅ 검증 체크리스트

### Terraform 배포 검증

```bash
# 1. 상태 확인
terraform show

# 2. HEC 토큰 생성 확인
terraform output hec_token
# Expected: 36자 UUID 형식

# 3. 알림 등록 확인
terraform output alert_names
# Expected: [FortiGate_Config_Change_Alert, FortiGate_Critical_Event_Alert, FortiGate_HA_Event_Alert]

# 4. Splunk에서 직접 확인
curl -k -u admin:changeme \
  "https://localhost:8089/servicesNS/nobody/search/saved/searches" | \
  grep "FortiGate_"
```

### Ansible 배포 검증

```bash
# 1. Playbook 실행 로그 확인
# 마지막 PLAY RECAP에서:
# - changed=0: 모든 리소스 이미 존재 (정상)
# - failed=0: 실패한 작업 없음
# - ok=20+: 성공한 작업 수

# 2. 플러그인 설치 확인
ls -ld /opt/splunk/etc/apps/slack_alerts
ls -ld /opt/splunk/etc/apps/TA-fortinet-fortigate

# 3. 알림 확인
/opt/splunk/bin/splunk list saved-search -auth admin:changeme | grep FortiGate

# 4. HEC 엔드포인트 확인
curl -k https://localhost:8088/services/collector/health
# Expected: {"text":"HEC is healthy","code":200}
```

---

**작성일**: 2025-10-30
**대상**: 로컬 테스트 + 에어갭 환경
**관련 문서**: LOCAL-ALERT-TEST-GUIDE.md, ALERT-BUG-FIXED.md
