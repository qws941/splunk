# ========================================
# Slack Block Kit Alert Action Specification
# App: security_alert v2.0.4
# ========================================

[slack]
param.bot_token = <string>
* Slack Bot OAuth Token (xoxb-<example>)
* Method 1: Preferred for production (OAuth)
* Required: Either bot_token OR webhook_url

param.webhook_url = <string>
* Slack incoming webhook URL (https://hooks.slack.com/services/...)
* Method 2: Alternative to bot_token
* Required: Either bot_token OR webhook_url

param.channel = <string>
* Slack channel to send alerts to (e.g., #security-firewall-alert)
* Required: Yes

param.icon_emoji = <string>
* Emoji icon for the bot (e.g., :rotating_light:)
* Default: :rotating_light:

param.username = <string>
* Display name for the bot
* Default: FortiGate Alert Bot
