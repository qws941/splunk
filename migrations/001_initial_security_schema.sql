-- ============================================================================
-- Migration: 001_initial_security_schema.sql
-- Description: Initial database schema for Splunk-FortiNet security integration
-- Created: 2025-09-28
-- ============================================================================

-- Security Events Table - 보안 이벤트 중앙 저장소
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL CHECK (source IN ('fortigate', 'fortianalyzer', 'splunk', 'system')),
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    raw_data TEXT, -- JSON 형태의 원본 데이터
    source_ip TEXT,
    dest_ip TEXT,
    source_port INTEGER,
    dest_port INTEGER,
    protocol TEXT,
    action_taken TEXT,
    processed BOOLEAN DEFAULT FALSE,
    processed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- FortiGate Policies Table - 정책 관리
CREATE TABLE IF NOT EXISTS fortigate_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    policy_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    source_zone TEXT,
    dest_zone TEXT,
    source_addr TEXT, -- JSON array
    dest_addr TEXT,   -- JSON array
    service TEXT,     -- JSON array
    action TEXT NOT NULL CHECK (action IN ('accept', 'deny', 'reject')),
    status TEXT DEFAULT 'enabled' CHECK (status IN ('enabled', 'disabled')),
    nat BOOLEAN DEFAULT FALSE,
    logging BOOLEAN DEFAULT TRUE,
    schedule TEXT DEFAULT 'always',
    comments TEXT,
    hit_count INTEGER DEFAULT 0,
    last_hit DATETIME,
    created_by TEXT DEFAULT 'system',
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    fortigate_device TEXT NOT NULL,
    sync_status TEXT DEFAULT 'synced' CHECK (sync_status IN ('synced', 'pending', 'error'))
);

-- FortiGate Devices Table - 디바이스 관리
CREATE TABLE IF NOT EXISTS fortigate_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    hostname TEXT UNIQUE NOT NULL,
    ip_address TEXT NOT NULL,
    serial_number TEXT UNIQUE,
    model TEXT,
    firmware_version TEXT,
    location TEXT,
    zone TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    last_sync DATETIME,
    sync_status TEXT DEFAULT 'unknown' CHECK (sync_status IN ('connected', 'disconnected', 'error', 'unknown')),
    policy_count INTEGER DEFAULT 0,
    cpu_usage REAL DEFAULT 0.0,
    memory_usage REAL DEFAULT 0.0,
    session_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Splunk Integration Table - Splunk 연동 상태
CREATE TABLE IF NOT EXISTS splunk_integration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    splunk_server TEXT NOT NULL,
    index_name TEXT NOT NULL,
    sourcetype TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
    last_sync DATETIME,
    events_synced INTEGER DEFAULT 0,
    last_event_timestamp DATETIME,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User Sessions Table - 사용자 세션 관리
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT DEFAULT 'viewer' CHECK (role IN ('admin', 'operator', 'viewer')),
    ip_address TEXT,
    user_agent TEXT,
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'expired', 'revoked'))
);

-- Audit Log Table - 감사 로그
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    username TEXT,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    old_values TEXT, -- JSON
    new_values TEXT, -- JSON
    ip_address TEXT,
    user_agent TEXT,
    status TEXT DEFAULT 'success' CHECK (status IN ('success', 'failure', 'error')),
    error_message TEXT
);

-- System Configuration Table - 시스템 설정
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'general',
    data_type TEXT DEFAULT 'string' CHECK (data_type IN ('string', 'number', 'boolean', 'json')),
    updated_by TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Alert Rules Table - 알림 규칙
CREATE TABLE IF NOT EXISTS alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    condition_query TEXT NOT NULL, -- SQL query for condition
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    enabled BOOLEAN DEFAULT TRUE,
    notification_channels TEXT, -- JSON array
    threshold_value REAL,
    threshold_period INTEGER DEFAULT 300, -- seconds
    last_triggered DATETIME,
    trigger_count INTEGER DEFAULT 0,
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES for Performance Optimization
-- ============================================================================

-- Security Events Indexes
CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_events_source ON security_events(source);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_processed ON security_events(processed);
CREATE INDEX IF NOT EXISTS idx_security_events_source_ip ON security_events(source_ip);
CREATE INDEX IF NOT EXISTS idx_security_events_dest_ip ON security_events(dest_ip);

-- FortiGate Policies Indexes
CREATE INDEX IF NOT EXISTS idx_fortigate_policies_status ON fortigate_policies(status);
CREATE INDEX IF NOT EXISTS idx_fortigate_policies_device ON fortigate_policies(fortigate_device);
CREATE INDEX IF NOT EXISTS idx_fortigate_policies_action ON fortigate_policies(action);
CREATE INDEX IF NOT EXISTS idx_fortigate_policies_updated ON fortigate_policies(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_fortigate_policies_sync ON fortigate_policies(sync_status);

-- FortiGate Devices Indexes
CREATE INDEX IF NOT EXISTS idx_fortigate_devices_status ON fortigate_devices(status);
CREATE INDEX IF NOT EXISTS idx_fortigate_devices_sync ON fortigate_devices(sync_status);
CREATE INDEX IF NOT EXISTS idx_fortigate_devices_last_sync ON fortigate_devices(last_sync DESC);

-- Splunk Integration Indexes
CREATE INDEX IF NOT EXISTS idx_splunk_integration_status ON splunk_integration(status);
CREATE INDEX IF NOT EXISTS idx_splunk_integration_last_sync ON splunk_integration(last_sync DESC);

-- User Sessions Indexes
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_status ON user_sessions(status);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

-- Audit Logs Indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(username);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Alert Rules Indexes
CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_alert_rules_severity ON alert_rules(severity);

-- ============================================================================
-- TRIGGERS for Automatic Timestamp Updates
-- ============================================================================

-- Security Events Update Trigger
CREATE TRIGGER IF NOT EXISTS trigger_security_events_updated_at
    AFTER UPDATE ON security_events
BEGIN
    UPDATE security_events SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- FortiGate Policies Update Trigger
CREATE TRIGGER IF NOT EXISTS trigger_fortigate_policies_updated_at
    AFTER UPDATE ON fortigate_policies
BEGIN
    UPDATE fortigate_policies SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- FortiGate Devices Update Trigger
CREATE TRIGGER IF NOT EXISTS trigger_fortigate_devices_updated_at
    AFTER UPDATE ON fortigate_devices
BEGIN
    UPDATE fortigate_devices SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Splunk Integration Update Trigger
CREATE TRIGGER IF NOT EXISTS trigger_splunk_integration_updated_at
    AFTER UPDATE ON splunk_integration
BEGIN
    UPDATE splunk_integration SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Alert Rules Update Trigger
CREATE TRIGGER IF NOT EXISTS trigger_alert_rules_updated_at
    AFTER UPDATE ON alert_rules
BEGIN
    UPDATE alert_rules SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- INITIAL DATA INSERTION
-- ============================================================================

-- Default System Configuration
INSERT OR IGNORE INTO system_config (key, value, description, category) VALUES
    ('app_version', '1.0.0', 'Application version', 'system'),
    ('max_events_per_page', '100', 'Maximum events to display per page', 'ui'),
    ('default_timezone', 'UTC', 'Default timezone for the application', 'system'),
    ('session_timeout', '3600', 'Session timeout in seconds', 'security'),
    ('max_login_attempts', '5', 'Maximum failed login attempts', 'security'),
    ('alert_email_enabled', 'false', 'Enable email alerts', 'notifications'),
    ('data_retention_days', '365', 'Days to retain security events', 'system'),
    ('auto_sync_interval', '300', 'Auto sync interval in seconds', 'integration'),
    ('fortigate_api_timeout', '30', 'FortiGate API timeout in seconds', 'integration'),
    ('splunk_hec_timeout', '30', 'Splunk HEC timeout in seconds', 'integration');

-- Default Alert Rules
INSERT OR IGNORE INTO alert_rules (name, description, condition_query, severity, enabled, notification_channels) VALUES
    ('High Severity Events', 'Alert when high severity events occur',
     'SELECT COUNT(*) FROM security_events WHERE severity = ''high'' AND timestamp > datetime(''now'', ''-5 minutes'')',
     'high', 1, '["email", "webhook"]'),
    ('Critical Security Events', 'Alert for critical security events',
     'SELECT COUNT(*) FROM security_events WHERE severity = ''critical'' AND timestamp > datetime(''now'', ''-1 minute'')',
     'critical', 1, '["email", "slack", "webhook"]'),
    ('FortiGate Policy Changes', 'Alert when FortiGate policies are modified',
     'SELECT COUNT(*) FROM audit_logs WHERE action = ''policy_update'' AND timestamp > datetime(''now'', ''-10 minutes'')',
     'medium', 1, '["email"]'),
    ('Device Disconnect Alert', 'Alert when FortiGate devices disconnect',
     'SELECT COUNT(*) FROM fortigate_devices WHERE sync_status = ''disconnected'' AND last_sync < datetime(''now'', ''-15 minutes'')',
     'high', 1, '["email", "webhook"]');

-- ============================================================================
-- Migration Complete
-- ============================================================================