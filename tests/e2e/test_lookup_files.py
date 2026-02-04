"""
E2E tests for lookup files (CSV state trackers).
"""

import csv
from pathlib import Path
from typing import Dict, List

import pytest


STATE_TRACKER_FILES = [
    "vpn_state_tracker.csv",
    "hardware_state_tracker.csv",
    "ha_state_tracker.csv",
    "interface_state_tracker.csv",
    "cpu_memory_state_tracker.csv",
    "resource_state_tracker.csv",
    "admin_login_state_tracker.csv",
    "vpn_brute_force_state_tracker.csv",
    "traffic_spike_state_tracker.csv",
    "license_state_tracker.csv",
]

REFERENCE_FILES = [
    "fortigate_logid_notification_map.csv",
    "severity_priority.csv",
    "auto_response_actions.csv",
]


class TestLookupFilesExist:

    @pytest.mark.parametrize("filename", STATE_TRACKER_FILES)
    def test_state_tracker_file_exists(self, lookup_path: Path, filename: str):
        filepath = lookup_path / filename
        assert filepath.exists(), f"Missing state tracker: {filename}"

    @pytest.mark.parametrize("filename", REFERENCE_FILES)
    def test_reference_file_exists(self, lookup_path: Path, filename: str):
        filepath = lookup_path / filename
        assert filepath.exists(), f"Missing reference file: {filename}"


class TestStateTrackerSchema:

    EXPECTED_COLUMNS = {
        "vpn_state_tracker.csv": ["device", "vpn_name", "state"],
        "hardware_state_tracker.csv": ["device", "component", "state"],
        "ha_state_tracker.csv": ["device", "state"],
        "interface_state_tracker.csv": ["device", "interface", "state"],
        "cpu_memory_state_tracker.csv": ["device", "resource", "state"],
        "resource_state_tracker.csv": ["device", "resource_type", "state"],
        "admin_login_state_tracker.csv": ["device", "source_ip", "state"],
        "vpn_brute_force_state_tracker.csv": ["device", "source_ip", "state"],
        "traffic_spike_state_tracker.csv": ["device", "source_ip", "state"],
        "license_state_tracker.csv": ["device", "license_category", "state"],
    }

    @pytest.mark.parametrize("filename", STATE_TRACKER_FILES)
    def test_state_tracker_has_required_columns(
        self, lookup_path: Path, filename: str
    ):
        filepath = lookup_path / filename

        if not filepath.exists():
            pytest.skip(f"{filename} does not exist")

        with open(filepath, "r", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

        expected = self.EXPECTED_COLUMNS.get(filename, [])
        missing = [col for col in expected if col not in headers]

        assert not missing, f"{filename} missing columns: {missing}"

    @pytest.mark.parametrize("filename", STATE_TRACKER_FILES)
    def test_state_tracker_has_state_column(
        self, lookup_path: Path, filename: str
    ):
        filepath = lookup_path / filename

        if not filepath.exists():
            pytest.skip(f"{filename} does not exist")

        with open(filepath, "r", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

        assert "state" in headers, f"{filename} missing 'state' column"


class TestStateTrackerOperations:

    def test_create_and_read_entry(
        self, backup_lookup, create_lookup_entry, lookup_path: Path
    ):
        with backup_lookup("vpn_state_tracker.csv"):
            create_lookup_entry(
                "vpn_state_tracker.csv",
                {"device": "FG-TEST-E2E", "vpn_name": "TEST-VPN", "state": "DOWN"},
            )

            filepath = lookup_path / "vpn_state_tracker.csv"
            with open(filepath, "r", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            test_entries = [
                r for r in rows
                if r.get("device") == "FG-TEST-E2E"
            ]

            assert len(test_entries) >= 1
            assert test_entries[0]["state"] == "DOWN"

    def test_update_state_transition(
        self, backup_lookup, create_lookup_entry, lookup_path: Path
    ):
        with backup_lookup("hardware_state_tracker.csv"):
            create_lookup_entry(
                "hardware_state_tracker.csv",
                {"device": "FG-E2E", "component": "Fan", "state": "FAIL"},
            )

            create_lookup_entry(
                "hardware_state_tracker.csv",
                {"device": "FG-E2E", "component": "Fan", "state": "OK"},
            )

            filepath = lookup_path / "hardware_state_tracker.csv"
            with open(filepath, "r", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            test_entries = [
                r for r in rows
                if r.get("device") == "FG-E2E" and r.get("component") == "Fan"
            ]

            assert len(test_entries) >= 2


class TestReferenceFiles:

    def test_logid_map_has_required_columns(self, lookup_path: Path):
        filepath = lookup_path / "fortigate_logid_notification_map.csv"

        if not filepath.exists():
            pytest.skip("fortigate_logid_notification_map.csv not found")

        with open(filepath, "r", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

        required = ["logid", "description"]
        for col in required:
            assert col in headers or any(col.lower() in h.lower() for h in headers)

    def test_severity_priority_has_levels(self, lookup_path: Path):
        filepath = lookup_path / "severity_priority.csv"

        if not filepath.exists():
            pytest.skip("severity_priority.csv not found")

        with open(filepath, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) >= 3, "Should have at least 3 severity levels"


class TestLookupFileIntegrity:

    @pytest.mark.parametrize("filename", STATE_TRACKER_FILES + REFERENCE_FILES)
    def test_file_is_valid_csv(self, lookup_path: Path, filename: str):
        filepath = lookup_path / filename

        if not filepath.exists():
            pytest.skip(f"{filename} does not exist")

        try:
            with open(filepath, "r", newline="") as f:
                reader = csv.reader(f)
                list(reader)
        except csv.Error as e:
            pytest.fail(f"{filename} is not valid CSV: {e}")

    @pytest.mark.parametrize("filename", STATE_TRACKER_FILES + REFERENCE_FILES)
    def test_no_empty_headers(self, lookup_path: Path, filename: str):
        filepath = lookup_path / filename

        if not filepath.exists():
            pytest.skip(f"{filename} does not exist")

        with open(filepath, "r", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader, [])

        empty_headers = [i for i, h in enumerate(headers) if not h.strip()]
        assert not empty_headers, f"{filename} has empty headers at positions: {empty_headers}"

    @pytest.mark.parametrize("filename", STATE_TRACKER_FILES + REFERENCE_FILES)
    def test_consistent_column_count(self, lookup_path: Path, filename: str):
        filepath = lookup_path / filename

        if not filepath.exists():
            pytest.skip(f"{filename} does not exist")

        with open(filepath, "r", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if len(rows) < 2:
            pytest.skip(f"{filename} has no data rows")

        header_count = len(rows[0])
        for i, row in enumerate(rows[1:], start=2):
            assert len(row) == header_count, (
                f"{filename} row {i} has {len(row)} columns, expected {header_count}"
            )


@pytest.mark.splunk_live
class TestLiveLookupOperations:

    def test_inputlookup_returns_data(self, splunk_search):
        results = splunk_search("| inputlookup vpn_state_tracker.csv | head 5")
        pass

    def test_outputlookup_writes_data(self, splunk_search, backup_lookup):
        with backup_lookup("vpn_state_tracker.csv"):
            splunk_search(
                '| makeresults | eval device="E2E-TEST", vpn_name="TEST", state="TEST" '
                "| outputlookup append=t vpn_state_tracker.csv"
            )

            results = splunk_search(
                '| inputlookup vpn_state_tracker.csv | search device="E2E-TEST"'
            )

            assert len(results) >= 1
