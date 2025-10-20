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
    this.baseIndex = 'fortigate_security';
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
      <title>Blocked Attacks</title>
      <single>
        <search>
          <query>index=${this.baseIndex} action=blocked earliest=-1h | stats count</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">all</option>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="rangeValues">[0,100,500,1000]</option>
        <option name="underLabel">Blocked</option>
        <option name="useColors">1</option>
      </single>
    </panel>

    <panel>
      <title>Unique Threat Sources</title>
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
      <title>Attack Actions Distribution</title>
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

  <!-- Row 3: Top Threats -->
  <row>
    <panel>
      <title>Top Attack Sources (Last Hour)</title>
      <table>
        <search>
          <query>index=${this.baseIndex} (action=blocked OR action=dropped) earliest=-1h
| stats count as attacks, dc(dst_ip) as targets, values(attack_name) as attack_types by src_ip
| eval threat_level=case(attacks > 100, "Critical", attacks > 50, "High", attacks > 10, "Medium", 1=1, "Low")
| sort -attacks
| head 10
| rename src_ip as "Source IP", attacks as "Attack Count", targets as "Unique Targets", attack_types as "Attack Types", threat_level as "Threat Level"</query>
          <refresh>30s</refresh>
        </search>
        <option name="drilldown">row</option>
        <option name="rowNumbers">true</option>
        <format type="color" field="Threat Level">
          <colorPalette type="map">{"Critical":#DC4E41,"High":#F1813F,"Medium":#F8BE34,"Low":#53A051}</colorPalette>
        </format>
      </table>
    </panel>

    <panel>
      <title>Top IPS Signatures</title>
      <table>
        <search>
          <query>index=${this.baseIndex} attack_name=* earliest=-1h
| stats count as hits, dc(src_ip) as sources by attack_name, severity
| sort -hits
| head 10
| rename attack_name as "Signature", hits as "Hits", sources as "Unique Sources", severity as "Severity"</query>
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
      <title>Attack Sources by Country</title>
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
   * Threat Intelligence Dashboard
   */
  getThreatIntelDashboard() {
    return `<dashboard version="1.1">
  <label>Threat Intelligence Dashboard</label>
  <description>Advanced threat detection and intelligence monitoring</description>

  <!-- Row 1: Threat Summary -->
  <row>
    <panel>
      <title>Malware Detections (24h)</title>
      <single>
        <search>
          <query>index=${this.fazIndex} virus_name=* earliest=-24h | stats count</query>
          <refresh>1m</refresh>
        </search>
        <option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
        <option name="underLabel">Detections</option>
      </single>
    </panel>

    <panel>
      <title>Botnet Communications</title>
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
      <title>Malicious DNS Queries</title>
      <single>
        <search>
          <query>index=${this.fazIndex} threat_category=malicious earliest=-24h | stats count</query>
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

  <!-- Row 2: Malware Analysis -->
  <row>
    <panel>
      <title>Top Malware Families</title>
      <chart>
        <search>
          <query>index=${this.fazIndex} virus_name=* earliest=-24h
| stats count as detections, dc(src_ip) as infected_hosts by virus_name
| sort -detections
| head 10</query>
          <refresh>2m</refresh>
        </search>
        <option name="charting.chart">bar</option>
        <option name="charting.axisTitleX.text">Malware Family</option>
        <option name="charting.axisTitleY.text">Detections</option>
      </chart>
    </panel>

    <panel>
      <title>Infected Hosts</title>
      <table>
        <search>
          <query>index=${this.fazIndex} virus_name=* earliest=-24h
| stats count as infections, values(virus_name) as malware by src_ip
| sort -infections
| head 15
| rename src_ip as "Host IP", infections as "Infection Count", malware as "Malware Types"</query>
          <refresh>2m</refresh>
        </search>
        <option name="drilldown">row</option>
      </table>
    </panel>
  </row>

  <!-- Row 3: Botnet Activity -->
  <row>
    <panel>
      <title>Botnet Command & Control Servers</title>
      <table>
        <search>
          <query>index=${this.fazIndex} category=botnet earliest=-24h
| stats count as connections, dc(src_ip) as bots by dst_ip, botnet_name
| sort -connections
| head 15
| rename dst_ip as "C&C Server", connections as "Connection Attempts", bots as "Bot Count", botnet_name as "Botnet Name"</query>
          <refresh>2m</refresh>
        </search>
        <option name="drilldown">row</option>
        <option name="rowNumbers">true</option>
      </table>
    </panel>

    <panel>
      <title>Botnet Timeline</title>
      <chart>
        <search>
          <query>index=${this.fazIndex} category=botnet earliest=-24h
| timechart span=1h count by botnet_name</query>
          <refresh>2m</refresh>
        </search>
        <option name="charting.chart">line</option>
      </chart>
    </panel>
  </row>

  <!-- Row 4: Web Threats -->
  <row>
    <panel>
      <title>Blocked Websites by Category</title>
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
      <title>Top Blocked URLs</title>
      <table>
        <search>
          <query>index=${this.baseIndex} service=webfilter action=blocked earliest=-24h
| stats count as blocks, dc(src_ip) as users by url, category
| sort -blocks
| head 15
| rename url as "URL", blocks as "Blocks", users as "Unique Users", category as "Category"</query>
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
