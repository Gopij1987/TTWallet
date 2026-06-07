#!/usr/bin/env pwsh

<#
.SYNOPSIS
Start both TT Dashboard servers
.DESCRIPTION
Launches backend API and frontend React app in separate terminal windows
.EXAMPLE
.\start-all.ps1
#>

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "TT Dashboard - Starting both servers" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# Check dependencies
if (-not (Test-Path "backend\node_modules")) {
    Write-Host "❌ Backend dependencies not installed!" -ForegroundColor Red
    Write-Host "   Run: cd backend; npm install" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "❌ Frontend dependencies not installed!" -ForegroundColor Red
    Write-Host "   Run: cd frontend; npm install" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting backend on port 5000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'backend'; npm run dev" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "Starting frontend on port 3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'frontend'; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Both servers starting:" -ForegroundColor Green
Write-Host ""
Write-Host "   Dashboard:    http://localhost:3000" -ForegroundColor Cyan
Write-Host "   API Backend:  http://localhost:5000/api/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Close the terminal windows when done" -ForegroundColor Yellow
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""
