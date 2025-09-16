#!/usr/bin/env powershell
# ============================================================================
# Total Life AI - AWS Production Deployment Script (PowerShell)
# ============================================================================
# This script sets up complete AWS infrastructure for your cost-optimized
# RAG system with Together AI + AWS Bedrock integration
# ============================================================================

param(
    [string]$AWSProfile = "default",
    [string]$AWSRegion = "us-east-1",
    [switch]$SkipInfrastructure,
    [switch]$OnlyInfrastructure,
    [switch]$Help
)

# Configuration
$ProjectName = "TotalLifeAI-Production"
$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host @"
🚀 Total Life AI - AWS Production Deployment

USAGE:
    .\deploy-aws.ps1 [options]

OPTIONS:
    -AWSProfile <profile>     AWS profile to use (default: default)
    -AWSRegion <region>       AWS region to deploy to (default: us-east-1)
    -SkipInfrastructure       Skip infrastructure deployment (only deploy code)
    -OnlyInfrastructure       Only deploy infrastructure (skip code deployment)
    -Help                     Show this help message

EXAMPLES:
    .\deploy-aws.ps1                                    # Full deployment
    .\deploy-aws.ps1 -AWSProfile myprofile              # Use named profile
    .\deploy-aws.ps1 -AWSRegion us-west-2               # Deploy to different region
    .\deploy-aws.ps1 -OnlyInfrastructure                # Just infrastructure
    .\deploy-aws.ps1 -SkipInfrastructure                # Just code updates

"@
}

function Write-Header {
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Magenta
    Write-Host "🚀 TOTAL LIFE AI - AWS PRODUCTION DEPLOYMENT" -ForegroundColor Magenta
    Write-Host "============================================================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "💰 Cost-Optimized RAG System with Together AI (90% savings!)" -ForegroundColor Cyan
    Write-Host "🏗️  Complete AWS infrastructure with ECS, RDS, CloudFront" -ForegroundColor Cyan
    Write-Host "🔒 Production-ready security and auto-scaling" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "▶ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Test-Prerequisites {
    Write-Step "Checking prerequisites..."
    
    # Check AWS CLI
    try {
        aws --version | Out-Null
    } catch {
        Write-Error-Custom "AWS CLI not found. Please install AWS CLI first."
        Write-Host "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    }
    
    # Check Docker
    try {
        docker --version | Out-Null
    } catch {
        Write-Error-Custom "Docker not found. Please install Docker first."
        Write-Host "Visit: https://docs.docker.com/get-docker/"
        exit 1
    }
    
    # Check Node.js and npm
    try {
        npm --version | Out-Null
    } catch {
        Write-Error-Custom "Node.js/npm not found. Please install Node.js first."
        Write-Host "Visit: https://nodejs.org/"
        exit 1
    }
    
    # Check Python
    try {
        python --version | Out-Null
    } catch {
        try {
            python3 --version | Out-Null
        } catch {
            Write-Error-Custom "Python not found. Please install Python 3.8+ first."
            exit 1
        }
    }
    
    # Check CDK
    try {
        cdk --version | Out-Null
    } catch {
        Write-Warning "AWS CDK not found. Installing CDK..."
        npm install -g aws-cdk
    }
    
    Write-Info "✅ All prerequisites satisfied"
}

function Test-AWSSetup {
    Write-Step "Checking AWS configuration..."
    
    # Test AWS credentials
    try {
        $identity = aws sts get-caller-identity --profile $AWSProfile | ConvertFrom-Json
        $script:AWSAccountId = $identity.Account
        $script:AWSUserArn = $identity.Arn
    } catch {
        Write-Error-Custom "AWS credentials not configured or invalid."
        Write-Host "Please run: aws configure --profile $AWSProfile"
        exit 1
    }
    
    Write-Info "✅ AWS Account: $AWSAccountId"
    Write-Info "✅ AWS User: $AWSUserArn"
    Write-Info "✅ AWS Region: $AWSRegion"
    
    # Set environment variables
    $env:AWS_ACCOUNT = $AWSAccountId
    $env:AWS_DEFAULT_REGION = $AWSRegion
}

function Initialize-CDK {
    Write-Step "Setting up CDK environment..."
    
    Set-Location "aws-infrastructure"
    
    # Run the setup script
    .\setup-cdk.ps1
    
    # Activate the environment for this session
    & ".venv\Scripts\Activate.ps1"
    
    Write-Info "✅ CDK environment ready"
}

function Initialize-CDKBootstrap {
    Write-Step "Bootstrapping CDK (if needed)..."
    
    # Check if already bootstrapped
    try {
        aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWSRegion --profile $AWSProfile | Out-Null
        Write-Info "✅ CDK already bootstrapped"
    } catch {
        Write-Warning "Bootstrapping CDK for the first time..."
        cdk bootstrap "aws://$AWSAccountId/$AWSRegion" --profile $AWSProfile
        Write-Info "✅ CDK bootstrapped successfully"
    }
}

function Deploy-Infrastructure {
    Write-Step "Deploying AWS infrastructure..."
    
    # Show what will be deployed
    Write-Info "Reviewing deployment plan..."
    cdk diff --profile $AWSProfile
    
    Write-Host ""
    Write-Host "This will create the following AWS resources:" -ForegroundColor Yellow
    Write-Host "• VPC with public/private subnets across 2 AZs"
    Write-Host "• RDS PostgreSQL database (production-ready)"
    Write-Host "• ECS Fargate cluster with auto-scaling"
    Write-Host "• Application Load Balancer"
    Write-Host "• CloudFront distribution + S3 bucket"
    Write-Host "• ECR repository for Docker images"
    Write-Host "• IAM roles and security groups"
    Write-Host "• Systems Manager parameters for configuration"
    Write-Host ""
    Write-Host "💰 Estimated monthly cost: `$50-150 (depending on usage)" -ForegroundColor Yellow
    Write-Host ""
    
    $deploy = Read-Host "Deploy infrastructure? (y/N)"
    if ($deploy -eq "y" -or $deploy -eq "Y") {
        Write-Step "Deploying infrastructure (this may take 10-15 minutes)..."
        cdk deploy --profile $AWSProfile --require-approval never
        Write-Info "✅ Infrastructure deployed successfully!"
        
        # Get outputs
        Write-Step "Getting deployment outputs..."
        $outputs = aws cloudformation describe-stacks --stack-name $ProjectName --profile $AWSProfile | ConvertFrom-Json
        $outputsHash = @{}
        foreach ($output in $outputs.Stacks[0].Outputs) {
            $outputsHash[$output.OutputKey] = $output.OutputValue
        }
        
        $script:ECRUri = $outputsHash["ECRRepositoryURI"]
        $script:ALBDns = $outputsHash["LoadBalancerDNS"]
        $script:CloudFrontDomain = $outputsHash["CloudFrontDomainName"]
        $script:FrontendBucket = $outputsHash["FrontendBucketName"]
        $script:ClusterName = $outputsHash["ClusterName"]
        $script:ServiceName = $outputsHash["ServiceName"]
        
        Write-Host ""
        Write-Host "============================================================================" -ForegroundColor Green
        Write-Host "🎉 INFRASTRUCTURE DEPLOYED SUCCESSFULLY!" -ForegroundColor Green
        Write-Host "============================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "📦 ECR Repository: $ECRUri" -ForegroundColor Cyan
        Write-Host "⚖️  Load Balancer: $ALBDns" -ForegroundColor Cyan
        Write-Host "🌐 CloudFront: $CloudFrontDomain" -ForegroundColor Cyan
        Write-Host "📁 S3 Bucket: $FrontendBucket" -ForegroundColor Cyan
        Write-Host ""
        
        # Save outputs for next steps
        @"
ECRUri=$ECRUri
ALBDns=$ALBDns
CloudFrontDomain=$CloudFrontDomain
FrontendBucket=$FrontendBucket
ClusterName=$ClusterName
ServiceName=$ServiceName
"@ | Out-File -FilePath "../deployment-outputs.env" -Encoding UTF8
    } else {
        Write-Warning "Infrastructure deployment cancelled"
        exit 0
    }
    
    Set-Location ".."
}

function Build-AndPushImage {
    Write-Step "Building and pushing Docker image..."
    
    # Load deployment outputs
    $outputs = Get-Content "deployment-outputs.env" | ConvertFrom-StringData
    
    # Login to ECR
    aws ecr get-login-password --region $AWSRegion --profile $AWSProfile | docker login --username AWS --password-stdin $outputs.ECRUri
    
    # Build image
    Write-Info "Building Docker image..."
    docker build -t totallifeai-backend .
    
    # Tag for ECR
    docker tag totallifeai-backend:latest "$($outputs.ECRUri):latest"
    docker tag totallifeai-backend:latest "$($outputs.ECRUri):v1.0.0"
    
    # Push to ECR
    Write-Info "Pushing to ECR..."
    docker push "$($outputs.ECRUri):latest"
    docker push "$($outputs.ECRUri):v1.0.0"
    
    Write-Info "✅ Docker image pushed successfully!"
}

function Update-ECSService {
    Write-Step "Updating ECS service with new image..."
    
    # Load deployment outputs
    $outputs = Get-Content "deployment-outputs.env" | ConvertFrom-StringData
    
    # Force new deployment
    aws ecs update-service `
        --cluster $outputs.ClusterName `
        --service $outputs.ServiceName `
        --force-new-deployment `
        --region $AWSRegion `
        --profile $AWSProfile
    
    Write-Info "✅ ECS service update initiated!"
    Write-Warning "Service deployment may take 3-5 minutes to complete"
}

function Deploy-Frontend {
    Write-Step "Building and deploying frontend..."
    
    # Load deployment outputs
    $outputs = Get-Content "deployment-outputs.env" | ConvertFrom-StringData
    
    # Check if frontend directory exists
    if (-not (Test-Path "frontend")) {
        Write-Warning "Frontend directory not found, skipping frontend deployment"
        return
    }
    
    Set-Location "frontend"
    
    # Install dependencies
    Write-Info "Installing frontend dependencies..."
    npm install
    
    # Create production environment file
    @"
REACT_APP_API_URL=https://$($outputs.CloudFrontDomain)/api
REACT_APP_ENVIRONMENT=production
"@ | Out-File -FilePath ".env.production" -Encoding UTF8
    
    # Build for production
    Write-Info "Building frontend for production..."
    npm run build
    
    # Deploy to S3
    Write-Info "Deploying to S3..."
    aws s3 sync build/ "s3://$($outputs.FrontendBucket)/" `
        --delete `
        --region $AWSRegion `
        --profile $AWSProfile `
        --cache-control "public, max-age=31536000" `
        --exclude "*.html" `
        --exclude "*.json"
    
    # Deploy HTML files with shorter cache
    aws s3 sync build/ "s3://$($outputs.FrontendBucket)/" `
        --delete `
        --region $AWSRegion `
        --profile $AWSProfile `
        --cache-control "public, max-age=300" `
        --include "*.html" `
        --include "*.json"
    
    # Invalidate CloudFront cache
    Write-Info "Invalidating CloudFront cache..."
    $distributions = aws cloudfront list-distributions --profile $AWSProfile | ConvertFrom-Json
    $distributionId = ($distributions.DistributionList.Items | Where-Object { $_.Comment -eq "Total Life AI Frontend Distribution" }).Id
    aws cloudfront create-invalidation `
        --distribution-id $distributionId `
        --paths "/*" `
        --region $AWSRegion `
        --profile $AWSProfile
    
    Set-Location ".."
    Write-Info "✅ Frontend deployed successfully!"
}

function Set-Configuration {
    Write-Step "Setting up configuration parameters..."
    
    Write-Host ""
    Write-Host "🔐 CONFIGURATION REQUIRED" -ForegroundColor Yellow
    Write-Host "You need to manually set these parameters in AWS Systems Manager:"
    Write-Host ""
    Write-Host "1. Together AI API Key (for 90% cost savings!):"
    Write-Host "   aws ssm put-parameter --name '/totallifeai/together-api-key' --value 'YOUR_TOGETHER_AI_KEY' --type 'SecureString' --overwrite"
    Write-Host ""
    Write-Host "2. OpenAI API Key (fallback):"
    Write-Host "   aws ssm put-parameter --name '/totallifeai/openai-api-key' --value 'YOUR_OPENAI_KEY' --type 'SecureString' --overwrite"
    Write-Host ""
    Write-Host "3. Application Secret Key:"
    Write-Host "   aws ssm put-parameter --name '/totallifeai/secret-key' --value 'GENERATE_RANDOM_32_CHAR_STRING' --type 'SecureString' --overwrite"
    Write-Host ""
    Write-Host "💡 Get your Together AI API key: https://api.together.xyz/settings/api-keys" -ForegroundColor Cyan
    Write-Host "💡 Get your OpenAI API key: https://platform.openai.com/api-keys" -ForegroundColor Cyan
    Write-Host ""
    
    Read-Host "Press Enter to continue once you've set these parameters"
}

function Test-DeploymentStatus {
    Write-Step "Checking deployment status..."
    
    # Load deployment outputs
    $outputs = Get-Content "deployment-outputs.env" | ConvertFrom-StringData
    
    # Check ALB health
    Write-Info "Testing backend health..."
    Start-Sleep -Seconds 30  # Wait for services to be ready
    
    try {
        Invoke-WebRequest -Uri "http://$($outputs.ALBDns)/health" -TimeoutSec 10 | Out-Null
        Write-Info "✅ Backend is healthy"
    } catch {
        Write-Warning "Backend may still be starting up"
    }
    
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "============================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Frontend URL: https://$($outputs.CloudFrontDomain)" -ForegroundColor Cyan
    Write-Host "🔧 Backend API: http://$($outputs.ALBDns)" -ForegroundColor Cyan
    Write-Host "📚 API Docs: http://$($outputs.ALBDns)/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "1. Set your API keys using the commands above"
    Write-Host "2. Visit your application: https://$($outputs.CloudFrontDomain)"
    Write-Host "3. Register an account and start using your AI!"
    Write-Host ""
    Write-Host "💰 Your system is configured for 90% cost savings with Together AI!" -ForegroundColor Green
    Write-Host "🔒 Production-ready with auto-scaling and security best practices" -ForegroundColor Green
    Write-Host ""
}

# Main deployment flow
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Header
    
    Test-Prerequisites
    Test-AWSSetup
    
    if (-not $SkipInfrastructure) {
        Initialize-CDK
        Initialize-CDKBootstrap
        Deploy-Infrastructure
    }
    
    if (-not $OnlyInfrastructure) {
        Build-AndPushImage
        Update-ECSService
        Deploy-Frontend
        Set-Configuration
        Test-DeploymentStatus
    }
    
    Write-Step "🎉 Total Life AI deployed successfully to AWS!"
}

# Error handling
trap {
    Write-Error-Custom "Deployment failed!"
    Write-Host "Check the logs above for details"
    Write-Host "You can re-run this script to retry"
    exit 1
}

# Run main function
Main
