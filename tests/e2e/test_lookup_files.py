"""E2E tests for Splunk lookup CSV files validation."""

import csv
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SECURITY_ALERT_PATH = PROJECT_ROOT / "security_alert"
LOOKUPS_PATH = SECURITY_ALERT_PATH / "lookups"


class TestLookupDirectoryExists:

    def test_lookups_directory_exists(self):
        assert LOOKUPS_PATH.exists(), "lookups/ directory not found"
        assert LOOKUPS_PATH.is_dir(), "lookups must be a directory"


class TestLookupFilesExist:

    def get_lookup_files(self):
        if not LOOKUPS_PATH.exists():
            return []
        return list(LOOKUPS_PATH.glob("*.csv"))

    def test_lookup_files_present(self):
        files = self.get_lookup_files()
        assert len(files) > 0, "No lookup CSV files found"

    @pytest.fixture
    def lookup_files(self):
        return self.get_lookup_files()

    def test_all_lookups_are_csv(self, lookup_files):
        for f in lookup_files:
            assert f.suffix == ".csv", f"{f.name} is not a CSV file"


class TestLookupFileValidity:

    @pytest.fixture
    def lookup_files(self):
        if not LOOKUPS_PATH.exists():
            return []
        return list(LOOKUPS_PATH.glob("*.csv"))

    def test_csv_files_are_parseable(self, lookup_files):
        for csv_file in lookup_files:
            try:
                with open(csv_file, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    assert len(rows) >= 1, f"{csv_file.name} is empty"
            except csv.Error as e:
                pytest.fail(f"{csv_file.name} is not valid CSV: {e}")

    def test_csv_files_have_headers(self, lookup_files):
        for csv_file in lookup_files:
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                assert header is not None, f"{csv_file.name} has no header row"
                assert len(header) > 0, f"{csv_file.name} has empty header"

    def test_csv_rows_match_header_columns(self, lookup_files):
        for csv_file in lookup_files:
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header is None:
                    continue

                header_len = len(header)
                for i, row in enumerate(reader, start=2):
                    assert (
                        len(row) == header_len
                    ), f"{csv_file.name} row {i} has {len(row)} cols, expected {header_len}"


class TestAlertStateLookup:

    ALERT_STATE_FILE = LOOKUPS_PATH / "alert_state.csv"

    def test_alert_state_exists(self):
        if not self.ALERT_STATE_FILE.exists():
            pytest.skip("alert_state.csv not found")
        assert self.ALERT_STATE_FILE.exists()

    def test_alert_state_has_required_columns(self):
        if not self.ALERT_STATE_FILE.exists():
            pytest.skip("alert_state.csv not found")

        with open(self.ALERT_STATE_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            required = ["alert_id", "status", "updated_at"]
            for col in required:
                assert col in fieldnames, f"alert_state.csv missing column: {col}"


class TestFortigateLogidMap:

    LOGID_MAP_FILE = LOOKUPS_PATH / "fortigate_logid_notification_map.csv"

    def test_logid_map_exists(self):
        if not self.LOGID_MAP_FILE.exists():
            pytest.skip("fortigate_logid_notification_map.csv not found")
        assert self.LOGID_MAP_FILE.exists()

    def test_logid_map_has_required_columns(self):
        if not self.LOGID_MAP_FILE.exists():
            pytest.skip("fortigate_logid_notification_map.csv not found")

        with open(self.LOGID_MAP_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            required = ["logid", "category"]
            for col in required:
                assert col in fieldnames, f"logid map missing column: {col}"


class TestAutoResponseActionsLookup:

    ACTIONS_FILE = LOOKUPS_PATH / "auto_response_actions.csv"

    def test_actions_file_exists(self):
        if not self.ACTIONS_FILE.exists():
            pytest.skip("auto_response_actions.csv not found")
        assert self.ACTIONS_FILE.exists()

    def test_actions_have_required_columns(self):
        if not self.ACTIONS_FILE.exists():
            pytest.skip("auto_response_actions.csv not found")

        with open(self.ACTIONS_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            required = ["action_type"]
            for col in required:
                assert col in fieldnames, f"auto_response_actions missing column: {col}"


class TestStateTrackerLookups:

    def get_state_tracker_files(self):
        if not LOOKUPS_PATH.exists():
            return []
        return [f for f in LOOKUPS_PATH.glob("*_state_tracker.csv")]

    def test_state_trackers_exist(self):
        trackers = self.get_state_tracker_files()
        assert len(trackers) > 0, "No state tracker lookups found"

    def test_state_trackers_have_state_column(self):
        for tracker in self.get_state_tracker_files():
            with open(tracker, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or []
                state_cols = [c for c in fieldnames if "state" in c.lower()]
                assert len(state_cols) > 0, f"{tracker.name} has no state column"


class TestNoSensitiveDataInLookups:

    SENSITIVE_PATTERNS = [
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "credential",
    ]

    def test_no_sensitive_column_names(self):
        if not LOOKUPS_PATH.exists():
            pytest.skip("lookups/ not found")

        for csv_file in LOOKUPS_PATH.glob("*.csv"):
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, [])

                for col in header:
                    col_lower = col.lower()
                    for pattern in self.SENSITIVE_PATTERNS:
                        assert (
                            pattern not in col_lower
                        ), f"{csv_file.name} has sensitive column: {col}"
