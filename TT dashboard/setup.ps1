#!/usr/bin/env pwsh

<#
.SYNOPSIS
TT Dashboard Setup Checker (PowerShell)
.DESCRIPTION
Checks system prerequisites and project setup status
.EXAMPLE
.\setup.ps1
#>

$ErrorActionPreference = "SilentlyContinue"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor Green
}

function Write-Error {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Text)
    Write-Host "⚠️  $Text" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️  $Text" -ForegroundColor Blue
}

$checks = @()

# Check Node.js
Write-Header "1. Checking Node.js"
$nodeVersion = node -v 2>$null
if ($nodeVersion) {
    Write-Success "Node.js $nodeVersion installed"
    $checks += $true
} else {
    Write-Error "Node.js not found. Install from https://nodejs.org/"
    $checks += $false
}

# Check npm
Write-Header "2. Checking npm"
$npmVersion = npm -v 2>$null
if ($npmVersion) {
    Write-Success "npm $npmVersion installed"
    $checks += $true
} else {
    Write-Error "npm not found"
    $checks += $false
}

# Check backend structure
Write-Header "3. Checking Backend Folder Structure"
$backendOk = $true
$backendFiles = @("server.js", "db.js", "package.json")
$backendDirs = @("routes")

foreach ($file in $backendFiles) {
    if (Test-Path "backend\$file") {
        Write-Success "Found: backend/$file"
    } else {
        Write-Error "Missing: backend/$file"
        $backendOk = $false
    }
}

foreach ($dir in $backendDirs) {
    if (Test-Path "backend\$dir") {
        Write-Success "Found directory: backend/$dir/"
    } else {
        Write-Error "Missing directory: backend/$dir/"
        $backendOk = $false
    }
}

$checks += $backendOk

# Check backend .env
Write-Header "4. Checking Backend Configuration (.env)"
if (Test-Path "backend\.env") {
    Write-Success ".env file exists"
    $envContent = Get-Content "backend\.env" -Raw
    if ($envContent -match "DB_HOST" -and $envContent -match "TT_COOKIES_B64") {
        Write-Success "Environment variables appear to be configured"
        $checks += $true
    } else {
        Write-Warning ".env exists but missing some variables"
        Write-Info "Required: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, TT_COOKIES_B64_*"
        $checks += $false
    }
} else {
    Write-Warning ".env file not found"
    if (Test-Path "backend\.env.example") {
        Write-Info "Create from template:"
        Write-Info "  Copy-Item backend\.env.example backend\.env"
        Write-Info "  Then edit and fill in your credentials"
    }
    $checks += $false
}

# Check backend node_modules
Write-Header "5. Checking Backend Dependencies"
if (Test-Path "backend\node_modules") {
    Write-Success "Backend node_modules found"
    $checks += $true
} else {
    Write-Warning "Backend node_modules not found"
    Write-Info "Run: cd backend; npm install"
    $checks += $false
}

# Check frontend structure
Write-Header "6. Checking Frontend Folder Structure"
$frontendOk = $true
$frontendFiles = @("package.json", "index.html", "vite.config.js")
$frontendDirs = @("src")

foreach ($file in $frontendFiles) {
    if (Test-Path "frontend\$file") {
        Write-Success "Found: frontend/$file"
    } else {
        Write-Error "Missing: frontend/$file"
        $frontendOk = $false
    }
}

foreach ($dir in $frontendDirs) {
    if (Test-Path "frontend\$dir") {
        Write-Success "Found directory: frontend/$dir/"
    } else {
        Write-Error "Missing directory: frontend/$dir/"
        $frontendOk = $false
    }
}

$checks += $frontendOk

# Check frontend node_modules
Write-Header "7. Checking Frontend Dependencies"
if (Test-Path "frontend\node_modules") {
    Write-Success "Frontend node_modules found"
    $checks += $true
} else {
    Write-Warning "Frontend node_modules not found"
    Write-Info "Run: cd frontend; npm install"
    $checks += $false
}

# Check PostgreSQL
Write-Header "8. Checking PostgreSQL Connection"
$psqlVersion = psql --version 2>$null
if ($psqlVersion) {
    Write-Success "PostgreSQL client found"
    $checks += $true
} else {
    Write-Warning "PostgreSQL client not found - verify PostgreSQL is running"
    $checks += $false
}

# Summary
Write-Header "SETUP STATUS SUMMARY"

$passed = ($checks | Where-Object { $_ -eq $true }).Count
$total = $checks.Count
$percentage = [math]::Round(($passed / $total) * 100)

Write-Host "Checks passed: $passed/$total ($percentage%)" -ForegroundColor Cyan
Write-Host ""

if ($percentage -eq 100) {
    Write-Success "All checks passed! Ready to start."
    Write-Host ""
    Write-Info "Next steps:"
    Write-Info "  Terminal 1: cd backend; npm run dev"
    Write-Info "  Terminal 2: cd frontend; npm run dev"
    Write-Info "  Visit: http://localhost:3000"
} elseif ($percentage -ge 70) {
    Write-Warning "Most checks passed. Some setup steps remaining."
    Write-Host ""
    Write-Info "Next steps:"
    Write-Info "  1. Install dependencies (see above for commands)"
    Write-Info "  2. Configure .env in backend/"
    Write-Info "  3. Verify PostgreSQL is running"
    Write-Info "  4. Re-run this script to verify"
} else {
    Write-Error "Several setup steps need attention (see above)"
    Write-Host ""
    Write-Info "Follow the setup instructions in QUICKSTART.md"
}

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""
