"""
Comprehensive Dashboard Feature Tests for React Frontend.

This module provides unit-style tests for frontend components and features
that can run WITHOUT Playwright or a running frontend server.

Tests cover:
- Component structure validation
- API service patterns
- Zustand store actions
- Data transformation logic
- CSS/styling conventions
- Page routing configuration

Requires: pip install pytest
Does NOT require: playwright, running frontend server
"""

import pytest
import json
import re
import os
from pathlib import Path

# Frontend paths
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
SRC_DIR = FRONTEND_DIR / "src"


@pytest.fixture
def frontend_exists():
    """Skip tests if frontend directory doesn't exist."""
    if not FRONTEND_DIR.exists():
        pytest.skip("Frontend directory not found")
    return True


@pytest.fixture
def package_json(frontend_exists):
    """Load package.json."""
    pkg_path = FRONTEND_DIR / "package.json"
    if not pkg_path.exists():
        pytest.skip("package.json not found")
    with open(pkg_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def app_jsx_content(frontend_exists):
    """Load App.jsx content."""
    app_path = SRC_DIR / "App.jsx"
    if not app_path.exists():
        pytest.skip("App.jsx not found")
    return app_path.read_text()


# ============================================================================
# Test: Package Configuration
# ============================================================================

class TestPackageConfiguration:
    """Verify package.json configuration is correct."""

    def test_package_name_is_correct(self, package_json):
        """Package name should match project."""
        assert "name" in package_json
        assert "splunk" in package_json["name"].lower() or "fortianalyzer" in package_json["name"].lower()

    def test_required_dependencies_present(self, package_json):
        """Core dependencies should be present."""
        required_deps = ["react", "react-dom", "react-router-dom", "zustand", "recharts"]
        deps = package_json.get("dependencies", {})
        
        for dep in required_deps:
            assert dep in deps, f"Missing required dependency: {dep}"

    def test_react_version_is_18(self, package_json):
        """React should be version 18+."""
        deps = package_json.get("dependencies", {})
        react_version = deps.get("react", "")
        assert "18" in react_version, f"Expected React 18+, got {react_version}"

    def test_dev_dependencies_present(self, package_json):
        """Development dependencies should be present."""
        dev_deps = package_json.get("devDependencies", {})
        assert "vite" in dev_deps, "Vite should be in devDependencies"
        assert "eslint" in dev_deps, "ESLint should be in devDependencies"

    def test_scripts_defined(self, package_json):
        """Required npm scripts should be defined."""
        scripts = package_json.get("scripts", {})
        required_scripts = ["dev", "build", "lint"]
        
        for script in required_scripts:
            assert script in scripts, f"Missing script: {script}"

    def test_node_engine_requirement(self, package_json):
        """Node version requirement should be specified."""
        engines = package_json.get("engines", {})
        if "node" in engines:
            assert "18" in engines["node"], "Should require Node 18+"


# ============================================================================
# Test: Routing Configuration
# ============================================================================

class TestRoutingConfiguration:
    """Verify React Router routes are correctly configured."""

    EXPECTED_ROUTES = [
        "/",
        "/dashboard",
        "/security",
        "/correlation",
        "/alerts",
        "/threats",
        "/system",
    ]

    def test_app_jsx_exists(self, frontend_exists):
        """App.jsx should exist."""
        assert (SRC_DIR / "App.jsx").exists()

    def test_all_routes_defined(self, app_jsx_content):
        """All expected routes should be defined."""
        for route in self.EXPECTED_ROUTES:
            pattern = rf'path=["\']{re.escape(route)}["\']'
            assert re.search(pattern, app_jsx_content), f"Route {route} not found in App.jsx"

    def test_root_redirects_to_dashboard(self, app_jsx_content):
        """Root path should redirect to /dashboard."""
        assert 'Navigate to="/dashboard"' in app_jsx_content or \
               "Navigate to='/dashboard'" in app_jsx_content

    def test_layout_component_used(self, app_jsx_content):
        """Layout component should wrap routes."""
        assert "<Layout>" in app_jsx_content
        assert "</Layout>" in app_jsx_content

    def test_uses_browser_router(self, app_jsx_content):
        """Should use BrowserRouter for routing."""
        assert "BrowserRouter" in app_jsx_content or "Router" in app_jsx_content


# ============================================================================
# Test: Page Components
# ============================================================================

class TestPageComponents:
    """Verify all page components exist and have correct structure."""

    PAGES = [
        ("Dashboard.jsx", ["StatsCard", "EventsChart", "AlertsTable"]),
        ("SecurityOverview.jsx", []),
        ("CorrelationAnalysis.jsx", []),
        ("AlertManagement.jsx", []),
        ("ThreatIntelligence.jsx", []),
        ("SystemHealth.jsx", []),
    ]

    def test_all_page_files_exist(self, frontend_exists):
        """All page component files should exist."""
        pages_dir = SRC_DIR / "pages"
        
        for page_name, _ in self.PAGES:
            page_path = pages_dir / page_name
            assert page_path.exists(), f"Page component missing: {page_name}"

    @pytest.mark.parametrize("page_name,expected_components", PAGES)
    def test_page_imports_required_components(self, frontend_exists, page_name, expected_components):
        """Pages should import their required components."""
        page_path = SRC_DIR / "pages" / page_name
        if not page_path.exists():
            pytest.skip(f"{page_name} not found")
        
        content = page_path.read_text()
        
        for component in expected_components:
            assert component in content, f"{page_name} should import {component}"

    def test_dashboard_uses_zustand_store(self, frontend_exists):
        """Dashboard should use Zustand store."""
        dashboard = SRC_DIR / "pages" / "Dashboard.jsx"
        content = dashboard.read_text()
        
        assert "useStore" in content, "Dashboard should use useStore hook"
        assert "from '../store/store'" in content or "from \"../store/store\"" in content

    def test_dashboard_has_stats_grid(self, frontend_exists):
        """Dashboard should render stats-grid."""
        dashboard = SRC_DIR / "pages" / "Dashboard.jsx"
        content = dashboard.read_text()
        
        assert "stats-grid" in content, "Dashboard should have stats-grid class"

    def test_dashboard_fetches_data_on_mount(self, frontend_exists):
        """Dashboard should fetch data in useEffect."""
        dashboard = SRC_DIR / "pages" / "Dashboard.jsx"
        content = dashboard.read_text()
        
        assert "useEffect" in content
        assert "fetchEvents" in content or "fetchAlerts" in content


# ============================================================================
# Test: UI Components
# ============================================================================

class TestUIComponents:
    """Verify UI component structure and exports."""

    COMPONENTS = [
        ("components/Layout/Layout.jsx", ["function Layout", "export default Layout"]),
        ("components/Cards/StatsCard.jsx", ["function StatsCard", "export default StatsCard"]),
        ("components/Charts/EventsChart.jsx", ["function EventsChart", "export default EventsChart"]),
        ("components/Tables/AlertsTable.jsx", ["function AlertsTable", "export default AlertsTable"]),
    ]

    @pytest.mark.parametrize("component_path,patterns", COMPONENTS)
    def test_component_exists_and_has_correct_structure(self, frontend_exists, component_path, patterns):
        """Components should exist and have correct function/export structure."""
        full_path = SRC_DIR / component_path
        
        if not full_path.exists():
            pytest.skip(f"Component not found: {component_path}")
        
        content = full_path.read_text()
        
        for pattern in patterns:
            assert pattern in content, f"{component_path} should contain: {pattern}"

    def test_events_chart_uses_recharts(self, frontend_exists):
        """EventsChart should use Recharts library."""
        chart_path = SRC_DIR / "components/Charts/EventsChart.jsx"
        if not chart_path.exists():
            pytest.skip("EventsChart not found")
        
        content = chart_path.read_text()
        
        assert "recharts" in content
        assert "LineChart" in content or "BarChart" in content or "AreaChart" in content

    def test_alerts_table_handles_empty_state(self, frontend_exists):
        """AlertsTable should handle empty alerts array."""
        table_path = SRC_DIR / "components/Tables/AlertsTable.jsx"
        if not table_path.exists():
            pytest.skip("AlertsTable not found")
        
        content = table_path.read_text()
        
        # Should check for empty/null alerts
        assert "!alerts" in content or "alerts.length === 0" in content or "alerts?.length" in content

    def test_stats_card_accepts_required_props(self, frontend_exists):
        """StatsCard should accept title, value, trend props."""
        card_path = SRC_DIR / "components/Cards/StatsCard.jsx"
        if not card_path.exists():
            pytest.skip("StatsCard not found")
        
        content = card_path.read_text()
        
        # Check for prop destructuring or usage
        assert "title" in content
        assert "value" in content


# ============================================================================
# Test: API Service
# ============================================================================

class TestAPIService:
    """Verify API service configuration and endpoints."""

    EXPECTED_ENDPOINTS = [
        ("getEvents", "/events"),
        ("getStats", "/stats"),
        ("getAlerts", "/alerts"),
        ("getCorrelation", "/correlation"),
        ("getThreats", "/threats"),
    ]

    def test_api_file_exists(self, frontend_exists):
        """API service file should exist."""
        api_path = SRC_DIR / "services/api.js"
        assert api_path.exists(), "services/api.js should exist"

    def test_api_uses_fetch(self, frontend_exists):
        """API should use fetch for HTTP requests."""
        api_path = SRC_DIR / "services/api.js"
        content = api_path.read_text()
        
        assert "fetch" in content, "API should use fetch"

    @pytest.mark.parametrize("method_name,endpoint", EXPECTED_ENDPOINTS)
    def test_api_endpoint_defined(self, frontend_exists, method_name, endpoint):
        """API should define all required endpoints."""
        api_path = SRC_DIR / "services/api.js"
        content = api_path.read_text()
        
        assert method_name in content, f"API should define {method_name}"
        assert endpoint in content, f"API should use endpoint {endpoint}"

    def test_api_handles_errors(self, frontend_exists):
        """API should handle HTTP errors."""
        api_path = SRC_DIR / "services/api.js"
        content = api_path.read_text()
        
        assert "catch" in content or "try" in content, "API should handle errors"

    def test_api_exports_object(self, frontend_exists):
        """API should export api object."""
        api_path = SRC_DIR / "services/api.js"
        content = api_path.read_text()
        
        assert "export" in content and "api" in content


# ============================================================================
# Test: Zustand Store
# ============================================================================

class TestZustandStore:
    """Verify Zustand store configuration and actions."""

    EXPECTED_STATE = ["stats", "events", "alerts", "loading", "error"]
    EXPECTED_ACTIONS = ["fetchStats", "fetchEvents", "fetchAlerts"]

    def test_store_file_exists(self, frontend_exists):
        """Store file should exist."""
        store_path = SRC_DIR / "store/store.js"
        assert store_path.exists(), "store/store.js should exist"

    def test_store_uses_zustand(self, frontend_exists):
        """Store should use Zustand create function."""
        store_path = SRC_DIR / "store/store.js"
        content = store_path.read_text()
        
        assert "zustand" in content
        assert "create" in content

    def test_store_exports_use_store_hook(self, frontend_exists):
        """Store should export useStore hook."""
        store_path = SRC_DIR / "store/store.js"
        content = store_path.read_text()
        
        assert "export" in content and "useStore" in content

    @pytest.mark.parametrize("state_key", EXPECTED_STATE)
    def test_store_has_state_key(self, frontend_exists, state_key):
        """Store should have all required state keys."""
        store_path = SRC_DIR / "store/store.js"
        content = store_path.read_text()
        
        assert state_key in content, f"Store should have state: {state_key}"

    @pytest.mark.parametrize("action_name", EXPECTED_ACTIONS)
    def test_store_has_action(self, frontend_exists, action_name):
        """Store should have all required actions."""
        store_path = SRC_DIR / "store/store.js"
        content = store_path.read_text()
        
        assert action_name in content, f"Store should have action: {action_name}"

    def test_store_actions_are_async(self, frontend_exists):
        """Fetch actions should be async."""
        store_path = SRC_DIR / "store/store.js"
        content = store_path.read_text()
        
        # Check for async/await pattern
        assert "async" in content
        assert "await" in content

    def test_store_handles_loading_state(self, frontend_exists):
        """Store should set loading state during fetches."""
        store_path = SRC_DIR / "store/store.js"
        content = store_path.read_text()
        
        assert "loading: true" in content or "loading:true" in content or \
               "set({ loading: true" in content


# ============================================================================
# Test: WebSocket Hook
# ============================================================================

class TestWebSocketHook:
    """Verify WebSocket hook implementation."""

    def test_websocket_hook_exists(self, frontend_exists):
        """WebSocket hook file should exist."""
        hook_path = SRC_DIR / "hooks/useWebSocket.js"
        assert hook_path.exists(), "hooks/useWebSocket.js should exist"

    def test_websocket_exports_hook(self, frontend_exists):
        """Should export useWebSocket hook."""
        hook_path = SRC_DIR / "hooks/useWebSocket.js"
        content = hook_path.read_text()
        
        assert "export" in content and "useWebSocket" in content

    def test_websocket_has_connect_disconnect(self, frontend_exists):
        """Hook should provide connect and disconnect functions."""
        hook_path = SRC_DIR / "hooks/useWebSocket.js"
        content = hook_path.read_text()
        
        assert "connect" in content
        assert "disconnect" in content

    def test_app_uses_websocket_hook(self, app_jsx_content):
        """App should use WebSocket hook."""
        assert "useWebSocket" in app_jsx_content


# ============================================================================
# Test: CSS and Styling
# ============================================================================

class TestCSSAndStyling:
    """Verify CSS files exist and follow conventions."""

    def test_dashboard_has_css_file(self, frontend_exists):
        """Dashboard page should have associated CSS file."""
        css_path = SRC_DIR / "pages/Dashboard.css"
        assert css_path.exists(), "Dashboard.css should exist"

    def test_dashboard_css_has_required_classes(self, frontend_exists):
        """Dashboard CSS should define required classes."""
        css_path = SRC_DIR / "pages/Dashboard.css"
        if not css_path.exists():
            pytest.skip("Dashboard.css not found")
        
        content = css_path.read_text()
        
        required_classes = ["dashboard-page", "stats-grid", "page-header"]
        for cls in required_classes:
            assert cls in content, f"CSS should define .{cls}"

    def test_alerts_table_has_css(self, frontend_exists):
        """AlertsTable component should have CSS file."""
        css_path = SRC_DIR / "components/Tables/AlertsTable.css"
        assert css_path.exists(), "AlertsTable.css should exist"


# ============================================================================
# Test: Data Transformation Logic
# ============================================================================

class TestDataTransformation:
    """Test data transformation patterns used in components."""

    def test_events_chart_groups_by_time(self, frontend_exists):
        """EventsChart should group events by time buckets."""
        chart_path = SRC_DIR / "components/Charts/EventsChart.jsx"
        if not chart_path.exists():
            pytest.skip("EventsChart not found")
        
        content = chart_path.read_text()
        
        # Should have time bucketing logic
        assert "reduce" in content or "group" in content.lower()
        assert "timestamp" in content or "time" in content

    def test_alerts_table_has_severity_colors(self, frontend_exists):
        """AlertsTable should define severity color mapping."""
        table_path = SRC_DIR / "components/Tables/AlertsTable.jsx"
        if not table_path.exists():
            pytest.skip("AlertsTable not found")
        
        content = table_path.read_text()
        
        # Should map severity to colors
        assert "critical" in content
        assert "high" in content
        assert "#" in content  # Color hex codes


# ============================================================================
# Test: File Organization
# ============================================================================

class TestFileOrganization:
    """Verify frontend file organization follows conventions."""

    REQUIRED_DIRECTORIES = [
        "components",
        "pages",
        "store",
        "services",
        "hooks",
    ]

    def test_src_directory_exists(self, frontend_exists):
        """src directory should exist."""
        assert SRC_DIR.exists(), "frontend/src should exist"

    @pytest.mark.parametrize("directory", REQUIRED_DIRECTORIES)
    def test_required_directory_exists(self, frontend_exists, directory):
        """Required directories should exist in src."""
        dir_path = SRC_DIR / directory
        assert dir_path.exists(), f"src/{directory} should exist"

    def test_main_jsx_exists(self, frontend_exists):
        """main.jsx entry point should exist."""
        main_path = SRC_DIR / "main.jsx"
        assert main_path.exists(), "main.jsx should exist"

    def test_vite_config_exists(self, frontend_exists):
        """vite.config.js should exist."""
        config_path = FRONTEND_DIR / "vite.config.js"
        assert config_path.exists(), "vite.config.js should exist"


# ============================================================================
# Test: Integration Patterns
# ============================================================================

class TestIntegrationPatterns:
    """Verify frontend integrates correctly with backend."""

    def test_api_base_url_configurable(self, frontend_exists):
        """API base URL should be configurable via environment."""
        api_path = SRC_DIR / "services/api.js"
        content = api_path.read_text()
        
        # Should use Vite env variable
        assert "VITE_" in content or "import.meta.env" in content

    def test_app_fetches_stats_on_mount(self, app_jsx_content):
        """App should fetch stats on initial mount."""
        assert "fetchStats" in app_jsx_content
        assert "useEffect" in app_jsx_content

    def test_app_sets_up_polling(self, app_jsx_content):
        """App should set up polling interval for stats."""
        assert "setInterval" in app_jsx_content
        assert "clearInterval" in app_jsx_content  # Cleanup
