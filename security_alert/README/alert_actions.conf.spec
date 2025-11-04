# alert_actions.conf.spec

[slack]
* Send formatted alert to Slack using Block Kit

param.slack_app_oauth_token = <string>
* Slack Bot OAuth Token (xoxb-...)
* Required if using Bot Token authentication

param.webhook_url = <string>
* Slack Incoming Webhook URL
* Required if using Webhook authentication
* Format: https://hooks.slack.com/services/...

param.proxy_enabled = <0|1>
* Enable proxy for Slack connection
* Default: 0

param.proxy_url = <string>
* Proxy server URL
* Required if proxy_enabled = 1

param.proxy_port = <integer>
* Proxy server port
* Required if proxy_enabled = 1

param.proxy_username = <string>
* Proxy authentication username
* Optional

param.proxy_password = <string>
* Proxy authentication password
* Optional
