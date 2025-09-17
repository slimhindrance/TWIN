#!/bin/bash

# ============================================================================
# TotalLifeAI - ECR Docker Build and Push Script
# ============================================================================
# Builds and pushes the backend Docker image to AWS ECR
# ============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_NAME="TotalLifeAI-Production"
AWS_REGION="us-east-1"
AWS_PROFILE="default"

print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step "Building and pushing Docker image to ECR..."

# Check prerequisites
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

# Get ECR repository URI from CloudFormation stack or directly from ECR
print_step "Getting ECR repository URI..."
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name $PROJECT_NAME \
    --profile $AWS_PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
    --output text 2>/dev/null)

# If CloudFormation outputs aren't available yet, try to get ECR URI directly
if [ -z "$ECR_URI" ] || [ "$ECR_URI" = "None" ]; then
    print_warning "CloudFormation outputs not ready yet, checking ECR directly..."
    ECR_URI=$(aws ecr describe-repositories \
        --repository-names totallifeai-backend \
        --profile $AWS_PROFILE \
        --query 'repositories[0].repositoryUri' \
        --output text 2>/dev/null)
fi

# If still no ECR URI found, check for the CDK-created repository
if [ -z "$ECR_URI" ] || [ "$ECR_URI" = "None" ]; then
    ECR_REPO_NAME=$(aws cloudformation describe-stack-resources \
        --stack-name $PROJECT_NAME \
        --profile $AWS_PROFILE \
        --query 'StackResources[?ResourceType==`AWS::ECR::Repository`].PhysicalResourceId' \
        --output text 2>/dev/null)

    if [ ! -z "$ECR_REPO_NAME" ] && [ "$ECR_REPO_NAME" != "None" ]; then
        ECR_URI=$(aws ecr describe-repositories \
            --repository-names $ECR_REPO_NAME \
            --profile $AWS_PROFILE \
            --query 'repositories[0].repositoryUri' \
            --output text 2>/dev/null)
    fi
fi

if [ -z "$ECR_URI" ] || [ "$ECR_URI" = "None" ]; then
    print_error "Could not find ECR repository URI. Make sure infrastructure is deployed first."
    print_info "Run: ./deploy-aws.sh to deploy infrastructure"
    exit 1
fi

print_info "✅ ECR Repository: $ECR_URI"

# Login to ECR
print_step "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | \
docker login --username AWS --password-stdin $ECR_URI

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    print_error "Dockerfile not found in current directory"
    print_info "Make sure you're running this script from the project root"
    exit 1
fi

# Build Docker image
print_step "Building Docker image..."
IMAGE_NAME="totallifeai-backend"
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
BUILD_TIMESTAMP=$(date +%Y%m%d%H%M%S)

print_info "Building image: $IMAGE_NAME"
print_info "Git commit: $GIT_COMMIT"
print_info "Build timestamp: $BUILD_TIMESTAMP"

# Build the image
docker build \
    --build-arg BUILD_TIMESTAMP=$BUILD_TIMESTAMP \
    --build-arg GIT_COMMIT=$GIT_COMMIT \
    -t $IMAGE_NAME:latest \
    -t $IMAGE_NAME:$GIT_COMMIT \
    .

# Tag for ECR
print_step "Tagging images for ECR..."
docker tag $IMAGE_NAME:latest $ECR_URI:latest
docker tag $IMAGE_NAME:$GIT_COMMIT $ECR_URI:$GIT_COMMIT
docker tag $IMAGE_NAME:latest $ECR_URI:v1.0.$BUILD_TIMESTAMP

# Push to ECR
print_step "Pushing images to ECR..."
docker push $ECR_URI:latest
docker push $ECR_URI:$GIT_COMMIT
docker push $ECR_URI:v1.0.$BUILD_TIMESTAMP

print_info "✅ Docker images pushed successfully!"

# Clean up local images to save space
print_step "Cleaning up local images..."
docker rmi $IMAGE_NAME:latest $IMAGE_NAME:$GIT_COMMIT $ECR_URI:latest $ECR_URI:$GIT_COMMIT $ECR_URI:v1.0.$BUILD_TIMESTAMP || true

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}🎉 DOCKER BUILD AND PUSH COMPLETE!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo -e "${BLUE}📦 Available images in ECR:${NC}"
echo -e "${BLUE}   • $ECR_URI:latest${NC}"
echo -e "${BLUE}   • $ECR_URI:$GIT_COMMIT${NC}"
echo -e "${BLUE}   • $ECR_URI:v1.0.$BUILD_TIMESTAMP${NC}"
echo ""
echo -e "${YELLOW}🚀 Next step: Update ECS service${NC}"
echo -e "${YELLOW}   Run: ./update-ecs-service.sh${NC}"
echo ""