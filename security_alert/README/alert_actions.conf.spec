# alert_actions.conf.spec
# Specification file for Slack Block Kit custom alert action

[slack]
# Slack Authentication Methods

param.slack_app_oauth_token = <string>
* Slack Bot User OAuth Token (starts with xoxb-)
* Required for Method 1: Bot Token authentication
* Optional if using webhook_url
* Default: empty

param.webhook_url = <string>
* Slack Incoming Webhook URL (starts with https://hooks.slack.com/services/)
* Required for Method 2: Webhook authentication
* Optional if using slack_app_oauth_token
* Default: empty

# Proxy Configuration (Optional)

param.proxy_enabled = <boolean>
* Enable HTTP/HTTPS proxy for Slack API calls
* Set to 1 or true to enable, 0 or false to disable
* Default: 0

param.proxy_url = <string>
* Proxy server hostname or IP address
* Required if proxy_enabled is true
* Example: proxy.company.com
* Default: empty

param.proxy_port = <string>
* Proxy server port number
* Required if proxy_enabled is true
* Example: 8080, 3128
* Default: empty

param.proxy_username = <string>
* Proxy authentication username
* Optional, only needed if proxy requires authentication
* Default: empty

param.proxy_password = <string>
* Proxy authentication password
* Optional, only needed if proxy requires authentication
* Default: empty
