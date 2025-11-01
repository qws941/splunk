/**
 * Splunk Dashboard Templates
 * Real, production-ready Splunk dashboard XML templates
 *
 * Domain: Integration
 * Purpose: Provide reusable dashboard templates for security monitoring
 */

/**
 * Splunk Dashboard Templates Class
 */
class SplunkDashboards {
  constructor() {
    this.baseIndex = 'fortianalyzer';
    this.fmgIndex = 'fortimanager_direct';
    this.fazIndex = 'fortianalyzer_security';
  }

  /**
   * Main Security Overview Dashboard
   */
  getSecurityOverviewDashboard() {
    return `<dashboard version="1.1">
  <label>FortiGate Security Overview</label>
  <description>Real-time security monitoring dashboard for FortiGate infrastructure</description>

  <!-- Row 1: Key Metrics -->
  <row>
    <panel>
      <title>Total Security Events (Last Hour)</title>
      <single>
        <search>
          <query>index=${this.baseIndex} earliest=-1h | stats count</query>
          <refresh>30s</refresh>
          <refreshType>delay</refreshType>
        </search>
        <option name="drilldown">none</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="rangeValues">[0,1000,5000,10000]</option>
        <option name="underLabel">Events</option>
        <option name="useColors">1</option>
      </single>
    </panel>

    <panel>
      <title>Critical Events</title>
      <single>
        <search>
          <query>index=${this.baseIndex} severity=critical earliest=-1h | stats count</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">all</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="rangeValues">[0,5,20,50]</option>
        <option name="underLabel">Critical</option>
        <option name="useColors">1</option>
        <drilldown>
          <link target="_blank">/app/search/search?q=search index=${this.baseIndex} severity=critical earliest=-1h</link>
        </drilldown>
      </single>
    </panel>

    <panel>
      <title>Filtered Traffic</title>
      <single>
        <search>
          <query>index=${this.baseIndex} action=blocked earliest=-1h | stats count</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">all</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="rangeValues">[0,100,500,1000]</option>
        <option name="underLabel">Filtered</option>
        <option name="useColors">1</option>
      </single>
    </panel>

    <panel>
      <title>Unique Event Sources</title>
      <single>
        <search>
          <query>index=${this.baseIndex} action=blocked earliest=-1h | stats dc(src_ip) as count</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">none</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="rangeValues">[0,10,50,100]</option>
        <option name="underLabel">Sources</option>
        <option name="useColors">1</option>
      </single>
    </panel>
  </row>

  <!-- Row 2: Timeline Visualizations -->
  <row>
    <panel>
      <title>Security Events Timeline (Last 4 Hours)</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} earliest=-4h
| timechart span=5m count by severity</query>
          <refresh>1m</refresh>
        </search>
        <option name="charting.chart">area</option>
        <option name="charting.axisTitleY.text">Event Count</option>
        <option name="charting.legend.placement">bottom</option>
        <option name="charting.drilldown">all</option>
      </chart>
    </panel>

    <panel>
      <title>Action Distribution</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} earliest=-1h
| stats count by action
| sort -count</query>
          <refresh>1m</refresh>
        </search>
        <option name="charting.chart">pie</option>
        <option name="charting.drilldown">all</option>
      </chart>
    </panel>
  </row>

  <!-- Row 3: Top Event Sources -->
  <row>
    <panel>
      <title>Top Traffic Sources (Last Hour)</title>
      <table>
        <search>
          <query>index=${this.baseIndex} (action=blocked OR action=dropped) earliest=-1h
| stats count as events, dc(dst_ip) as targets, values(signature_name) as signatures by src_ip
| eval event_level=case(events > 100, "Critical", events > 50, "High", events > 10, "Medium", 1=1, "Low")
| sort -events
| head 10
| rename src_ip as "Source IP", events as "Event Count", targets as "Unique Targets", signatures as "Signatures", event_level as "Event Level"</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">row</option>
        <option name="rowNumbers">true</option>
        <format type="color" field="Event Level">
          <colorPalette type="map">{"Critical":#DC4E41,"High":#F1813F,"Medium":#F8BE34,"Low":#53A051}</colorPalette>
        </format>
      </table>
    </panel>

    <panel>
      <title>Top Filter Signatures</title>
      <table>
        <search>
          <query>index=${this.baseIndex} signature_name=* earliest=-1h
| stats count as hits, dc(src_ip) as sources by signature_name, severity
| sort -hits
| head 10
| rename signature_name as "Signature", hits as "Hits", sources as "Unique Sources", severity as "Severity"</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">row</option>
        <option name="rowNumbers">true</option>
      </table>
    </panel>
  </row>

  <!-- Row 4: Device Status -->
  <row>
    <panel>
      <title>FortiGate Device Status</title>
      <table>
        <search>
          <query>index=${this.fmgIndex} sourcetype="fortimanager:device_status" earliest=-5m
| stats latest(conn_status) as connection, latest(conf_status) as config, latest(os_ver) as version by name, ip
| eval status=case(connection=1 AND config=1, "✓ Healthy", connection=1 AND config!=1, "⚠ Config Out of Sync", connection!=1, "✗ Disconnected")
| sort name
| rename name as "Device Name", ip as "IP Address", status as "Status", version as "OS Version"</query>
          <refresh>1m</refresh>
        </search>
        <option name="drilldown">none</option>
        <format type="color" field="Status">
          <colorPalette type="map">{"✓ Healthy":#53A051,"⚠ Config Out of Sync":#F8BE34,"✗ Disconnected":#DC4E41}</colorPalette>
        </format>
      </table>
    </panel>
  </row>

  <!-- Row 5: Geographic Distribution -->
  <row>
    <panel>
      <title>Event Sources by Country</title>
      <map>
        <search>
          <query>index=${this.baseIndex} action=blocked earliest=-24h
| iplocation src_ip
| geostats latfield=lat longfield=lon count by Country</query>
          <refresh>5m</refresh>
        </search>
        <option name="mapping.type">marker</option>
        <option name="mapping.map.center">(0,0)</option>
        <option name="mapping.map.zoom">2</option>
      </map>
    </panel>
  </row>
</dashboard>`;
  }

  /**
   * Event Analysis Dashboard
   */
  getThreatIntelDashboard() {
    return `<dashboard version="1.1">
  <label>Event Analysis Dashboard</label>
  <description>Advanced event detection and pattern monitoring</description>

  <!-- Row 1: Event Summary -->
  <row>
    <panel>
      <title>File Detections (24h)</title>
      <single>
        <search>
          <query>index=${this.fazIndex} file_signature=* earliest=-24h | stats count</query>
          <refresh>1m</refresh>
        </search>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="underLabel">Detections</option>
      </single>
    </panel>

    <panel>
      <title>C&C Communications</title>
      <single>
        <search>
          <query>index=${this.fazIndex} category=botnet earliest=-24h | stats count</query>
          <refresh>1m</refresh>
        </search>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="underLabel">C&C Attempts</option>
      </single>
    </panel>

    <panel>
      <title>Flagged DNS Queries</title>
      <single>
        <search>
          <query>index=${this.fazIndex} dns_category=flagged earliest=-24h | stats count</query>
          <refresh>1m</refresh>
        </search>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="underLabel">Queries</option>
      </single>
    </panel>

    <panel>
      <title>WebFilter Blocks</title>
      <single>
        <search>
          <query>index=${this.baseIndex} service=webfilter action=blocked earliest=-24h | stats count</query>
          <refresh>1m</refresh>
        </search>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="underLabel">Blocked</option>
      </single>
    </panel>
  </row>

  <!-- Row 2: File Analysis -->
  <row>
    <panel>
      <title>Top File Signatures</title>
      <chart>
        <search>
          <query>index=${this.fazIndex} file_signature=* earliest=-24h
| stats count as detections, dc(src_ip) as affected_hosts by file_signature
| sort -detections
| head 10</query>
          <refresh>2m</refresh>
        </search>
        <option name="charting.chart">bar</option>
        <option name="charting.axisTitleX.text">File Signature</option>
        <option name="charting.axisTitleY.text">Detections</option>
      </chart>
    </panel>

    <panel>
      <title>Affected Hosts</title>
      <table>
        <search>
          <query>index=${this.fazIndex} file_signature=* earliest=-24h
| stats count as detections, values(file_signature) as signatures by src_ip
| sort -detections
| head 15
| rename src_ip as "Host IP", detections as "Detection Count", signatures as "File Signatures"</query>
          <refresh>2m</refresh>
        </search>
        <option name="drilldown">row</option>
      </table>
    </panel>
  </row>

  <!-- Row 3: C&C Activity -->
  <row>
    <panel>
      <title>Command & Control Servers</title>
      <table>
        <search>
          <query>index=${this.fazIndex} category=c2 earliest=-24h
| stats count as connections, dc(src_ip) as clients by dst_ip, pattern_name
| sort -connections
| head 15
| rename dst_ip as "Server", connections as "Connection Attempts", clients as "Client Count", pattern_name as "Pattern Name"</query>
          <refresh>2m</refresh>
        </search>
        <option name="drilldown">row</option>
        <option name="rowNumbers">true</option>
      </table>
    </panel>

    <panel>
      <title>C&C Timeline</title>
      <chart>
        <search>
          <query>index=${this.fazIndex} category=c2 earliest=-24h
| timechart span=1h count by pattern_name</query>
          <refresh>2m</refresh>
        </search>
        <option name="charting.chart">line</option>
      </chart>
    </panel>
  </row>

  <!-- Row 4: Web Filtering -->
  <row>
    <panel>
      <title>Filtered Websites by Category</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} service=webfilter action=blocked earliest=-24h
| stats count by category
| sort -count
| head 15</query>
          <refresh>2m</refresh>
        </search>
        <option name="charting.chart">pie</option>
      </chart>
    </panel>

    <panel>
      <title>Top Filtered URLs</title>
      <table>
        <search>
          <query>index=${this.baseIndex} service=webfilter action=blocked earliest=-24h
| stats count as filters, dc(src_ip) as users by url, category
| sort -filters
| head 15
| rename url as "URL", filters as "Filters", users as "Unique Users", category as "Category"</query>
          <refresh>2m</refresh>
        </search>
        <option name="drilldown">row</option>
      </table>
    </panel>
  </row>
</dashboard>`;
  }

  /**
   * Traffic Analysis Dashboard
   */
  getTrafficAnalysisDashboard() {
    return `<dashboard version="1.1">
  <label>Network Traffic Analysis</label>
  <description>Comprehensive network traffic monitoring and analysis</description>

  <!-- Row 1: Traffic Metrics -->
  <row>
    <panel>
      <title>Total Traffic (Last Hour)</title>
      <single>
        <search>
          <query>index=${this.baseIndex} earliest=-1h
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received
| eval total_gb=round((sent+received)/1024/1024/1024, 2)
| fields total_gb</query>
          <refresh>30s</refresh>
        </search>
        <option name="underLabel">GB</option>
        <option name="drilldown">none</option>
      </single>
    </panel>

    <panel>
      <title>Active Sessions</title>
      <single>
        <search>
          <query>index=${this.baseIndex} earliest=-5m | stats count</query>
          <refresh>30s</refresh>
        </search>
        <option name="underLabel">Sessions</option>
      </single>
    </panel>

    <panel>
      <title>Connections/Sec</title>
      <single>
        <search>
          <query>index=${this.baseIndex} earliest=-1m
| stats count as connections
| eval conn_per_sec=connections/60
| fields conn_per_sec</query>
          <refresh>10s</refresh>
        </search>
        <option name="underLabel">conn/s</option>
      </single>
    </panel>

    <panel>
      <title>Unique Sources</title>
      <single>
        <search>
          <query>index=${this.baseIndex} earliest=-1h | stats dc(src_ip)</query>
          <refresh>1m</refresh>
        </search>
        <option name="underLabel">IPs</option>
      </single>
    </panel>
  </row>

  <!-- Row 2: Bandwidth Timeline -->
  <row>
    <panel>
      <title>Bandwidth Usage Timeline (Last 4 Hours)</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} earliest=-4h
| bucket _time span=5m
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received by _time
| eval sent_mbps=round(sent*8/1024/1024/300, 2)
| eval received_mbps=round(received*8/1024/1024/300, 2)
| timechart span=5m avg(sent_mbps) as "Outbound", avg(received_mbps) as "Inbound"</query>
          <refresh>1m</refresh>
        </search>
        <option name="charting.chart">area</option>
        <option name="charting.axisTitleY.text">Mbps</option>
        <option name="charting.legend.placement">bottom</option>
      </chart>
    </panel>
  </row>

  <!-- Row 3: Top Talkers and Applications -->
  <row>
    <panel>
      <title>Top Bandwidth Consumers</title>
      <table>
        <search>
          <query>index=${this.baseIndex} earliest=-1h
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received by src_ip
| eval total_mb=round((sent+received)/1024/1024, 2)
| sort -total_mb
| head 15
| rename src_ip as "Source IP", total_mb as "Total MB"</query>
          <refresh>1m</refresh>
        </search>
        <option name="drilldown">row</option>
        <option name="rowNumbers">true</option>
      </table>
    </panel>

    <panel>
      <title>Top Applications</title>
      <table>
        <search>
          <query>index=${this.baseIndex} app=* earliest=-1h
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received, count as sessions by app
| eval total_mb=round((sent+received)/1024/1024, 2)
| sort -total_mb
| head 15
| rename app as "Application", total_mb as "Total MB", sessions as "Sessions"</query>
          <refresh>1m</refresh>
        </search>
        <option name="drilldown">row</option>
        <option name="rowNumbers">true</option>
      </table>
    </panel>
  </row>

  <!-- Row 4: Protocol Distribution -->
  <row>
    <panel>
      <title>Traffic by Protocol</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} earliest=-1h
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received by proto
| eval total_mb=round((sent+received)/1024/1024, 2)
| sort -total_mb
| head 10</query>
          <refresh>1m</refresh>
        </search>
        <option name="charting.chart">pie</option>
      </chart>
    </panel>

    <panel>
      <title>Traffic by Service Port</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} service=* earliest=-1h
| stats sum(sent_bytes) as bytes by service
| eval mb=round(bytes/1024/1024, 2)
| sort -mb
| head 10</query>
          <refresh>1m</refresh>
        </search>
        <option name="charting.chart">bar</option>
      </chart>
    </panel>
  </row>

  <!-- Row 5: Hourly Pattern -->
  <row>
    <panel>
      <title>24-Hour Traffic Pattern</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} earliest=-24h
| bucket _time span=1h
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received by _time
| eval traffic_gb=round((sent+received)/1024/1024/1024, 2)
| timechart span=1h sum(traffic_gb) as "Traffic (GB)"</query>
          <refresh>5m</refresh>
        </search>
        <option name="charting.chart">area</option>
        <option name="charting.axisTitleY.text">Traffic (GB)</option>
      </chart>
    </panel>
  </row>
</dashboard>`;
  }

  /**
   * Performance Monitoring Dashboard
   */
  getPerformanceDashboard() {
    return `<dashboard version="1.1">
  <label>FortiGate Performance Monitoring</label>
  <description>Device performance, resource usage, and system health</description>

  <!-- Row 1: Resource Usage -->
  <row>
    <panel>
      <title>Average CPU Usage</title>
      <single>
        <search>
          <query>index=${this.baseIndex} cpu_usage=* earliest=-5m | stats avg(cpu_usage) as cpu | eval cpu=round(cpu,1) | fields cpu</query>
          <refresh>30s</refresh>
        </search>
        <option name="underLabel">%</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="rangeValues">[0,50,75,90]</option>
        <option name="useColors">1</option>
      </single>
    </panel>

    <panel>
      <title>Average Memory Usage</title>
      <single>
        <search>
          <query>index=${this.baseIndex} memory_usage=* earliest=-5m | stats avg(memory_usage) as mem | eval mem=round(mem,1) | fields mem</query>
          <refresh>30s</refresh>
        </search>
        <option name="underLabel">%</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="rangeValues">[0,60,80,90]</option>
        <option name="useColors">1</option>
      </single>
    </panel>

    <panel>
      <title>Average Latency</title>
      <single>
        <search>
          <query>index=${this.baseIndex} latency_ms=* earliest=-5m | stats avg(latency_ms) as latency | eval latency=round(latency,1) | fields latency</query>
          <refresh>30s</refresh>
        </search>
        <option name="underLabel">ms</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="rangeValues">[0,50,100,200]</option>
        <option name="useColors">1</option>
      </single>
    </panel>

    <panel>
      <title>Active Sessions</title>
      <single>
        <search>
          <query>index=${this.baseIndex} session_count=* earliest=-5m | stats avg(session_count) as sessions | eval sessions=round(sessions,0) | fields sessions</query>
          <refresh>30s</refresh>
        </search>
        <option name="underLabel">Sessions</option>
      </single>
    </panel>
  </row>

  <!-- Row 2: CPU and Memory Timeline -->
  <row>
    <panel>
      <title>CPU Usage by Device (Last Hour)</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} cpu_usage=* earliest=-1h
| timechart span=1m avg(cpu_usage) by device_name</query>
          <refresh>30s</refresh>
        </search>
        <option name="charting.chart">line</option>
        <option name="charting.axisTitleY.text">CPU %</option>
        <option name="charting.legend.placement">bottom</option>
      </chart>
    </panel>

    <panel>
      <title>Memory Usage by Device (Last Hour)</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} memory_usage=* earliest=-1h
| timechart span=1m avg(memory_usage) by device_name</query>
          <refresh>30s</refresh>
        </search>
        <option name="charting.chart">line</option>
        <option name="charting.axisTitleY.text">Memory %</option>
      </chart>
    </panel>
  </row>

  <!-- Row 3: Session and Throughput -->
  <row>
    <panel>
      <title>Active Sessions Timeline</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} session_count=* earliest=-1h
| timechart span=1m avg(session_count) by device_name</query>
          <refresh>30s</refresh>
        </search>
        <option name="charting.chart">area</option>
        <option name="charting.axisTitleY.text">Sessions</option>
      </chart>
    </panel>

    <panel>
      <title>Network Throughput</title>
      <chart>
        <search>
          <query>index=${this.baseIndex} earliest=-1h
| bucket _time span=1m
| stats sum(sent_bytes) as sent, sum(rcvd_bytes) as received by _time
| eval throughput_mbps=round((sent+received)/1024/1024/60*8, 2)
| timechart span=1m avg(throughput_mbps) as "Throughput (Mbps)"</query>
          <refresh>30s</refresh>
        </search>
        <option name="charting.chart">area</option>
        <option name="charting.axisTitleY.text">Mbps</option>
      </chart>
    </panel>
  </row>

  <!-- Row 4: Device Health -->
  <row>
    <panel>
      <title>Device Health Status</title>
      <table>
        <search>
          <query>index=${this.baseIndex} earliest=-5m
| stats latest(cpu_usage) as cpu, latest(memory_usage) as mem, latest(session_count) as sessions by device_name
| eval health=case(cpu>80 OR mem>80, "Critical", cpu>60 OR mem>60, "Warning", 1=1, "Healthy")
| sort device_name
| rename device_name as "Device", cpu as "CPU %", mem as "Memory %", sessions as "Sessions", health as "Health Status"</query>
          <refresh>30s</refresh>
        </search>
        <format type="color" field="Health Status">
          <colorPalette type="map">{"Healthy":#53A051,"Warning":#F8BE34,"Critical":#DC4E41}</colorPalette>
        </format>
      </table>
    </panel>
  </row>
</dashboard>`;
  }

  /**
   * Get dashboard by name
   * @param {string} dashboardName - Dashboard name
   */
  getDashboard(dashboardName) {
    const method = `get${dashboardName.charAt(0).toUpperCase() + dashboardName.slice(1)}Dashboard`;
    if (typeof this[method] === 'function') {
      return this[method]();
    }
    return null;
  }

  /**
   * Get all dashboards
   */
  getAllDashboards() {
    return {
      securityOverview: this.getSecurityOverviewDashboard(),
      threatIntel: this.getThreatIntelDashboard(),
      trafficAnalysis: this.getTrafficAnalysisDashboard(),
      performance: this.getPerformanceDashboard()
    };
  }

  /**
   * Get dashboard list
   */
  getDashboardList() {
    return [
      {
        id: 'securityOverview',
        name: 'Security Overview',
        description: 'Main security monitoring dashboard',
        category: 'security'
      },
      {
        id: 'threatIntel',
        name: 'Threat Intelligence',
        description: 'Advanced threat detection and analysis',
        category: 'security'
      },
      {
        id: 'trafficAnalysis',
        name: 'Traffic Analysis',
        description: 'Network traffic monitoring',
        category: 'network'
      },
      {
        id: 'performance',
        name: 'Performance Monitoring',
        description: 'Device performance and health',
        category: 'system'
      }
    ];
  }
}

// Export
export default SplunkDashboards;
