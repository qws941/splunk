-- ============================================================================
-- Migration: 002_sample_data_insertion.sql
-- Description: Sample data for testing and demonstration
-- Created: 2025-09-28
-- Dependencies: 001_initial_security_schema.sql
-- ============================================================================

-- Sample FortiGate Devices
INSERT OR IGNORE INTO fortigate_devices (
    hostname, ip_address, serial_number, model, firmware_version,
    location, zone, status, policy_count, cpu_usage, memory_usage, session_count
) VALUES
    ('FGT-HQ-01', '192.168.1.10', 'FGT-001-12345', 'FortiGate-100F', '7.4.1', 'Headquarters', 'dmz', 'active', 45, 23.5, 67.8, 1250),
    ('FGT-HQ-02', '192.168.1.11', 'FGT-002-12346', 'FortiGate-100F', '7.4.1', 'Headquarters', 'internal', 'active', 38, 18.2, 54.3, 890),
    ('FGT-BR-01', '10.10.1.10', 'FGT-BR1-12347', 'FortiGate-60F', '7.4.0', 'Branch Office 1', 'wan', 'active', 25, 45.1, 72.5, 450),
    ('FGT-BR-02', '10.10.2.10', 'FGT-BR2-12348', 'FortiGate-60F', '7.3.8', 'Branch Office 2', 'wan', 'maintenance', 22, 0.0, 0.0, 0),
    ('FGT-DC-01', '172.16.1.10', 'FGT-DC1-12349', 'FortiGate-200F', '7.4.1', 'Data Center', 'server', 'active', 67, 31.7, 59.2, 2100);

-- Sample FortiGate Policies
INSERT OR IGNORE INTO fortigate_policies (
    policy_id, name, description, source_zone, dest_zone, source_addr, dest_addr,
    service, action, status, nat, logging, fortigate_device, hit_count
) VALUES
    ('1', 'Allow Internal to DMZ', 'Allow internal users to access DMZ servers', 'internal', 'dmz',
     '["internal_subnet"]', '["dmz_servers"]', '["HTTP", "HTTPS", "SSH"]', 'accept', 'enabled', 1, 1, 'FGT-HQ-01', 15420),
    ('2', 'Block P2P Traffic', 'Block peer-to-peer traffic from internal network', 'internal', 'wan',
     '["internal_subnet"]', '["any"]', '["P2P_ALL"]', 'deny', 'enabled', 1, 1, 'FGT-HQ-01', 234),
    ('3', 'Allow Web Browsing', 'Allow HTTP/HTTPS browsing to internet', 'internal', 'wan',
     '["internal_users"]', '["any"]', '["HTTP", "HTTPS"]', 'accept', 'enabled', 1, 1, 'FGT-HQ-02', 45670),
    ('4', 'VPN Remote Access', 'Allow VPN clients to access internal resources', 'vpn', 'internal',
     '["vpn_users"]', '["internal_servers"]', '["ALL"]', 'accept', 'enabled', 0, 1, 'FGT-HQ-01', 892),
    ('5', 'Database Access Control', 'Restrict database access to authorized servers only', 'dmz', 'server',
     '["web_servers"]', '["db_servers"]', '["MYSQL", "PGSQL"]', 'accept', 'enabled', 0, 1, 'FGT-DC-01', 3456),
    ('6', 'Emergency Deny All', 'Emergency rule to block all traffic', 'any', 'any',
     '["any"]', '["any"]', '["ALL"]', 'deny', 'disabled', 0, 1, 'FGT-HQ-01', 0);

-- Sample Security Events
INSERT OR IGNORE INTO security_events (
    source, event_type, severity, title, message, source_ip, dest_ip,
    source_port, dest_port, protocol, action_taken, processed
) VALUES
    ('fortigate', 'intrusion_attempt', 'high', 'SQL Injection Attempt Detected',
     'Potential SQL injection attack detected from external source', '203.0.113.45', '192.168.1.100',
     52341, 80, 'TCP', 'blocked', 1),
    ('fortigate', 'policy_violation', 'medium', 'Unauthorized Port Access',
     'Attempt to access restricted port from internal network', '192.168.1.150', '10.0.0.50',
     35678, 23, 'TCP', 'denied', 1),
    ('fortianalyzer', 'traffic_anomaly', 'low', 'Unusual Traffic Pattern',
     'Detected unusual traffic pattern in network segment', '192.168.1.0/24', '0.0.0.0/0',
     0, 0, 'ALL', 'monitored', 0),
    ('splunk', 'login_failure', 'medium', 'Multiple Failed Login Attempts',
     'User account locked due to multiple failed login attempts', '203.0.113.67', '192.168.1.10',
     45231, 22, 'TCP', 'account_locked', 1),
    ('fortigate', 'malware_detected', 'critical', 'Malware Download Blocked',
     'Malicious file download attempt blocked by antivirus', '192.168.1.200', '198.51.100.42',
     52914, 80, 'TCP', 'quarantined', 1),
    ('system', 'configuration_change', 'medium', 'Security Policy Updated',
     'Administrator updated firewall security policy', '192.168.1.5', '192.168.1.10',
     0, 0, 'MGMT', 'logged', 1),
    ('fortigate', 'dos_attack', 'high', 'DDoS Attack Detected',
     'Distributed Denial of Service attack detected and mitigated', '203.0.113.0/24', '203.0.113.100',
     0, 80, 'TCP', 'rate_limited', 0),
    ('fortianalyzer', 'bandwidth_exceeded', 'low', 'Bandwidth Threshold Exceeded',
     'Network bandwidth usage exceeded 80% threshold', '192.168.2.0/24', '0.0.0.0/0',
     0, 0, 'ALL', 'alert_sent', 1);

-- Sample Splunk Integration Configuration
INSERT OR IGNORE INTO splunk_integration (
    splunk_server, index_name, sourcetype, status, events_synced, last_event_timestamp
) VALUES
    ('splunk-prod.company.com:8088', 'security_main', 'fortigate:traffic', 'active', 125680, datetime('now', '-5 minutes')),
    ('splunk-prod.company.com:8088', 'security_threats', 'fortigate:threat', 'active', 4532, datetime('now', '-2 minutes')),
    ('splunk-dr.company.com:8088', 'security_backup', 'fortigate:all', 'inactive', 0, NULL);

-- Sample User Sessions
INSERT OR IGNORE INTO user_sessions (
    session_id, user_id, username, role, ip_address, user_agent, expires_at, status
) VALUES
    ('sess_' || lower(hex(randomblob(16))), 'admin001', 'admin', 'admin', '192.168.1.5',
     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', datetime('now', '+1 hour'), 'active'),
    ('sess_' || lower(hex(randomblob(16))), 'analyst001', 'security_analyst', 'operator', '192.168.1.25',
     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', datetime('now', '+45 minutes'), 'active'),
    ('sess_' || lower(hex(randomblob(16))), 'viewer001', 'readonly_user', 'viewer', '192.168.1.45',
     'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36', datetime('now', '-5 minutes'), 'expired');

-- Sample Audit Logs
INSERT OR IGNORE INTO audit_logs (
    username, action, resource_type, resource_id, old_values, new_values,
    ip_address, user_agent, status
) VALUES
    ('admin', 'policy_create', 'fortigate_policy', '6', NULL,
     '{"name": "Emergency Deny All", "action": "deny", "status": "disabled"}',
     '192.168.1.5', 'Web Interface', 'success'),
    ('security_analyst', 'event_processed', 'security_event', '1',
     '{"processed": false}', '{"processed": true, "action_taken": "blocked"}',
     '192.168.1.25', 'API Client', 'success'),
    ('admin', 'device_update', 'fortigate_device', '4',
     '{"status": "active"}', '{"status": "maintenance"}',
     '192.168.1.5', 'Web Interface', 'success'),
    ('system', 'sync_operation', 'splunk_integration', '1', NULL,
     '{"events_synced": 125680, "last_sync": "' || datetime('now') || '"}',
     '127.0.0.1', 'System Process', 'success');

-- Update some timestamps to create realistic data distribution
UPDATE security_events SET
    timestamp = datetime('now', '-' || (RANDOM() % 1440) || ' minutes'),
    created_at = datetime('now', '-' || (RANDOM() % 1440) || ' minutes')
WHERE id IN (1, 2, 3, 4);

UPDATE security_events SET
    timestamp = datetime('now', '-' || (RANDOM() % 60) || ' minutes'),
    created_at = datetime('now', '-' || (RANDOM() % 60) || ' minutes')
WHERE id IN (5, 6, 7, 8);

UPDATE fortigate_policies SET
    last_updated = datetime('now', '-' || (RANDOM() % 10080) || ' minutes')
WHERE id <= 6;

UPDATE fortigate_devices SET
    last_sync = datetime('now', '-' || (RANDOM() % 30) || ' minutes'),
    updated_at = datetime('now', '-' || (RANDOM() % 30) || ' minutes')
WHERE status = 'active';

-- Set maintenance device with older sync time
UPDATE fortigate_devices SET
    last_sync = datetime('now', '-2 days'),
    updated_at = datetime('now', '-2 days'),
    cpu_usage = 0.0,
    memory_usage = 0.0,
    session_count = 0
WHERE status = 'maintenance';

-- ============================================================================
-- Data Verification Queries (for testing)
-- ============================================================================

-- These queries can be used to verify the sample data was inserted correctly:

-- SELECT 'Device Count:' as metric, COUNT(*) as value FROM fortigate_devices
-- UNION ALL
-- SELECT 'Policy Count:' as metric, COUNT(*) as value FROM fortigate_policies
-- UNION ALL
-- SELECT 'Security Events:' as metric, COUNT(*) as value FROM security_events
-- UNION ALL
-- SELECT 'Active Sessions:' as metric, COUNT(*) as value FROM user_sessions WHERE status = 'active'
-- UNION ALL
-- SELECT 'Recent Events (1h):' as metric, COUNT(*) as value FROM security_events WHERE timestamp > datetime('now', '-1 hour');

-- ============================================================================
-- Sample Data Migration Complete
-- ============================================================================