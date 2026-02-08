#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deployment Health Check System
배포 후 자동 검증 및 상태 점검
"""

import functools
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Splunk alert protocol reserves stdout; redirect print to stderr
print = functools.partial(print, file=sys.stderr)  # noqa: A001


class DeploymentHealthCheck:
    """배포 상태 검증 및 헬스 체크"""

    def __init__(self, app_dir=None):
        """
        Args:
            app_dir: Splunk app 디렉토리 경로
        """
        if app_dir is None:
            app_dir = "/opt/splunk/etc/apps/security_alert"
        self.app_dir = Path(app_dir)
        self.splunk_bin = "/opt/splunk/bin/splunk"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "errors": [],
            "warnings": [],
            "summary": {},
        }

    def run_all_checks(self):
        """전체 헬스 체크 실행"""
        print("=" * 70)
        print("🏥 Security Alert System - Deployment Health Check")
        print("=" * 70)
        print("")

        # 1. 파일 구조 검증
        self.check_file_structure()

        # 2. Splunk 서비스 상태
        self.check_splunk_service()

        # 3. 앱 활성화 상태
        self.check_app_status()

        # 4. 데이터 가용성
        self.check_data_availability()

        # 5. 알림 스케줄러 상태
        self.check_scheduler_status()

        # 6. Slack 연동 상태
        self.check_slack_integration()

        # 7. 룩업 파일 상태
        self.check_lookup_health()

        # 8. REST API 엔드포인트
        self.check_rest_api()

        # 9. 대시보드 접근성
        self.check_dashboards()

        # 10. Python 스크립트 실행 권한
        self.check_script_permissions()

        # 결과 출력
        self.print_results()

        # JSON 출력 (옵션)
        return self.results

    def check_file_structure(self):
        """파일 구조 검증"""
        print("📁 [1/10] 파일 구조 검증")
        print("-" * 70)

        required_dirs = ["bin", "default", "local", "lookups", "metadata"]

        required_files = [
            "default/app.conf",
            "default/alert_actions.conf",
            "default/setup.xml",
            "bin/slack_blockkit_alert.py",
            "bin/auto_validator.py",
            "bin/splunk_feature_checker.py",
        ]

        check_result = {"name": "File Structure", "status": "OK", "details": []}

        # 디렉토리 확인
        for dir_name in required_dirs:
            dir_path = self.app_dir / dir_name
            if dir_path.exists():
                check_result["details"].append(f"✅ {dir_name}/ - 존재")
            else:
                check_result["status"] = "ERROR"
                check_result["details"].append(f"❌ {dir_name}/ - 없음")
                self.results["errors"].append(f"필수 디렉토리 없음: {dir_name}")

        # 파일 확인
        for file_name in required_files:
            file_path = self.app_dir / file_name
            if file_path.exists():
                check_result["details"].append(f"✅ {file_name} - 존재")
            else:
                check_result["status"] = "ERROR"
                check_result["details"].append(f"❌ {file_name} - 없음")
                self.results["errors"].append(f"필수 파일 없음: {file_name}")

        self.results["checks"].append(check_result)
        print("")

    def check_splunk_service(self):
        """Splunk 서비스 상태"""
        print("🔧 [2/10] Splunk 서비스 상태")
        print("-" * 70)

        check_result = {"name": "Splunk Service", "status": "OK", "details": []}

        try:
            result = subprocess.run(
                [self.splunk_bin, "status"], capture_output=True, text=True, timeout=10
            )

            if "splunkd is running" in result.stdout:
                check_result["details"].append("✅ Splunk 서비스 실행 중")
            else:
                check_result["status"] = "ERROR"
                check_result["details"].append("❌ Splunk 서비스 중지됨")
                self.results["errors"].append("Splunk 서비스가 실행 중이지 않음")

        except subprocess.TimeoutExpired:
            check_result["status"] = "WARNING"
            check_result["details"].append("⚠️ Splunk 상태 확인 타임아웃")
            self.results["warnings"].append("Splunk 상태 확인 타임아웃")

        except Exception as e:
            check_result["status"] = "ERROR"
            check_result["details"].append(f"❌ Splunk 상태 확인 실패: {str(e)}")
            self.results["errors"].append(f"Splunk 상태 확인 실패: {str(e)}")

        self.results["checks"].append(check_result)
        print("")

    def check_app_status(self):
        """앱 활성화 상태"""
        print("📦 [3/10] 앱 활성화 상태")
        print("-" * 70)

        check_result = {"name": "App Status", "status": "OK", "details": []}

        try:
            result = subprocess.run(
                [self.splunk_bin, "display", "app", "security_alert"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if "ENABLED" in result.stdout.upper():
                check_result["details"].append("✅ security_alert 앱 활성화됨")
            elif "DISABLED" in result.stdout.upper():
                check_result["status"] = "WARNING"
                check_result["details"].append("⚠️ security_alert 앱 비활성화됨")
                self.results["warnings"].append("앱이 비활성화 상태")
            else:
                check_result["status"] = "ERROR"
                check_result["details"].append("❌ security_alert 앱 상태 불명")
                self.results["errors"].append("앱 상태를 확인할 수 없음")

        except Exception as e:
            check_result["status"] = "ERROR"
            check_result["details"].append(f"❌ 앱 상태 확인 실패: {str(e)}")
            self.results["errors"].append(f"앱 상태 확인 실패: {str(e)}")

        self.results["checks"].append(check_result)
        print("")

    def check_data_availability(self):
        """데이터 가용성 (index=fw)"""
        print("💾 [4/10] 데이터 가용성 (index=fw)")
        print("-" * 70)

        check_result = {"name": "Data Availability", "status": "OK", "details": []}

        try:
            # SPL 쿼리 실행
            spl_query = "search index=fw earliest=-1h | stats count"
            result = subprocess.run(
                [self.splunk_bin, "search", spl_query],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # 결과 파싱
            if "count" in result.stdout:
                # 이벤트 수 추출
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if line.strip().isdigit():
                        count = int(line.strip())
                        if count > 0:
                            check_result["details"].append(
                                f"✅ index=fw 데이터 존재: {count} 이벤트 (최근 1시간)"
                            )
                        else:
                            check_result["status"] = "WARNING"
                            check_result["details"].append(
                                "⚠️ index=fw 데이터 없음 (최근 1시간)"
                            )
                            self.results["warnings"].append(
                                "최근 1시간 동안 index=fw에 데이터 없음"
                            )
                        break
            else:
                check_result["status"] = "WARNING"
                check_result["details"].append("⚠️ index=fw 데이터 확인 불가")
                self.results["warnings"].append("index=fw 데이터 확인 불가")

        except subprocess.TimeoutExpired:
            check_result["status"] = "WARNING"
            check_result["details"].append("⚠️ 데이터 확인 타임아웃")
            self.results["warnings"].append("데이터 확인 타임아웃")

        except Exception as e:
            check_result["status"] = "WARNING"
            check_result["details"].append(f"⚠️ 데이터 확인 실패: {str(e)}")
            self.results["warnings"].append(f"데이터 확인 실패: {str(e)}")

        self.results["checks"].append(check_result)
        print("")

    def check_scheduler_status(self):
        """알림 스케줄러 상태"""
        print("⏰ [5/10] 알림 스케줄러 상태")
        print("-" * 70)

        check_result = {"name": "Scheduler Status", "status": "OK", "details": []}

        savedsearches_path = self.app_dir / "local" / "savedsearches.conf"
        if savedsearches_path.exists():
            with open(savedsearches_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 알림 수 계산
            import re

            alerts = re.findall(r"\[([^\]]+_Alert)\]", content)
            enabled_alerts = content.count("enableSched = 1")

            check_result["details"].append(f"✅ 정의된 알림: {len(alerts)}개")
            check_result["details"].append(f"✅ 활성화된 알림: {enabled_alerts}개")

            if enabled_alerts == 0 and len(alerts) > 0:
                check_result["status"] = "WARNING"
                check_result["details"].append("⚠️ 모든 알림이 비활성화 상태")
                self.results["warnings"].append("활성화된 알림 없음")
        else:
            check_result["status"] = "WARNING"
            check_result["details"].append("⚠️ savedsearches.conf 파일 없음")
            self.results["warnings"].append("savedsearches.conf 파일 없음")

        self.results["checks"].append(check_result)
        print("")

    def check_slack_integration(self):
        """Slack 연동 상태"""
        print("💬 [6/10] Slack 연동 상태")
        print("-" * 70)

        check_result = {"name": "Slack Integration", "status": "OK", "details": []}

        # alert_actions.conf 확인
        alert_actions_path = self.app_dir / "local" / "alert_actions.conf"
        if not alert_actions_path.exists():
            alert_actions_path = self.app_dir / "default" / "alert_actions.conf"

        if alert_actions_path.exists():
            with open(alert_actions_path, "r", encoding="utf-8") as f:
                content = f.read()

            has_bot_token = "param.bot_token" in content
            has_webhook = "param.webhook_url" in content
            has_channel = "param.channel" in content

            if has_bot_token or has_webhook:
                check_result["details"].append("✅ Slack 인증 설정 존재")
            else:
                check_result["status"] = "WARNING"
                check_result["details"].append(
                    "⚠️ Slack 인증 미설정 (bot_token 또는 webhook_url 필요)"
                )
                self.results["warnings"].append("Slack 인증 미설정")

            if has_channel:
                check_result["details"].append("✅ Slack 채널 설정됨")
            else:
                check_result["status"] = "WARNING"
                check_result["details"].append("⚠️ Slack 채널 미설정")
                self.results["warnings"].append("Slack 채널 미설정")
        else:
            check_result["status"] = "ERROR"
            check_result["details"].append("❌ alert_actions.conf 파일 없음")
            self.results["errors"].append("alert_actions.conf 파일 없음")

        self.results["checks"].append(check_result)
        print("")

    def check_lookup_health(self):
        """룩업 파일 상태"""
        print("📚 [7/10] 룩업 파일 상태")
        print("-" * 70)

        check_result = {"name": "Lookup Files", "status": "OK", "details": []}

        lookups_dir = self.app_dir / "lookups"
        if lookups_dir.exists():
            csv_files = list(lookups_dir.glob("*.csv"))
            check_result["details"].append(f"✅ 룩업 파일 수: {len(csv_files)}개")

            # 빈 파일 확인
            empty_files = [f.name for f in csv_files if f.stat().st_size < 10]
            if empty_files:
                check_result["status"] = "WARNING"
                check_result["details"].append(
                    f"⚠️ 빈 룩업 파일: {', '.join(empty_files)}"
                )
                self.results["warnings"].append(
                    f"빈 룩업 파일 존재: {len(empty_files)}개"
                )
        else:
            check_result["status"] = "ERROR"
            check_result["details"].append("❌ lookups 디렉토리 없음")
            self.results["errors"].append("lookups 디렉토리 없음")

        self.results["checks"].append(check_result)
        print("")

    def check_rest_api(self):
        """REST API 엔드포인트"""
        print("🌐 [8/10] REST API 엔드포인트")
        print("-" * 70)

        check_result = {"name": "REST API", "status": "OK", "details": []}

        restmap_path = self.app_dir / "local" / "restmap.conf"
        if restmap_path.exists():
            with open(restmap_path, "r", encoding="utf-8") as f:
                content = f.read()

            if "security_alert/alerts" in content:
                check_result["details"].append("✅ REST API 엔드포인트 정의됨")
            else:
                check_result["status"] = "WARNING"
                check_result["details"].append("⚠️ REST API 엔드포인트 정의 없음")
                self.results["warnings"].append("REST API 엔드포인트 정의 없음")
        else:
            check_result["status"] = "WARNING"
            check_result["details"].append("⚠️ restmap.conf 파일 없음")
            self.results["warnings"].append("restmap.conf 파일 없음")

        self.results["checks"].append(check_result)
        print("")

    def check_dashboards(self):
        """대시보드 접근성"""
        print("📊 [9/10] 대시보드 접근성")
        print("-" * 70)

        check_result = {"name": "Dashboards", "status": "OK", "details": []}

        views_dir = self.app_dir / "local" / "data" / "ui" / "views"
        if views_dir.exists():
            xml_files = list(views_dir.glob("*.xml"))
            check_result["details"].append(f"✅ 대시보드 파일: {len(xml_files)}개")

            for xml_file in xml_files:
                check_result["details"].append(f"   - {xml_file.name}")
        else:
            check_result["status"] = "WARNING"
            check_result["details"].append("⚠️ 대시보드 디렉토리 없음")
            self.results["warnings"].append("대시보드 디렉토리 없음")

        self.results["checks"].append(check_result)
        print("")

    def check_script_permissions(self):
        """Python 스크립트 실행 권한"""
        print("🔐 [10/10] Python 스크립트 실행 권한")
        print("-" * 70)

        check_result = {"name": "Script Permissions", "status": "OK", "details": []}

        bin_dir = self.app_dir / "bin"
        if bin_dir.exists():
            py_files = list(bin_dir.glob("*.py"))

            for py_file in py_files:
                if os.access(py_file, os.X_OK):
                    check_result["details"].append(f"✅ {py_file.name} - 실행 가능")
                else:
                    check_result["status"] = "WARNING"
                    check_result["details"].append(f"⚠️ {py_file.name} - 실행 권한 없음")
                    self.results["warnings"].append(f"{py_file.name} 실행 권한 없음")
        else:
            check_result["status"] = "ERROR"
            check_result["details"].append("❌ bin 디렉토리 없음")
            self.results["errors"].append("bin 디렉토리 없음")

        self.results["checks"].append(check_result)
        print("")

    def print_results(self):
        """결과 출력"""
        print("=" * 70)
        print("📊 헬스 체크 결과 요약")
        print("=" * 70)
        print("")

        # 통계
        total_checks = len(self.results["checks"])
        ok_checks = len([c for c in self.results["checks"] if c["status"] == "OK"])
        warning_checks = len(
            [c for c in self.results["checks"] if c["status"] == "WARNING"]
        )
        error_checks = len(
            [c for c in self.results["checks"] if c["status"] == "ERROR"]
        )

        print(f"총 검사 항목: {total_checks}개")
        print(f"  ✅ 정상: {ok_checks}개")
        print(f"  ⚠️ 경고: {warning_checks}개")
        print(f"  ❌ 오류: {error_checks}개")
        print("")

        # 오류
        if self.results["errors"]:
            print(f"❌ 오류 ({len(self.results['errors'])}개):")
            for error in self.results["errors"]:
                print(f"   {error}")
            print("")

        # 경고
        if self.results["warnings"]:
            print(f"⚠️ 경고 ({len(self.results['warnings'])}개):")
            for warning in self.results["warnings"]:
                print(f"   {warning}")
            print("")

        # 종합 판정
        print("=" * 70)
        if not self.results["errors"]:
            if not self.results["warnings"]:
                print("✅ 전체 헬스 체크 통과! (오류 0, 경고 0)")
            else:
                print(f"⚠️ 헬스 체크 경고 있음 ({len(self.results['warnings'])}개 경고)")
        else:
            print(f"❌ 헬스 체크 실패 ({len(self.results['errors'])}개 오류)")
        print("=" * 70)

        # Summary
        self.results["summary"] = {
            "total_checks": total_checks,
            "ok": ok_checks,
            "warnings": warning_checks,
            "errors": error_checks,
            "overall_status": "OK" if error_checks == 0 else "ERROR",
        }


def main():
    """메인 함수"""
    # 인자 파싱
    if len(sys.argv) > 1:
        app_dir = sys.argv[1]
    else:
        app_dir = None

    # 헬스 체크 실행
    checker = DeploymentHealthCheck(app_dir)
    results = checker.run_all_checks()

    # JSON 출력 (옵션)
    if "--json" in sys.argv:
        print("")
        print(json.dumps(results, indent=2, ensure_ascii=False))

    # 종료 코드
    sys.exit(0 if results["summary"]["errors"] == 0 else 1)


if __name__ == "__main__":
    main()
