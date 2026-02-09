#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Splunk Feature Checker & Automation Framework
모든 Splunk 기능 점검 + 저장화 설정 + 자동화 기법 적용
"""

import functools
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Splunk alert protocol reserves stdout; redirect print to stderr
print = functools.partial(print, file=sys.stderr)  # noqa: A001


class SplunkFeatureChecker:
    """Splunk 전체 기능 점검 및 자동화"""

    def __init__(self, splunk_home="/opt/splunk"):
        self.splunk_home = Path(splunk_home)
        self.splunk_bin = self.splunk_home / "bin" / "splunk"
        self.app_dir = self.splunk_home / "etc" / "apps" / "security_alert"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "storage": {},
            "automation": {},
            "recommendations": [],
        }

    def check_all_features(self):
        """전체 Splunk 기능 점검"""
        print("=" * 80)
        print("🔍 Splunk Feature Checker & Automation Framework")
        print("=" * 80)
        print("")

        # 1. 기본 시스템 점검
        self.check_system_info()

        # 2. 저장화 설정 점검 (Storage/Persistence)
        self.check_storage_configuration()

        # 3. 인덱스 설정 점검
        self.check_indexes()

        # 4. 데이터 입력 점검
        self.check_inputs()

        # 5. 알림 시스템 점검
        self.check_alert_system()

        # 6. 룩업 테이블 점검
        self.check_lookups()

        # 7. KV Store 점검 (저장화)
        self.check_kvstore()

        # 8. 요약 인덱싱 점검 (Summary Indexing)
        self.check_summary_indexing()

        # 9. 데이터 모델 가속화 점검
        self.check_data_model_acceleration()

        # 10. 검색 헤드 클러스터링 점검
        self.check_shc_status()

        # 11. 인덱서 클러스터링 점검
        self.check_indexer_clustering()

        # 12. 포워딩 설정 점검
        self.check_forwarding()

        # 13. 자동화 기법 적용 제안
        self.suggest_automation()

        # 결과 출력 및 저장
        self.print_results()
        self.save_results()

        return self.results

    def check_system_info(self):
        """시스템 기본 정보 점검"""
        print("📊 [1/13] 시스템 정보 점검")
        print("-" * 80)

        checks = {}

        # Splunk 버전
        try:
            version_output = self.run_splunk_command("version")
            checks["splunk_version"] = {"status": "OK", "value": version_output.strip()}
            print(f"   ✅ Splunk 버전: {version_output.strip()}")
        except Exception as e:
            checks["splunk_version"] = {"status": "ERROR", "error": str(e)}
            print(f"   ❌ Splunk 버전 확인 실패: {e}")

        # Splunk 상태
        try:
            status_output = self.run_splunk_command("status")
            is_running = "running" in status_output.lower()
            checks["splunk_status"] = {
                "status": "OK" if is_running else "WARNING",
                "running": is_running,
            }
            print(
                f"   {'✅' if is_running else '⚠️'} Splunk 상태: {'실행 중' if is_running else '중지됨'}"
            )
        except Exception as e:
            checks["splunk_status"] = {"status": "ERROR", "error": str(e)}
            print(f"   ❌ Splunk 상태 확인 실패: {e}")

        # 라이선스 정보
        try:
            self.run_splunk_command("list license")
            checks["license"] = {"status": "OK", "info": "License configured"}
            print("   ✅ 라이선스: 설정됨")
        except Exception as e:
            checks["license"] = {"status": "WARNING", "error": str(e)}
            print("   ⚠️ 라이선스 확인 실패 (Free 버전일 수 있음)")

        self.results["checks"]["system"] = checks
        print("")

    def check_storage_configuration(self):
        """저장화 설정 점검 (Storage/Persistence)"""
        print("💾 [2/13] 저장화 설정 점검 (Storage/Persistence)")
        print("-" * 80)

        storage = {}

        # 1. 인덱스 저장소 경로
        indexes_conf = self.splunk_home / "etc" / "system" / "local" / "indexes.con"
        if indexes_conf.exists():
            storage["indexes_conf"] = {
                "status": "OK",
                "path": str(indexes_conf),
                "exists": True,
            }
            print(f"   ✅ indexes.conf 존재: {indexes_conf}")

            # 저장 경로 확인
            with open(indexes_conf, "r") as f:
                content = f.read()
                if "homePath" in content:
                    storage["custom_homePath"] = True
                    print("   ✅ 커스텀 homePath 설정됨")
                if "coldPath" in content:
                    storage["custom_coldPath"] = True
                    print("   ✅ 커스텀 coldPath 설정됨 (콜드 데이터 분리)")
        else:
            storage["indexes_conf"] = {"status": "WARNING", "exists": False}
            print("   ⚠️ indexes.conf 없음 (기본 설정 사용)")

        # 2. 디스크 사용량 점검
        try:
            db_path = self.splunk_home / "var" / "lib" / "splunk"
            if db_path.exists():
                disk_usage = subprocess.check_output(
                    ["du", "-sh", str(db_path)], encoding="utf-8"
                )
                storage["disk_usage"] = {"status": "OK", "size": disk_usage.split()[0]}
                print(f"   ✅ 인덱스 디스크 사용량: {disk_usage.split()[0]}")
        except Exception as e:
            storage["disk_usage"] = {"status": "ERROR", "error": str(e)}
            print(f"   ❌ 디스크 사용량 확인 실패: {e}")

        # 3. Frozen 데이터 경로 (장기 보관)
        frozen_path = self.splunk_home / "var" / "lib" / "splunk" / "frozen"
        storage["frozen_archive"] = {
            "status": "OK" if frozen_path.exists() else "INFO",
            "exists": frozen_path.exists(),
            "path": str(frozen_path),
        }
        if frozen_path.exists():
            print(f"   ✅ Frozen 아카이브 설정됨: {frozen_path}")
        else:
            print("   ℹ️ Frozen 아카이브 미설정 (오래된 데이터 자동 삭제)")

        # 4. SmartStore 설정 (S3/Azure 통합)
        smartstore_conf = self.splunk_home / "etc" / "system" / "local" / "server.con"
        if smartstore_conf.exists():
            with open(smartstore_conf, "r") as f:
                content = f.read()
                if "[s3]" in content or "[azure]" in content:
                    storage["smartstore"] = {"status": "OK", "enabled": True}
                    print("   ✅ SmartStore 설정됨 (S3/Azure 통합)")
                else:
                    storage["smartstore"] = {"status": "INFO", "enabled": False}
                    print("   ℹ️ SmartStore 미사용 (로컬 스토리지)")
        else:
            storage["smartstore"] = {"status": "INFO", "enabled": False}
            print("   ℹ️ SmartStore 미설정")

        self.results["storage"] = storage
        print("")

    def check_indexes(self):
        """인덱스 설정 점검"""
        print("📚 [3/13] 인덱스 설정 점검")
        print("-" * 80)

        try:
            # 인덱스 목록 조회
            indexes_output = self.run_splunk_command("list index")
            index_count = len(indexes_output.strip().split("\n"))

            self.results["checks"]["indexes"] = {
                "status": "OK",
                "total_count": index_count,
            }
            print(f"   ✅ 총 {index_count}개 인덱스 설정됨")

            # fw 인덱스 존재 확인
            if "fw" in indexes_output.lower():
                print("   ✅ fw 인덱스 존재 (FortiGate 데이터용)")
            else:
                print("   ⚠️ fw 인덱스 없음 (생성 필요)")
                self.results["recommendations"].append(
                    {
                        "type": "INDEX",
                        "priority": "HIGH",
                        "message": "fw 인덱스 생성 필요: splunk add index fw",
                    }
                )

        except Exception as e:
            self.results["checks"]["indexes"] = {"status": "ERROR", "error": str(e)}
            print(f"   ❌ 인덱스 조회 실패: {e}")

        print("")

    def check_inputs(self):
        """데이터 입력 점검"""
        print("📥 [4/13] 데이터 입력 설정 점검")
        print("-" * 80)

        inputs_conf = self.splunk_home / "etc" / "system" / "local" / "inputs.conf"
        inputs_check = {}

        if inputs_conf.exists():
            with open(inputs_conf, "r") as f:
                content = f.read()

                # TCP 입력
                if "[tcp://" in content:
                    inputs_check["tcp"] = {"status": "OK", "configured": True}
                    print("   ✅ TCP 입력 설정됨")
                else:
                    inputs_check["tcp"] = {"status": "INFO", "configured": False}

                # UDP 입력
                if "[udp://" in content:
                    inputs_check["udp"] = {"status": "OK", "configured": True}
                    print("   ✅ UDP 입력 설정됨 (Syslog 수신 가능)")
                else:
                    inputs_check["udp"] = {"status": "INFO", "configured": False}

                # HEC (HTTP Event Collector)
                if "[http" in content:
                    inputs_check["hec"] = {"status": "OK", "configured": True}
                    print("   ✅ HEC 입력 설정됨")
                else:
                    inputs_check["hec"] = {"status": "INFO", "configured": False}
                    print("   ℹ️ HEC 미설정 (HTTP 기반 이벤트 수집)")

                # 파일 모니터링
                if "[monitor://" in content:
                    inputs_check["monitor"] = {"status": "OK", "configured": True}
                    print("   ✅ 파일 모니터링 설정됨")
                else:
                    inputs_check["monitor"] = {"status": "INFO", "configured": False}

        else:
            print("   ⚠️ inputs.conf 없음 (데이터 입력 미설정)")

        self.results["checks"]["inputs"] = inputs_check
        print("")

    def check_alert_system(self):
        """알림 시스템 점검"""
        print("🚨 [5/13] 알림 시스템 점검")
        print("-" * 80)

        alert_checks = {}

        # savedsearches.conf
        savedsearches = self.app_dir / "default" / "savedsearches.con"
        if savedsearches.exists():
            with open(savedsearches, "r") as f:
                content = f.read()
                alert_count = content.count("[") - 1  # 스탠자 개수
                enabled_count = content.count("enableSched = 1")
                disabled_count = content.count("enableSched = 0")

                alert_checks["savedsearches"] = {
                    "status": "OK",
                    "total_alerts": alert_count,
                    "enabled": enabled_count,
                    "disabled": disabled_count,
                }
                print(f"   ✅ {alert_count}개 알림 정의됨 ({enabled_count}개 활성)")
        else:
            alert_checks["savedsearches"] = {"status": "WARNING", "exists": False}
            print("   ⚠️ savedsearches.conf 없음")

        # alert_actions.conf
        alert_actions = self.app_dir / "default" / "alert_actions.con"
        if alert_actions.exists():
            with open(alert_actions, "r") as f:
                content = f.read()
                has_slack = "[slack]" in content
                has_email = "[email]" in content

                alert_checks["alert_actions"] = {
                    "status": "OK",
                    "slack": has_slack,
                    "email": has_email,
                }
                print(f"   ✅ Slack 알림: {'설정됨' if has_slack else '미설정'}")
                print(
                    f"   {'✅' if has_email else 'ℹ️'} Email 알림: {'설정됨' if has_email else '미설정'}"
                )
        else:
            alert_checks["alert_actions"] = {"status": "WARNING", "exists": False}

        self.results["checks"]["alerts"] = alert_checks
        print("")

    def check_lookups(self):
        """룩업 테이블 점검"""
        print("📋 [6/13] 룩업 테이블 점검")
        print("-" * 80)

        lookups_dir = self.app_dir / "lookups"
        lookup_checks = {}

        if lookups_dir.exists():
            csv_files = list(lookups_dir.glob("*.csv"))
            lookup_checks["csv_count"] = len(csv_files)
            lookup_checks["files"] = [f.name for f in csv_files]

            print(f"   ✅ {len(csv_files)}개 룩업 CSV 파일")

            # State tracker 개수
            state_trackers = [f for f in csv_files if "state_tracker" in f.name]
            print(f"   ✅ {len(state_trackers)}개 State Tracker (상태 저장)")

            # 자동 룩업 적용 확인
            transforms_conf = self.app_dir / "default" / "transforms.con"
            if transforms_conf.exists():
                with open(transforms_conf, "r") as f:
                    content = f.read()
                    stanza_count = content.count("[") - 1
                    lookup_checks["transforms_stanzas"] = stanza_count
                    print(f"   ✅ {stanza_count}개 룩업 정의 (transforms.conf)")

        else:
            lookup_checks["status"] = "WARNING"
            print("   ⚠️ lookups 디렉토리 없음")

        self.results["checks"]["lookups"] = lookup_checks
        print("")

    def check_kvstore(self):
        """KV Store 점검 (NoSQL 저장소)"""
        print("🗄️ [7/13] KV Store 점검 (NoSQL 저장소)")
        print("-" * 80)

        kvstore_checks = {}

        try:
            # KV Store 상태 확인
            kvstore_status = self.run_splunk_command("show kvstore-status")
            is_ready = "ready" in kvstore_status.lower()

            kvstore_checks["status"] = "OK" if is_ready else "WARNING"
            kvstore_checks["ready"] = is_ready

            print(
                f"   {'✅' if is_ready else '⚠️'} KV Store: {'Ready' if is_ready else 'Not Ready'}"
            )

            if is_ready:
                # collections.conf 확인
                collections_conf = self.app_dir / "default" / "collections.con"
                if collections_conf.exists():
                    with open(collections_conf, "r") as f:
                        content = f.read()
                        collection_count = content.count("[") - 1
                        kvstore_checks["collections"] = collection_count
                        print(f"   ✅ {collection_count}개 KV Store 컬렉션 정의됨")
                else:
                    print("   ℹ️ collections.conf 없음 (KV Store 미사용)")

        except Exception as e:
            kvstore_checks["status"] = "ERROR"
            kvstore_checks["error"] = str(e)
            print(f"   ❌ KV Store 확인 실패: {e}")

        self.results["checks"]["kvstore"] = kvstore_checks
        print("")

    def check_summary_indexing(self):
        """요약 인덱싱 점검 (Summary Indexing)"""
        print("📊 [8/13] 요약 인덱싱 점검 (Summary Indexing)")
        print("-" * 80)

        summary_checks = {}

        # summary 인덱스 존재 확인
        try:
            indexes_output = self.run_splunk_command("list index")
            if "summary" in indexes_output.lower():
                summary_checks["summary_index"] = {"status": "OK", "exists": True}
                print("   ✅ summary 인덱스 존재")
            else:
                summary_checks["summary_index"] = {"status": "INFO", "exists": False}
                print("   ℹ️ summary 인덱스 없음 (요약 인덱싱 미사용)")

            # savedsearches.conf에서 요약 검색 확인
            savedsearches = self.app_dir / "default" / "savedsearches.con"
            if savedsearches.exists():
                with open(savedsearches, "r") as f:
                    content = f.read()
                    summary_count = content.count("action.summary_index")
                    summary_checks["summary_searches"] = summary_count

                    if summary_count > 0:
                        print(f"   ✅ {summary_count}개 요약 인덱싱 검색 설정됨")
                    else:
                        print("   ℹ️ 요약 인덱싱 검색 없음")

        except Exception as e:
            summary_checks["status"] = "ERROR"
            summary_checks["error"] = str(e)
            print(f"   ❌ 요약 인덱싱 확인 실패: {e}")

        self.results["checks"]["summary_indexing"] = summary_checks
        print("")

    def check_data_model_acceleration(self):
        """데이터 모델 가속화 점검"""
        print("⚡ [9/13] 데이터 모델 가속화 점검")
        print("-" * 80)

        dm_checks = {}

        datamodels_dir = self.app_dir / "default" / "data" / "models"
        if datamodels_dir.exists():
            dm_files = list(datamodels_dir.glob("*.json"))
            dm_checks["model_count"] = len(dm_files)
            print(f"   ✅ {len(dm_files)}개 데이터 모델 정의됨")

            # 가속화 설정 확인
            accelerated_count = 0
            for dm_file in dm_files:
                with open(dm_file, "r") as f:
                    content = f.read()
                    if '"acceleration"' in content and '"enabled": true' in content:
                        accelerated_count += 1

            dm_checks["accelerated_count"] = accelerated_count
            if accelerated_count > 0:
                print(f"   ✅ {accelerated_count}개 데이터 모델 가속화 활성화됨")
            else:
                print("   ℹ️ 가속화된 데이터 모델 없음")

        else:
            dm_checks["status"] = "INFO"
            print("   ℹ️ 데이터 모델 미사용")

        self.results["checks"]["data_model"] = dm_checks
        print("")

    def check_shc_status(self):
        """검색 헤드 클러스터링 점검"""
        print("🔍 [10/13] 검색 헤드 클러스터링 점검 (SHC)")
        print("-" * 80)

        shc_checks = {}

        try:
            shc_status = self.run_splunk_command("show shcluster-status")
            is_member = (
                "captain" in shc_status.lower() or "member" in shc_status.lower()
            )

            shc_checks["is_member"] = is_member
            if is_member:
                print("   ✅ 검색 헤드 클러스터 멤버임")
            else:
                print("   ℹ️ 검색 헤드 클러스터 미사용 (단일 검색 헤드)")

        except Exception:
            shc_checks["status"] = "INFO"
            shc_checks["is_member"] = False
            print("   ℹ️ 검색 헤드 클러스터 미사용")

        self.results["checks"]["shc"] = shc_checks
        print("")

    def check_indexer_clustering(self):
        """인덱서 클러스터링 점검"""
        print("📦 [11/13] 인덱서 클러스터링 점검")
        print("-" * 80)

        idx_cluster_checks = {}

        try:
            cluster_status = self.run_splunk_command("show cluster-status")
            is_clustered = (
                "master" in cluster_status.lower() or "peer" in cluster_status.lower()
            )

            idx_cluster_checks["is_clustered"] = is_clustered
            if is_clustered:
                print("   ✅ 인덱서 클러스터 구성됨 (고가용성)")
            else:
                print("   ℹ️ 인덱서 클러스터 미사용 (단일 인덱서)")

        except Exception:
            idx_cluster_checks["status"] = "INFO"
            idx_cluster_checks["is_clustered"] = False
            print("   ℹ️ 인덱서 클러스터 미사용")

        self.results["checks"]["indexer_clustering"] = idx_cluster_checks
        print("")

    def check_forwarding(self):
        """포워딩 설정 점검"""
        print("📡 [12/13] 포워딩 설정 점검")
        print("-" * 80)

        forwarding_checks = {}

        outputs_conf = self.splunk_home / "etc" / "system" / "local" / "outputs.con"
        if outputs_conf.exists():
            with open(outputs_conf, "r") as f:
                content = f.read()

                # 인덱서 포워딩
                if "[tcpout:" in content:
                    forwarding_checks["tcpout"] = {"status": "OK", "configured": True}
                    print("   ✅ TCP 포워딩 설정됨 (인덱서로 전송)")
                else:
                    forwarding_checks["tcpout"] = {
                        "status": "INFO",
                        "configured": False,
                    }

                # 자동 로드 밸런싱
                if "autoLB" in content or "autoLBFrequency" in content:
                    print("   ✅ 자동 로드 밸런싱 설정됨")

        else:
            forwarding_checks["status"] = "INFO"
            print("   ℹ️ outputs.conf 없음 (포워딩 미사용)")

        self.results["checks"]["forwarding"] = forwarding_checks
        print("")

    def suggest_automation(self):
        """자동화 기법 제안"""
        print("🤖 [13/13] 자동화 기법 제안")
        print("-" * 80)

        automation_suggestions = []

        # 1. Saved Search 자동화
        automation_suggestions.append(
            {
                "type": "SAVED_SEARCH",
                "title": "실시간 알림 자동화",
                "description": "cron_schedule 사용하여 주기적 검색 실행",
                "example": "cron_schedule = */10 * * * * (10분마다 실행)",
                "benefit": "CPU 효율적, 자원 관리 용이",
            }
        )

        # 2. Summary Indexing 자동화
        automation_suggestions.append(
            {
                "type": "SUMMARY_INDEX",
                "title": "요약 인덱싱으로 대시보드 성능 개선",
                "description": "대량 데이터 사전 집계 후 summary 인덱스 저장",
                "example": "action.summary_index = 1\naction.summary_index._name = summary",
                "benefit": "대시보드 로딩 10배 이상 빠름, 검색 부하 감소",
            }
        )

        # 3. Data Model Acceleration
        automation_suggestions.append(
            {
                "type": "DATA_MODEL",
                "title": "데이터 모델 가속화",
                "description": "자주 사용하는 검색 패턴을 데이터 모델로 정의 + 가속화",
                "example": '"acceleration": {"enabled": true}',
                "benefit": "복잡한 검색 100배 이상 빠름",
            }
        )

        # 4. KV Store 활용
        automation_suggestions.append(
            {
                "type": "KVSTORE",
                "title": "KV Store로 상태 저장",
                "description": "상태 추적 CSV 대신 KV Store 사용 (읽기/쓰기 빠름)",
                "example": "| outputlookup state_tracker append=true",
                "benefit": "동시 접근 안전, 인덱싱 불필요, 빠른 조회",
            }
        )

        # 5. 자동 Response Action
        automation_suggestions.append(
            {
                "type": "AUTO_RESPONSE",
                "title": "자동 대응 액션",
                "description": "알림 트리거 시 자동으로 스크립트 실행 (차단, 격리 등)",
                "example": "action.script = 1\naction.script.filename = auto_block_ip.py",
                "benefit": "사람 개입 없이 즉시 대응, MTTR 감소",
            }
        )

        # 6. SmartStore
        automation_suggestions.append(
            {
                "type": "SMARTSTORE",
                "title": "SmartStore로 스토리지 비용 절감",
                "description": "오래된 데이터 자동으로 S3/Azure로 이동",
                "example": "remotePath = volume:remote1/$_index_name",
                "benefit": "로컬 디스크 70% 절감, 무제한 확장",
            }
        )

        # 7. 자동 Frozen 아카이브
        automation_suggestions.append(
            {
                "type": "FROZEN_ARCHIVE",
                "title": "Frozen 데이터 자동 아카이브",
                "description": "frozenTimePeriodInSecs 후 자동으로 외부 저장소 이동",
                "example": "coldToFrozenDir = /mnt/archive/frozen",
                "benefit": "규정 준수, 장기 보관, 디스크 확보",
            }
        )

        # 8. REST API 자동화
        automation_suggestions.append(
            {
                "type": "REST_API",
                "title": "REST API로 설정 자동화",
                "description": "Python/Bash로 알림/대시보드 자동 생성",
                "example": "curl -k -u admin:pass https://localhost:8089/servicesNS/.../alerts",
                "benefit": "수동 작업 제거, 일관성, 버전 관리",
            }
        )

        # 결과 저장
        self.results["automation"] = {
            "suggestions": automation_suggestions,
            "count": len(automation_suggestions),
        }

        # 출력
        for i, suggestion in enumerate(automation_suggestions, 1):
            print(f"   {i}. {suggestion['title']}")
            print(f"      💡 {suggestion['description']}")
            print(f"      📋 예시: {suggestion['example']}")
            print(f"      ✅ 효과: {suggestion['benefit']}")
            print("")

    def run_splunk_command(self, command):
        """Splunk CLI 명령 실행"""
        if not self.splunk_bin.exists():
            raise Exception(f"Splunk binary not found: {self.splunk_bin}")

        full_command = f"{self.splunk_bin} {command}"
        result = subprocess.run(
            full_command, shell=True, capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")

        return result.stdout

    def print_results(self):
        """결과 요약 출력"""
        print("=" * 80)
        print("📊 검증 결과 요약")
        print("=" * 80)
        print("")

        # 권장 사항
        if self.results["recommendations"]:
            print(f"⚠️ 권장 사항 ({len(self.results['recommendations'])}개):")
            for rec in self.results["recommendations"]:
                print(f"   [{rec['priority']}] {rec['type']}: {rec['message']}")
            print("")

        # 자동화 제안
        if self.results["automation"]:
            print(f"🤖 자동화 기법: {self.results['automation']['count']}개 제안")
            print("")

        print("✅ 전체 점검 완료!")
        print("=" * 80)

    def save_results(self):
        """결과 JSON 저장"""
        output_file = self.app_dir / "splunk_feature_check_results.json"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 결과 저장됨: {output_file}")
        except Exception as e:
            print(f"\n❌ 결과 저장 실패: {e}")


def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        splunk_home = sys.argv[1]
    else:
        splunk_home = "/opt/splunk"

    checker = SplunkFeatureChecker(splunk_home)
    checker.check_all_features()

    # 결과 반환
    sys.exit(0)


if __name__ == "__main__":
    main()
