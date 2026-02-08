# Archive - Legacy Dashboard Files

**Created**: 2025-10-24
**Purpose**: Archive of legacy/backup dashboard files after simplification

## Archived Files

### Studio Dashboards (JSON)
- `fortinet-management-dashboard.json` (37KB) - Original template with Slack controls
- `slack-toggle-control.json` (12KB) - Standalone Slack control dashboard
- `correlation-analysis-studio.json.backup` (22KB) - Backup before Slack removal

### Classic Dashboards (XML)
- `correlation-analysis.xml` (27KB) - Legacy XML correlation dashboard
- `slack-alert-control.xml` (10KB) - Legacy XML Slack control

## Active Dashboards

Use these instead:

### Studio (configs/dashboards/studio/)
- **`correlation-analysis-studio.json`** - Pure operational FMG/FAZ monitoring (18 visualizations)

### Classic XML (configs/dashboards/)
- **`fortigate-operations.xml`** - Firewall operations monitoring

## Migration Notes

**2025-10-24**: Simplified dashboard structure
- Removed Slack alert control features (moved to separate tool)
- Focused on pure operational monitoring
- Reduced from 21 to 18 visualizations
- Archived 5 legacy files
