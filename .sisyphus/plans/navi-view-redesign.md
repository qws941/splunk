# Navi View (Navigation) 전체 리디자인

## TL;DR

> **Quick Summary**: Complete redesign of React frontend navigation - replacing emoji icons with lucide-react, adding collapsible sidebar, nested menus, breadcrumbs, command palette (Cmd+K), responsive design, and comprehensive page content with new backend APIs.
> 
> **Deliverables**:
> - Modern navigation with SVG icons, collapsible sidebar, nested menus
> - Breadcrumb component with route awareness
> - Command palette (Cmd+K) for quick navigation
> - Responsive layout (mobile drawer, tablet collapse)
> - Enhanced 5 placeholder pages with real visualizations
> - New backend API endpoints for enhanced data
> - Vitest test infrastructure + component tests
> - Updated Splunk nav.xml to match React theme (#4ade80)
> 
> **Estimated Effort**: Large (3-4 days)
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4 → Task 11

---

## Context

### Original Request
Complete redesign of the Navi View (navigation) for Splunk Security Alert System React frontend with modern UI, collapsible sidebar, nested navigation, breadcrumbs, Cmd+K search, responsive design, and enhanced page content.

### Interview Summary
**Key Discussions**:
- **Page Content Depth**: FULL - new backend API endpoints + comprehensive visualizations
- **Animation Style**: Enterprise-friendly, Splunk-compatible (~200ms, subtle)
- **Color Theme**: Unify to React green (#4ade80), update Splunk nav.xml
- **Splunk Deep Links**: Via VITE_SPLUNK_BASE_URL environment variable
- **Test Strategy**: Set up Vitest, TDD for new components

**Research Findings**:
- Current Layout.jsx: 65 LOC with emoji icons, flat nav, no collapse
- Current Layout.css: 139 LOC, dark theme (#0f0f0f), no responsive
- 5 placeholder pages (29-36 LOC), 1 full dashboard (88 LOC)
- No test infrastructure exists
- Splunk nav.xml: 3 collections, 9 views, green #65A637
- Store has fetch* actions ready for expansion

### Metis Review (Self-Applied)
**Identified Gaps** (addressed):
- Browser compatibility: Assumed modern browsers (Chrome, Firefox, Edge, Safari latest)
- Responsive approach: Desktop-first, consistent with current design
- Backend scope: Limited to what's needed for 5 pages

---

## Work Objectives

### Core Objective
Transform the React frontend navigation from a basic emoji-icon flat menu into a professional, responsive, collapsible navigation system with nested menus, breadcrumbs, and command palette.

### Concrete Deliverables
- `frontend/src/components/Navigation/Sidebar.jsx` - Collapsible sidebar component
- `frontend/src/components/Navigation/NavItem.jsx` - Nested menu item component
- `frontend/src/components/Navigation/Breadcrumbs.jsx` - Route-aware breadcrumbs
- `frontend/src/components/Navigation/CommandPalette.jsx` - Cmd+K search modal
- `frontend/src/components/Navigation/MobileDrawer.jsx` - Mobile responsive drawer
- `frontend/src/hooks/useSidebarState.js` - LocalStorage sidebar state hook
- `frontend/src/hooks/useCommandPalette.js` - Keyboard shortcut hook
- Updated `frontend/src/components/Layout/Layout.jsx` - Refactored layout
- Updated `frontend/src/components/Layout/Layout.css` - Responsive styles
- Enhanced pages: SecurityOverview, CorrelationAnalysis, AlertManagement, ThreatIntelligence, SystemHealth
- New API endpoints in `backend/server.js`
- `frontend/vitest.config.js` - Test configuration
- `security_alert/default/data/ui/nav/default.xml` - Updated color

### Definition of Done
- [ ] `npm run dev` starts with no console errors
- [ ] `npm run build` completes successfully
- [ ] `npm run test` passes all tests
- [ ] Sidebar collapses/expands with state persisted across refresh
- [ ] Nested menus expand/collapse correctly
- [ ] Breadcrumbs show correct path on all routes
- [ ] Cmd+K opens command palette
- [ ] Mobile layout (< 768px) shows hamburger + drawer
- [ ] All 5 pages show real data visualizations

### Must Have
- lucide-react icons (tree-shakeable)
- Collapsible sidebar with localStorage persistence
- Nested navigation structure for sub-pages
- Breadcrumb component
- Command palette with Cmd+K / Ctrl+K
- Responsive breakpoints (desktop > 1024px, tablet 768-1024px, mobile < 768px)
- ~200ms CSS transitions
- All pages with loading states and error handling

### Must NOT Have (Guardrails)
- ❌ No new charting libraries (Recharts only per AGENTS.md)
- ❌ No Redux/Context (Zustand only per AGENTS.md)
- ❌ No complex fuzzy search in command palette (basic substring matching)
- ❌ No dark/light theme toggle (out of scope)
- ❌ No authentication system (out of scope)
- ❌ No internationalization (out of scope)
- ❌ No changes to bin/*.py files (Python Splunk handlers)
- ❌ No spring physics animations (keep enterprise-simple)

---

## Verification Strategy

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.
> Every criterion is executable by the agent using Playwright, Bash, or curl.

### Test Decision
- **Infrastructure exists**: NO
- **Automated tests**: YES (TDD)
- **Framework**: Vitest (Vite-native)

### Test Setup Task (Task 1)
- Install: `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`
- Config: Create `vitest.config.js`
- Verify: `npm run test` → shows help or passes
- Example: Create `src/__tests__/example.test.jsx`
- Verify: `npm run test` → 1 test passes

### Agent-Executed QA Scenarios
All tasks include Playwright-based verification for UI components.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
├── Task 1: Setup Vitest test infrastructure
├── Task 5: Install lucide-react dependency
└── Task 10: Backend API endpoint stubs

Wave 2 (After Wave 1):
├── Task 2: Sidebar state hook (useSidebarState)
├── Task 6: NavItem component with icons
└── Task 11: Backend API implementations

Wave 3 (After Wave 2):
├── Task 3: Collapsible Sidebar component
├── Task 7: Breadcrumbs component
├── Task 8: Command Palette component
└── Task 9: Mobile Drawer component

Wave 4 (After Wave 3):
├── Task 4: Layout.jsx refactor + Layout.css responsive
├── Task 12: SecurityOverview page
├── Task 13: CorrelationAnalysis page
├── Task 14: AlertManagement page
├── Task 15: ThreatIntelligence page
├── Task 16: SystemHealth page
└── Task 17: Splunk nav.xml color update

Wave 5 (After Wave 4):
└── Task 18: App.jsx route restructure + final integration

Critical Path: Task 1 → Task 2 → Task 3 → Task 4 → Task 18
Parallel Speedup: ~50% faster than sequential
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2,3,6,7,8,9 | 5, 10 |
| 2 | 1 | 3, 4 | 6, 11 |
| 3 | 2, 6 | 4 | 7, 8, 9 |
| 4 | 3, 7, 8, 9 | 18 | 12-17 |
| 5 | None | 6 | 1, 10 |
| 6 | 5 | 3 | 2, 11 |
| 7 | 1 | 4 | 3, 8, 9 |
| 8 | 1 | 4 | 3, 7, 9 |
| 9 | 1 | 4 | 3, 7, 8 |
| 10 | None | 11 | 1, 5 |
| 11 | 10 | 12-16 | 2, 6 |
| 12-16 | 11 | 18 | 4, each other |
| 17 | None | 18 | 12-16 |
| 18 | 4, 12-17 | None | None (final) |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Category |
|------|-------|-------------------|
| 1 | 1, 5, 10 | quick (setup tasks) |
| 2 | 2, 6, 11 | quick to visual-engineering |
| 3 | 3, 7, 8, 9 | visual-engineering |
| 4 | 4, 12-17 | visual-engineering |
| 5 | 18 | quick (integration) |

---

## TODOs

---

### Wave 1: Foundation Setup

---

- [ ] 1. Setup Vitest Test Infrastructure

  **What to do**:
  - Install Vitest and testing-library: `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`
  - Create `vitest.config.js` with jsdom environment
  - Add `"test": "vitest"` script to package.json
  - Create example test file to verify setup

  **Must NOT do**:
  - Don't install Jest (use Vitest for Vite)
  - Don't configure complex coverage yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple setup task with clear steps
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**:
    - `frontend-ui-ux`: No UI work in this task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 5, 10)
  - **Blocks**: Tasks 2, 3, 6, 7, 8, 9
  - **Blocked By**: None

  **References**:
  - `frontend/package.json:7-11` - Current scripts section
  - `frontend/vite.config.js` - Vite configuration for reference
  - https://vitest.dev/guide/ - Vitest setup guide

  **Acceptance Criteria**:

  **If TDD:**
  - [ ] vitest.config.js created with jsdom environment
  - [ ] package.json has "test": "vitest" script
  - [ ] `npm run test` → shows Vitest test runner
  - [ ] Example test passes: `src/__tests__/example.test.jsx`

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Vitest runs successfully
    Tool: Bash
    Preconditions: npm install completed
    Steps:
      1. Run: cd /home/jclee/dev/splunk/frontend && npm run test -- --run
      2. Assert: exit code 0
      3. Assert: stdout contains "pass" or "PASS"
    Expected Result: Vitest executes and finds tests
    Evidence: Terminal output captured
  ```

  **Commit**: YES
  - Message: `feat(frontend): setup vitest test infrastructure`
  - Files: `vitest.config.js`, `package.json`, `src/__tests__/example.test.jsx`
  - Pre-commit: `npm run test -- --run`

  **Estimated LOC**: +50

---

- [ ] 5. Install lucide-react Dependency

  **What to do**:
  - Install lucide-react: `npm install lucide-react`
  - Verify installation by checking package.json

  **Must NOT do**:
  - Don't install other icon libraries (heroicons, react-icons)
  - Don't add any components yet (just install)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single npm install command
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 10)
  - **Blocks**: Task 6
  - **Blocked By**: None

  **References**:
  - `frontend/package.json:13-19` - Dependencies section
  - https://lucide.dev/guide/packages/lucide-react - Installation guide

  **Acceptance Criteria**:
  - [ ] `lucide-react` in package.json dependencies
  - [ ] No npm install errors

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: lucide-react installed correctly
    Tool: Bash
    Preconditions: In frontend directory
    Steps:
      1. Run: cd /home/jclee/dev/splunk/frontend && cat package.json | grep lucide-react
      2. Assert: output contains "lucide-react"
      3. Run: ls node_modules/lucide-react/package.json
      4. Assert: file exists (exit code 0)
    Expected Result: Package installed and accessible
    Evidence: package.json grep output
  ```

  **Commit**: YES (group with Task 1)
  - Message: `feat(frontend): setup vitest and lucide-react dependencies`
  - Files: `package.json`, `package-lock.json`

  **Estimated LOC**: +2 (package.json only)

---

- [ ] 10. Backend API Endpoint Stubs

  **What to do**:
  - Add stub endpoints to `backend/server.js`:
    - `GET /api/security/overview` - Security metrics
    - `GET /api/security/events/detailed` - Detailed event list
    - `GET /api/correlation/analysis` - Correlation data
    - `GET /api/threats/detailed` - Threat intel details
    - `GET /api/system/health/detailed` - System health metrics
  - Return mock data structure (implement in Task 11)

  **Must NOT do**:
  - Don't implement actual Splunk queries yet (stubs only)
  - Don't break existing endpoints

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Adding route stubs with mock responses
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 5)
  - **Blocks**: Task 11
  - **Blocked By**: None

  **References**:
  - `backend/server.js` - Existing server (modern entry point per AGENTS.md)
  - `frontend/src/services/api.js` - Current API client patterns

  **Acceptance Criteria**:
  - [ ] All 5 new endpoints respond with 200 + mock JSON
  - [ ] Existing endpoints still work

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: New API stubs return mock data
    Tool: Bash (curl)
    Preconditions: Backend server running on localhost:3001
    Steps:
      1. curl -s http://localhost:3001/api/security/overview
      2. Assert: HTTP 200
      3. Assert: response is valid JSON
      4. curl -s http://localhost:3001/api/correlation/analysis
      5. Assert: HTTP 200
      6. curl -s http://localhost:3001/api/threats/detailed
      7. Assert: HTTP 200
      8. curl -s http://localhost:3001/api/system/health/detailed
      9. Assert: HTTP 200
    Expected Result: All endpoints return 200 with JSON
    Evidence: Response bodies saved

  Scenario: Existing endpoints still work
    Tool: Bash (curl)
    Preconditions: Backend server running
    Steps:
      1. curl -s http://localhost:3001/api/stats
      2. Assert: HTTP 200 (existing endpoint)
    Expected Result: No regression
    Evidence: Response body
  ```

  **Commit**: YES
  - Message: `feat(backend): add stub API endpoints for enhanced pages`
  - Files: `backend/server.js`
  - Pre-commit: `curl test endpoints`

  **Estimated LOC**: +80

---

### Wave 2: Core Hooks and Components

---

- [ ] 2. Create useSidebarState Hook

  **What to do**:
  - Create `frontend/src/hooks/useSidebarState.js`
  - Manage collapsed/expanded state with localStorage persistence
  - Key: `sidebar-collapsed`
  - Expose: `isCollapsed`, `toggle()`, `expand()`, `collapse()`
  - Write test first (TDD)

  **Must NOT do**:
  - Don't use Context API (Zustand pattern per AGENTS.md)
  - Don't store in Zustand global store (keep local to sidebar)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single hook file with tests
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 11)
  - **Blocks**: Tasks 3, 4
  - **Blocked By**: Task 1

  **References**:
  - `frontend/src/hooks/useWebSocket.js` - Existing hook pattern
  - `frontend/src/store/store.js` - State patterns (but don't use for this)

  **Acceptance Criteria**:

  **If TDD:**
  - [ ] Test file: `src/hooks/__tests__/useSidebarState.test.js`
  - [ ] Tests cover: initial state, toggle, persist to localStorage, restore from localStorage
  - [ ] `npm run test useSidebarState` → PASS

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Hook tests pass
    Tool: Bash
    Preconditions: Test infrastructure set up
    Steps:
      1. Run: cd /home/jclee/dev/splunk/frontend && npm run test -- --run useSidebarState
      2. Assert: exit code 0
      3. Assert: stdout contains "PASS" or all tests pass
    Expected Result: All hook tests pass
    Evidence: Test output

  Scenario: Hook persists state in localStorage
    Tool: Playwright
    Preconditions: Dev server running, hook integrated into test page
    Steps:
      1. Navigate to http://localhost:5173
      2. Execute JS: localStorage.getItem('sidebar-collapsed')
      3. Note initial value
      4. Click sidebar collapse button
      5. Execute JS: localStorage.getItem('sidebar-collapsed')
      6. Assert: value changed
      7. Reload page
      8. Assert: sidebar still in collapsed state
    Expected Result: State persists across reload
    Evidence: .sisyphus/evidence/task-2-localstorage.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add useSidebarState hook with localStorage persistence`
  - Files: `src/hooks/useSidebarState.js`, `src/hooks/__tests__/useSidebarState.test.js`
  - Pre-commit: `npm run test -- --run`

  **Estimated LOC**: +80

---

- [ ] 6. Create NavItem Component with Icons

  **What to do**:
  - Create `frontend/src/components/Navigation/NavItem.jsx`
  - Props: `icon` (lucide-react component), `label`, `path`, `children` (for nesting), `isCollapsed`
  - Support nested items with expand/collapse
  - Use lucide-react icons (Shield, LayoutDashboard, Link, Bell, Target, Settings, ChevronDown, ChevronRight)
  - Write test first (TDD)

  **Must NOT do**:
  - Don't use emoji icons
  - Don't add routing logic (just render, parent handles)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI component with icon integration
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Component styling and structure

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 2, 11)
  - **Blocks**: Task 3
  - **Blocked By**: Task 5

  **References**:
  - `frontend/src/components/Layout/Layout.jsx:45-54` - Current nav-link pattern
  - https://lucide.dev/icons - Icon names reference
  - `frontend/src/components/Layout/Layout.css:102-131` - Current nav styles

  **Acceptance Criteria**:

  **If TDD:**
  - [ ] Test file: `src/components/Navigation/__tests__/NavItem.test.jsx`
  - [ ] Tests cover: renders icon, renders label, collapsed mode shows icon only, nested expansion
  - [ ] `npm run test NavItem` → PASS

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: NavItem renders with lucide icon
    Tool: Playwright
    Preconditions: Component integrated in dev
    Steps:
      1. Navigate to http://localhost:5173
      2. Wait for: nav visible
      3. Assert: svg element exists within nav item (lucide renders as svg)
      4. Assert: No emoji characters in navigation
      5. Screenshot: .sisyphus/evidence/task-6-icons.png
    Expected Result: SVG icons visible, no emojis
    Evidence: .sisyphus/evidence/task-6-icons.png

  Scenario: Nested menu expands on click
    Tool: Playwright
    Preconditions: NavItem with children rendered
    Steps:
      1. Navigate to http://localhost:5173
      2. Find nav item with nested children (e.g., "Security")
      3. Assert: children not visible initially
      4. Click the nav item expand button
      5. Wait for: nested items visible (200ms transition)
      6. Assert: nested items now visible
      7. Screenshot: .sisyphus/evidence/task-6-nested.png
    Expected Result: Nested items expand with animation
    Evidence: .sisyphus/evidence/task-6-nested.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add NavItem component with lucide-react icons`
  - Files: `src/components/Navigation/NavItem.jsx`, `src/components/Navigation/NavItem.css`, `src/components/Navigation/__tests__/NavItem.test.jsx`
  - Pre-commit: `npm run test -- --run`

  **Estimated LOC**: +180

---

- [ ] 11. Backend API Implementations

  **What to do**:
  - Implement the 5 stub endpoints with real data structures:
    - `/api/security/overview`: Attack types breakdown, severity distribution, top sources
    - `/api/security/events/detailed`: Paginated events with filters
    - `/api/correlation/analysis`: Correlation rules, triggered counts, patterns
    - `/api/threats/detailed`: Threat intel with geo data, abuse scores, timelines
    - `/api/system/health/detailed`: Component status, metrics, uptime
  - Connect to existing data sources where available

  **Must NOT do**:
  - Don't modify existing endpoints
  - Don't add new database connections (use existing)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Backend endpoint implementation, straightforward
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 2, 6)
  - **Blocks**: Tasks 12-16
  - **Blocked By**: Task 10

  **References**:
  - `backend/server.js` - Existing endpoint patterns
  - `frontend/src/store/store.js:60-78` - Expected data shapes for correlation, threats

  **Acceptance Criteria**:
  - [ ] All 5 endpoints return structured data
  - [ ] Data shapes match frontend expectations
  - [ ] No errors on existing endpoints

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Security overview returns structured data
    Tool: Bash (curl)
    Preconditions: Backend server running
    Steps:
      1. curl -s http://localhost:3001/api/security/overview | jq '.'
      2. Assert: response has "attackTypes" array
      3. Assert: response has "severityDistribution" object
      4. Assert: response has "topSources" array
    Expected Result: Well-structured security data
    Evidence: Response JSON saved

  Scenario: Threats endpoint has geo data
    Tool: Bash (curl)
    Preconditions: Backend server running
    Steps:
      1. curl -s http://localhost:3001/api/threats/detailed | jq '.threats[0]'
      2. Assert: object has "ip", "country", "abuseScore" fields
    Expected Result: Threat objects have required fields
    Evidence: Response JSON saved
  ```

  **Commit**: YES
  - Message: `feat(backend): implement enhanced API endpoints for frontend pages`
  - Files: `backend/server.js`
  - Pre-commit: `curl test all endpoints`

  **Estimated LOC**: +250

---

### Wave 3: Navigation Components

---

- [ ] 3. Create Collapsible Sidebar Component

  **What to do**:
  - Create `frontend/src/components/Navigation/Sidebar.jsx`
  - Use `useSidebarState` hook for collapse state
  - Render `NavItem` components in hierarchical structure:
    ```
    Dashboard (LayoutDashboard icon)
    Security (Shield icon)
      ├── Overview
      ├── Alerts
      └── Splunk Dashboards → [deep links]
    Monitoring (Activity icon)
      ├── FortiGate
      ├── Correlation
      └── Threats
    System (Settings icon)
      └── Health
    ```
  - Collapse button in sidebar header
  - Collapsed width: 64px (icons only)
  - Expanded width: 240px
  - ~200ms CSS transition
  - Write test first (TDD)

  **Must NOT do**:
  - Don't implement mobile drawer here (Task 9)
  - Don't add command palette here (Task 8)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Complex UI component with state and transitions
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Component architecture and styling

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 7, 8, 9)
  - **Blocks**: Task 4
  - **Blocked By**: Tasks 2, 6

  **References**:
  - `frontend/src/hooks/useSidebarState.js` - Hook from Task 2
  - `frontend/src/components/Navigation/NavItem.jsx` - NavItem from Task 6
  - `frontend/src/components/Layout/Layout.jsx:44-55` - Current sidebar structure
  - `frontend/src/components/Layout/Layout.css:94-131` - Current sidebar styles

  **Acceptance Criteria**:

  **If TDD:**
  - [ ] Test file: `src/components/Navigation/__tests__/Sidebar.test.jsx`
  - [ ] Tests cover: renders all nav items, collapse button works, width changes on collapse
  - [ ] `npm run test Sidebar` → PASS

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Sidebar collapses and expands
    Tool: Playwright
    Preconditions: Dev server running with new Sidebar
    Steps:
      1. Navigate to http://localhost:5173
      2. Measure sidebar width: await page.locator('nav.sidebar').boundingBox()
      3. Assert: width approximately 240px
      4. Click collapse button: button[aria-label="Collapse sidebar"]
      5. Wait for: 250ms (transition)
      6. Measure sidebar width again
      7. Assert: width approximately 64px
      8. Assert: nav labels not visible
      9. Assert: icons still visible
      10. Screenshot: .sisyphus/evidence/task-3-collapsed.png
    Expected Result: Sidebar smoothly collapses to icon-only view
    Evidence: .sisyphus/evidence/task-3-collapsed.png

  Scenario: Nested menu navigation structure
    Tool: Playwright
    Preconditions: Sidebar rendered
    Steps:
      1. Navigate to http://localhost:5173
      2. Find "Security" nav item
      3. Click to expand
      4. Assert: "Overview", "Alerts" sub-items visible
      5. Click "Overview"
      6. Assert: URL is /security
      7. Screenshot: .sisyphus/evidence/task-3-nested.png
    Expected Result: Nested navigation works
    Evidence: .sisyphus/evidence/task-3-nested.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add collapsible Sidebar component with nested navigation`
  - Files: `src/components/Navigation/Sidebar.jsx`, `src/components/Navigation/Sidebar.css`, `src/components/Navigation/__tests__/Sidebar.test.jsx`
  - Pre-commit: `npm run test -- --run`

  **Estimated LOC**: +280

---

- [ ] 7. Create Breadcrumbs Component

  **What to do**:
  - Create `frontend/src/components/Navigation/Breadcrumbs.jsx`
  - Auto-generate from React Router location
  - Route map for labels: `/security` → "Security", `/security/alerts` → "Security / Alerts"
  - Clickable path segments (except current)
  - Show Home icon for root
  - Write test first (TDD)

  **Must NOT do**:
  - Don't hardcode breadcrumb data in each page
  - Don't add complex styling (keep minimal)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Router-aware UI component
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Component structure

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 3, 8, 9)
  - **Blocks**: Task 4
  - **Blocked By**: Task 1

  **References**:
  - `frontend/src/App.jsx:38-46` - Current route structure
  - https://reactrouter.com/en/main/hooks/use-location - useLocation hook

  **Acceptance Criteria**:

  **If TDD:**
  - [ ] Test file: `src/components/Navigation/__tests__/Breadcrumbs.test.jsx`
  - [ ] Tests cover: shows Home on root, shows path segments, clicking navigates
  - [ ] `npm run test Breadcrumbs` → PASS

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Breadcrumbs show current path
    Tool: Playwright
    Preconditions: Dev server running
    Steps:
      1. Navigate to http://localhost:5173/security
      2. Find breadcrumbs container: [aria-label="Breadcrumb"]
      3. Assert: contains "Home" or home icon
      4. Assert: contains "Security"
      5. Navigate to http://localhost:5173/alerts
      6. Assert: breadcrumb shows "Home / Alerts"
      7. Screenshot: .sisyphus/evidence/task-7-breadcrumbs.png
    Expected Result: Breadcrumbs reflect current route
    Evidence: .sisyphus/evidence/task-7-breadcrumbs.png

  Scenario: Breadcrumb segment is clickable
    Tool: Playwright
    Preconditions: On a nested page
    Steps:
      1. Navigate to http://localhost:5173/alerts
      2. Click "Home" in breadcrumb
      3. Assert: URL is now /dashboard
    Expected Result: Navigation works from breadcrumb
    Evidence: URL change confirmed
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Breadcrumbs component with route awareness`
  - Files: `src/components/Navigation/Breadcrumbs.jsx`, `src/components/Navigation/Breadcrumbs.css`, `src/components/Navigation/__tests__/Breadcrumbs.test.jsx`
  - Pre-commit: `npm run test -- --run`

  **Estimated LOC**: +150

---

- [ ] 8. Create Command Palette Component

  **What to do**:
  - Create `frontend/src/components/Navigation/CommandPalette.jsx`
  - Create `frontend/src/hooks/useCommandPalette.js`
  - Global keyboard shortcut: Cmd+K (Mac) / Ctrl+K (Windows)
  - Modal overlay with search input
  - Search through navigation items + Splunk deep links
  - Basic substring matching (not fuzzy)
  - Navigate on selection
  - Write test first (TDD)

  **Must NOT do**:
  - Don't implement fuzzy search (basic substring only)
  - Don't add recent searches or history

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Modal with keyboard handling
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Modal UI and keyboard UX

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 3, 7, 9)
  - **Blocks**: Task 4
  - **Blocked By**: Task 1

  **References**:
  - `frontend/src/components/Layout/Layout.jsx` - Where to mount
  - Splunk nav structure from `security_alert/default/data/ui/nav/default.xml:4-20`

  **Acceptance Criteria**:

  **If TDD:**
  - [ ] Test file: `src/components/Navigation/__tests__/CommandPalette.test.jsx`
  - [ ] Tests cover: opens on Cmd+K, closes on Escape, filters results, navigates on select
  - [ ] `npm run test CommandPalette` → PASS

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Cmd+K opens command palette
    Tool: Playwright
    Preconditions: Dev server running
    Steps:
      1. Navigate to http://localhost:5173
      2. Press: Meta+K (or Control+K)
      3. Wait for: modal visible
      4. Assert: input field focused
      5. Assert: overlay visible
      6. Screenshot: .sisyphus/evidence/task-8-palette-open.png
    Expected Result: Command palette opens with keyboard shortcut
    Evidence: .sisyphus/evidence/task-8-palette-open.png

  Scenario: Search filters navigation items
    Tool: Playwright
    Preconditions: Command palette open
    Steps:
      1. Navigate to http://localhost:5173
      2. Press: Meta+K
      3. Type: "sec"
      4. Wait for: results to filter
      5. Assert: "Security" visible in results
      6. Assert: results count reduced from initial
      7. Screenshot: .sisyphus/evidence/task-8-search.png
    Expected Result: Results filtered by search term
    Evidence: .sisyphus/evidence/task-8-search.png

  Scenario: Selecting item navigates
    Tool: Playwright
    Preconditions: Command palette open with results
    Steps:
      1. Open command palette
      2. Type: "alert"
      3. Click first result or press Enter
      4. Assert: modal closes
      5. Assert: URL contains "alert"
    Expected Result: Navigation happens on selection
    Evidence: URL change confirmed

  Scenario: Escape closes palette
    Tool: Playwright
    Preconditions: Command palette open
    Steps:
      1. Open command palette
      2. Press: Escape
      3. Assert: modal not visible
    Expected Result: Modal closes on Escape
    Evidence: Modal hidden confirmed
  ```

  **Commit**: YES
  - Message: `feat(frontend): add CommandPalette with Cmd+K shortcut`
  - Files: `src/components/Navigation/CommandPalette.jsx`, `src/components/Navigation/CommandPalette.css`, `src/hooks/useCommandPalette.js`, `src/components/Navigation/__tests__/CommandPalette.test.jsx`
  - Pre-commit: `npm run test -- --run`

  **Estimated LOC**: +250

---

- [ ] 9. Create Mobile Drawer Component

  **What to do**:
  - Create `frontend/src/components/Navigation/MobileDrawer.jsx`
  - Render same nav structure as Sidebar
  - Slide-in from left as overlay
  - Hamburger menu button in header (visible < 768px)
  - Close on backdrop click or route change
  - ~200ms slide transition
  - Write test first (TDD)

  **Must NOT do**:
  - Don't duplicate nav structure code (import from shared config)
  - Don't show on desktop (CSS media query hide)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Mobile-first responsive component
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Mobile drawer patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 3, 7, 8)
  - **Blocks**: Task 4
  - **Blocked By**: Task 1

  **References**:
  - `frontend/src/components/Navigation/Sidebar.jsx` - Share nav config
  - `frontend/src/components/Layout/Layout.css` - Current layout styles

  **Acceptance Criteria**:

  **If TDD:**
  - [ ] Test file: `src/components/Navigation/__tests__/MobileDrawer.test.jsx`
  - [ ] Tests cover: hidden on desktop, visible on hamburger click, closes on nav
  - [ ] `npm run test MobileDrawer` → PASS

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Hamburger shows on mobile viewport
    Tool: Playwright
    Preconditions: Dev server running
    Steps:
      1. Set viewport: 375x667 (mobile)
      2. Navigate to http://localhost:5173
      3. Assert: hamburger button visible (button[aria-label="Open menu"])
      4. Assert: sidebar NOT visible
      5. Screenshot: .sisyphus/evidence/task-9-mobile.png
    Expected Result: Mobile layout with hamburger menu
    Evidence: .sisyphus/evidence/task-9-mobile.png

  Scenario: Drawer opens and closes
    Tool: Playwright
    Preconditions: Mobile viewport
    Steps:
      1. Set viewport: 375x667
      2. Navigate to http://localhost:5173
      3. Click hamburger button
      4. Wait for: drawer slide-in animation (200ms)
      5. Assert: drawer visible
      6. Assert: backdrop overlay visible
      7. Click backdrop
      8. Wait for: drawer slide-out (200ms)
      9. Assert: drawer NOT visible
      10. Screenshot: .sisyphus/evidence/task-9-drawer.png
    Expected Result: Drawer animates open/close
    Evidence: .sisyphus/evidence/task-9-drawer.png

  Scenario: Drawer closes on route change
    Tool: Playwright
    Preconditions: Mobile viewport, drawer open
    Steps:
      1. Set viewport: 375x667
      2. Open drawer
      3. Click "Dashboard" nav item
      4. Assert: drawer closes
      5. Assert: URL is /dashboard
    Expected Result: Navigation closes drawer
    Evidence: URL and drawer state confirmed
  ```

  **Commit**: YES
  - Message: `feat(frontend): add MobileDrawer for responsive navigation`
  - Files: `src/components/Navigation/MobileDrawer.jsx`, `src/components/Navigation/MobileDrawer.css`, `src/components/Navigation/__tests__/MobileDrawer.test.jsx`
  - Pre-commit: `npm run test -- --run`

  **Estimated LOC**: +200

---

### Wave 4: Integration and Pages

---

- [ ] 4. Refactor Layout.jsx and Layout.css

  **What to do**:
  - Refactor `frontend/src/components/Layout/Layout.jsx`:
    - Remove old emoji navigation
    - Import and use new Sidebar component
    - Add Breadcrumbs to content header
    - Add CommandPalette mount
    - Add MobileDrawer for responsive
    - Adjust grid for collapsed sidebar width
  - Refactor `frontend/src/components/Layout/Layout.css`:
    - Responsive breakpoints (1024px, 768px)
    - Sidebar width CSS variable: `--sidebar-width: 240px` / `--sidebar-width-collapsed: 64px`
    - ~200ms transitions on layout changes
    - Hide sidebar on mobile (drawer replaces it)
  - Update color variable to #4ade80 (already in use, confirm consistency)

  **Must NOT do**:
  - Don't change header design dramatically (keep current structure)
  - Don't remove status indicator or stats from header

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Major layout refactor with responsive CSS
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Layout architecture and responsive design

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 12-17)
  - **Blocks**: Task 18
  - **Blocked By**: Tasks 3, 7, 8, 9

  **References**:
  - `frontend/src/components/Layout/Layout.jsx:1-65` - Current layout (full)
  - `frontend/src/components/Layout/Layout.css:1-139` - Current styles (full)
  - `frontend/src/components/Navigation/Sidebar.jsx` - New sidebar from Task 3
  - `frontend/src/components/Navigation/Breadcrumbs.jsx` - From Task 7
  - `frontend/src/components/Navigation/CommandPalette.jsx` - From Task 8
  - `frontend/src/components/Navigation/MobileDrawer.jsx` - From Task 9

  **Acceptance Criteria**:
  - [ ] Sidebar integrates smoothly
  - [ ] Breadcrumbs visible in content area
  - [ ] Cmd+K works globally
  - [ ] Mobile layout shows hamburger + drawer
  - [ ] Collapse transition animates grid
  - [ ] `npm run build` succeeds
  - [ ] `npm run lint` passes

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Full layout renders correctly
    Tool: Playwright
    Preconditions: Dev server running
    Steps:
      1. Navigate to http://localhost:5173
      2. Assert: sidebar visible (nav.sidebar or equivalent)
      3. Assert: breadcrumbs visible
      4. Assert: header with stats visible
      5. Assert: content area visible
      6. Screenshot: .sisyphus/evidence/task-4-layout.png
    Expected Result: All layout components render
    Evidence: .sisyphus/evidence/task-4-layout.png

  Scenario: Responsive at tablet breakpoint
    Tool: Playwright
    Preconditions: Dev server running
    Steps:
      1. Set viewport: 900x768 (tablet)
      2. Navigate to http://localhost:5173
      3. Assert: sidebar collapsed by default OR hamburger visible
      4. Screenshot: .sisyphus/evidence/task-4-tablet.png
    Expected Result: Tablet-appropriate layout
    Evidence: .sisyphus/evidence/task-4-tablet.png

  Scenario: Layout transition on sidebar collapse
    Tool: Playwright
    Preconditions: Desktop viewport
    Steps:
      1. Navigate to http://localhost:5173
      2. Record sidebar width
      3. Click collapse button
      4. Wait for: 250ms
      5. Record new sidebar width
      6. Assert: content area expanded
      7. Assert: no layout jumping (smooth transition)
    Expected Result: Smooth layout transition
    Evidence: Width measurements
  ```

  **Commit**: YES
  - Message: `refactor(frontend): integrate navigation components into Layout`
  - Files: `src/components/Layout/Layout.jsx`, `src/components/Layout/Layout.css`
  - Pre-commit: `npm run lint && npm run build`

  **Estimated LOC**: +100 (net change, some removal)

---

- [ ] 12. Enhance SecurityOverview Page

  **What to do**:
  - Refactor `frontend/src/pages/SecurityOverview.jsx`:
    - Remove emoji from header
    - Fetch from `/api/security/overview` endpoint
    - Add charts: Attack type pie chart, Severity bar chart
    - Add table: Top attack sources
    - Loading states with skeleton
    - Error handling with retry
  - Update `frontend/src/services/api.js` with new endpoint
  - Add to store if needed

  **Must NOT do**:
  - Don't add new chart library (Recharts only)
  - Don't change page route

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Page with charts and data visualization
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Dashboard page design

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 4, 13-17)
  - **Blocks**: Task 18
  - **Blocked By**: Task 11

  **References**:
  - `frontend/src/pages/SecurityOverview.jsx:1-29` - Current minimal page
  - `frontend/src/pages/Dashboard.jsx:1-88` - Full page example pattern
  - `frontend/src/components/Charts/EventsChart.jsx` - Recharts pattern

  **Acceptance Criteria**:
  - [ ] Page loads data from new API
  - [ ] Pie chart shows attack types
  - [ ] Bar chart shows severity distribution
  - [ ] Loading skeleton during fetch
  - [ ] Error state with retry button

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: SecurityOverview shows charts
    Tool: Playwright
    Preconditions: Dev server + backend running
    Steps:
      1. Navigate to http://localhost:5173/security
      2. Wait for: loading skeleton to disappear OR data to load
      3. Assert: Recharts SVG element exists (attack type chart)
      4. Assert: Table with source IPs exists
      5. Assert: No emoji in h2 header
      6. Screenshot: .sisyphus/evidence/task-12-security.png
    Expected Result: Full security overview page
    Evidence: .sisyphus/evidence/task-12-security.png

  Scenario: Loading state shows skeleton
    Tool: Playwright
    Preconditions: Dev server running, backend slow or mocked
    Steps:
      1. Navigate to http://localhost:5173/security
      2. Assert: skeleton loader visible initially
      3. Wait for: data to load
      4. Assert: skeleton replaced with content
    Expected Result: Loading UX works
    Evidence: Visual transition observed
  ```

  **Commit**: YES
  - Message: `feat(frontend): enhance SecurityOverview page with visualizations`
  - Files: `src/pages/SecurityOverview.jsx`, `src/pages/SecurityOverview.css`, `src/services/api.js`
  - Pre-commit: `npm run lint`

  **Estimated LOC**: +200

---

- [ ] 13. Enhance CorrelationAnalysis Page

  **What to do**:
  - Refactor `frontend/src/pages/CorrelationAnalysis.jsx`:
    - Remove emoji from header
    - Fetch from `/api/correlation/analysis` endpoint
    - Add correlation rules table with trigger counts
    - Add pattern detection visualization
    - Time range selector
    - Loading and error states

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 4, 12, 14-17)
  - **Blocks**: Task 18
  - **Blocked By**: Task 11

  **References**:
  - `frontend/src/pages/CorrelationAnalysis.jsx:1-33` - Current page
  - `frontend/src/store/store.js:60-68` - fetchCorrelation pattern

  **Acceptance Criteria**:
  - [ ] Correlation rules table with sorting
  - [ ] Pattern visualization
  - [ ] Time range filter works

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: CorrelationAnalysis shows rules table
    Tool: Playwright
    Preconditions: Dev server + backend running
    Steps:
      1. Navigate to http://localhost:5173/correlation
      2. Wait for: table to load
      3. Assert: table header has "Rule Name", "Triggered", "Score" columns
      4. Assert: at least 1 row of data
      5. Screenshot: .sisyphus/evidence/task-13-correlation.png
    Expected Result: Correlation page with data table
    Evidence: .sisyphus/evidence/task-13-correlation.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): enhance CorrelationAnalysis page`
  - Files: `src/pages/CorrelationAnalysis.jsx`, `src/pages/CorrelationAnalysis.css`

  **Estimated LOC**: +180

---

- [ ] 14. Enhance AlertManagement Page

  **What to do**:
  - Refactor `frontend/src/pages/AlertManagement.jsx`:
    - Remove emoji from header
    - Add filter controls (severity, status, time range)
    - Improve AlertsTable with sorting, pagination
    - Add alert detail modal on row click
    - Add acknowledge action inline

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 4, 12, 13, 15-17)
  - **Blocks**: Task 18
  - **Blocked By**: Task 11

  **References**:
  - `frontend/src/pages/AlertManagement.jsx:1-28` - Current page
  - `frontend/src/components/Tables/AlertsTable.jsx` - Existing table
  - `frontend/src/store/store.js:49-57` - acknowledgeAlert action

  **Acceptance Criteria**:
  - [ ] Filter controls for severity/status
  - [ ] Sortable columns
  - [ ] Alert detail modal works
  - [ ] Acknowledge button updates state

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: Alert filters work
    Tool: Playwright
    Preconditions: Dev server + backend running with alerts
    Steps:
      1. Navigate to http://localhost:5173/alerts
      2. Count initial rows
      3. Select "Critical" filter
      4. Assert: row count reduced or shows only critical
      5. Screenshot: .sisyphus/evidence/task-14-filters.png
    Expected Result: Filtering reduces visible alerts
    Evidence: .sisyphus/evidence/task-14-filters.png

  Scenario: Alert detail modal opens
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:5173/alerts
      2. Click first alert row
      3. Wait for: modal visible
      4. Assert: modal shows alert details
      5. Press: Escape
      6. Assert: modal closes
    Expected Result: Detail modal interaction works
    Evidence: Modal state confirmed
  ```

  **Commit**: YES
  - Message: `feat(frontend): enhance AlertManagement page with filters and detail modal`
  - Files: `src/pages/AlertManagement.jsx`, `src/pages/AlertManagement.css`

  **Estimated LOC**: +220

---

- [ ] 15. Enhance ThreatIntelligence Page

  **What to do**:
  - Refactor `frontend/src/pages/ThreatIntelligence.jsx`:
    - Remove emoji from header
    - Fetch from `/api/threats/detailed` endpoint
    - Add threat table with IP, country, abuse score
    - Add geo distribution chart (by country)
    - Add threat detail panel

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 4, 12-14, 16, 17)
  - **Blocks**: Task 18
  - **Blocked By**: Task 11

  **References**:
  - `frontend/src/pages/ThreatIntelligence.jsx:1-33` - Current page
  - `frontend/src/store/store.js:71-78` - fetchThreats pattern

  **Acceptance Criteria**:
  - [ ] Threat table with sortable columns
  - [ ] Geo distribution bar chart
  - [ ] Abuse score color coding

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: ThreatIntelligence shows geo chart
    Tool: Playwright
    Preconditions: Dev server + backend running
    Steps:
      1. Navigate to http://localhost:5173/threats
      2. Wait for: data to load
      3. Assert: bar chart for country distribution visible
      4. Assert: threat table has IP column
      5. Screenshot: .sisyphus/evidence/task-15-threats.png
    Expected Result: Threat page with geo visualization
    Evidence: .sisyphus/evidence/task-15-threats.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): enhance ThreatIntelligence page with geo visualization`
  - Files: `src/pages/ThreatIntelligence.jsx`, `src/pages/ThreatIntelligence.css`

  **Estimated LOC**: +190

---

- [ ] 16. Enhance SystemHealth Page

  **What to do**:
  - Refactor `frontend/src/pages/SystemHealth.jsx`:
    - Remove emoji from header and status indicators
    - Fetch from `/api/system/health/detailed` endpoint
    - Add component status cards (FortiAnalyzer, Splunk, Slack, WebSocket)
    - Add metrics: uptime, processed count, error rate
    - Add health history chart (last 24h)
    - Replace ✅❌ with lucide-react CheckCircle/XCircle icons

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 4, 12-15, 17)
  - **Blocks**: Task 18
  - **Blocked By**: Task 11

  **References**:
  - `frontend/src/pages/SystemHealth.jsx:1-36` - Current page
  - `frontend/src/store/store.js:5,16` - wsConnected state

  **Acceptance Criteria**:
  - [ ] Component status cards with icons (not emoji)
  - [ ] Metrics display with proper formatting
  - [ ] Health history line chart

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: SystemHealth shows status icons
    Tool: Playwright
    Preconditions: Dev server running
    Steps:
      1. Navigate to http://localhost:5173/system
      2. Assert: NO emoji characters (✅❌) visible
      3. Assert: SVG icons visible for status
      4. Assert: metrics cards visible
      5. Screenshot: .sisyphus/evidence/task-16-system.png
    Expected Result: System health page with SVG icons
    Evidence: .sisyphus/evidence/task-16-system.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): enhance SystemHealth page with metrics and icons`
  - Files: `src/pages/SystemHealth.jsx`, `src/pages/SystemHealth.css`

  **Estimated LOC**: +180

---

- [ ] 17. Update Splunk nav.xml Color

  **What to do**:
  - Update `security_alert/default/data/ui/nav/default.xml`:
    - Change `color="#65A637"` to `color="#4ade80"`
  - Verify XML validity

  **Must NOT do**:
  - Don't change navigation structure
  - Don't add new views

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single line XML edit
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 4, 12-16)
  - **Blocks**: Task 18
  - **Blocked By**: None

  **References**:
  - `security_alert/default/data/ui/nav/default.xml:1` - Color attribute line

  **Acceptance Criteria**:
  - [ ] Color value is #4ade80
  - [ ] XML is valid (no syntax errors)

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: nav.xml has updated color
    Tool: Bash
    Steps:
      1. grep "color" /home/jclee/dev/splunk/security_alert/default/data/ui/nav/default.xml
      2. Assert: output contains "#4ade80"
      3. Assert: output does NOT contain "#65A637"
    Expected Result: Color updated
    Evidence: grep output

  Scenario: XML is valid
    Tool: Bash
    Steps:
      1. xmllint --noout /home/jclee/dev/splunk/security_alert/default/data/ui/nav/default.xml
      2. Assert: exit code 0
    Expected Result: Valid XML
    Evidence: No errors from xmllint
  ```

  **Commit**: YES
  - Message: `style(splunk): update nav.xml color to match React theme`
  - Files: `security_alert/default/data/ui/nav/default.xml`
  - Pre-commit: `xmllint --noout`

  **Estimated LOC**: +1

---

### Wave 5: Final Integration

---

- [ ] 18. App.jsx Route Restructure and Final Integration

  **What to do**:
  - Update `frontend/src/App.jsx`:
    - Add nested routes if needed for breadcrumb consistency
    - Ensure all pages work with new Layout
    - Add any missing route redirects
  - Create `.env.example` with `VITE_SPLUNK_BASE_URL` template
  - Update `frontend/src/services/api.js` with all new endpoints
  - Final smoke test all routes

  **Must NOT do**:
  - Don't change WebSocket or stats polling logic
  - Don't add new routes beyond the 6 existing

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Integration and final verification
  - **Skills**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: NO (final task)
  - **Parallel Group**: Wave 5 (alone)
  - **Blocks**: None (final)
  - **Blocked By**: Tasks 4, 12-17

  **References**:
  - `frontend/src/App.jsx:1-53` - Current routes
  - `frontend/src/services/api.js` - API client

  **Acceptance Criteria**:
  - [ ] All 6 routes load without error
  - [ ] `npm run build` succeeds
  - [ ] `npm run lint` passes
  - [ ] `npm run test -- --run` all pass
  - [ ] `.env.example` has VITE_SPLUNK_BASE_URL

  **Agent-Executed QA Scenarios:**

  ```
  Scenario: All routes work end-to-end
    Tool: Playwright
    Preconditions: Dev server + backend running
    Steps:
      1. Navigate to http://localhost:5173/dashboard
      2. Assert: page loads, no console errors
      3. Navigate to http://localhost:5173/security
      4. Assert: page loads
      5. Navigate to http://localhost:5173/correlation
      6. Assert: page loads
      7. Navigate to http://localhost:5173/alerts
      8. Assert: page loads
      9. Navigate to http://localhost:5173/threats
      10. Assert: page loads
      11. Navigate to http://localhost:5173/system
      12. Assert: page loads
      13. Screenshot each: .sisyphus/evidence/task-18-{route}.png
    Expected Result: All pages functional
    Evidence: 6 screenshots

  Scenario: Production build succeeds
    Tool: Bash
    Preconditions: All tasks complete
    Steps:
      1. cd /home/jclee/dev/splunk/frontend
      2. npm run build
      3. Assert: exit code 0
      4. Assert: dist/ directory exists
      5. npm run lint
      6. Assert: exit code 0
      7. npm run test -- --run
      8. Assert: exit code 0
    Expected Result: Build, lint, and tests all pass
    Evidence: Command outputs
  ```

  **Commit**: YES
  - Message: `feat(frontend): finalize navigation redesign integration`
  - Files: `src/App.jsx`, `src/services/api.js`, `.env.example`
  - Pre-commit: `npm run build && npm run lint && npm run test -- --run`

  **Estimated LOC**: +50

---

## Commit Strategy

| After Task(s) | Message | Files | Verification |
|---------------|---------|-------|--------------|
| 1, 5 | `feat(frontend): setup vitest and lucide-react dependencies` | vitest.config.js, package.json, example.test.jsx | npm test |
| 2 | `feat(frontend): add useSidebarState hook with localStorage persistence` | useSidebarState.js, test | npm test |
| 6 | `feat(frontend): add NavItem component with lucide-react icons` | NavItem.jsx, NavItem.css, test | npm test |
| 10 | `feat(backend): add stub API endpoints for enhanced pages` | server.js | curl tests |
| 11 | `feat(backend): implement enhanced API endpoints for frontend pages` | server.js | curl tests |
| 3 | `feat(frontend): add collapsible Sidebar component with nested navigation` | Sidebar.jsx, Sidebar.css, test | npm test |
| 7 | `feat(frontend): add Breadcrumbs component with route awareness` | Breadcrumbs.jsx, test | npm test |
| 8 | `feat(frontend): add CommandPalette with Cmd+K shortcut` | CommandPalette.jsx, useCommandPalette.js, test | npm test |
| 9 | `feat(frontend): add MobileDrawer for responsive navigation` | MobileDrawer.jsx, test | npm test |
| 4 | `refactor(frontend): integrate navigation components into Layout` | Layout.jsx, Layout.css | npm build |
| 12-16 | `feat(frontend): enhance all pages with visualizations` | 5 page files | npm lint |
| 17 | `style(splunk): update nav.xml color to match React theme` | default.xml | xmllint |
| 18 | `feat(frontend): finalize navigation redesign integration` | App.jsx, api.js, .env.example | full test suite |

---

## Success Criteria

### Verification Commands
```bash
# Frontend
cd frontend
npm run dev          # Expected: starts on localhost:5173
npm run build        # Expected: builds to dist/
npm run lint         # Expected: 0 errors
npm run test -- --run  # Expected: all tests pass

# Backend
cd backend
node server.js       # Expected: starts on localhost:3001
curl http://localhost:3001/api/security/overview  # Expected: JSON response
curl http://localhost:3001/api/threats/detailed   # Expected: JSON response

# Splunk XML
xmllint --noout security_alert/default/data/ui/nav/default.xml  # Expected: valid
```

### Final Checklist
- [ ] All emoji icons replaced with lucide-react SVG icons
- [ ] Sidebar collapses/expands with localStorage persistence
- [ ] Nested navigation menus work
- [ ] Breadcrumbs show on all pages
- [ ] Cmd+K opens command palette
- [ ] Mobile layout (< 768px) uses drawer navigation
- [ ] All 5 placeholder pages have real content + charts
- [ ] All new API endpoints return structured data
- [ ] Vitest tests pass for all new components
- [ ] Splunk nav.xml has #4ade80 color
- [ ] `npm run build` produces no errors
- [ ] No emoji characters anywhere in navigation UI
