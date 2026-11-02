# =============================================================================
# Agent Forge - Start Frontend Dev Server
# Run this from the project root: .\start_frontend.ps1
# =============================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "   Agent Forge Frontend - Vite + React" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

Set-Location "$PSScriptRoot\frontend"

# Install node deps if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "[1/2] Installing npm dependencies..." -ForegroundColor Green
    npm install
} else {
    Write-Host "[1/2] node_modules found. Skipping npm install." -ForegroundColor Gray
}

Write-Host ""
Write-Host "[2/2] Starting Vite dev server on http://localhost:5173" -ForegroundColor Green
Write-Host "      Make sure the backend is running on port 8000 first!" -ForegroundColor Yellow
Write-Host "      Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

npm run dev -- --host 0.0.0.0
