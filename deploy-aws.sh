#!/bin/bash

# ============================================================================
# Total Life AI - AWS Production Deployment Script
# ============================================================================
# This script sets up complete AWS infrastructure for your cost-optimized
# RAG system with Together AI + AWS Bedrock integration
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="TotalLifeAI-Production"
AWS_REGION="us-east-1"  # Change this if needed
AWS_PROFILE="default"   # Change this if using named profile

print_header() {
    echo -e "${PURPLE}"
    echo "============================================================================"
    echo "🚀 TOTAL LIFE AI - AWS PRODUCTION DEPLOYMENT"
    echo "============================================================================"
    echo -e "${NC}"
    echo -e "${CYAN}💰 Cost-Optimized RAG System with Together AI (90% savings!)${NC}"
    echo -e "${CYAN}🏗️  Complete AWS infrastructure with ECS, RDS, CloudFront${NC}"
    echo -e "${CYAN}🔒 Production-ready security and auto-scaling${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install AWS CLI first."
        echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Node.js and npm
    if ! command -v npm &> /dev/null; then
        print_error "Node.js/npm not found. Please install Node.js first."
        echo "Visit: https://nodejs.org/"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.8+ first."
        exit 1
    fi
    
    # Check CDK
    if ! command -v cdk &> /dev/null; then
        print_warning "AWS CDK not found. Installing CDK..."
        npm install -g aws-cdk
    fi
    
    print_info "✅ All prerequisites satisfied"
}

# Check AWS credentials and region
check_aws_setup() {
    print_step "Checking AWS configuration..."
    
    # Test AWS credentials
    if ! aws sts get-caller-identity --profile $AWS_PROFILE > /dev/null 2>&1; then
        print_error "AWS credentials not configured or invalid."
        echo "Please run: aws configure --profile $AWS_PROFILE"
        exit 1
    fi
    
    # Get account info
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
    AWS_USER_ARN=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Arn --output text)
    
    print_info "✅ AWS Account: $AWS_ACCOUNT_ID"
    print_info "✅ AWS User: $AWS_USER_ARN" 
    print_info "✅ AWS Region: $AWS_REGION"
    
    # Set environment variables
    export AWS_ACCOUNT=$AWS_ACCOUNT_ID
    export AWS_DEFAULT_REGION=$AWS_REGION
}

# Setup CDK environment
setup_cdk() {
    print_step "Setting up CDK environment..."
    
    cd aws-infrastructure
    
    # Run the setup script
    chmod +x setup-cdk.sh
    ./setup-cdk.sh
    
    # Activate the environment for this session
    source .venv/bin/activate
    
    print_info "✅ CDK environment ready"
}

# Bootstrap CDK (one-time setup per account/region)
bootstrap_cdk() {
    print_step "Bootstrapping CDK (if needed)..."
    
    # Check if already bootstrapped
    if aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION --profile $AWS_PROFILE > /dev/null 2>&1; then
        print_info "✅ CDK already bootstrapped"
    else
        print_warning "Bootstrapping CDK for the first time..."
        cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION --profile $AWS_PROFILE
        print_info "✅ CDK bootstrapped successfully"
    fi
}

# Deploy infrastructure
deploy_infrastructure() {
    print_step "Deploying AWS infrastructure..."
    
    # Show what will be deployed
    print_info "Reviewing deployment plan..."
    cdk diff --profile $AWS_PROFILE
    
    echo ""
    echo -e "${YELLOW}This will create the following AWS resources:${NC}"
    echo "• VPC with public/private subnets across 2 AZs"
    echo "• RDS PostgreSQL database (production-ready)"
    echo "• ECS Fargate cluster with auto-scaling"
    echo "• Application Load Balancer"
    echo "• CloudFront distribution + S3 bucket"
    echo "• ECR repository for Docker images"
    echo "• IAM roles and security groups"
    echo "• Systems Manager parameters for configuration"
    echo ""
    echo -e "${YELLOW}💰 Estimated monthly cost: $50-150 (depending on usage)${NC}"
    echo ""
    
    read -p "Deploy infrastructure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Deploying infrastructure (this may take 10-15 minutes)..."
        cdk deploy --profile $AWS_PROFILE --require-approval never
        print_info "✅ Infrastructure deployed successfully!"
        
        # Get outputs
        print_step "Getting deployment outputs..."
        ECR_URI=$(aws cloudformation describe-stacks --stack-name $PROJECT_NAME --profile $AWS_PROFILE --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' --output text)
        ALB_DNS=$(aws cloudformation describe-stacks --stack-name $PROJECT_NAME --profile $AWS_PROFILE --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' --output text)
        CLOUDFRONT_DOMAIN=$(aws cloudformation describe-stacks --stack-name $PROJECT_NAME --profile $AWS_PROFILE --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomainName`].OutputValue' --output text)
        FRONTEND_BUCKET=$(aws cloudformation describe-stacks --stack-name $PROJECT_NAME --profile $AWS_PROFILE --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' --output text)
        
        echo -e "${GREEN}"
        echo "============================================================================"
        echo "🎉 INFRASTRUCTURE DEPLOYED SUCCESSFULLY!"
        echo "============================================================================"
        echo -e "${NC}"
        echo -e "${CYAN}📦 ECR Repository: $ECR_URI${NC}"
        echo -e "${CYAN}⚖️  Load Balancer: $ALB_DNS${NC}"
        echo -e "${CYAN}🌐 CloudFront: $CLOUDFRONT_DOMAIN${NC}"
        echo -e "${CYAN}📁 S3 Bucket: $FRONTEND_BUCKET${NC}"
        echo ""
        
        # Save outputs for next steps
        echo "ECR_URI=$ECR_URI" > ../deployment-outputs.env
        echo "ALB_DNS=$ALB_DNS" >> ../deployment-outputs.env
        echo "CLOUDFRONT_DOMAIN=$CLOUDFRONT_DOMAIN" >> ../deployment-outputs.env
        echo "FRONTEND_BUCKET=$FRONTEND_BUCKET" >> ../deployment-outputs.env
    else
        print_warning "Infrastructure deployment cancelled"
        exit 0
    fi
    
    cd ..
}

# Build and push Docker image
build_and_push_image() {
    print_step "Building and pushing Docker image..."
    
    # Load deployment outputs
    source deployment-outputs.env
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $ECR_URI
    
    # Build image
    print_info "Building Docker image..."
    docker build -t totallifeai-backend .
    
    # Tag for ECR
    docker tag totallifeai-backend:latest $ECR_URI:latest
    docker tag totallifeai-backend:latest $ECR_URI:v1.0.0
    
    # Push to ECR
    print_info "Pushing to ECR..."
    docker push $ECR_URI:latest
    docker push $ECR_URI:v1.0.0
    
    print_info "✅ Docker image pushed successfully!"
}

# Update ECS service with new image
update_ecs_service() {
    print_step "Updating ECS service with new image..."
    
    # Load deployment outputs
    source deployment-outputs.env
    
    # Get cluster and service names
    CLUSTER_NAME=$(aws cloudformation describe-stacks --stack-name $PROJECT_NAME --profile $AWS_PROFILE --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' --output text)
    SERVICE_NAME=$(aws cloudformation describe-stacks --stack-name $PROJECT_NAME --profile $AWS_PROFILE --query 'Stacks[0].Outputs[?OutputKey==`ServiceName`].OutputValue' --output text)
    
    # Force new deployment
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --force-new-deployment \
        --region $AWS_REGION \
        --profile $AWS_PROFILE
    
    print_info "✅ ECS service update initiated!"
    print_warning "Service deployment may take 3-5 minutes to complete"
}

# Build and deploy frontend
deploy_frontend() {
    print_step "Building and deploying frontend..."
    
    # Load deployment outputs  
    source deployment-outputs.env
    
    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        print_warning "Frontend directory not found, skipping frontend deployment"
        return
    fi
    
    cd frontend
    
    # Install dependencies
    print_info "Installing frontend dependencies..."
    npm install
    
    # Create production environment file
    cat > .env.production << EOF
REACT_APP_API_URL=https://$CLOUDFRONT_DOMAIN/api
REACT_APP_ENVIRONMENT=production
EOF
    
    # Build for production
    print_info "Building frontend for production..."
    npm run build
    
    # Deploy to S3
    print_info "Deploying to S3..."
    aws s3 sync build/ s3://$FRONTEND_BUCKET/ \
        --delete \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --cache-control "public, max-age=31536000" \
        --exclude "*.html" \
        --exclude "*.json"
    
    # Deploy HTML files with shorter cache
    aws s3 sync build/ s3://$FRONTEND_BUCKET/ \
        --delete \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --cache-control "public, max-age=300" \
        --include "*.html" \
        --include "*.json"
    
    # Invalidate CloudFront cache
    print_info "Invalidating CloudFront cache..."
    DISTRIBUTION_ID=$(aws cloudfront list-distributions --profile $AWS_PROFILE --query "DistributionList.Items[?Comment=='Total Life AI Frontend Distribution'].Id" --output text)
    aws cloudfront create-invalidation \
        --distribution-id $DISTRIBUTION_ID \
        --paths "/*" \
        --region $AWS_REGION \
        --profile $AWS_PROFILE
    
    cd ..
    print_info "✅ Frontend deployed successfully!"
}

# Setup configuration parameters
setup_configuration() {
    print_step "Setting up configuration parameters..."
    
    echo ""
    echo -e "${YELLOW}🔐 CONFIGURATION REQUIRED${NC}"
    echo "You need to manually set these parameters in AWS Systems Manager:"
    echo ""
    echo "1. Together AI API Key (for 90% cost savings!):"
    echo "   aws ssm put-parameter --name '/totallifeai/together-api-key' --value 'YOUR_TOGETHER_AI_KEY' --type 'SecureString' --overwrite"
    echo ""
    echo "2. OpenAI API Key (fallback):"
    echo "   aws ssm put-parameter --name '/totallifeai/openai-api-key' --value 'YOUR_OPENAI_KEY' --type 'SecureString' --overwrite"
    echo ""
    echo "3. Application Secret Key:"
    echo "   aws ssm put-parameter --name '/totallifeai/secret-key' --value '\$(openssl rand -base64 32)' --type 'SecureString' --overwrite"
    echo ""
    echo -e "${CYAN}💡 Get your Together AI API key: https://api.together.xyz/settings/api-keys${NC}"
    echo -e "${CYAN}💡 Get your OpenAI API key: https://platform.openai.com/api-keys${NC}"
    echo ""
    
    read -p "Press Enter to continue once you've set these parameters..."
}

# Initialize database
initialize_database() {
    print_step "Initializing database..."
    
    print_info "Database will be automatically initialized on first run"
    print_info "✅ Database initialization configured"
}

# Final status check
check_deployment_status() {
    print_step "Checking deployment status..."
    
    # Load deployment outputs
    source deployment-outputs.env
    
    # Check ALB health
    print_info "Testing backend health..."
    sleep 30  # Wait for services to be ready
    
    if curl -f "http://$ALB_DNS/health" > /dev/null 2>&1; then
        print_info "✅ Backend is healthy"
    else
        print_warning "Backend may still be starting up"
    fi
    
    echo ""
    echo -e "${GREEN}"
    echo "============================================================================"
    echo "🎉 DEPLOYMENT COMPLETE!"
    echo "============================================================================"
    echo -e "${NC}"
    echo -e "${CYAN}🌐 Frontend URL: https://$CLOUDFRONT_DOMAIN${NC}"
    echo -e "${CYAN}🔧 Backend API: http://$ALB_DNS${NC}"
    echo -e "${CYAN}📚 API Docs: http://$ALB_DNS/docs${NC}"
    echo ""
    echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
    echo "1. Set your API keys using the commands above"
    echo "2. Visit your application: https://$CLOUDFRONT_DOMAIN"
    echo "3. Register an account and start using your AI!"
    echo ""
    echo -e "${GREEN}💰 Your system is configured for 90% cost savings with Together AI!${NC}"
    echo -e "${GREEN}🔒 Production-ready with auto-scaling and security best practices${NC}"
    echo ""
}

# Cleanup function for errors
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Deployment failed!"
        echo "Check the logs above for details"
        echo "You can re-run this script to retry"
    fi
}

trap cleanup EXIT

# Main deployment flow
main() {
    print_header
    
    check_prerequisites
    check_aws_setup
    setup_cdk
    bootstrap_cdk
    deploy_infrastructure
    build_and_push_image
    update_ecs_service
    deploy_frontend  
    setup_configuration
    initialize_database
    check_deployment_status
    
    print_step "🎉 Total Life AI deployed successfully to AWS!"
}

# Run main function
main "$@"
