#!/bin/bash
# AWS Infrastructure Setup Script
# Creates complete AWS infrastructure for Digital Twin

set -e

# Configuration
STACK_NAME="digital-twin-infrastructure"
AWS_REGION="us-east-1"
TEMPLATE_FILE="../aws/infrastructure.yaml"

echo "🚀 Setting up AWS Infrastructure for Digital Twin"
echo "================================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Get parameters
read -p "Enter your Azure Container Registry login server: " ACR_LOGIN_SERVER
read -p "Enter your ACR username: " ACR_USERNAME
read -s -p "Enter your ACR password: " ACR_PASSWORD
echo ""
read -s -p "Enter your OpenAI API key: " OPENAI_API_KEY
echo ""
read -p "Enter your domain name (optional, press enter to skip): " DOMAIN_NAME

echo ""
echo "🏗️  Deploying CloudFormation stack..."

# Deploy the CloudFormation stack
aws cloudformation deploy \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        ACRLoginServer="$ACR_LOGIN_SERVER" \
        ACRUsername="$ACR_USERNAME" \
        ACRPassword="$ACR_PASSWORD" \
        OpenAIAPIKey="$OPENAI_API_KEY" \
        DomainName="$DOMAIN_NAME" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION"

echo "✅ Infrastructure deployment complete!"

# Get outputs
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerDNS`].OutputValue' \
    --output text)

CLUSTER_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' \
    --output text)

echo "================================================"
echo "✅ AWS Infrastructure Ready!"
echo "================================================"
echo "📋 Infrastructure Details:"
echo "   ECS Cluster: $CLUSTER_NAME"
echo "   Load Balancer: $ALB_DNS"
echo "   Region: $AWS_REGION"
echo ""
echo "🚀 Next Steps:"
echo "   1. Build and push your Docker image:"
echo "      cd ../docker && ./build-and-push.sh"
echo "   2. Deploy to ECS:"
echo "      cd ../scripts && ./deploy-to-ecs.sh"
echo "================================================"
