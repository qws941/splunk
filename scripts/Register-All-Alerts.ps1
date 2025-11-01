# Register-All-Alerts.ps1
# FortiGate 17개 알림을 Splunk REST API로 등록
# 하드코딩된 설정: 172.28.32.67:8089, secmon / Ntmxmec15!

# SSL 인증서 무시 (자체 서명 인증서)
add-type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicy : ICertificatePolicy {
    public bool CheckValidationResult(
        ServicePoint svcPoint, X509Certificate certificate,
        WebRequest request, int certificateProblem) {
        return true;
    }
}
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# 하드코딩된 설정
$SplunkHost = "172.28.32.67"
$SplunkPort = 8000  # Web UI 포트 (REST API도 가능, 8089는 관리 포트)
$SplunkUser = "secmon"
$SplunkPassword = "Ntmxmec15!"
$DryRun = $false  # $true로 변경하면 테스트 모드

# Splunk REST API 엔드포인트
$baseUrl = "https://${SplunkHost}:${SplunkPort}"
$apiUrl = "$baseUrl/servicesNS/nobody/search/saved/searches"

# 인증
$base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${SplunkUser}:${SplunkPassword}"))
$headers = @{
    "Authorization" = "Basic $base64Auth"
    "Content-Type" = "application/x-www-form-urlencoded"
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Splunk Alert Registration Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Splunk Host: $SplunkHost" -ForegroundColor Yellow
Write-Host "API Port: $SplunkPort" -ForegroundColor Yellow
Write-Host "User: $SplunkUser" -ForegroundColor Yellow
Write-Host "Dry Run: $DryRun" -ForegroundColor Yellow
Write-Host ""

# api 폴더의 모든 .txt 파일 읽기
$alertFiles = Get-ChildItem -Path ".\api" -Filter "*-blockkit.txt" | Sort-Object Name

if ($alertFiles.Count -eq 0) {
    Write-Host "❌ No alert files found in current directory" -ForegroundColor Red
    exit 1
}

Write-Host "Found $($alertFiles.Count) alert files" -ForegroundColor Green
Write-Host ""

$successCount = 0
$errorCount = 0

foreach ($file in $alertFiles) {
    Write-Host "Processing: $($file.Name)" -ForegroundColor Cyan

    # 파일 내용을 key=value 형식으로 파싱
    $content = Get-Content $file.FullName -Raw
    $params = @{}

    # 각 줄을 파싱 (name=value)
    $lines = $content -split "`n"
    foreach ($line in $lines) {
        if ($line -match '^([^=]+)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            $params[$key] = $value
        }
    }

    if (-not $params.ContainsKey('name') -or -not $params.ContainsKey('search')) {
        Write-Host "  ⚠️  Skipping: Missing name or search" -ForegroundColor Yellow
        continue
    }

    $alertName = $params['name']
    Write-Host "  Alert Name: $alertName" -ForegroundColor White

    if ($DryRun) {
        Write-Host "  ✓ DRY RUN - Would register this alert" -ForegroundColor Green
        $successCount++
        Write-Host ""
        continue
    }

    # URL 인코딩된 body 생성
    $body = ""
    foreach ($key in $params.Keys) {
        $encodedValue = [System.Web.HttpUtility]::UrlEncode($params[$key])
        if ($body -ne "") { $body += "&" }
        $body += "$key=$encodedValue"
    }

    try {
        # REST API 호출
        $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers $headers -Body $body -ErrorAction Stop

        Write-Host "  ✓ Successfully registered" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host "  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red

        # 상세 에러 정보
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "  Response: $responseBody" -ForegroundColor Red
        }

        $errorCount++
    }

    Write-Host ""
    Start-Sleep -Milliseconds 500  # API 호출 간 짧은 대기
}

# 결과 요약
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Registration Summary" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Total Alerts: $($alertFiles.Count)" -ForegroundColor White
Write-Host "Success: $successCount" -ForegroundColor Green
Write-Host "Errors: $errorCount" -ForegroundColor Red

if ($DryRun) {
    Write-Host ""
    Write-Host "This was a DRY RUN. No alerts were actually registered." -ForegroundColor Yellow
    Write-Host "Change `$DryRun = `$false in script to register alerts." -ForegroundColor Yellow
}

# 검증 쿼리 출력
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Verification" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Splunk Web: http://172.28.32.67:8000" -ForegroundColor Yellow
Write-Host "Login: secmon / Ntmxmec15!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Run this SPL query in Splunk to verify:" -ForegroundColor Yellow
Write-Host ""
Write-Host "| rest /services/saved/searches" -ForegroundColor White
Write-Host "| search title=`"*_*`"" -ForegroundColor White
Write-Host "| table title, disabled, realtime_schedule, actions" -ForegroundColor White
Write-Host "| sort title" -ForegroundColor White
Write-Host ""

if ($errorCount -eq 0 -and -not $DryRun) {
    Write-Host "✓ All alerts registered successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Login to Splunk: http://172.28.32.67:8000" -ForegroundColor White
    Write-Host "2. Go to: Settings → Searches, reports, and alerts" -ForegroundColor White
    Write-Host "3. Enable alerts you want to activate" -ForegroundColor White
    exit 0
} else {
    exit 1
}
