#!/usr/bin/env powershell
# Total Life AI - Basic Environment Setup

Write-Host "Creating .env file..." -ForegroundColor Green

# Navigate to project directory
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Get-Location }
Set-Location $ProjectRoot

if (-not (Test-Path "backend")) {
    Write-Host "ERROR: Backend directory not found!" -ForegroundColor Red
    exit 1
}

$envPath = "backend\.env"

$envContent = @"
# Total Life AI - Cost Optimized Configuration
AI_PRIMARY_PROVIDER=together
AI_FALLBACK_PROVIDER=openai

# Add your API keys here:
# TOGETHER_API_KEY=your_together_key_here  
# OPENAI_API_KEY=your_openai_key_here

TOGETHER_MODEL=meta-llama/Llama-3.1-8B-Instruct-Turbo
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

SECRET_KEY=dev-secret-key-replace-in-production
DATABASE_URL=sqlite:///./total_life_ai.db
MAX_REQUESTS_PER_MINUTE=100
VECTOR_DB_PATH=./chroma_db
ENVIRONMENT=development
DEBUG=True
"@

try {
    $envContent | Out-File -FilePath $envPath -Encoding UTF8
    Write-Host "SUCCESS: Created $envPath" -ForegroundColor Green
    Write-Host "Next: Get Together AI key from https://api.together.xyz/settings/api-keys" -ForegroundColor Yellow
} catch {
    Write-Host "ERROR: Failed to create .env file" -ForegroundColor Red
    exit 1
}
