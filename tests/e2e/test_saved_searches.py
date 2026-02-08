"""E2E tests for Splunk saved searches SPL validation."""

import configparser
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SECURITY_ALERT_PATH = PROJECT_ROOT / "security_alert"
DEFAULT_PATH = SECURITY_ALERT_PATH / "default"
SAVEDSEARCHES_PATH = DEFAULT_PATH / "savedsearches.conf"


class TestSavedSearchesFileExists:

    def test_savedsearches_conf_exists(self):
        assert SAVEDSEARCHES_PATH.exists(), "savedsearches.conf not found"


class TestSavedSearchesParsing:

    @pytest.fixture
    def saved_searches(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(SAVEDSEARCHES_PATH))
        return parser

    def test_has_saved_searches(self, saved_searches):
        sections = [s for s in saved_searches.sections() if s != "default"]
        assert len(sections) > 0, "No saved searches defined"


class TestSPLSyntax:

    VALID_SPL_COMMANDS = [
        "search",
        "index",
        "source",
        "sourcetype",
        "host",
        "stats",
        "count",
        "sum",
        "avg",
        "max",
        "min",
        "eval",
        "where",
        "table",
        "fields",
        "rename",
        "sort",
        "head",
        "tail",
        "dedup",
        "rex",
        "spath",
        "join",
        "lookup",
        "inputlookup",
        "outputlookup",
        "timechart",
        "chart",
        "top",
        "rare",
        "transaction",
        "streamstats",
        "eventstats",
        "tstats",
        "datamodel",
        "pivot",
        "append",
        "appendpipe",
        "multisearch",
        "map",
        "foreach",
        "return",
    ]

    @pytest.fixture
    def search_queries(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(SAVEDSEARCHES_PATH))

        queries = {}
        for section in parser.sections():
            if section == "default":
                continue
            if parser.has_option(section, "search"):
                queries[section] = parser.get(section, "search")
        return queries

    def test_searches_not_empty(self, search_queries):
        for name, query in search_queries.items():
            assert len(query.strip()) > 0, f"Search '{name}' has empty query"

    def test_searches_have_valid_commands(self, search_queries):
        for name, query in search_queries.items():
            query_lower = query.lower()
            has_valid = any(cmd in query_lower for cmd in self.VALID_SPL_COMMANDS)
            assert has_valid, f"Search '{name}' has no valid SPL command"

    def test_balanced_parentheses(self, search_queries):
        for name, query in search_queries.items():
            open_count = query.count("(")
            close_count = query.count(")")
            assert (
                open_count == close_count
            ), f"Search '{name}' has unbalanced parentheses: ({open_count} vs {close_count})"

    def test_balanced_brackets(self, search_queries):
        for name, query in search_queries.items():
            open_count = query.count("[")
            close_count = query.count("]")
            assert (
                open_count == close_count
            ), f"Search '{name}' has unbalanced brackets: [{open_count} vs {close_count}]"

    def test_balanced_quotes(self, search_queries):
        for name, query in search_queries.items():
            unescaped = re.sub(r'\\"', "", query)
            double_quotes = unescaped.count('"')
            assert (
                double_quotes % 2 == 0
            ), f"Search '{name}' has unbalanced double quotes"


class TestSavedSearchAlerts:

    @pytest.fixture
    def alert_searches(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(SAVEDSEARCHES_PATH))

        alerts = {}
        for section in parser.sections():
            if section == "default":
                continue
            if parser.has_option(section, "alert.track"):
                alerts[section] = dict(parser.items(section))
            elif parser.has_option(section, "action.slack"):
                alerts[section] = dict(parser.items(section))
        return alerts

    def test_alerts_have_cron(self, alert_searches):
        for name, config in alert_searches.items():
            has_cron = "cron_schedule" in config
            has_realtime = "dispatch.earliest_time" in config and "rt" in config.get(
                "dispatch.earliest_time", ""
            )
            assert has_cron or has_realtime, f"Alert '{name}' has no schedule"


class TestMacroUsage:

    @pytest.fixture
    def search_queries(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(SAVEDSEARCHES_PATH))

        queries = {}
        for section in parser.sections():
            if section == "default":
                continue
            if parser.has_option(section, "search"):
                queries[section] = parser.get(section, "search")
        return queries

    @pytest.fixture
    def defined_macros(self):
        macros_path = DEFAULT_PATH / "macros.conf"
        if not macros_path.exists():
            return set()

        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(macros_path))
        return set(parser.sections())

    def test_used_macros_are_defined(self, search_queries, defined_macros):
        macro_pattern = re.compile(r"`(\w+)(?:\([^)]*\))?`")

        for name, query in search_queries.items():
            used_macros = macro_pattern.findall(query)
            for macro in used_macros:
                base_macro = macro.split("(")[0]
                macro_variants = [
                    base_macro,
                    f"{base_macro}(1)",
                    f"{base_macro}(2)",
                    f"{base_macro}(3)",
                ]
                found = any(m in defined_macros for m in macro_variants)
                assert found, f"Search '{name}' uses undefined macro: {macro}"


class TestSearchSecurity:

    @pytest.fixture
    def search_queries(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(SAVEDSEARCHES_PATH))

        queries = {}
        for section in parser.sections():
            if section == "default":
                continue
            if parser.has_option(section, "search"):
                queries[section] = parser.get(section, "search")
        return queries

    def test_no_hardcoded_credentials(self, search_queries):
        patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]

        for name, query in search_queries.items():
            for pattern in patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                assert len(matches) == 0, f"Search '{name}' has hardcoded credential"
