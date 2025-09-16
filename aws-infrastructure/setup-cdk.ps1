#!/usr/bin/env powershell
# Setup script for AWS CDK environment

Write-Host "Setting up AWS CDK environment for Total Life AI..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    try {
        $pythonVersion = python3 --version  
        Write-Host "✅ Python3 found: $pythonVersion" -ForegroundColor Green
        $pythonCmd = "python3"
    } catch {
        Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
        exit 1
    }
}

if (-not $pythonCmd) {
    $pythonCmd = "python"
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    & $pythonCmd -m venv .venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
} elseif (Test-Path ".venv\bin\activate") {
    & source .venv/bin/activate
} else {
    Write-Host "❌ Could not find virtual environment activation script" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "⬆️ Upgrading pip..." -ForegroundColor Yellow
& $pythonCmd -m pip install --upgrade pip

# Install requirements
Write-Host "📚 Installing CDK dependencies..." -ForegroundColor Yellow
& $pythonCmd -m pip install -r requirements.txt

# Verify installations
Write-Host "✅ Verifying installations..." -ForegroundColor Green
try {
    & $pythonCmd -c "import aws_cdk; print(f'AWS CDK: {aws_cdk.__version__}')"
    & $pythonCmd -c "import constructs; print(f'Constructs: {constructs.__version__}')"
    Write-Host "✅ All dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Dependency verification failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 CDK environment setup complete!" -ForegroundColor Green
Write-Host "Testing CDK configuration..." -ForegroundColor Yellow

# Test CDK synth
try {
    cdk synth --quiet | Out-Null
    Write-Host "✅ CDK synthesis test passed!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ CDK synthesis test failed - check your configuration" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "You can now run: cdk synth or cdk deploy" -ForegroundColor Cyan
