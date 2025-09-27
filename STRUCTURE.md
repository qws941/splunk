# 📁 Project Structure

## 🏗️ Directory Organization

```
splunk/
├── 📚 docs/                           # Technical Documentation
│   ├── REAL_IMPLEMENTATION_PROOF.md    # Official API proof
│   ├── PRODUCTION_READINESS.md         # Production deployment analysis
│   ├── ACTUAL_OPERATION_ANALYSIS.md    # Feasibility verification
│   ├── SPLUNK_HEC_PRODUCTION_VERIFICATION.md  # Splunk integration
│   ├── LARGE_SCALE_80_DEVICES_IMPLEMENTATION.md  # Large-scale guide
│   ├── FORTINET_INTEGRATION_SPEC.md    # Technical specifications
│   ├── POLICY_VERIFICATION_README.md   # Policy verification guide
│   ├── IMPLEMENTATION_SUMMARY.md       # Implementation summary
│   ├── E2E_TESTING_GUIDE.md           # E2E testing documentation
│   ├── DEPLOYMENT_SETUP.md            # Deployment instructions
│   └── DEPLOY.md                       # Basic deployment guide
│
├── 🧪 tests/                          # Integration & E2E Tests
│   ├── test-fortimanager-api.js        # FortiManager API tests
│   ├── test-fortianalyzer-integration.js  # FortiAnalyzer tests
│   └── e2e/                           # Playwright E2E tests
│       ├── visual-regression.spec.js   # Visual regression tests
│       └── homepage.spec.js            # Homepage functionality tests
│
├── 📦 src/                            # Source Code
│   ├── components/                     # UI Components
│   ├── api/                           # API Integrations
│   ├── utils/                         # Utilities
│   ├── worker.js                      # Cloudflare Worker entry
│   ├── index.js                       # Main application logic
│   ├── index.html                     # Web interface
│   ├── fortimanager-direct-connector.js    # FMG API connector
│   ├── fortianalyzer-direct-connector.js   # FAZ API connector
│   ├── splunk-api-connector.js        # Splunk HEC connector
│   ├── policy-verification-server.js  # Policy server
│   ├── policy-verification-web.html   # Policy verification UI
│   ├── security-event-processor.js    # Event processing
│   ├── ai-alert-classifier.js         # AI alert classification
│   ├── auto-recovery-system.js        # Auto-recovery logic
│   └── predictive-error-analyzer.js   # Error prediction
│
├── 🔧 scripts/                        # Build & Deploy Scripts
│   ├── setup-secrets.sh               # Environment setup
│   └── set-secrets.sh                 # Secret configuration
│
├── ⚙️ configs/                        # Configuration Files
│   └── enhanced-fortinet-dashboard.xml # Splunk dashboard config
│
├── 🌐 public/                         # Static Web Assets
│   ├── css/                           # Stylesheets
│   ├── js/                            # Client-side JavaScript
│   └── images/                        # Images and icons
│
├── 📋 Configuration Files
│   ├── package.json                   # Dependencies and scripts
│   ├── playwright.config.js           # E2E test configuration
│   ├── wrangler.toml                  # Cloudflare Workers config
│   ├── .gitignore                     # Git ignore rules
│   └── _redirects                     # Cloudflare Pages redirects
│
└── 🚀 CI/CD & Deployment
    └── .github/workflows/              # GitHub Actions
        ├── cloudflare-pages.yml        # Pages deployment
        ├── deploy.yml                  # Workers deployment
        ├── e2e-tests.yml              # E2E testing
        └── slack-notify-deploy.yml     # Slack notifications
```

## 📊 File Count Summary

| Directory | Files | Description |
|-----------|-------|-------------|
| `docs/` | 11 files | Comprehensive technical documentation |
| `tests/` | 4 files | Integration tests and E2E testing |
| `src/` | 15+ files | Core application source code |
| `configs/` | 1 file | Configuration templates |
| `scripts/` | 2 files | Deployment and setup scripts |
| `.github/` | 4 files | CI/CD workflow definitions |

## 🎯 Key Components

### Core Application Files
- **`src/worker.js`** - Cloudflare Workers entry point
- **`src/index.js`** - Main application logic with API routing
- **`src/index.html`** - Primary web interface

### Integration Connectors
- **`fortimanager-direct-connector.js`** - FortiManager JSON-RPC API
- **`fortianalyzer-direct-connector.js`** - FortiAnalyzer REST API
- **`splunk-api-connector.js`** - Splunk HTTP Event Collector

### Testing Infrastructure
- **`tests/test-fortimanager-api.js`** - FMG connectivity verification
- **`tests/test-fortianalyzer-integration.js`** - FAZ-Splunk integration
- **`tests/e2e/`** - Playwright visual regression tests

### Documentation Categories
- **Implementation Proof** - Technical feasibility verification
- **Production Readiness** - Deployment and scaling guides
- **Integration Specs** - API specifications and protocols

## 🔧 Development Workflow

```bash
# Development
npm install                    # Install dependencies
npm run pages:dev             # Local development server

# Testing
node tests/test-fortimanager-api.js        # API integration tests
npm run test:e2e                           # E2E visual tests

# Deployment
git push                      # Auto-deploy via GitHub Actions
npm run deploy               # Manual Cloudflare Workers deploy
```

## 🛡️ Security & Configuration

- **Environment Variables**: Managed through Cloudflare secrets
- **API Keys**: Secured in `scripts/setup-secrets.sh`
- **Git Ignores**: Comprehensive `.gitignore` for sensitive files

## 🚀 Live Deployment

- **Production URL**: https://splunk.jclee.me
- **Auto-deployment**: Git push triggers CI/CD pipeline
- **E2E Testing**: Automated visual regression testing
- **Performance**: Optimized for 80+ device management

This structure supports both development flexibility and production scalability for the FortiNet-Splunk integration system.