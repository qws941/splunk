# CLAUDE.md - Splunk-FortiNet Security Integration Platform

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with this Domain-Driven Design architecture codebase.

## 🎯 Project Overview

**Splunk-FortiNet Security Integration Platform** is an enterprise-grade security event processing system built with **Domain-Driven Design Level 3 architecture**. The system provides real-time integration between FortiGate security devices, FortiManager/FortiAnalyzer management platforms, and Splunk Enterprise for comprehensive security monitoring and analysis across 80+ FortiGate devices.

### Key Capabilities
- **Real-time Security Event Processing**: Process 100,000+ events/second
- **Direct API Integration**: No middleware - direct connections to FortiManager JSON-RPC, FortiAnalyzer REST, and Splunk HEC
- **AI-Powered Analysis**: Machine learning-based alert classification and predictive analytics
- **Automated Response**: Proactive defense systems with auto-recovery capabilities
- **Enterprise Scale**: Designed for large-scale security infrastructure management

## 🏗️ Domain-Driven Architecture (Level 3)

This project follows Domain-Driven Design principles with high cohesion and low coupling across 9 specialized domains:

### Core Domains
- **🔗 Integration** (`domains/integration/`): FortiManager JSON-RPC, FortiAnalyzer REST, Splunk HEC connectors
- **🛡️ Security** (`domains/security/`): Real-time event processing, credential management, access control
- **🔍 Analysis** (`domains/analysis/`): AI alert classification, predictive analytics, pattern recognition
- **🛠️ Defense** (`domains/defense/`): Auto-recovery systems, proactive monitoring, resilient architecture
- **🤖 Automation** (`domains/automation/`): CI/CD pipelines, automated testing, deployment automation

### Supporting Domains
- **📊 Monitoring** (`domains/monitoring/`): System health, Grafana integration, alert management
- **🚀 Deployment** (`domains/deployment/`): CloudFlare Workers, environment management, GitOps
- **🔌 API** (`domains/api/`): Real-time feedback APIs, performance metrics, integration endpoints
- **🛠️ Utils** (`domains/utils/`): Common utilities, configuration management, logging

## Key Commands

### Development
```bash
# Start main application (Node.js server)
npm start
npm run dev                    # With auto-reload

# Start policy verification server
npm run policy-server
npm run policy-server:dev     # With auto-reload

# Local development web server
npm run pages:dev              # Builds and serves on localhost:8080
```

### Testing
```bash
# Node.js unit tests
npm test

# E2E tests with Playwright
npm run test:e2e
npm run test:e2e:headed       # With browser UI
npm run test:e2e:debug        # Debug mode
npm run test:e2e:ui           # Playwright UI mode
npm run test:e2e:report       # Show test report

# All tests
npm run test:all

# Integration tests (require environment variables)
node tests/test-fortimanager-api.js
node tests/test-fortianalyzer-integration.js
```

### Build & Deploy
```bash
# Build for production
npm run build                 # Creates dist/ directory

# Deploy to Cloudflare Workers
npm run deploy                # Uses wrangler

# Auto-deployment via git push to main branch
git push                      # Triggers GitHub Actions CI/CD
```

## Architecture Overview

### Multi-Platform Deployment
- **Cloudflare Workers**: Primary deployment (`src/worker.js`) at https://splunk.jclee.me
- **Node.js Server**: Local development and policy verification (`src/index.js`)
- **Static Pages**: Cloudflare Pages build via `build.js`

### Core Integration Pattern: Direct API Connections
The system bypasses middleware and connects directly to enterprise security platforms:

1. **FortiManager Direct Connector** (`src/fortimanager-direct-connector.js`)
   - JSON-RPC API for policy management
   - Multi-device configuration (80+ FortiGates)
   - Real-time policy verification

2. **FortiAnalyzer Direct Connector** (`src/fortianalyzer-direct-connector.js`)
   - REST API for log analysis
   - Security event processing
   - Real-time monitoring

3. **Splunk API Connector** (`src/splunk-api-connector.js`)
   - Enterprise API integration
   - HTTP Event Collector (HEC)
   - Dashboard management

### Environment Configuration
The system requires these environment variables for production:
```bash
# FortiManager
FMG_HOST=your-fortimanager-ip
FMG_USERNAME=admin
FMG_PASSWORD=your-password
FMG_ADOM=Global

# FortiAnalyzer
FAZ_HOST=your-fortianalyzer-ip
FAZ_USERNAME=admin
FAZ_PASSWORD=your-password

# Splunk
SPLUNK_HOST=your-splunk-server
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your-password
SPLUNK_HEC_HOST=your-splunk-server
SPLUNK_HEC_TOKEN=your-hec-token
```

### Testing Strategy
- **E2E Tests**: Playwright tests in `tests/e2e/` validate full web interface
- **Integration Tests**: Direct API connectivity tests in `tests/`
- **Visual Regression**: Automated screenshot comparison for UI consistency
- **CI/CD Testing**: Automated on every push via GitHub Actions

### Key Architectural Decisions

1. **ES Modules**: Project uses `"type": "module"` - all imports must use ES6 syntax
2. **Direct Connections**: No middleware layers - all connectors speak directly to enterprise APIs
3. **Multi-Runtime**: Code works in both Node.js and Cloudflare Workers environments
4. **Environment-Based Config**: All external connections configured via environment variables

### File Organization Pattern (Domain-Driven Design)
```
domains/
├── integration/           # API connectors (FortiManager, FortiAnalyzer, Splunk)
├── security/             # Security event processing and credential management
├── analysis/             # AI-powered analysis and predictive systems
├── defense/              # Auto-recovery and proactive defense systems
├── automation/           # CI/CD workflows and automated processes
├── monitoring/           # System health and Grafana integration
├── deployment/           # CloudFlare Workers and deployment management
├── api/                  # Real-time feedback and performance APIs
└── utils/                # Common utilities and configuration management

src/                      # Legacy source code (being migrated to domains/)
├── worker.js             # Cloudflare Workers entry point
├── index.js              # Node.js application entry point (updated imports)
└── index.html            # Web interface

tests/
├── test-*.js             # Integration tests (executable scripts)
└── e2e/                  # Playwright E2E tests
```

### Domain Import Patterns
With the new DDD architecture, imports have been updated:
```javascript
// Updated imports in src/index.js
import SecurityEventProcessor from '../domains/security/security-event-processor.js';
import FortiManagerDirectConnector from '../domains/integration/fortimanager-direct-connector.js';
import SplunkAPIConnector from '../domains/integration/splunk-api-connector.js';
```

### Build Process
The `build.js` script creates a `dist/` directory by:
1. Copying `src/index.html` to `dist/index.html`
2. Copying `_redirects` for Cloudflare Pages routing
3. Generating `build-info.json` with timestamp and version info

### Deployment Environments
- **Production**: Auto-deploys on push to main branch via GitHub Actions
- **Development**: Local Node.js server with `--watch` flag for hot reload
- **Testing**: Playwright tests run against live production URL (https://splunk.jclee.me)

When working with this codebase, always test both the Node.js server functionality and the Cloudflare Workers deployment to ensure compatibility across both runtime environments.