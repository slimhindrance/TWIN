# Total Life AI - Backend Startup Script
# Ensures server starts from correct directory with proper environment

Write-Host "🚀 Starting Total Life AI Backend Server..." -ForegroundColor Green
Write-Host ""

# Ensure we're in the project root
$ProjectRoot = "C:\Users\641792\OneDrive - BOOZ ALLEN HAMILTON\Desktop\Projects\TWIN"
if (-not (Test-Path $ProjectRoot)) {
    Write-Host "❌ Project directory not found: $ProjectRoot" -ForegroundColor Red
    exit 1
}

Set-Location $ProjectRoot
Write-Host "📁 Working directory: $(Get-Location)" -ForegroundColor Yellow

# Check if backend directory exists
if (-not (Test-Path "backend")) {
    Write-Host "❌ Backend directory not found!" -ForegroundColor Red
    exit 1
}

# Move to backend directory
Set-Location "backend"
Write-Host "📁 Changed to backend directory: $(Get-Location)" -ForegroundColor Yellow

# Check if Poetry is available
try {
    poetry --version | Out-Null
    Write-Host "✅ Poetry is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Poetry not found! Please install Poetry first." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
try {
    poetry env info | Out-Null
    Write-Host "✅ Poetry environment is set up" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Setting up Poetry environment..." -ForegroundColor Yellow
    poetry install
}

# Display environment configuration
Write-Host ""
Write-Host "🔧 Environment Configuration:" -ForegroundColor Cyan
Write-Host "   - Check .env file for AI provider API keys" -ForegroundColor White
Write-Host "   - Primary Provider: Together AI (90% cost savings!)" -ForegroundColor White
Write-Host "   - Fallback Provider: AWS Bedrock" -ForegroundColor White
Write-Host ""

# Start the server
Write-Host "🎯 Starting FastAPI server with multi-provider AI routing..." -ForegroundColor Green
Write-Host "   Server will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "   API docs at: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
} catch {
    Write-Host ""
    Write-Host "❌ Server failed to start. Check the error above." -ForegroundColor Red
    Write-Host "💡 Common issues:" -ForegroundColor Yellow
    Write-Host "   - Missing dependencies: Run 'poetry install'" -ForegroundColor White
    Write-Host "   - Port in use: Change port or kill existing processes" -ForegroundColor White
    Write-Host "   - Missing .env file: Copy .env.template to .env" -ForegroundColor White
    exit 1
}