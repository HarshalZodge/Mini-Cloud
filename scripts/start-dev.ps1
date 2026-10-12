# ==============================================================================
# MiniCloud Dual-Port Development Launcher (Windows PowerShell)
# Launches Backend (Flask :5000) and Frontend (Vite :5173 with proxy) in parallel
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       MiniCloud Cloud Controller - Dev Mode Launcher     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$backendPath = Join-Path $PSScriptRoot "..\backend"
$frontendPath = Join-Path $PSScriptRoot "..\frontend"

Write-Host "Starting Flask Backend in background..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "python" -ArgumentList "app.py" -WorkingDirectory $backendPath -PassThru

Start-Sleep -Seconds 2

Write-Host "Starting Vite Frontend..." -ForegroundColor Green
Push-Location $frontendPath
try {
    npm run dev
} finally {
    Write-Host "Stopping Flask Backend process..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Pop-Location
}
