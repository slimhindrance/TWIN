# Digital Twin Backend Startup Script
Write-Host "🚀 Starting Digital Twin Backend..." -ForegroundColor Green
Write-Host "📁 Project Directory: $(Get-Location)" -ForegroundColor Yellow

# Navigate to backend directory
Set-Location backend

# Start the server
Write-Host "🔧 Starting FastAPI server on http://127.0.0.1:8000" -ForegroundColor Cyan
poetry run uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
