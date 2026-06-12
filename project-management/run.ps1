$projectId = "02505df5-3137-49f1-961c-e04c795eb7d6"
$url = "http://localhost:8765/project/$projectId"

$configPath = "$env:USERPROFILE\.cc-pm\config.json"
$serverDir = $null
if (Test-Path $configPath) {
    $config = Get-Content $configPath | ConvertFrom-Json
    $serverDir = $config.server_dir
}
if (-not $serverDir) {
    Write-Host "ERROR: server_dir not set in $configPath" -ForegroundColor Red; pause; exit 1
}

$running = $false
try { $null = Invoke-RestMethod "http://localhost:8765/api/v1/projects" -TimeoutSec 2 -EA Stop; $running = $true } catch {}

if (-not $running) {
    Write-Host "Starting CC-PM server..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit -Command `"Set-Location '$serverDir'; python -m uvicorn src.main:app --host 0.0.0.0 --port 8765`""
    $retries = 0
    while ($retries -lt 10) {
        Start-Sleep 1
        try { $null = Invoke-RestMethod "http://localhost:8765/api/v1/projects" -TimeoutSec 1 -EA Stop; break } catch { $retries++ }
    }
}

Start-Process $url
