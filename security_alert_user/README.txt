⚠️ 사용자별 앱 제약사항

이 앱을 /opt/splunk/etc/users/secmon/security_alert/ 에 배포하면:

❌ 작동 안 하는 기능:
1. Slack 알림 전송 (bin/ 스크립트 실행 안 됨)
2. 자동 field extraction (props.conf 무시됨)
3. Alert 자동 실행 (스케줄러 불안정)

✅ 작동하는 기능:
1. Dashboard 보기
2. 수동 Search 실행
3. Lookup 조회

권장: 시스템 전역 배포 (/opt/splunk/etc/apps/) + metadata 권한 제한
