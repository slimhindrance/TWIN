# Digital Twin - Complete Startup Script
Write-Host "DIGITAL TWIN - LAUNCHING SERVERS" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Yellow
Write-Host ""

# Kill any existing processes
Write-Host "Stopping existing servers..." -ForegroundColor Yellow
Get-Process -Name "python*","node*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Start Backend Server
Write-Host "Starting Backend Server..." -ForegroundColor Green
Set-Location backend
Write-Host "   Backend directory: $(Get-Location)" -ForegroundColor Gray
Write-Host "   Starting FastAPI on http://127.0.0.1:8000" -ForegroundColor Cyan
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "poetry run uvicorn app.main:app --reload --port 8000 --host 127.0.0.1"
Set-Location ..
Write-Host "   Backend server starting in new window" -ForegroundColor Green

Start-Sleep -Seconds 3

# Start Frontend Server
Write-Host "Starting Frontend Server..." -ForegroundColor Green
Set-Location frontend
Write-Host "   Frontend directory: $(Get-Location)" -ForegroundColor Gray
Write-Host "   Starting React on http://localhost:3000" -ForegroundColor Cyan
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "npm start"
Set-Location ..
Write-Host "   Frontend server starting in new window" -ForegroundColor Green

Write-Host ""
Write-Host "SERVERS LAUNCHING!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Waiting 10 seconds for startup..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "YOUR DIGITAL TWIN IS READY!" -ForegroundColor Green
Write-Host "Open http://localhost:3000 to start chatting" -ForegroundColor Cyan
Write-Host ""