#!/usr/bin/env python3
"""
FortiGate Alert Test Event Generator
Generates sample events for all 15 alert definitions to test Slack notifications.
Usage: python3 generate_test_events.py [alert_name|all]
"""

import os
import sys
import random
import datetime
import gzip

DEVICES = ["FGT-HQ-01", "FGT-BR-01", "FGT-DC-01"]
USERS = ["admin", "netadmin", "security_admin"]
CFGPATHS = ["firewall policy", "firewall address", "system interface", "vpn ipsec phase1-interface"]
TUNNELNAMES = ["VPN-HQ-to-Branch", "VPN-DC-Primary", "VPN-Partner-01"]
INTERFACES = ["port1", "port2", "wan1", "wan2", "dmz"]
COMPONENTS = ["Fan 1", "Fan 2", "PSU 1", "PSU 2", "Temperature Sensor"]
LICENSES = ["FortiCare Support", "FortiGuard AV", "FortiGuard IPS", "FortiGuard Web Filtering"]
RESOURCES = ["CPU", "Memory"]
RESOURCE_TYPES = ["Disk", "Sessions", "Memory"]
REASONS = ["firmware upgrade", "manual reboot", "unexpected crash", "kernel panic"]
HA_STATES = ["master", "slave", "standalone"]

ATTACKER_IPS = [
    "185.220.101.1", "185.220.101.2", "45.155.205.100",
    "91.240.118.50", "193.27.228.100", "193.27.228.101"
]

TEST_LOG_DIR = "/opt/splunk/var/log/fortigate_test"

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def random_ip():
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

ALERTS = {
    "001_config_change": {
        "description": "Configuration Change",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0100044546" type="event" subtype="system" level="notice" eventtime={int(datetime.datetime.now().timestamp())} logdesc="Configuration changed" user="{random.choice(USERS)}" ui="CLI" action="Edit" cfgpath="{random.choice(CFGPATHS)}" cfgattr="set status enable" msg="Configuration changed by admin from CLI"'
    },
    "002_vpn_tunnel_down": {
        "description": "VPN Tunnel Down",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0101037124" type="event" subtype="vpn" level="warning" eventtime={int(datetime.datetime.now().timestamp())} logdesc="IPsec tunnel down" tunnelid="{random.choice(TUNNELNAMES)}" tunnelname="{random.choice(TUNNELNAMES)}" remip="{random_ip()}" locip="192.168.1.1" reason="timeout" msg="IPsec tunnel is down, reason: timeout"'
    },
    "002_vpn_tunnel_up": {
        "description": "VPN Tunnel Up",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0101037125" type="event" subtype="vpn" level="information" eventtime={int(datetime.datetime.now().timestamp())} logdesc="Phase1 up" tunnelid="{random.choice(TUNNELNAMES)}" tunnelname="{random.choice(TUNNELNAMES)}" remip="203.0.113.50" locip="192.168.1.1" msg="Phase1 up for tunnel"'
    },
    "006_cpu_memory": {
        "description": "CPU/Memory Anomaly",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0104043001" type="event" subtype="system" level="warning" eventtime={int(datetime.datetime.now().timestamp())} logdesc="{random.choice(RESOURCES)} usage high" msg="{random.choice(RESOURCES)} usage is {random.randint(75,95)}% which exceeds threshold"'
    },
    "007_hardware_failure": {
        "description": "Hardware Failure",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0103040001" type="event" subtype="system" level="alert" eventtime={int(datetime.datetime.now().timestamp())} logdesc="Hardware failure" msg="{random.choice(COMPONENTS)} failed on device"'
    },
    "007_hardware_restored": {
        "description": "Hardware Restored",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0103040014" type="event" subtype="system" level="notice" eventtime={int(datetime.datetime.now().timestamp())} logdesc="Hardware restored" msg="{random.choice(COMPONENTS)} restored on device"'
    },
    "008_ha_state": {
        "description": "HA State Change",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0100020010" type="event" subtype="ha" level="warning" eventtime={int(datetime.datetime.now().timestamp())} logdesc="HA state changed" ha_state="{random.choice(HA_STATES)}" from_state="{random.choice(HA_STATES)}" member="FG100F0000000002" msg="HA state changed"'
    },
    "010_resource_limit": {
        "description": "Resource Limit",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0104043003" type="event" subtype="system" level="warning" eventtime={int(datetime.datetime.now().timestamp())} logdesc="{random.choice(RESOURCE_TYPES)} limit reached" msg="{random.choice(RESOURCE_TYPES)} usage {random.randint(80,98)}% limit reached"'
    },
    "011_admin_login": {
        "description": "Admin Login Failed",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0105032003" type="event" subtype="admin" level="warning" eventtime={int(datetime.datetime.now().timestamp())} logdesc="Admin login failed" user="{random.choice(USERS)}" srcip="{random.choice(ATTACKER_IPS)}" authproto="https" msg="Administrator login failed"'
    },
    "012_interface_down": {
        "description": "Interface Down",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0100032001" type="event" subtype="system" level="warning" eventtime={int(datetime.datetime.now().timestamp())} logdesc="Interface down" interface="{random.choice(INTERFACES)}" port="{random.choice(INTERFACES)}" msg="Interface link down"'
    },
    "012_interface_up": {
        "description": "Interface Up",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0100032001" type="event" subtype="system" level="notice" eventtime={int(datetime.datetime.now().timestamp())} logdesc="Interface up" interface="{random.choice(INTERFACES)}" port="{random.choice(INTERFACES)}" msg="Interface link up"'
    },
    "013_ssl_vpn_brute_force": {
        "description": "SSL VPN Brute Force",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0101039424" type="event" subtype="vpn" level="warning" eventtime={int(datetime.datetime.now().timestamp())} logdesc="SSL VPN login failed" user="{random.choice(["vpnuser", "admin", "test"])}" srcip="{random.choice(ATTACKER_IPS)}" reason="invalid credentials" msg="SSL VPN login failed"'
    },
    "015_traffic_spike": {
        "description": "Traffic Spike",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0000000013" type="traffic" subtype="forward" level="notice" eventtime={int(datetime.datetime.now().timestamp())} srcip="{random_ip()}" dstip="{random_ip()}" proto=6 sentbyte={random.randint(10000000,100000000)} rcvdbyte={random.randint(5000000,50000000)} duration=300 msg="Traffic session forward"'
    },
    "016_system_reboot": {
        "description": "System Reboot",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0100032002" type="event" subtype="system" level="warning" eventtime={int(datetime.datetime.now().timestamp())} logdesc="System reboot" uptime="15d 4h 32m" msg="System reboot initiated, reason: {random.choice(REASONS)}"'
    },
    "017_license_expiry": {
        "description": "License Expiry Warning",
        "event": lambda: f'{get_timestamp()} devname="{random.choice(DEVICES)}" devid="FG100F0000000001" vd="root" logid="0104043009" type="event" subtype="system" level="warning" eventtime={int(datetime.datetime.now().timestamp())} logdesc="License expiring" license="{random.choice(LICENSES)}" msg="{random.choice(LICENSES)} license expires in {random.randint(3,25)} days"'
    },
}

def generate_event(alert_name, count=1):
    """Generate test events for a specific alert."""
    if alert_name not in ALERTS:
        print(f"Unknown alert: {alert_name}")
        print(f"Available: {', '.join(ALERTS.keys())}")
        return []
    
    events = []
    for _ in range(count):
        events.append(ALERTS[alert_name]["event"]())
    return events

def inject_to_splunk(events, source="fortigate_test"):
    """Inject events via monitored directory."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    os.makedirs(TEST_LOG_DIR, exist_ok=True)
    log_file = os.path.join(TEST_LOG_DIR, f"fgt_test_{timestamp}.log")
    
    content = "\n".join(events) + "\n"
    
    try:
        with open(log_file, "w") as f:
            f.write(content)
        os.chmod(log_file, 0o644)
        print(f"✓ {len(events)} events written: {log_file}")
        return True
    except Exception as e:
        print(f"✗ Write failed: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("FortiGate Alert Test Event Generator")
        print("=" * 50)
        print("\nUsage:")
        print("  python3 generate_test_events.py <alert_name> [count]")
        print("  python3 generate_test_events.py all")
        print("  python3 generate_test_events.py list")
        print("\nAvailable alerts:")
        for name, info in ALERTS.items():
            print(f"  {name:30} - {info['description']}")
        return
    
    alert_name = sys.argv[1].lower()
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    if alert_name == "list":
        print("Available alerts:")
        for name, info in ALERTS.items():
            print(f"  {name:30} - {info['description']}")
        return
    
    if alert_name == "all":
        print("Generating events for ALL alerts...")
        all_events = []
        for name in ALERTS.keys():
            events = generate_event(name, count)
            all_events.extend(events)
            print(f"  [{ALERTS[name]['description']}] {count} event(s)")
        inject_to_splunk(all_events)
    else:
        print(f"Generating {count} event(s) for: {alert_name}")
        events = generate_event(alert_name, count)
        if events:
            inject_to_splunk(events)

if __name__ == "__main__":
    main()
