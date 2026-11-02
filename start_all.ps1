# =============================================================================
# Agent Forge - One-Click Full Stack Launch Script
# Run from project root: .\start_all.ps1
# =============================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Agent Forge - Multilingual Legal Support System" -ForegroundColor Cyan
Write-Host "   Starting Backend (FastAPI) and Frontend (Vite + React)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

# 1. Start Backend in a separate window
Write-Host "[1/2] Launching Backend Server on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$root\start_backend.ps1"

# 2. Brief wait for backend to bind port
Start-Sleep -Seconds 3

# 3. Start Frontend in a separate window
Write-Host "[2/2] Launching Frontend Dev Server on http://localhost:5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$root\start_frontend.ps1"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "   Both servers are starting!" -ForegroundColor Yellow
Write-Host "   • Web App UI : http://localhost:5173" -ForegroundColor White
Write-Host "   • Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   • API Docs   : http://localhost:8000/docs" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
