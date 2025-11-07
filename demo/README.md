# Demo Materials

This directory contains screenshots, videos, and examples demonstrating the Security Alert System.

## Screenshots

*To be added: Screenshots of Slack alerts, Splunk dashboards, and alert configurations*

## Video Demos

*To be added: Screen recordings of alert workflows*

## Sample Data

### Sample Alert Messages

**VPN Tunnel Down:**
```
VPN Type: HQ-Branch-VPN | Tunnel Down | Remote: 192.168.100.1 | Reason: Phase1 negotiation failed
```

**Hardware Failure:**
```
🔴 Hardware: PSU-1 | Status: FAIL | Device: FW-DC1-01 | Severity: Critical
```

**Brute Force Attack:**
```
🟠 Brute Force from 203.0.113.45 | 15 failures | Users: admin, vpnuser1, vpnuser2 +more
```

**CPU Anomaly:**
```
⚠️ CPU Usage Anomaly | Device: FW-DC1-01 | Current: 85.3% | Baseline: 45.2% | Delta: +88.9%
```

## Example Configurations

### Slack Channel Setup

1. Create channel: `#security-firewall-alert`
2. Add incoming webhook integration
3. Copy webhook URL to `local/alert_actions.conf`

### FortiGate Syslog Configuration

```
config log syslogd setting
    set status enable
    set server "<SPLUNK_IP>"
    set port 514
    set facility local7
    set source-ip <FORTIGATE_IP>
    set format default
end
```

### Splunk Input Configuration

```ini
# inputs.conf
[udp://514]
connection_host = ip
sourcetype = fortigate:syslog
index = fw
no_priority_stripping = true
```

## Dashboard Examples

*To be added: XML dashboard definitions and screenshots*

## Use Cases

### 1. VPN Tunnel Monitoring
- **Trigger**: VPN tunnel state changes from UP to DOWN
- **Alert**: Sent to Slack immediately
- **Response**: Network team investigates tunnel status

### 2. Hardware Failure Detection
- **Trigger**: PSU, fan, or disk failure detected
- **Alert**: Critical severity to Slack
- **Response**: Hardware replacement scheduled

### 3. Security Threat Detection
- **Trigger**: Multiple failed login attempts (>5 in 10min)
- **Alert**: Brute force warning to security team
- **Response**: IP blocked at perimeter

### 4. Performance Monitoring
- **Trigger**: CPU usage exceeds 20% above baseline
- **Alert**: Warning sent to operations team
- **Response**: Capacity planning review initiated

## Testing Scenarios

*To be added: Step-by-step testing procedures with expected results*
