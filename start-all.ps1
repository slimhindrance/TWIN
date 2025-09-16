#!/usr/bin/env powershell
# Total Life AI - Complete System Startup
# Starts both backend and frontend servers

Write-Host ""
Write-Host "🚀 TOTAL LIFE AI - COMPLETE SYSTEM STARTUP" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host "💰 Cost-Optimized RAG System with Together AI" -ForegroundColor Yellow
Write-Host ""

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

Set-Location $ProjectRoot

# Step 1: Start Backend
Write-Host "Step 1: Starting Backend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; .\start-backend.ps1" -WindowStyle Normal

# Wait for backend to start
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Test backend health
$backendReady = $false
$attempts = 0
$maxAttempts = 5

while (-not $backendReady -and $attempts -lt $maxAttempts) {
    $attempts++
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "✅ Backend is ready!" -ForegroundColor Green
        }
    } catch {
        Write-Host "⏳ Backend starting... (attempt $attempts/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

if (-not $backendReady) {
    Write-Host "⚠️  Backend might still be starting - continuing with frontend" -ForegroundColor Yellow
}

# Step 2: Start Frontend  
Write-Host ""
Write-Host "Step 2: Starting Frontend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectRoot'; .\start-frontend.ps1" -WindowStyle Normal

# Final instructions
Write-Host ""
Write-Host "🎉 SYSTEM STARTUP COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Your Total Life AI is running at:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API: http://127.0.0.1:8000" -ForegroundColor White  
Write-Host "   API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Add your API keys to backend/.env" -ForegroundColor White
Write-Host "   2. Register an account in the web app" -ForegroundColor White
Write-Host "   3. Connect your data sources (YNAB, etc.)" -ForegroundColor White
Write-Host "   4. Start chatting with your personal AI!" -ForegroundColor White
Write-Host ""
Write-Host "💰 Cost Optimization: Together AI = 90% savings vs OpenAI!" -ForegroundColor Green
Write-Host ""
