<#
.SYNOPSIS
    Deploy Splunk Dashboard Studio JSON files via REST API (Windows PowerShell)

.DESCRIPTION
    Deploys Dashboard Studio JSON files to Splunk Enterprise via REST API.
    Supports single dashboard or batch deployment.

.PARAMETER SplunkHost
    Splunk server hostname (default: splunk.jclee.me)

.PARAMETER SplunkPort
    Splunk REST API port (default: 8089)

.PARAMETER Username
    Splunk admin username (default: admin)

.PARAMETER Password
    Splunk admin password (if not provided, will prompt)

.PARAMETER DashboardPath
    Path to dashboard JSON file or directory

.PARAMETER Validate
    Validate JSON syntax only (no deployment)

.PARAMETER Verify
    Verify deployed dashboards after deployment

.EXAMPLE
    .\Deploy-SplunkDashboards.ps1 -DashboardPath "configs\dashboards\studio-production"

.EXAMPLE
    .\Deploy-SplunkDashboards.ps1 -DashboardPath "01-fortigate-operations.json" -Validate

.EXAMPLE
    .\Deploy-SplunkDashboards.ps1 -Verify

.NOTES
    Author: JC Lee
    Date: 2025-10-25
    Version: 1.0
    Requires: PowerShell 5.1+, Splunk 9.0+
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$SplunkHost = "splunk.jclee.me",

    [Parameter(Mandatory=$false)]
    [int]$SplunkPort = 8089,

    [Parameter(Mandatory=$false)]
    [string]$Username = "admin",

    [Parameter(Mandatory=$false)]
    [SecureString]$Password,

    [Parameter(Mandatory=$false)]
    [string]$DashboardPath = "configs\dashboards\studio-production",

    [Parameter(Mandatory=$false)]
    [switch]$Validate,

    [Parameter(Mandatory=$false)]
    [switch]$Verify
)

# =============================================================================
# Configuration
# =============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # Faster Invoke-WebRequest

# Script directories
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DashboardDir = Join-Path $ProjectRoot $DashboardPath

# =============================================================================
# Functions
# =============================================================================

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )

    switch ($Type) {
        "Success" { Write-Host "✅ $Message" -ForegroundColor Green }
        "Error"   { Write-Host "❌ $Message" -ForegroundColor Red }
        "Warning" { Write-Host "⚠ $Message" -ForegroundColor Yellow }
        "Info"    { Write-Host "ℹ $Message" -ForegroundColor Cyan }
        default   { Write-Host $Message }
    }
}

function Test-JsonSyntax {
    param([string]$FilePath)

    try {
        $null = Get-Content $FilePath -Raw | ConvertFrom-Json
        return $true
    } catch {
        Write-ColorOutput "Invalid JSON: $($_.Exception.Message)" -Type Error
        return $false
    }
}

function Get-SplunkCredential {
    if (-not $Password) {
        $Password = Read-Host "Enter Splunk password for '$Username'" -AsSecureString
    }

    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)
    $PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

    # Create Basic Auth header
    $base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${PlainPassword}"))

    return @{
        Authorization = "Basic $base64Auth"
    }
}

function Test-SplunkConnection {
    param([hashtable]$Headers)

    try {
        $uri = "https://${SplunkHost}:${SplunkPort}/services/server/info"

        $response = Invoke-RestMethod -Uri $uri `
            -Method Get `
            -Headers $Headers `
            -SkipCertificateCheck `
            -TimeoutSec 10

        Write-ColorOutput "Connected to Splunk $($response.entry.content.version)" -Type Success
        return $true
    } catch {
        Write-ColorOutput "Connection failed: $($_.Exception.Message)" -Type Error
        return $false
    }
}

function Deploy-Dashboard {
    param(
        [string]$FilePath,
        [hashtable]$Headers
    )

    $DashboardName = [System.IO.Path]::GetFileNameWithoutExtension($FilePath)

    Write-ColorOutput "Deploying: $DashboardName" -Type Info

    # Validate JSON
    if (-not (Test-JsonSyntax -FilePath $FilePath)) {
        return $false
    }

    # Read JSON content
    $JsonContent = Get-Content $FilePath -Raw

    # Prepare form data for Splunk REST API
    # Splunk expects: name=<dashboard_name>&eai:data=<json_content>
    $FormData = @{
        "name" = $DashboardName
        "eai:data" = $JsonContent
    }

    # Deploy via REST API
    try {
        $uri = "https://${SplunkHost}:${SplunkPort}/servicesNS/nobody/search/data/ui/views"

        $response = Invoke-RestMethod -Uri $uri `
            -Method Post `
            -Headers $Headers `
            -ContentType "application/x-www-form-urlencoded" `
            -Body $FormData `
            -SkipCertificateCheck `
            -TimeoutSec 30

        Write-ColorOutput "Deployed: $DashboardName" -Type Success
        return $true

    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__

        if ($statusCode -eq 409) {
            Write-ColorOutput "Dashboard already exists, updating..." -Type Warning

            # Update via POST (Splunk uses POST for updates, not PUT)
            try {
                $updateUri = "${uri}/${DashboardName}"

                $response = Invoke-RestMethod -Uri $updateUri `
                    -Method Post `
                    -Headers $Headers `
                    -ContentType "application/x-www-form-urlencoded" `
                    -Body @{ "eai:data" = $JsonContent } `
                    -SkipCertificateCheck `
                    -TimeoutSec 30

                Write-ColorOutput "Updated: $DashboardName" -Type Success
                return $true
            } catch {
                Write-ColorOutput "Update failed: $($_.Exception.Message)" -Type Error
                return $false
            }
        } else {
            Write-ColorOutput "Deployment failed (HTTP $statusCode): $($_.Exception.Message)" -Type Error
            return $false
        }
    }
}

function Get-DeployedDashboards {
    param([hashtable]$Headers)

    try {
        $uri = "https://${SplunkHost}:${SplunkPort}/servicesNS/nobody/search/data/ui/views?output_mode=json&count=-1"

        $response = Invoke-RestMethod -Uri $uri `
            -Method Get `
            -Headers $Headers `
            -SkipCertificateCheck `
            -TimeoutSec 30

        return $response.entry
    } catch {
        Write-ColorOutput "Failed to retrieve dashboards: $($_.Exception.Message)" -Type Error
        return @()
    }
}

# =============================================================================
# Main Script
# =============================================================================

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Splunk Dashboard Studio Deployment (PowerShell)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Get credentials
$Headers = Get-SplunkCredential

# Validate only mode
if ($Validate) {
    Write-ColorOutput "Validation mode (no deployment)" -Type Info
    Write-Host ""

    if (Test-Path $DashboardDir -PathType Container) {
        $Files = Get-ChildItem -Path $DashboardDir -Filter "*.json"
    } elseif (Test-Path $DashboardPath -PathType Leaf) {
        $Files = @(Get-Item $DashboardPath)
    } else {
        Write-ColorOutput "Path not found: $DashboardPath" -Type Error
        exit 1
    }

    $ValidCount = 0
    $InvalidCount = 0

    foreach ($File in $Files) {
        Write-Host "Validating: $($File.Name)" -NoNewline

        if (Test-JsonSyntax -FilePath $File.FullName) {
            Write-ColorOutput " ✅" -Type Success
            $ValidCount++
        } else {
            Write-ColorOutput " ❌" -Type Error
            $InvalidCount++
        }
    }

    Write-Host ""
    Write-ColorOutput "Validation complete: $ValidCount valid, $InvalidCount invalid" -Type Info
    exit 0
}

# Verify mode
if ($Verify) {
    Write-ColorOutput "Verification mode" -Type Info
    Write-Host ""

    if (-not (Test-SplunkConnection -Headers $Headers)) {
        exit 1
    }

    $Dashboards = Get-DeployedDashboards -Headers $Headers
    $StudioDashboards = $Dashboards | Where-Object { $_.name -like "*fortigate*" -or $_.name -like "*faz*" -or $_.name -like "*slack*" }

    if ($StudioDashboards.Count -eq 0) {
        Write-ColorOutput "No Studio dashboards found" -Type Warning
    } else {
        Write-ColorOutput "Found $($StudioDashboards.Count) dashboards:" -Type Info
        Write-Host ""

        foreach ($Dashboard in $StudioDashboards) {
            Write-Host "  - $($Dashboard.name)" -ForegroundColor Green
            Write-Host "    Author: $($Dashboard.author)" -ForegroundColor Gray
            Write-Host "    Updated: $($Dashboard.updated)" -ForegroundColor Gray
        }
    }

    Write-Host ""
    exit 0
}

# Deployment mode
Write-ColorOutput "Deployment mode" -Type Info
Write-Host ""

# Test connection
if (-not (Test-SplunkConnection -Headers $Headers)) {
    exit 1
}

Write-Host ""

# Get dashboard files
if (Test-Path $DashboardDir -PathType Container) {
    $Files = Get-ChildItem -Path $DashboardDir -Filter "*.json"
    Write-ColorOutput "Found $($Files.Count) dashboard(s) in $DashboardDir" -Type Info
} elseif (Test-Path $DashboardPath -PathType Leaf) {
    $Files = @(Get-Item $DashboardPath)
    Write-ColorOutput "Deploying single dashboard: $($Files[0].Name)" -Type Info
} else {
    Write-ColorOutput "Path not found: $DashboardPath" -Type Error
    exit 1
}

Write-Host ""

# Deploy each dashboard
$SuccessCount = 0
$FailCount = 0

foreach ($File in $Files) {
    if (Deploy-Dashboard -FilePath $File.FullName -Headers $Headers) {
        $SuccessCount++
    } else {
        $FailCount++
    }

    Start-Sleep -Milliseconds 500  # Rate limiting
    Write-Host ""
}

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-ColorOutput "Deployment Summary" -Type Info
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Write-ColorOutput "Successfully deployed: $SuccessCount" -Type Success

if ($FailCount -gt 0) {
    Write-ColorOutput "Failed deployments: $FailCount" -Type Error
    exit 1
} else {
    Write-ColorOutput "All dashboards deployed successfully!" -Type Success
    Write-Host ""
    Write-ColorOutput "View dashboards: https://${SplunkHost}:8000/app/search/dashboards" -Type Info
}

Write-Host ""
