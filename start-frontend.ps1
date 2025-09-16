#!/usr/bin/env powershell
# Total Life AI - Frontend Startup Script  
# Ensures React app starts from correct directory

Write-Host "🎨 Total Life AI - Starting Frontend Server" -ForegroundColor Magenta
Write-Host "=========================================" -ForegroundColor Magenta
Write-Host ""

# Ensure we're in the correct project directory
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

Write-Host "📁 Project Root: $ProjectRoot" -ForegroundColor Cyan
Set-Location $ProjectRoot

# Verify frontend directory exists
if (-not (Test-Path "frontend")) {
    Write-Host "❌ ERROR: Frontend directory not found!" -ForegroundColor Red
    Write-Host "Make sure you're running this from the TWIN project root directory" -ForegroundColor Red
    exit 1
}

# Change to frontend directory
Set-Location "frontend"
Write-Host "📁 Current Directory: $(Get-Location)" -ForegroundColor Cyan

# Check if package.json exists
if (-not (Test-Path "package.json")) {
    Write-Host "❌ ERROR: package.json not found in frontend directory!" -ForegroundColor Red
    exit 1
}

# Check for node_modules, install if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
}

# Start the development server
Write-Host ""
Write-Host "🚀 Starting React development server on http://localhost:3000" -ForegroundColor Green
Write-Host "🔗 Make sure backend is running on http://127.0.0.1:8000" -ForegroundColor Cyan  
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start React app
Write-Host "🚀 Starting React development server..." -ForegroundColor Green
npm start

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Frontend failed to start. Common fixes:" -ForegroundColor Red
    Write-Host "  1. Make sure you're in the frontend/ directory" -ForegroundColor Yellow
    Write-Host "  2. Run: npm install" -ForegroundColor Yellow
    Write-Host "  3. Check if port 3000 is available" -ForegroundColor Yellow
    exit 1
}
