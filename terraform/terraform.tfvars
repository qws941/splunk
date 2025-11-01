# Terraform Variables - Local Test Environment
# Generated: 2025-10-30

# Splunk Configuration (Local Docker)
splunk_url      = "https://localhost:8089"
splunk_username = "admin"
splunk_password = "changeme"
insecure_ssl    = true  # Local testing with self-signed cert

# Slack Integration (Optional for local testing)
# Alert execution logs can be verified without Slack
slack_webhook_url = "https://hooks.slack.com/services/PLACEHOLDER/PLACEHOLDER/PLACEHOLDER"
slack_channel     = "#security-firewall-alert"
