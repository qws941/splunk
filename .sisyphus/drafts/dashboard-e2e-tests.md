# Draft: Dashboard E2E Tests

## Requirements (confirmed)

- **Output file**: `tests/e2e/test_dashboard_xml.py`
- **Test scope**: 5 SimpleXML dashboard files (file-based validation only)
- **No live Splunk required**: Static analysis only
- **Follow existing patterns**: From `test_saved_searches.py` and `test_lookup_files.py`

## Dashboard Files to Test

1. `security_alert/default/data/ui/views/slack_test_dashboard.xml` (85 LOC)
2. `security_alert_user/default/data/ui/views/alert-management-dashboard.xml` (267 LOC)
3. `security_alert_user/default/data/ui/views/data-explorer-dashboard.xml` (155 LOC)
4. `configs/dashboards/alert-testing-dashboard.xml` (525 LOC)
5. `configs/dashboards/fortigate-production-alerts-dashboard.xml` (573 LOC)

## Research Findings

### Existing Test Patterns
- `conftest.py` provides: `project_root`, `security_alert_path`, `parse_conf_file`, `macros` fixtures
- Tests use `@pytest.mark.parametrize` for multiple items
- Class-based organization (`class TestXxx:`)
- Tests check structure, schema, required fields

### Dashboard Structure (from slack_test_dashboard.xml)
```xml
<form version="1.1" theme="dark">
  <label>Dashboard Title</label>
  <description>Optional description</description>
  <fieldset submitButton="true" autoRun="false">
    <input type="dropdown" token="token_name">
      <label>Input Label</label>
      <choice value="...">...</choice>
      <default>...</default>
    </input>
  </fieldset>
  <row>
    <panel>
      <title>Panel Title</title>
      <table>
        <search>
          <query>SPL query here</query>
          <earliest>...</earliest>
          <latest>...</latest>
        </search>
        <option name="drilldown">none</option>
      </table>
    </panel>
  </row>
</form>
```

### Macro References (from macros.conf)
Macros are defined as `[macro_name]` stanzas. In SPL they're referenced with backticks: `` `macro_name` ``

Key macros:
- `fortigate_index`
- `logids_config_change`, `logids_vpn_tunnel`, etc.
- `baseline_time_range`, `realtime_time_range`
- `cpu_high_threshold`, `memory_high_threshold`

### SPL Syntax Validation Points
- Balanced parentheses: `(` and `)`
- Balanced brackets: `[` and `]`
- Balanced backticks: `` ` `` (macros must be paired)
- Balanced quotes: `"` and `'`
- No unclosed pipes at end of query

## Test Categories (from user request)

1. **XML Well-formedness**: `ET.parse()` succeeds without exceptions
2. **Dashboard structure**: Root is `<form>` or `<dashboard>`, has version, label
3. **Panel completeness**: Each `<panel>` has `<title>`, visualization, and `<search>`
4. **SPL syntax validation**: Balanced brackets, backticks, parentheses
5. **Macro references**: Backtick macros exist in macros.conf
6. **Time picker consistency**: `$earliest$` and `$latest$` tokens used correctly
7. **Theme consistency**: `theme="dark"` recommended

## Technical Decisions

- Use `xml.etree.ElementTree` for parsing (stdlib, no extra deps)
- Create `dashboard_files()` fixture similar to `state_tracker_files()`
- Add `@pytest.mark.dashboard` marker for filtering
- Extract macro names with regex: `` `([a-z_]+)` ``
- Validate SPL with bracket-counting helper functions

## Scope Boundaries

### INCLUDE
- Static XML validation
- Structure verification
- SPL syntax checking (balanced delimiters)
- Macro reference validation against macros.conf
- Token usage validation

### EXCLUDE
- Live Splunk validation
- SPL semantic correctness (does query make sense)
- Actual query execution
- JavaScript/CSS validation in HTML panels

## Open Questions

None - all requirements are clear from context.
