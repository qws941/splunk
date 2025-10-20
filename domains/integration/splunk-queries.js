/**
 * Splunk Query Library
 * Real, production-ready Splunk queries for FortiGate security monitoring
 *
 * Domain: Integration
 * Purpose: Provide reusable Splunk SPL queries for security analysis
 */

/**
 * Splunk Query Library Class
 */
class SplunkQueries {
  constructor() {
    this.baseIndex = 'fortigate_security';
    this.fmgIndex = 'fortimanager_direct';
    this.fazIndex = 'fortianalyzer_security';
  }

  /**
   * Get all available query categories
   */
  getCategories() {
    return {
      security: 'Security Event Queries',
      traffic: 'Traffic Analysis Queries',
      policy: 'Policy Management Queries',
      device: 'Device Health Queries',
      threat: 'Threat Intelligence Queries',
      performance: 'Performance Metrics Queries'
    };
  }

  /**
   * Security Event Queries
   */
  getSecurity Queries() {
    return {
      // 1. Critical Security Events (Last Hour)
      criticalEvents: {
        name: 'Critical Security Events',
        description: 'All critical security events in the last hour',
        spl: `index=${this.baseIndex} severity=critical earliest=-1h
| stats count by src_ip, dst_ip, action, attack_name
| sort -count
| head 20`,
        timeRange: '-1h',
        visualization: 'table'
      },

      // 2. Top Attack Sources
      topAttackSources: {
        name: 'Top Attack Sources',
        description: 'Top 10 source IPs generating security events',
        spl: `index=${this.baseIndex} (action=blocked OR action=dropped) earliest=-24h
| stats count as attacks, dc(dst_ip) as targets, values(attack_name) as attack_types by src_ip
| sort -attacks
| head 10
| eval threat_level=case(
    attacks > 1000, "Critical",
    attacks > 500, "High",
    attacks > 100, "Medium",
    1=1, "Low"
)`,
        timeRange: '-24h',
        visualization: 'table'
      },

      // 3. Blocked Traffic Timeline
      blockedTrafficTimeline: {
        name: 'Blocked Traffic Timeline',
        description: 'Timeline of blocked/dropped traffic',
        spl: `index=${this.baseIndex} (action=blocked OR action=dropped) earliest=-4h
| timechart span=5m count by action`,
        timeRange: '-4h',
        visualization: 'timechart'
      },

      // 4. IPS Signature Hits
      ipsSignatures: {
        name: 'IPS Signature Hits',
        description: 'Most triggered IPS signatures',
        spl: `index=${this.baseIndex} attack_name=* earliest=-24h
| stats count as hits, dc(src_ip) as unique_sources, dc(dst_ip) as unique_targets by attack_name, severity
| sort -hits
| head 15`,
        timeRange: '-24h',
        visualization: 'table'
      },

      // 5. Geographic Attack Distribution
      geoAttackDist: {
        name: 'Geographic Attack Distribution',
        description: 'Attack sources by country (requires geoip)',
        spl: `index=${this.baseIndex} action=blocked earliest=-24h
| iplocation src_ip
| stats count as attacks by Country
| sort -attacks
| head 20`,
        timeRange: '-24h',
        visualization: 'map'
      }
    };
  }

  /**
   * Traffic Analysis Queries
   */
  getTrafficQueries() {
    return {
      // 1. Top Protocols
      topProtocols: {
        name: 'Top Protocols',
        description: 'Most used protocols',
        spl: `index=${this.baseIndex} earliest=-1h
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received, count as sessions by proto
| eval total_bytes=sent+received
| eval total_mb=round(total_bytes/1024/1024, 2)
| sort -total_bytes
| fields proto, sent, received, total_mb, sessions`,
        timeRange: '-1h',
        visualization: 'pie'
      },

      // 2. Top Talkers (Bandwidth)
      topTalkers: {
        name: 'Top Talkers',
        description: 'Hosts consuming most bandwidth',
        spl: `index=${this.baseIndex} earliest=-1h
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received by src_ip
| eval total_bytes=sent+received
| eval total_gb=round(total_bytes/1024/1024/1024, 3)
| sort -total_bytes
| head 20
| fields src_ip, total_gb, sent, received`,
        timeRange: '-1h',
        visualization: 'table'
      },

      // 3. Application Usage
      appUsage: {
        name: 'Application Usage',
        description: 'Most used applications',
        spl: `index=${this.baseIndex} app=* earliest=-4h
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received, count as sessions by app
| eval total_mb=round((sent+received)/1024/1024, 2)
| sort -total_mb
| head 15
| fields app, total_mb, sessions`,
        timeRange: '-4h',
        visualization: 'bar'
      },

      // 4. Traffic by Service
      trafficByService: {
        name: 'Traffic by Service',
        description: 'Traffic breakdown by service/port',
        spl: `index=${this.baseIndex} service=* earliest=-1h
| stats sum(sent_bytes) as bytes, count as connections by service
| eval mb=round(bytes/1024/1024, 2)
| sort -mb
| head 20
| fields service, mb, connections`,
        timeRange: '-1h',
        visualization: 'table'
      },

      // 5. Hourly Traffic Pattern
      hourlyPattern: {
        name: 'Hourly Traffic Pattern',
        description: '24-hour traffic pattern',
        spl: `index=${this.baseIndex} earliest=-24h
| bucket _time span=1h
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received by _time
| eval total_gb=round((sent+received)/1024/1024/1024, 2)
| timechart span=1h sum(total_gb) as traffic_gb`,
        timeRange: '-24h',
        visualization: 'area'
      }
    };
  }

  /**
   * Policy Management Queries
   */
  getPolicyQueries() {
    return {
      // 1. Policy Hit Count
      policyHitCount: {
        name: 'Policy Hit Count',
        description: 'Most used firewall policies',
        spl: `index=${this.baseIndex} policyid=* earliest=-24h
| stats count as hits, dc(src_ip) as unique_sources, dc(dst_ip) as unique_destinations by policyid, policyname
| sort -hits
| head 20`,
        timeRange: '-24h',
        visualization: 'table'
      },

      // 2. Unused Policies
      unusedPolicies: {
        name: 'Unused Policies',
        description: 'Policies with no hits in the last 7 days',
        spl: `index=${this.fmgIndex} sourcetype="fortimanager:policy" earliest=-7d
| stats count by policyid, name
| join type=left policyid [
    search index=${this.baseIndex} earliest=-7d
    | stats count as hits by policyid
]
| where isnull(hits) OR hits=0
| fields policyid, name
| sort policyid`,
        timeRange: '-7d',
        visualization: 'table'
      },

      // 3. Policy Changes
      policyChanges: {
        name: 'Policy Changes',
        description: 'Recent policy modifications',
        spl: `index=${this.fmgIndex} sourcetype="fortimanager:critical_policy" earliest=-7d
| stats latest(_time) as last_change, values(action) as actions by policyid, name, user
| convert ctime(last_change)
| sort -last_change
| head 20`,
        timeRange: '-7d',
        visualization: 'table'
      },

      // 4. Deny Policy Hits
      denyPolicyHits: {
        name: 'Deny Policy Hits',
        description: 'Traffic blocked by deny policies',
        spl: `index=${this.baseIndex} action=deny earliest=-24h
| stats count as blocked_attempts, dc(src_ip) as unique_sources by policyid, policyname, src_ip
| sort -blocked_attempts
| head 20`,
        timeRange: '-24h',
        visualization: 'table'
      }
    };
  }

  /**
   * Device Health Queries
   */
  getDeviceQueries() {
    return {
      // 1. Device Status
      deviceStatus: {
        name: 'Device Status',
        description: 'Current status of all FortiGate devices',
        spl: `index=${this.fmgIndex} sourcetype="fortimanager:device_status" earliest=-5m
| stats latest(conn_status) as connection, latest(conf_status) as config, latest(os_ver) as version by name, ip
| eval status=case(
    connection=1 AND config=1, "Healthy",
    connection=1 AND config!=1, "Config Out of Sync",
    connection!=1, "Disconnected"
)
| sort name`,
        timeRange: '-5m',
        visualization: 'table'
      },

      // 2. CPU Usage
      cpuUsage: {
        name: 'CPU Usage',
        description: 'CPU usage across devices',
        spl: `index=${this.baseIndex} cpu_usage=* earliest=-15m
| timechart span=1m avg(cpu_usage) by device_name
| where avg(cpu_usage) > 0`,
        timeRange: '-15m',
        visualization: 'timechart'
      },

      // 3. Memory Usage
      memoryUsage: {
        name: 'Memory Usage',
        description: 'Memory usage across devices',
        spl: `index=${this.baseIndex} memory_usage=* earliest=-15m
| stats latest(memory_usage) as memory_pct by device_name
| sort -memory_pct
| eval alert=if(memory_pct>80, "⚠️ High", "✓ Normal")`,
        timeRange: '-15m',
        visualization: 'table'
      },

      // 4. Session Count
      sessionCount: {
        name: 'Active Sessions',
        description: 'Active session count per device',
        spl: `index=${this.baseIndex} session_count=* earliest=-15m
| timechart span=1m avg(session_count) as avg_sessions by device_name`,
        timeRange: '-15m',
        visualization: 'timechart'
      },

      // 5. HA Status
      haStatus: {
        name: 'HA Status',
        description: 'High Availability cluster status',
        spl: `index=${this.baseIndex} ha_status=* earliest=-5m
| stats latest(ha_status) as status, latest(ha_role) as role by device_name, ha_group
| sort ha_group, role`,
        timeRange: '-5m',
        visualization: 'table'
      }
    };
  }

  /**
   * Threat Intelligence Queries
   */
  getThreatQueries() {
    return {
      // 1. Malware Detections
      malwareDetections: {
        name: 'Malware Detections',
        description: 'Detected malware and viruses',
        spl: `index=${this.fazIndex} virus_name=* earliest=-24h
| stats count as detections, dc(src_ip) as infected_hosts, values(src_ip) as sources by virus_name, action
| sort -detections
| head 20`,
        timeRange: '-24h',
        visualization: 'table'
      },

      // 2. Botnet Activity
      botnetActivity: {
        name: 'Botnet Activity',
        description: 'Detected botnet communications',
        spl: `index=${this.fazIndex} category=botnet earliest=-24h
| stats count as connections, dc(src_ip) as bots, values(dst_ip) as command_servers by botnet_name
| sort -connections`,
        timeRange: '-24h',
        visualization: 'table'
      },

      // 3. WebFilter Blocks
      webfilterBlocks: {
        name: 'WebFilter Blocks',
        description: 'Blocked websites by category',
        spl: `index=${this.baseIndex} service=webfilter action=blocked earliest=-24h
| stats count as blocks, dc(src_ip) as users by category, url
| sort -blocks
| head 20`,
        timeRange: '-24h',
        visualization: 'table'
      },

      // 4. SSL Inspection
      sslInspection: {
        name: 'SSL Inspection',
        description: 'SSL/TLS traffic inspection results',
        spl: `index=${this.baseIndex} ssl_inspection=* earliest=-1h
| stats count as inspected, sum(eval(if(ssl_cert_valid="no",1,0))) as invalid_certs by ssl_inspection_result
| eval invalid_pct=round(invalid_certs*100/inspected, 2)`,
        timeRange: '-1h',
        visualization: 'pie'
      },

      // 5. DNS Queries to Malicious Domains
      maliciousDns: {
        name: 'Malicious DNS Queries',
        description: 'DNS queries to known malicious domains',
        spl: `index=${this.fazIndex} dns_query=* threat_category=malicious earliest=-24h
| stats count as queries, dc(src_ip) as clients by dns_query, threat_category
| sort -queries
| head 20`,
        timeRange: '-24h',
        visualization: 'table'
      }
    };
  }

  /**
   * Performance Metrics Queries
   */
  getPerformanceQueries() {
    return {
      // 1. Bandwidth Utilization
      bandwidthUtil: {
        name: 'Bandwidth Utilization',
        description: 'Interface bandwidth utilization',
        spl: `index=${this.baseIndex} interface=* earliest=-1h
| timechart span=1m avg(bandwidth_in) as inbound_mbps, avg(bandwidth_out) as outbound_mbps by interface`,
        timeRange: '-1h',
        visualization: 'timechart'
      },

      // 2. Latency Monitoring
      latencyMonitor: {
        name: 'Latency Monitoring',
        description: 'Network latency metrics',
        spl: `index=${this.baseIndex} latency_ms=* earliest=-1h
| timechart span=1m avg(latency_ms) as avg_latency, p95(latency_ms) as p95_latency by device_name`,
        timeRange: '-1h',
        visualization: 'timechart'
      },

      // 3. Packet Loss
      packetLoss: {
        name: 'Packet Loss',
        description: 'Packet loss percentage',
        spl: `index=${this.baseIndex} packets_sent=* packets_received=* earliest=-1h
| eval loss_pct=round((packets_sent-packets_received)*100/packets_sent, 2)
| timechart span=5m avg(loss_pct) as avg_loss by interface`,
        timeRange: '-1h',
        visualization: 'timechart'
      },

      // 4. Connection Rate
      connectionRate: {
        name: 'Connection Rate',
        description: 'New connections per second',
        spl: `index=${this.baseIndex} earliest=-1h
| bucket _time span=1m
| stats count as new_connections by _time, device_name
| timechart span=1m avg(new_connections) as conn_per_min by device_name`,
        timeRange: '-1h',
        visualization: 'timechart'
      },

      // 5. Throughput Statistics
      throughputStats: {
        name: 'Throughput Statistics',
        description: 'Overall throughput metrics',
        spl: `index=${this.baseIndex} earliest=-1h
| bucket _time span=1m
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received by _time
| eval throughput_mbps=round((sent+received)/1024/1024/60*8, 2)
| timechart span=1m avg(throughput_mbps) as avg_throughput`,
        timeRange: '-1h',
        visualization: 'area'
      }
    };
  }

  /**
   * Get query by name
   * @param {string} category - Query category
   * @param {string} queryName - Query name
   */
  getQuery(category, queryName) {
    const categoryMethod = `get${category.charAt(0).toUpperCase() + category.slice(1)}Queries`;
    if (typeof this[categoryMethod] === 'function') {
      const queries = this[categoryMethod]();
      return queries[queryName] || null;
    }
    return null;
  }

  /**
   * Get all queries
   */
  getAllQueries() {
    return {
      security: this.getSecurityQueries(),
      traffic: this.getTrafficQueries(),
      policy: this.getPolicyQueries(),
      device: this.getDeviceQueries(),
      threat: this.getThreatQueries(),
      performance: this.getPerformanceQueries()
    };
  }

  /**
   * Search queries by keyword
   * @param {string} keyword - Search keyword
   */
  searchQueries(keyword) {
    const allQueries = this.getAllQueries();
    const results = [];

    for (const [category, queries] of Object.entries(allQueries)) {
      for (const [name, query] of Object.entries(queries)) {
        if (
          query.name.toLowerCase().includes(keyword.toLowerCase()) ||
          query.description.toLowerCase().includes(keyword.toLowerCase())
        ) {
          results.push({ category, name, ...query });
        }
      }
    }

    return results;
  }

  /**
   * Format query with custom parameters
   * @param {string} spl - Base SPL query
   * @param {Object} params - Parameters to replace
   */
  formatQuery(spl, params = {}) {
    let formatted = spl;
    for (const [key, value] of Object.entries(params)) {
      formatted = formatted.replace(new RegExp(`\\$${key}\\$`, 'g'), value);
    }
    return formatted;
  }
}

// Export
export default SplunkQueries;
