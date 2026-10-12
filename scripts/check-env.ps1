# ==============================================================================
# MiniCloud - Environment Prerequisites Check Script (Windows PowerShell)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   MiniCloud Cloud Controller - Environment Pre-check     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$results = @()

function Test-Prerequisite {
    param (
        [string]$Name,
        [scriptblock]$CheckBlock,
        [string]$ExpectedVersion,
        [bool]$Mandatory = $true
    )

    Write-Host -NoNewline "Checking $Name... "
    try {
        $version = & $CheckBlock
        if ($version) {
            Write-Host "[OK] ($version)" -ForegroundColor Green
            return [PSCustomObject]@{
                Component = $Name
                Status = "Installed"
                Details = $version
                Required = if ($Mandatory) { "Yes" } else { "Optional" }
            }
        } else {
            throw "Not found"
        }
    } catch {
        if ($Mandatory) {
            Write-Host "[MISSING] - Required: $ExpectedVersion" -ForegroundColor Red
        } else {
            Write-Host "[OPTIONAL - NOT DETECTED]" -ForegroundColor Yellow
        }
        return [PSCustomObject]@{
            Component = $Name
            Status = if ($Mandatory) { "Missing" } else { "Not Present" }
            Details = "Required: $ExpectedVersion"
            Required = if ($Mandatory) { "Yes" } else { "Optional" }
        }
    }
}

# 1. Python Check
$results += Test-Prerequisite -Name "Python" -ExpectedVersion "3.11.x (or >= 3.10)" -CheckBlock {
    $out = python --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $out -match "Python (\d+\.\d+\.\d+)") {
        return $matches[1]
    }
    return $null
}

# 2. Node.js Check
$results += Test-Prerequisite -Name "Node.js" -ExpectedVersion "20.x LTS (or >= 18.x)" -CheckBlock {
    $out = node --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $out -match "v(\d+\.\d+\.\d+)") {
        return $matches[1]
    }
    return $null
}

# 3. npm Check
$results += Test-Prerequisite -Name "npm" -ExpectedVersion ">= 9.x" -CheckBlock {
    $out = npm --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        return $out.Trim()
    }
    return $null
}

# 4. Java Check (OpenJDK / JDK)
$results += Test-Prerequisite -Name "Java JDK" -ExpectedVersion "11 (OpenJDK)" -Mandatory $false -CheckBlock {
    $out = java -version 2>&1
    $firstLine = ($out | Select-Object -First 1)
    if ($firstLine -match "version `"?([0-9._]+)`"?") {
        return $matches[1]
    }
    return $null
}

# 5. Git Check
$results += Test-Prerequisite -Name "Git" -ExpectedVersion ">= 2.x" -CheckBlock {
    $out = git --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $out -match "git version (\d+\.\d+\.\d+)") {
        return $matches[1]
    }
    return $null
}

# 6. Docker Check (Optional - needed if using Option C for Hadoop)
$results += Test-Prerequisite -Name "Docker" -ExpectedVersion "Docker Desktop (for Option C)" -Mandatory $false -CheckBlock {
    $out = docker --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $out -match "Docker version ([\d\.]+)") {
        return $matches[1]
    }
    return $null
}

# 7. WSL Check (Optional - needed if using Option B for Hadoop)
$results += Test-Prerequisite -Name "WSL" -ExpectedVersion "WSL2 (for Option B)" -Mandatory $false -CheckBlock {
    $out = wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) {
        return "Installed"
    }
    return $null
}

Write-Host ""
Write-Host "Summary of Environment:" -ForegroundColor Cyan
$results | Format-Table -AutoSize

Write-Host "Hadoop Deployment Options for Windows Demo:" -ForegroundColor Yellow
Write-Host " - Option A (Default/Recommended): Ubuntu 22.04 VM with Bridged IP running Hadoop 3.3.6"
Write-Host " - Option B: WSL2 Ubuntu with mirrored networking or portproxy"
Write-Host " - Option C: Docker Compose with 1 NameNode + 2 DataNodes (Requires Docker Desktop)"
Write-Host ""
