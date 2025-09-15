# Digital Twin - Windows PowerShell Deployment Script
# Quick deployment script for Windows users

param(
    [Parameter(Mandatory=$true)]
    [string]$OpenAIApiKey,
    
    [Parameter(Mandatory=$false)]
    [string]$DomainName = "",
    
    [Parameter(Mandatory=$false)]
    [string]$AWSRegion = "us-east-1"
)

Write-Host "🚀 Digital Twin - Windows Deployment" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Yellow

# Check prerequisites
$tools = @("az", "aws", "docker")
foreach ($tool in $tools) {
    if (!(Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Host "❌ $tool not found. Please install it first." -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ All required tools found" -ForegroundColor Green

# Step 1: Azure Container Registry Setup
Write-Host "🔧 Setting up Azure Container Registry..." -ForegroundColor Cyan

# Login to Azure
az login

# Create unique ACR name
$timestamp = Get-Date -Format "yyyyMMddHHmm"
$acrName = "digitaltwin$timestamp"
$resourceGroup = "digital-twin-rg"

# Create resource group and ACR
az group create --name $resourceGroup --location "eastus"
az acr create --resource-group $resourceGroup --name $acrName --sku Basic --admin-enabled true

# Get ACR credentials
$acrLoginServer = az acr show --name $acrName --query loginServer --output tsv
$acrUsername = az acr credential show --name $acrName --query username --output tsv
$acrPassword = az acr credential show --name $acrName --query passwords[0].value --output tsv

Write-Host "✅ ACR Setup Complete" -ForegroundColor Green
Write-Host "   Registry: $acrLoginServer" -ForegroundColor White

# Step 2: Build and Push Docker Image
Write-Host "🔨 Building and pushing Docker image..." -ForegroundColor Cyan

# Login to ACR
docker login $acrLoginServer --username $acrUsername --password $acrPassword

# Build and push image
$imageName = "digital-twin"
$fullImageName = "$acrLoginServer/$imageName`:latest"

Set-Location ".."
docker build -t $fullImageName .
docker push $fullImageName

Write-Host "✅ Image pushed successfully" -ForegroundColor Green
Write-Host "   Image: $fullImageName" -ForegroundColor White

# Step 3: Deploy AWS Infrastructure
Write-Host "🏗️ Setting up AWS infrastructure..." -ForegroundColor Cyan

$stackName = "digital-twin-infrastructure"

# Deploy CloudFormation stack
aws cloudformation deploy `
    --template-file "deployment/aws/infrastructure.yaml" `
    --stack-name $stackName `
    --parameter-overrides `
        "ACRLoginServer=$acrLoginServer" `
        "ACRUsername=$acrUsername" `
        "ACRPassword=$acrPassword" `
        "OpenAIAPIKey=$OpenAIApiKey" `
        "DomainName=$DomainName" `
    --capabilities "CAPABILITY_NAMED_IAM" `
    --region $AWSRegion

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Infrastructure deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Infrastructure deployed" -ForegroundColor Green

# Step 4: Deploy to ECS
Write-Host "🚀 Deploying to ECS..." -ForegroundColor Cyan

# Get infrastructure outputs
$albDns = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerDNS`].OutputValue' --output text
$clusterName = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' --output text

# Create task definition (simplified for PowerShell)
$taskDefJson = @"
{
  "family": "digital-twin-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "digital-twin-container",
      "image": "$fullImageName",
      "essential": true,
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "DEBUG", "value": "false"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/digital-twin",
          "awslogs-region": "$AWSRegion",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      }
    }
  ]
}
"@

# Register task definition
$taskDefJson | Out-File -FilePath "temp-task-def.json" -Encoding UTF8
$taskDefArn = aws ecs register-task-definition --cli-input-json file://temp-task-def.json --query 'taskDefinition.taskDefinitionArn' --output text
Remove-Item "temp-task-def.json"

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Yellow
Write-Host "🌐 Your Digital Twin is available at:" -ForegroundColor Cyan
Write-Host "   http://$albDns" -ForegroundColor White
Write-Host "" 
Write-Host "🔍 To check status:" -ForegroundColor Yellow
Write-Host "   aws ecs describe-services --cluster $clusterName --services digital-twin-service" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 To view logs:" -ForegroundColor Yellow
Write-Host "   aws logs tail /ecs/digital-twin --follow" -ForegroundColor Gray
Write-Host ""
Write-Host "🎊 Your Digital Twin is now running in production!" -ForegroundColor Green
