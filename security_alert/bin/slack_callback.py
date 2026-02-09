#!/usr/bin/env python3
"""
Splunk Custom REST Handler for Slack Interactive Components
Handles button callbacks from Slack alerts (Acknowledge, Snooze)
"""

import os
import sys

# Add vendored libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

import csv
import hashlib
import hmac
import json
import time
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

import fcntl

import splunk.admin as admin


def get_alert_state_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "..", "lookups", "alert_state.csv")


def verify_slack_signature(signing_secret, timestamp, body, signature):
    """Verify Slack request signature for security"""
    if abs(time.time() - float(timestamp)) > 60 * 5:
        return False

    sig_basestring = f"v0:{timestamp}:{body}"
    my_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode(), sig_basestring.encode(), hashlib.sha256
        ).hexdigest()
    )

    return hmac.compare_digest(my_signature, signature)


def update_alert_state(alert_id, status, acked_by=""):
    state_file = get_alert_state_path()

    if not os.path.exists(state_file):
        return False

    rows = []
    updated = False

    with open(state_file, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row.get("alert_id") == alert_id or row.get("message_ts") == alert_id:
                    row["status"] = status
                    row["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row["acked_by"] = acked_by
                    updated = True
                rows.append(row)

            if updated:
                f.seek(0)
                f.truncate()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    return updated


def update_slack_message(bot_token, channel, ts, new_text, original_blocks=None):
    """Update Slack message to show acknowledged status"""
    if requests is None:
        return {"ok": False, "error": "requests library not available"}

    if original_blocks:
        for block in original_blocks:
            if block.get("type") == "actions":
                original_blocks.remove(block)
                break

        original_blocks.append(
            {"type": "context", "elements": [{"type": "mrkdwn", "text": new_text}]}
        )
        payload = {"channel": channel, "ts": ts, "blocks": original_blocks}
    else:
        payload = {"channel": channel, "ts": ts, "text": new_text}

    response = requests.post(
        "https://slack.com/api/chat.update",
        json=payload,
        timeout=10,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bot_token}",
        },
    )
    return response.json()


class SlackCallbackHandler(admin.MConfigHandler):

    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            self.supportedArgs.addOptArg("payload")
            self.supportedArgs.addOptArg("*")

    def handleEdit(self, confInfo):
        try:
            # Verify Slack request signature if signing secret is configured
            signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "")
            timestamp = self.callerArgs.get("X-Slack-Request-Timestamp", [None])[0]
            signature = self.callerArgs.get("X-Slack-Signature", [None])[0]
            raw_body = self.callerArgs.get("payload", [None])[0] or ""

            if signing_secret and timestamp and signature:
                if not verify_slack_signature(
                    signing_secret, timestamp, raw_body, signature
                ):
                    confInfo["result"]["status"] = "error"
                    confInfo["result"]["message"] = "Invalid Slack signature"
                    return

            payload_str = self.callerArgs.get("payload", [None])[0]

            if not payload_str:
                confInfo["result"]["status"] = "error"
                confInfo["result"]["message"] = "No payload received"
                return

            payload = json.loads(payload_str)

            action_type = payload.get("type")

            if action_type == "block_actions":
                actions = payload.get("actions", [])
                user = payload.get("user", {})
                user_name = user.get("name", user.get("username", "Unknown"))

                for action in actions:
                    action_id = action.get("action_id")
                    alert_id = action.get("value")

                    if action_id == "ack_alert":
                        update_alert_state(alert_id, "acknowledged", user_name)

                        confInfo["result"]["status"] = "ok"
                        confInfo["result"]["response_action"] = "update"
                        confInfo["result"][
                            "text"
                        ] = f"✅ *Acknowledged* by @{user_name} at {datetime.now().strftime('%H:%M:%S')}"

                    elif action_id.startswith("snooze_alert"):
                        duration = action_id.split("_")[-1]
                        update_alert_state(alert_id, f"snoozed_{duration}", user_name)

                        confInfo["result"]["status"] = "ok"
                        confInfo["result"]["response_action"] = "update"
                        confInfo["result"][
                            "text"
                        ] = f"🔇 *Snoozed* for {duration} by @{user_name}"

            else:
                confInfo["result"]["status"] = "ignored"
                confInfo["result"]["message"] = f"Unknown action type: {action_type}"

        except Exception as e:
            confInfo["result"]["status"] = "error"
            confInfo["result"]["message"] = str(e)


admin.init(SlackCallbackHandler, admin.CONTEXT_NONE)
