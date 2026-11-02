# =============================================================================
# Agent Forge - Start Backend Server
# Run this from the project root: .\start_backend.ps1
# =============================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Agent Forge Backend - FastAPI + Uvicorn" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend
Set-Location "$PSScriptRoot\backend"

# Check .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[ERROR] .env file not found in backend/" -ForegroundColor Red
    Write-Host "Copy .env.example to .env and fill in your API keys." -ForegroundColor Yellow
    exit 1
}

# Check Gemini key is present
$envContent = Get-Content ".env" -Raw
if ($envContent -notmatch "GEMINI_API_KEY=\S+") {
    Write-Host ""
    Write-Host "[WARNING] GEMINI_API_KEY is not set in backend/.env" -ForegroundColor Yellow
    Write-Host "Get your key at: https://aistudio.google.com/app/apikey" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ""
Write-Host "[1/1] Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "      API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "      Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

# Run uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
