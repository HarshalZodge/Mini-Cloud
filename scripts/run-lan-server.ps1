# ==============================================================================
# MiniCloud LAN Deployment Launcher (Windows PowerShell)
# Finds Local IP, Checks Firewall Rule, and Starts Waitress Production Server
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       MiniCloud Cloud Controller - LAN Deployment        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Detect IPv4 Address on Active Network Adapter
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -notmatch "Loopback|vEthernet|WSL" -and $_.IPAddress -notmatch "^169\.254\."
} | Select-Object -ExpandProperty IPAddress

$primaryIp = $ipAddresses | Select-Object -First 1

if (-not $primaryIp) {
    $primaryIp = "127.0.0.1"
}

Write-Host "Detected Host IPv4 Address on Lab Network: " -NoNewline
Write-Host "$primaryIp" -ForegroundColor Green
Write-Host ""

# 2. Check & Advise Firewall
Write-Host "Checking Windows Firewall status for Port 5000..."
$rule = Get-NetFirewallRule -DisplayName "MiniCloud Cloud Controller (Port 5000)" -ErrorAction SilentlyContinue

if ($rule) {
    Write-Host "[OK] Firewall rule already exists for port 5000." -ForegroundColor Green
} else {
    Write-Host "[NOTE] Windows Firewall rule not detected. To allow lab computers to connect, run this in an Administrator PowerShell:" -ForegroundColor Yellow
    Write-Host "  New-NetFirewallRule -DisplayName 'MiniCloud Cloud Controller (Port 5000)' -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow" -ForegroundColor Cyan
    Write-Host ""
}

# 3. Check for Frontend Build
$distPath = Join-Path $PSScriptRoot "..\frontend\dist"
if (-not (Test-Path $distPath)) {
    Write-Host "[BUILDING FRONTEND] No frontend build found. Building production assets now..." -ForegroundColor Yellow
    Push-Location (Join-Path $PSScriptRoot "..\frontend")
    npm run build
    Pop-Location
}

# 4. Instructions
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "URL for this computer:      http://localhost:5000" -ForegroundColor White
Write-Host "URL for other lab PCs:      http://$($primaryIp):5000" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting Waitress Production Server on 0.0.0.0:5000..." -ForegroundColor Green
Write-Host "Press Ctrl+C to terminate the server at any time." -ForegroundColor Gray
Write-Host ""

Push-Location (Join-Path $PSScriptRoot "..\backend")
python server.py
Pop-Location
