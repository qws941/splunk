import os


def test_security_alert_bin_exists():
    bin_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "security_alert", "bin"
    )
    assert os.path.isdir(bin_dir), f"security_alert/bin/ not found at {bin_dir}"


def test_lookup_csvs_exist():
    lookups_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "security_alert", "lookups"
    )
    assert os.path.isdir(lookups_dir), f"security_alert/lookups/ not found"
    csv_files = [f for f in os.listdir(lookups_dir) if f.endswith(".csv")]
    assert len(csv_files) > 0, "No CSV lookup files found"
