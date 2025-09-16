#!/usr/bin/env powershell
# Total Life AI - Backend Startup Script
# Ensures server starts from correct directory with proper environment

Write-Host "🚀 Total Life AI - Starting Backend Server" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Kill any existing servers
Write-Host "🔄 Stopping any existing servers..." -ForegroundColor Yellow
try {
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force
    Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✅ Existing servers stopped" -ForegroundColor Green
} catch {
    Write-Host "✅ No existing servers to stop" -ForegroundColor Green
}

# Ensure we're in the correct project directory
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

Write-Host "📁 Project Root: $ProjectRoot" -ForegroundColor Cyan
Set-Location $ProjectRoot

# Verify backend directory exists
if (-not (Test-Path "backend")) {
    Write-Host "❌ ERROR: Backend directory not found!" -ForegroundColor Red
    Write-Host "Make sure you're running this from the TWIN project root directory" -ForegroundColor Red
    exit 1
}

# Change to backend directory
Set-Location "backend"
Write-Host "📁 Current Directory: $(Get-Location)" -ForegroundColor Cyan

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  No .env file found. Creating minimal configuration..." -ForegroundColor Yellow
    @"
# Minimal configuration for local development
AI_PRIMARY_PROVIDER=together
AI_FALLBACK_PROVIDER=openai

# Add your API keys here:
# TOGETHER_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here

# Database
SECRET_KEY=dev-secret-key-replace-in-production
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Created basic .env file - add your API keys" -ForegroundColor Green
}

# Verify Poetry is available
try {
    $poetryVersion = poetry --version
    Write-Host "✅ Poetry found: $poetryVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Poetry not found. Please install Poetry first:" -ForegroundColor Red
    Write-Host "  https://python-poetry.org/docs/#installation" -ForegroundColor Yellow
    exit 1
}

# Install dependencies if needed
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
poetry install --no-dev

# Start the server
Write-Host ""
Write-Host "🚀 Starting FastAPI server on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "📚 API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "🔍 Health Check: http://127.0.0.1:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start server with proper error handling
Write-Host "🚀 Starting server..." -ForegroundColor Green
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Server failed to start. Common fixes:" -ForegroundColor Red
    Write-Host "  1. Make sure you're in the backend/ directory" -ForegroundColor Yellow
    Write-Host "  2. Run: poetry install" -ForegroundColor Yellow  
    Write-Host "  3. Check your .env file configuration" -ForegroundColor Yellow
    exit 1
}
