#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Validator for Security Alert System
자동 검증 시스템: 룩업, SPL 문법, 설정 파일 검증
"""

import sys
import os
import json
import re
import csv
from pathlib import Path

class AutoValidator:
    """자동 검증 클래스"""

    def __init__(self, app_dir=None):
        """
        Args:
            app_dir: Splunk app 디렉토리 경로 (default: /opt/splunk/etc/apps/security_alert)
        """
        if app_dir is None:
            app_dir = '/opt/splunk/etc/apps/security_alert'
        self.app_dir = Path(app_dir)
        self.lookups_dir = self.app_dir / 'lookups'
        self.errors = []
        self.warnings = []
        self.info = []

    def validate_all(self):
        """전체 검증 실행"""
        sys.stderr.write("=" * 60 + "\n")
        sys.stderr.write("🔍 Security Alert System - Auto Validation\n")
        sys.stderr.write("=" * 60 + "\n")
        sys.stderr.write("\n")

        # 1. 룩업 CSV 파일 검증
        self.validate_lookups()

        # 2. transforms.conf 검증 (룩업 정의)
        self.validate_transforms_conf()

        # 3. props.conf 검증 (자동 룩업)
        self.validate_props_conf()

        # 4. savedsearches.conf 검증 (알림 정의)
        self.validate_savedsearches_conf()

        # 5. alert_actions.conf 검증 (Slack 설정)
        self.validate_alert_actions_conf()

        # 결과 출력
        self.print_results()

        # 검증 통과 여부 반환
        return len(self.errors) == 0

    def validate_lookups(self):
        """룩업 CSV 파일 검증"""
        sys.stderr.write("📚 [1/5] 룩업 CSV 파일 검증\n")
        sys.stderr.write("-" * 60 + "\n")

        if not self.lookups_dir.exists():
            self.errors.append(f"❌ 룩업 디렉토리 없음: {self.lookups_dir}")
            return

        # 필수 룩업 파일 목록
        required_lookups = [
            'fortigate_logid_notification_map.csv',
            'severity_priority.csv',
            'auto_response_actions.csv'
        ]

        # State tracker CSV 파일
        state_trackers = [
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

        # 필수 룩업 검증
        for lookup_file in required_lookups:
            lookup_path = self.lookups_dir / lookup_file
            if not lookup_path.exists():
                self.errors.append(f"❌ 필수 룩업 파일 없음: {lookup_file}")
            else:
                self.validate_csv_file(lookup_path)
                self.info.append(f"✅ {lookup_file} - OK")

        # State tracker 검증 (없으면 생성)
        for tracker_file in state_trackers:
            tracker_path = self.lookups_dir / tracker_file
            if not tracker_path.exists():
                # 자동 생성
                self.create_state_tracker(tracker_path)
                self.info.append(f"🆕 {tracker_file} - 자동 생성됨")
            else:
                self.info.append(f"✅ {tracker_file} - 존재")

        sys.stderr.write("\n")

    def validate_csv_file(self, csv_path):
        """CSV 파일 구조 검증"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                if not headers:
                    self.errors.append(f"❌ {csv_path.name}: 헤더가 없습니다")
                    return

                # 행 수 확인
                row_count = sum(1 for row in reader)
                if row_count == 0:
                    self.warnings.append(f"⚠️ {csv_path.name}: 데이터 행이 없습니다")

        except Exception as e:
            self.errors.append(f"❌ {csv_path.name}: CSV 읽기 실패 - {str(e)}")

    def create_state_tracker(self, tracker_path):
        """State tracker CSV 자동 생성"""
        # 기본 헤더
        headers = ['device', 'prev_state', 'current_state', 'last_change', '_key']

        try:
            with open(tracker_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            os.chmod(tracker_path, 0o644)
        except Exception as e:
            self.errors.append(f"❌ {tracker_path.name}: 자동 생성 실패 - {str(e)}")

    def validate_transforms_conf(self):
        """transforms.conf 검증 (룩업 정의)"""
        sys.stderr.write("🔧 [2/5] transforms.conf 검증\n")
        sys.stderr.write("-" * 60 + "\n")

        transforms_path = self.app_dir / 'default' / 'transforms.conf'
        if not transforms_path.exists():
            self.errors.append("❌ transforms.conf 파일이 없습니다")
            sys.stderr.write("\n")
            return

        # 필수 룩업 스탠자
        required_stanzas = [
            'fortigate_logid_lookup',
            'severity_priority_lookup',
            'auto_response_lookup',
            'vpn_state_tracker',
            'hardware_state_tracker'
        ]

        with open(transforms_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for stanza in required_stanzas:
            if f"[{stanza}]" in content:
                self.info.append(f"✅ [{stanza}] - 정의됨")
            else:
                self.errors.append(f"❌ [{stanza}] - 정의 없음")

        sys.stderr.write("\n")

    def validate_props_conf(self):
        """props.conf 검증 (자동 룩업)"""
        sys.stderr.write("⚙️ [3/5] props.conf 검증\n")
        sys.stderr.write("-" * 60 + "\n")

        props_path = self.app_dir / 'default' / 'props.conf'
        if not props_path.exists():
            self.errors.append("❌ props.conf 파일이 없습니다")
            sys.stderr.write("\n")
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

        sys.stderr.write("\n")

    def validate_savedsearches_conf(self):
        """savedsearches.conf 검증 (알림 정의)"""
        sys.stderr.write("🚨 [4/5] savedsearches.conf 검증\n")
        sys.stderr.write("-" * 60 + "\n")

        savedsearches_path = self.app_dir / 'default' / 'savedsearches.conf'
        if not savedsearches_path.exists():
            self.warnings.append("⚠️ savedsearches.conf 파일이 없습니다 (알림 없음)")
            sys.stderr.write("\n")
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

        sys.stderr.write("\n")

    def validate_spl_in_alert(self, content, alert_name):
        """알림 내 SPL 쿼리 기본 검증"""
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
        if not spl_query.startswith('index='):
            self.warnings.append(f"⚠️ {alert_name}: index 지정 권장")

        # 파이프 문법 검증
        if '|' in spl_query:
            # 기본 명령어 검증
            valid_commands = ['stats', 'eval', 'where', 'table', 'sort', 'head', 'tail', 'dedup', 'rex', 'rename']
            pipes = spl_query.split('|')
            for pipe in pipes[1:]:  # 첫 번째는 index 쿼리
                cmd = pipe.strip().split()[0]
                if cmd not in valid_commands and not cmd.startswith('lookup'):
                    self.warnings.append(f"⚠️ {alert_name}: 알 수 없는 SPL 명령어 '{cmd}'")

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
        sys.stderr.write("💬 [5/5] alert_actions.conf 검증\n")
        sys.stderr.write("-" * 60 + "\n")

        alert_actions_path = self.app_dir / 'default' / 'alert_actions.conf'
        if not alert_actions_path.exists():
            self.errors.append("❌ alert_actions.conf 파일이 없습니다")
            sys.stderr.write("\n")
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

        sys.stderr.write("\n")

    def print_results(self):
        """검증 결과 출력"""
        sys.stderr.write("=" * 60 + "\n")
        sys.stderr.write("📊 검증 결과 요약\n")
        sys.stderr.write("=" * 60 + "\n")
        sys.stderr.write("\n")

        # 오류
        if self.errors:
            sys.stderr.write(f"❌ 오류 ({len(self.errors)}개):\n")
            for error in self.errors:
                sys.stderr.write(f"   {error}\n")
            sys.stderr.write("\n")

        # 경고
        if self.warnings:
            sys.stderr.write(f"⚠️ 경고 ({len(self.warnings)}개):\n")
            for warning in self.warnings:
                sys.stderr.write(f"   {warning}\n")
            sys.stderr.write("\n")

        # 정보
        if self.info:
            sys.stderr.write(f"✅ 정상 ({len(self.info)}개):\n")
            for info_msg in self.info:
                sys.stderr.write(f"   {info_msg}\n")
            sys.stderr.write("\n")

        # 종합 판정
        sys.stderr.write("=" * 60 + "\n")
        if not self.errors:
            sys.stderr.write("✅ 전체 검증 통과!\n")
        else:
            sys.stderr.write(f"❌ 검증 실패 ({len(self.errors)}개 오류)\n")
        sys.stderr.write("=" * 60 + "\n")


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
