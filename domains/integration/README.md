# 🔗 Integration Domain

**MCP trinity, Claude connectors, External API integrations**

This domain handles all external system integrations and API connections following the principle of direct connectivity without middleware layers.

## 📁 Components

### Core Connectors
- **`fortimanager-direct-connector.js`** - FortiManager JSON-RPC API integration
- **`fortianalyzer-direct-connector.js`** - FortiAnalyzer REST API integration
- **`splunk-api-connector.js`** - Splunk Enterprise API and HEC integration

### Integration Patterns
- **Direct API Connections**: No middleware servers or proxies
- **Authentication Management**: Secure credential handling
- **Error Handling**: Robust retry mechanisms
- **Connection Pooling**: Optimized resource management

## 🎯 Design Principles

### Direct Connectivity
All connectors establish direct connections to enterprise security platforms without intermediate layers.

### Protocol Compliance
- **JSON-RPC 2.0**: FortiManager integration
- **REST API**: FortiAnalyzer and Splunk integration
- **HTTP Event Collector**: Real-time Splunk data ingestion

### Scalability
Designed to handle 80+ FortiGate devices with efficient batch processing and connection pooling.

## 🔧 Configuration

All connectors use environment-based configuration:

```bash
# FortiManager
FMG_HOST=your-fortimanager-ip
FMG_USERNAME=admin
FMG_PASSWORD=your-password

# FortiAnalyzer
FAZ_HOST=your-fortianalyzer-ip
FAZ_USERNAME=admin
FAZ_PASSWORD=your-password

# Splunk
SPLUNK_HOST=your-splunk-server
SPLUNK_HEC_TOKEN=your-hec-token
```

## 📊 Performance Characteristics

- **FortiManager**: 1,000+ API calls/second capacity
- **Splunk HEC**: 100,000+ events/second processing
- **Connection Pooling**: Optimized for minimal latency
- **Batch Processing**: 10-device concurrent operations