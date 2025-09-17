#!/bin/bash

# ============================================================================
# TotalLifeAI - Frontend Deployment Script
# ============================================================================
# Builds and deploys the React frontend to S3 + CloudFront
# ============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
# CloudFormation stack name (override with env var PROJECT_NAME)
# Default matches CDK stack in aws-infrastructure/app.py
PROJECT_NAME="${PROJECT_NAME:-TotalLifeAI-Prod-Clean}"
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

print_step "Deploying frontend to S3 + CloudFront..."

# Check prerequisites
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm not found. Please install Node.js first."
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    print_error "Frontend directory not found"
    print_info "Make sure you're running this script from the project root"
    exit 1
fi

# Get infrastructure details from CloudFormation
print_step "Getting infrastructure details..."

# Helper to resolve outputs from possible stack names
resolve_output() {
  local output_key="$1"; shift
  local stack
  for stack in "$@"; do
    if aws cloudformation describe-stacks --stack-name "$stack" --profile "$AWS_PROFILE" >/dev/null 2>&1; then
      aws cloudformation describe-stacks \
        --stack-name "$stack" \
        --profile "$AWS_PROFILE" \
        --query "Stacks[0].Outputs[?OutputKey==\`$output_key\`].OutputValue" \
        --output text 2>/dev/null && return 0
    fi
  done
  return 1
}

STACK_CANDIDATES=("$PROJECT_NAME" "TotalLifeAI-Prod-Clean" "TotalLifeAI-Production")

FRONTEND_BUCKET=$(resolve_output "FrontendBucketName" "${STACK_CANDIDATES[@]}")
CLOUDFRONT_DOMAIN=$(resolve_output "CloudFrontDomainName" "${STACK_CANDIDATES[@]}")
ALB_DNS=$(resolve_output "LoadBalancerDNS" "${STACK_CANDIDATES[@]}")

if [ -z "$FRONTEND_BUCKET" ] || [ "$FRONTEND_BUCKET" = "None" ]; then
    print_error "Could not find S3 bucket output (FrontendBucketName)."
    print_info "Checked stacks: ${STACK_CANDIDATES[*]}"
    print_info "Set PROJECT_NAME env var if your stack has a different name."
    exit 1
fi

if [ -z "$CLOUDFRONT_DOMAIN" ] || [ "$CLOUDFRONT_DOMAIN" = "None" ]; then
    print_error "Could not find CloudFront distribution output (CloudFrontDomainName)."
    print_info "Checked stacks: ${STACK_CANDIDATES[*]}"
    exit 1
fi

print_info "✅ S3 Bucket: $FRONTEND_BUCKET"
print_info "✅ CloudFront Domain: $CLOUDFRONT_DOMAIN"
print_info "✅ API Backend: $ALB_DNS"

# Navigate to frontend directory
cd frontend

# Install dependencies
print_step "Installing frontend dependencies..."
npm install

# Create production environment file
print_step "Creating production environment configuration..."
# Route API via CloudFront using relative path to avoid CORS/mixed content
cat > .env.production << EOF
# Production Environment Configuration
REACT_APP_API_URL=/api/v1
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
REACT_APP_BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GENERATE_SOURCEMAP=false
EOF

print_info "✅ Environment configuration created"

# Build for production
print_step "Building frontend for production..."
npm run build

if [ ! -d "build" ]; then
    print_error "Build directory not found. Build may have failed."
    exit 1
fi

print_info "✅ Frontend build completed"

# Deploy to S3
print_step "Deploying to S3..."

# Deploy static assets with long cache (CSS, JS, images)
print_info "Uploading static assets (with long cache)..."
aws s3 sync build/static/ s3://$FRONTEND_BUCKET/static/ \
    --region $AWS_REGION \
    --profile $AWS_PROFILE \
    --cache-control "public, max-age=31536000, immutable" \
    --delete

# Deploy other assets with medium cache
print_info "Uploading other assets (with medium cache)..."
aws s3 sync build/ s3://$FRONTEND_BUCKET/ \
    --region $AWS_REGION \
    --profile $AWS_PROFILE \
    --cache-control "public, max-age=3600" \
    --exclude "*.html" \
    --exclude "static/*" \
    --delete

# Deploy HTML files with short cache
print_info "Uploading HTML files (with short cache)..."
aws s3 sync build/ s3://$FRONTEND_BUCKET/ \
    --region $AWS_REGION \
    --profile $AWS_PROFILE \
    --cache-control "public, max-age=300, must-revalidate" \
    --include "*.html" \
    --delete

print_info "✅ Files uploaded to S3"

# Get CloudFront distribution ID
print_step "Getting CloudFront distribution ID..."
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --profile $AWS_PROFILE \
    --query "DistributionList.Items[?Comment=='TotalLifeAI Frontend Distribution'].Id" \
    --output text)

if [ -z "$DISTRIBUTION_ID" ] || [ "$DISTRIBUTION_ID" = "None" ]; then
    print_warning "Could not find CloudFront distribution ID. Skipping cache invalidation."
else
    # Invalidate CloudFront cache
    print_step "Invalidating CloudFront cache..."
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id $DISTRIBUTION_ID \
        --paths "/*" \
        --profile $AWS_PROFILE \
        --query 'Invalidation.Id' \
        --output text)

    print_info "✅ Cache invalidation initiated (ID: $INVALIDATION_ID)"
    print_warning "Cache invalidation may take 5-15 minutes to complete"
fi

# Return to project root
cd ..

# Test the deployment
print_step "Testing deployment..."
sleep 10  # Give some time for S3 to propagate

if curl -f "https://$CLOUDFRONT_DOMAIN" > /dev/null 2>&1; then
    print_info "✅ Frontend is accessible"
else
    print_warning "Frontend may not be immediately accessible due to CloudFront cache"
    print_info "It may take a few minutes for changes to propagate"
fi

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}🎉 FRONTEND DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo -e "${BLUE}🌐 Frontend URL: https://$CLOUDFRONT_DOMAIN${NC}"
echo -e "${BLUE}📦 S3 Bucket: $FRONTEND_BUCKET${NC}"
if [ ! -z "$DISTRIBUTION_ID" ]; then
    echo -e "${BLUE}☁️  CloudFront: $DISTRIBUTION_ID${NC}"
fi
echo -e "${BLUE}🔧 API Backend (via CloudFront): https://$CLOUDFRONT_DOMAIN/api/v1${NC}"
echo ""
echo -e "${YELLOW}📋 Environment Configuration:${NC}"
echo -e "${YELLOW}   • Environment: production${NC}"
echo -e "${YELLOW}   • API URL: /api/v1 (proxied by CloudFront)${NC}"
echo -e "${YELLOW}   • Version: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")${NC}"
echo ""
echo -e "${GREEN}✅ Your frontend is now live!${NC}"
echo ""
