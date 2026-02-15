#!/bin/bash
# Deploy Syslog-based Slack Alert System (Dashboard + 5 Alerts)

SPLUNK_HOST="${SPLUNK_HOST:-splunk.jclee.me}"
SPLUNK_PORT="${SPLUNK_PORT:-8065}"
SPLUNK_USER="${SPLUNK_USER:-admin}"
SPLUNK_PASSWORD="${SPLUNK_PASSWORD}"

if [ -z "$SPLUNK_PASSWORD" ]; then
    echo "🔑 Splunk password not set in environment variable"
    read -sp "Enter Splunk password for $SPLUNK_USER: " SPLUNK_PASSWORD
    echo ""
    if [ -z "$SPLUNK_PASSWORD" ]; then
        echo "❌ Error: Password cannot be empty"
        exit 1
    fi
fi

echo "🚀 Deploying Syslog Slack Alert System..."
echo "   Host: $SPLUNK_HOST:$SPLUNK_PORT"
echo ""

# Deploy Dashboard
echo "📊 [1/6] Deploying Dashboard..."
curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
    -d "eai:data=$(cat configs/dashboards/slack-control.xml)" \
    "https://$SPLUNK_HOST:$SPLUNK_PORT/servicesNS/nobody/search/data/ui/views/slack_control" > /dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ Dashboard deployed"
else
    echo "   ❌ Dashboard failed"
fi

# Deploy Alert 1: FAZ_Critical_Alerts
echo "🔴 [2/6] Deploying FAZ_Critical_Alerts..."
curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
    -d "name=FAZ_Critical_Alerts" \
    -d "description=FortiAnalyzer 크리티컬 이벤트 (Update Fail, Login Fail 제외)" \
    -d 'search=index=fw sourcetype=fw_log earliest=-5m latest=now | search (severity=critical OR level=critical) | search NOT msg="*Update Fail*" | search NOT msg="*login*fail*" | search NOT msg="*authentication*fail*" | eval src_ip=coalesce(srcip, src, "N/A") | eval dst_ip=coalesce(dstip, dst, "N/A") | eval severity_level=coalesce(severity, level, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="🔴 *FAZ Critical Alert*\n출발지: ".src_ip."\n목적지: ".dst_ip."\n심각도: ".severity_level."\n메시지: ".message | head 1 | table alert_text' \
    -d "cron_schedule=*/5 * * * *" \
    -d "dispatch.earliest_time=-5m" \
    -d "dispatch.latest_time=now" \
    -d "alert.track=1" \
    -d "counttype=number of events" \
    -d "quantity=0" \
    -d "relation=greater than" \
    -d "action.slack=1" \
    -d "action.slack.param.channel=#splunk-alerts" \
    -d 'action.slack.param.message=$result.alert_text$' \
    "https://$SPLUNK_HOST:$SPLUNK_PORT/servicesNS/nobody/search/saved/searches" > /dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ FAZ_Critical_Alerts created"
else
    echo "   ❌ FAZ_Critical_Alerts failed"
fi

# Deploy Alert 2: FMG_Policy_Install
echo "📦 [3/6] Deploying FMG_Policy_Install..."
curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
    -d "name=FMG_Policy_Install" \
    -d "description=FortiManager 정책 설치 이벤트" \
    -d 'search=index=fw sourcetype=fw_log earliest=-5m latest=now | search (action=install OR msg="*install*policy*") | eval user_name=coalesce(user, "N/A") | eval src_ip=coalesce(srcip, src, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="📦 *FMG Policy Install*\n사용자: ".user_name."\n출발지: ".src_ip."\n메시지: ".message | head 1 | table alert_text' \
    -d "cron_schedule=*/5 * * * *" \
    -d "dispatch.earliest_time=-5m" \
    -d "dispatch.latest_time=now" \
    -d "alert.track=1" \
    -d "counttype=number of events" \
    -d "quantity=0" \
    -d "relation=greater than" \
    -d "action.slack=1" \
    -d "action.slack.param.channel=#splunk-alerts" \
    -d 'action.slack.param.message=$result.alert_text$' \
    "https://$SPLUNK_HOST:$SPLUNK_PORT/servicesNS/nobody/search/saved/searches" > /dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ FMG_Policy_Install created"
else
    echo "   ❌ FMG_Policy_Install failed"
fi

# Deploy Alert 3: FMG_Policy_CRUD
echo "✏️ [4/6] Deploying FMG_Policy_CRUD..."
curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
    -d "name=FMG_Policy_CRUD" \
    -d "description=FortiManager 정책 CRUD 작업" \
    -d 'search=index=fw sourcetype=fw_log earliest=-5m latest=now | search object="*policy*" operation IN (add,set,delete,create,modify,remove) | eval operation_type=coalesce(operation, action, "N/A") | eval user_name=coalesce(user, "N/A") | eval object_name=coalesce(object, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="✏️ *FMG Policy CRUD*\n작업: ".operation_type."\n사용자: ".user_name."\n객체: ".object_name."\n메시지: ".message | head 1 | table alert_text' \
    -d "cron_schedule=*/5 * * * *" \
    -d "dispatch.earliest_time=-5m" \
    -d "dispatch.latest_time=now" \
    -d "alert.track=1" \
    -d "counttype=number of events" \
    -d "quantity=0" \
    -d "relation=greater than" \
    -d "action.slack=1" \
    -d "action.slack.param.channel=#splunk-alerts" \
    -d 'action.slack.param.message=$result.alert_text$' \
    "https://$SPLUNK_HOST:$SPLUNK_PORT/servicesNS/nobody/search/saved/searches" > /dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ FMG_Policy_CRUD created"
else
    echo "   ❌ FMG_Policy_CRUD failed"
fi

# Deploy Alert 4: FMG_Object_CRUD
echo "🔧 [5/6] Deploying FMG_Object_CRUD..."
curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
    -d "name=FMG_Object_CRUD" \
    -d "description=FortiManager 객체 CRUD 작업" \
    -d 'search=index=fw sourcetype=fw_log earliest=-5m latest=now | search object IN (address,service,vip,addrgrp,servgrp) operation IN (add,set,delete,create,modify,remove) | eval operation_type=coalesce(operation, action, "N/A") | eval user_name=coalesce(user, "N/A") | eval object_type=coalesce(object, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="🔧 *FMG Object CRUD*\n작업: ".operation_type."\n사용자: ".user_name."\n객체 유형: ".object_type."\n메시지: ".message | head 1 | table alert_text' \
    -d "cron_schedule=*/5 * * * *" \
    -d "dispatch.earliest_time=-5m" \
    -d "dispatch.latest_time=now" \
    -d "alert.track=1" \
    -d "counttype=number of events" \
    -d "quantity=0" \
    -d "relation=greater than" \
    -d "action.slack=1" \
    -d "action.slack.param.channel=#splunk-alerts" \
    -d 'action.slack.param.message=$result.alert_text$' \
    "https://$SPLUNK_HOST:$SPLUNK_PORT/servicesNS/nobody/search/saved/searches" > /dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ FMG_Object_CRUD created"
else
    echo "   ❌ FMG_Object_CRUD failed"
fi

# Deploy Alert 5: Security_High_Severity
echo "⚠️ [6/6] Deploying Security_High_Severity..."
curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
    -d "name=Security_High_Severity" \
    -d "description=높은 심각도 보안 이벤트" \
    -d 'search=index=fw sourcetype=fw_log earliest=-5m latest=now | search (severity=high OR level=high) | eval src_ip=coalesce(srcip, src, "N/A") | eval dst_ip=coalesce(dstip, dst, "N/A") | eval severity_level=coalesce(severity, level, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="⚠️ *Security High Alert*\n출발지: ".src_ip."\n목적지: ".dst_ip."\n심각도: ".severity_level."\n메시지: ".message | head 1 | table alert_text' \
    -d "cron_schedule=*/5 * * * *" \
    -d "dispatch.earliest_time=-5m" \
    -d "dispatch.latest_time=now" \
    -d "alert.track=1" \
    -d "counttype=number of events" \
    -d "quantity=0" \
    -d "relation=greater than" \
    -d "action.slack=1" \
    -d "action.slack.param.channel=#splunk-alerts" \
    -d 'action.slack.param.message=$result.alert_text$' \
    "https://$SPLUNK_HOST:$SPLUNK_PORT/servicesNS/nobody/search/saved/searches" > /dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ Security_High_Severity created"
else
    echo "   ❌ Security_High_Severity failed"
fi

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "🔗 Dashboard: https://$SPLUNK_HOST/app/search/slack_control"
echo "📋 Alerts: Settings → Searches, reports, and alerts"
echo ""
