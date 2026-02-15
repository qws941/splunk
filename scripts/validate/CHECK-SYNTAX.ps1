# Check PowerShell syntax
$scriptPath = "Register-All-Alerts.ps1"
$errors = $null
$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $scriptPath -Raw), [ref]$errors)

if ($errors) {
    Write-Host "Syntax Errors Found:" -ForegroundColor Red
    $errors | ForEach-Object {
        Write-Host "Line $($_.Token.StartLine): $($_.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "No syntax errors found!" -ForegroundColor Green
}
