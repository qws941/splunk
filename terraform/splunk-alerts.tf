# Terraform Configuration for Splunk Alert Deployment
# Provider: Splunk REST API
# Purpose: Automate HEC token creation and alert registration

terraform {
  required_version = ">= 1.0"
  required_providers {
    splunk = {
      source  = "splunk/splunk"
      version = "~> 1.4"
    }
  }
}

# Splunk Provider Configuration
provider "splunk" {
  url                  = var.splunk_url
  username             = var.splunk_username
  password             = var.splunk_password
  insecure_skip_verify = var.insecure_ssl
}

# Variables
variable "splunk_url" {
  description = "Splunk management port URL"
  type        = string
  default     = "https://localhost:8089"
}

variable "splunk_username" {
  description = "Splunk admin username"
  type        = string
  default     = "admin"
}

variable "splunk_password" {
  description = "Splunk admin password"
  type        = string
  sensitive   = true
  default     = "changeme"
}

variable "insecure_ssl" {
  description = "Skip SSL verification (local testing only)"
  type        = bool
  default     = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  sensitive   = true
}

variable "slack_channel" {
  description = "Slack channel for alerts"
  type        = string
  default     = "#security-firewall-alert"
}

# HEC Token for Local Testing
resource "splunk_inputs_http_event_collector" "fortigate_hec" {
  name     = "local-test-token"
  index    = "fortianalyzer"
  source   = "fortigate:hec"
  disabled = false

  # Allow automatic sourcetype assignment
  use_ack = 0
}

# Alert 1: FortiGate Config Change Alert
resource "splunk_saved_searches" "config_change_alert" {
  name     = "FortiGate_Config_Change_Alert"
  search   = <<-EOT
    index=fortianalyzer earliest=rt-30s latest=rt type=event subtype=system
      (logid=0100044546 OR logid=0100044547)
      (cfgpath="firewall.policy*" OR cfgpath="firewall.address*" OR
       cfgpath="firewall.service*" OR cfgpath="system.interface*" OR
       cfgpath="router.static*" OR cfgpath="vpn.ipsec*")
    | dedup devname, user, cfgpath
    | eval details = case(
        isnull(cfgattr), "No details available",
        1=1, substr(cfgattr, 1, 100))
    | eval alert_message = "🔥 FortiGate Config Change - Device: " + devname +
        " | Admin: " + user + " (" + ui + ") | " +
        "Path: " + cfgpath + " | Object: " + cfgobj + " | " +
        "Details: " + details
    | table alert_message, device, admin, access_method, config_path, config_object, details
    | rename alert_message as "Alert Message", device as "Device", admin as "Admin User",
        access_method as "Access Method", config_path as "Config Path",
        config_object as "Config Object", details as "Details"
  EOT
  disabled = false

  # Real-time scheduling
  is_scheduled          = true
  realtime_schedule     = true
  cron_schedule         = "* * * * *"
  schedule_window       = 0
  schedule_priority     = "default"
  max_concurrent        = 1
  restart_on_searchpeer_add = true

  # Alert actions
  actions = "slack"
  action_slack_param_channel = var.slack_channel
  action_slack_param_message = "$result.Alert Message$"
  action_slack_param_webhook_url_override = var.slack_webhook_url

  # Suppression settings (15 seconds)
  alert_suppress         = true
  alert_suppress_period  = "15s"
  alert_suppress_fields  = "user,cfgpath"

  # Trigger condition
  alert_type      = "number of events"
  alert_comparator = "greater than"
  alert_threshold  = "0"
}

# Alert 2: FortiGate Critical Event Alert
resource "splunk_saved_searches" "critical_event_alert" {
  name     = "FortiGate_Critical_Event_Alert"
  search   = <<-EOT
    index=fortianalyzer earliest=rt-30s latest=rt type=event subtype=system level=critical
      logid!=0100044546 logid!=0100044547
    | search NOT msg="*Update Fail*"
    | dedup devname, logid
    | eval alert_message = "🚨 FortiGate CRITICAL Event - Device: " + devname +
        " | LogID: " + logid + " | Severity: " + level + " | " +
        "Description: " + msg
    | table alert_message, device, log_id, severity, description
    | rename alert_message as "Alert Message", device as "Device",
        log_id as "Log ID", severity as "Severity", description as "Description"
  EOT
  disabled = false

  # Real-time scheduling
  is_scheduled          = true
  realtime_schedule     = true
  cron_schedule         = "* * * * *"
  schedule_window       = 0
  schedule_priority     = "default"
  max_concurrent        = 1
  restart_on_searchpeer_add = true

  # Alert actions
  actions = "slack"
  action_slack_param_channel = var.slack_channel
  action_slack_param_message = "$result.Alert Message$"
  action_slack_param_webhook_url_override = var.slack_webhook_url

  # Suppression settings (15 seconds)
  alert_suppress         = true
  alert_suppress_period  = "15s"
  alert_suppress_fields  = "devname"

  # Trigger condition
  alert_type      = "number of events"
  alert_comparator = "greater than"
  alert_threshold  = "0"
}

# Alert 3: FortiGate HA Event Alert
resource "splunk_saved_searches" "ha_event_alert" {
  name     = "FortiGate_HA_Event_Alert"
  search   = <<-EOT
    index=fortianalyzer earliest=rt-30s latest=rt type=event subtype=system logid=0103*
    | dedup devname, logid, level
    | eval icon = case(
        level="critical", "🔴",
        level="error", "🟠",
        level="warning", "🟡",
        1=1, "🔵")
    | eval alert_message = icon + " FortiGate HA Event - Device: " + devname +
        " | Severity: " + level + " | LogID: " + logid + " | " +
        "Description: " + msg
    | table alert_message, device, log_id, severity, description
    | rename alert_message as "Alert Message", device as "Device",
        log_id as "Log ID", severity as "Severity", description as "Description"
  EOT
  disabled = false

  # Real-time scheduling
  is_scheduled          = true
  realtime_schedule     = true
  cron_schedule         = "* * * * *"
  schedule_window       = 0
  schedule_priority     = "default"
  max_concurrent        = 1
  restart_on_searchpeer_add = true

  # Alert actions
  actions = "slack"
  action_slack_param_channel = var.slack_channel
  action_slack_param_message = "$result.Alert Message$"
  action_slack_param_webhook_url_override = var.slack_webhook_url

  # Suppression settings (15 seconds)
  alert_suppress         = true
  alert_suppress_period  = "15s"
  alert_suppress_fields  = "devname"

  # Trigger condition
  alert_type      = "number of events"
  alert_comparator = "greater than"
  alert_threshold  = "0"
}

# Outputs
output "hec_token" {
  description = "HEC token for FortiGate events"
  value       = splunk_inputs_http_event_collector.fortigate_hec.token
  sensitive   = true
}

output "alert_names" {
  description = "Names of created alerts"
  value = [
    splunk_saved_searches.config_change_alert.name,
    splunk_saved_searches.critical_event_alert.name,
    splunk_saved_searches.ha_event_alert.name
  ]
}
