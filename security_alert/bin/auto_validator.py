#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Validator for Security Alert System
자동 검증 시스템: 룩업, SPL 문법, 설정 파일 검증

Optimized version with type hints and reduced redundancy
"""

import sys
import os
import json
import re
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Constants
DEFAULT_APP_DIR = '/opt/splunk/etc/apps/security_alert'
STATE_TRACKER_HEADERS = ['device', 'prev_state', 'current_state', 'last_change', '_key']

# Required files
REQUIRED_LOOKUPS = [
    'fortigate_logid_notification_map.csv',
    'severity_priority.csv',
    'auto_response_actions.csv'
]

STATE_TRACKERS = [
    'vpn_state_tracker.csv',
    'hardware_state_tracker.csv',
    'ha_state_tracker.csv',
    'interface_state_tracker.csv',
    'cpu_memory_state_tracker.csv',
    'resource_state_tracker.csv',
    'admin_login_state_tracker.csv',
    'vpn_brute_force_state_tracker.csv',
    'traffic_spike_state_tracker.csv',
    'license_state_tracker.csv'
]

REQUIRED_TRANSFORMS_STANZAS = [
    'fortigate_logid_lookup',
    'severity_priority_lookup',
    'auto_response_lookup',
    'vpn_state_tracker',
    'hardware_state_tracker'
]

VALID_SPL_COMMANDS = [
    'stats', 'eval', 'where', 'table', 'sort', 'head', 'tail',
    'dedup', 'rex', 'rename', 'join', 'inputlookup', 'outputlookup'
]

class AutoValidator:
    """자동 검증 클래스 (Optimized)"""

    def __init__(self, app_dir: Optional[str] = None):
        """
        Initialize Auto Validator

        Args:
            app_dir: Splunk app 디렉토리 경로 (default: /opt/splunk/etc/apps/security_alert)
        """
        if app_dir is None:
            app_dir = DEFAULT_APP_DIR
        self.app_dir = Path(app_dir)
        self.lookups_dir = self.app_dir / 'lookups'
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate_all(self) -> bool:
        """
        전체 검증 실행

        Returns:
            True if validation passes, False otherwise
        """
        print("=" * 60)
        print("🔍 Security Alert System - Auto Validation (Optimized)")
        print("=" * 60)
        print("")

        validation_steps = [
            ("룩업 CSV 파일", self.validate_lookups),
            ("transforms.conf", self.validate_transforms_conf),
            ("props.conf", self.validate_props_conf),
            ("savedsearches.conf", self.validate_savedsearches_conf),
            ("alert_actions.conf", self.validate_alert_actions_conf)
        ]

        for step_num, (step_name, validation_func) in enumerate(validation_steps, 1):
            print(f"[{step_num}/{len(validation_steps)}] {step_name} 검증")
            validation_func()

        # 결과 출력
        self.print_results()

        # 검증 통과 여부 반환
        return len(self.errors) == 0

    def validate_lookups(self) -> None:
        """룩업 CSV 파일 검증"""
        print("-" * 60)

        if not self.lookups_dir.exists():
            self.errors.append(f"❌ 룩업 디렉토리 없음: {self.lookups_dir}")
            print("")
            return

        # 필수 룩업 검증
        for lookup_file in REQUIRED_LOOKUPS:
            lookup_path = self.lookups_dir / lookup_file
            if not lookup_path.exists():
                self.errors.append(f"❌ 필수 룩업 파일 없음: {lookup_file}")
            else:
                self.validate_csv_file(lookup_path)
                self.info.append(f"✅ {lookup_file} - OK")

        # State tracker 검증 (없으면 생성)
        for tracker_file in STATE_TRACKERS:
            tracker_path = self.lookups_dir / tracker_file
            if not tracker_path.exists():
                # 자동 생성
                if self.create_state_tracker(tracker_path):
                    self.info.append(f"🆕 {tracker_file} - 자동 생성됨")
            else:
                self.info.append(f"✅ {tracker_file} - 존재")

        print("")

    def validate_csv_file(self, csv_path: Path) -> bool:
        """
        CSV 파일 구조 검증

        Args:
            csv_path: Path to CSV file

        Returns:
            True if valid, False otherwise
        """
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                if not headers:
                    self.errors.append(f"❌ {csv_path.name}: 헤더가 없습니다")
                    return False

                # 행 수 확인
                row_count = sum(1 for row in reader)
                if row_count == 0:
                    self.warnings.append(f"⚠️ {csv_path.name}: 데이터 행이 없습니다")

                return True

        except (IOError, csv.Error) as e:
            self.errors.append(f"❌ {csv_path.name}: CSV 읽기 실패 - {str(e)}")
            return False

    def create_state_tracker(self, tracker_path: Path) -> bool:
        """
        State tracker CSV 자동 생성

        Args:
            tracker_path: Path where tracker should be created

        Returns:
            True if created successfully, False otherwise
        """
        try:
            with open(tracker_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(STATE_TRACKER_HEADERS)
            os.chmod(tracker_path, 0o644)
            return True
        except (IOError, OSError) as e:
            self.errors.append(f"❌ {tracker_path.name}: 자동 생성 실패 - {str(e)}")
            return False

    def _check_config_file_stanzas(self, config_name: str, required_stanzas: List[str]) -> None:
        """
        Helper method to validate configuration file stanzas

        Args:
            config_name: Name of the configuration file (e.g., 'transforms.conf')
            required_stanzas: List of required stanza names
        """
        config_path = self.app_dir / 'default' / config_name
        if not config_path.exists():
            self.errors.append(f"❌ {config_name} 파일이 없습니다")
            print("")
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for stanza in required_stanzas:
                if f"[{stanza}]" in content:
                    self.info.append(f"✅ [{stanza}] - 정의됨")
                else:
                    self.errors.append(f"❌ [{stanza}] - 정의 없음")

        except IOError as e:
            self.errors.append(f"❌ {config_name} 읽기 실패: {str(e)}")

        print("")

    def validate_transforms_conf(self) -> None:
        """transforms.conf 검증 (룩업 정의)"""
        print("-" * 60)
        self._check_config_file_stanzas('transforms.conf', REQUIRED_TRANSFORMS_STANZAS)

    def validate_props_conf(self):
        """props.conf 검증 (자동 룩업)"""
        print("⚙️ [3/5] props.conf 검증")
        print("-" * 60)

        props_path = self.app_dir / 'default' / 'props.conf'
        if not props_path.exists():
            self.errors.append("❌ props.conf 파일이 없습니다")
            print("")
            return

        with open(props_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 자동 룩업 정의 확인
        auto_lookups = [
            'LOOKUP-fortigate_logid',
            'LOOKUP-severity_priority',
            'LOOKUP-auto_response'
        ]

        for lookup in auto_lookups:
            if lookup in content:
                self.info.append(f"✅ {lookup} - 자동 적용됨")
            else:
                self.warnings.append(f"⚠️ {lookup} - 자동 적용 안 됨")

        print("")

    def validate_savedsearches_conf(self):
        """savedsearches.conf 검증 (알림 정의)"""
        print("🚨 [4/5] savedsearches.conf 검증")
        print("-" * 60)

        savedsearches_path = self.app_dir / 'default' / 'savedsearches.conf'
        if not savedsearches_path.exists():
            self.warnings.append("⚠️ savedsearches.conf 파일이 없습니다 (알림 없음)")
            print("")
            return

        with open(savedsearches_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 알림 스탠자 찾기
        alert_stanzas = re.findall(r'\[([^\]]+_Alert)\]', content)

        if not alert_stanzas:
            self.warnings.append("⚠️ 정의된 알림이 없습니다")
        else:
            self.info.append(f"✅ {len(alert_stanzas)}개 알림 정의됨")

            # 각 알림의 필수 필드 검증
            for alert in alert_stanzas:
                # SPL 쿼리 검증
                if not self.validate_spl_in_alert(content, alert):
                    self.errors.append(f"❌ {alert}: SPL 쿼리 문법 오류")

                # cron_schedule 검증
                if not self.validate_cron_schedule(content, alert):
                    self.warnings.append(f"⚠️ {alert}: cron_schedule 미정의")

        print("")

    def validate_spl_in_alert(self, content: str, alert_name: str) -> bool:
        """
        알림 내 SPL 쿼리 기본 검증

        Args:
            content: Configuration file content
            alert_name: Name of the alert

        Returns:
            True if SPL is valid, False otherwise
        """
        # 알림 스탠자 추출
        pattern = rf'\[{re.escape(alert_name)}\](.*?)(?=\[|$)'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return False

        stanza_content = match.group(1)

        # search 필드 확인
        search_match = re.search(r'search\s*=\s*(.+)', stanza_content)
        if not search_match:
            return False

        spl_query = search_match.group(1).strip()

        # 기본 SPL 문법 검증
        if not spl_query.startswith(('index=', '`')):  # Allow macro starts
            self.warnings.append(f"⚠️ {alert_name}: index 지정 또는 매크로 사용 권장")

        # 파이프 문법 검증
        if '|' in spl_query:
            pipes = spl_query.split('|')
            for pipe in pipes[1:]:  # 첫 번째는 index 쿼리
                cmd = pipe.strip().split()[0] if pipe.strip() else ''
                if cmd and cmd not in VALID_SPL_COMMANDS and not cmd.startswith('lookup') and not cmd.startswith('`'):
                    self.warnings.append(f"⚠️ {alert_name}: 검증 필요 SPL 명령어 '{cmd}'")

        return True

    def validate_cron_schedule(self, content, alert_name):
        """cron_schedule 검증"""
        pattern = rf'\[{re.escape(alert_name)}\](.*?)(?=\[|$)'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return False

        stanza_content = match.group(1)

        # cron_schedule 확인
        cron_match = re.search(r'cron_schedule\s*=\s*(.+)', stanza_content)
        if not cron_match:
            return False

        cron_expr = cron_match.group(1).strip()

        # 기본 cron 문법 검증 (5개 필드)
        parts = cron_expr.split()
        if len(parts) != 5:
            self.errors.append(f"❌ {alert_name}: cron_schedule 형식 오류 (5개 필드 필요)")
            return False

        return True

    def validate_alert_actions_conf(self):
        """alert_actions.conf 검증 (Slack 설정)"""
        print("💬 [5/5] alert_actions.conf 검증")
        print("-" * 60)

        alert_actions_path = self.app_dir / 'default' / 'alert_actions.conf'
        if not alert_actions_path.exists():
            self.errors.append("❌ alert_actions.conf 파일이 없습니다")
            print("")
            return

        with open(alert_actions_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # [slack] 스탠자 확인
        if '[slack]' not in content:
            self.errors.append("❌ [slack] 스탠자가 정의되지 않았습니다")
            return

        # 필수 파라미터 확인
        required_params = [
            'param.bot_token',
            'param.webhook_url',
            'param.channel'
        ]

        for param in required_params:
            if param in content:
                self.info.append(f"✅ {param} - 정의됨")
            else:
                self.warnings.append(f"⚠️ {param} - 정의 안 됨")

        # Python 버전 확인
        if 'python.version = python3' in content:
            self.info.append("✅ python.version = python3")
        else:
            self.errors.append("❌ python.version 미지정 또는 python2")

        print("")

    def print_results(self):
        """검증 결과 출력"""
        print("=" * 60)
        print("📊 검증 결과 요약")
        print("=" * 60)
        print("")

        # 오류
        if self.errors:
            print(f"❌ 오류 ({len(self.errors)}개):")
            for error in self.errors:
                print(f"   {error}")
            print("")

        # 경고
        if self.warnings:
            print(f"⚠️ 경고 ({len(self.warnings)}개):")
            for warning in self.warnings:
                print(f"   {warning}")
            print("")

        # 정보
        if self.info:
            print(f"✅ 정상 ({len(self.info)}개):")
            for info_msg in self.info:
                print(f"   {info_msg}")
            print("")

        # 종합 판정
        print("=" * 60)
        if not self.errors:
            print("✅ 전체 검증 통과!")
        else:
            print(f"❌ 검증 실패 ({len(self.errors)}개 오류)")
        print("=" * 60)


def main():
    """메인 함수"""
    # 인자 파싱
    if len(sys.argv) > 1:
        app_dir = sys.argv[1]
    else:
        app_dir = None

    # 검증 실행
    validator = AutoValidator(app_dir)
    success = validator.validate_all()

    # 종료 코드
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
