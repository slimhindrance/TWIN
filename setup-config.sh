#!/bin/bash

# ============================================================================
# TotalLifeAI - Configuration Setup Script
# ============================================================================
# Sets up required configuration parameters in AWS Systems Manager
# ============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${CYAN}"
    echo "============================================================================"
    echo "🔐 TOTALLIFEAI - CONFIGURATION SETUP"
    echo "============================================================================"
    echo -e "${NC}"
    echo -e "${BLUE}Setting up required API keys and configuration parameters${NC}"
    echo ""
}

# Function to check if parameter exists
parameter_exists() {
    local param_name=$1
    aws ssm get-parameter --name "$param_name" --profile $AWS_PROFILE > /dev/null 2>&1
}

# Function to set parameter
set_parameter() {
    local param_name=$1
    local param_value=$2
    local param_type=${3:-"SecureString"}

    if parameter_exists "$param_name"; then
        aws ssm put-parameter \
            --name "$param_name" \
            --value "$param_value" \
            --type "$param_type" \
            --overwrite \
            --profile $AWS_PROFILE > /dev/null
        print_info "✅ Updated: $param_name"
    else
        aws ssm put-parameter \
            --name "$param_name" \
            --value "$param_value" \
            --type "$param_type" \
            --profile $AWS_PROFILE > /dev/null
        print_info "✅ Created: $param_name"
    fi
}

# Function to generate secure random key
generate_secret_key() {
    openssl rand -base64 32
}

print_header

# Check prerequisites
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

if ! command -v openssl &> /dev/null; then
    print_error "OpenSSL not found. Please install OpenSSL first."
    exit 1
fi

print_step "Setting up configuration parameters..."

echo ""
echo -e "${YELLOW}🔑 API KEY CONFIGURATION${NC}"
echo ""
echo -e "${CYAN}We need to configure the following API keys:${NC}"
echo "1. Together AI API Key (primary AI provider - 90% cost savings!)"
echo "2. OpenAI API Key (fallback AI provider)"
echo "3. Application Secret Key (for JWT tokens and encryption)"
echo ""

# Together AI API Key
echo -e "${CYAN}📝 Together AI API Key${NC}"
echo "Together AI provides the same quality as OpenAI at 90% lower cost!"
echo -e "Get your API key at: ${BLUE}https://api.together.xyz/settings/api-keys${NC}"
echo ""

if parameter_exists "/totallifeai/together-api-key"; then
    print_info "Together AI API key already configured"
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -s -p "Enter your Together AI API key: " TOGETHER_API_KEY
        echo ""
        if [ ! -z "$TOGETHER_API_KEY" ]; then
            set_parameter "/totallifeai/together-api-key" "$TOGETHER_API_KEY"
        else
            print_warning "Empty key provided, skipping update"
        fi
    fi
else
    read -s -p "Enter your Together AI API key: " TOGETHER_API_KEY
    echo ""
    if [ ! -z "$TOGETHER_API_KEY" ]; then
        set_parameter "/totallifeai/together-api-key" "$TOGETHER_API_KEY"
    else
        print_warning "No Together AI API key provided"
    fi
fi

echo ""

# OpenAI API Key
echo -e "${CYAN}📝 OpenAI API Key (Fallback)${NC}"
echo -e "Get your API key at: ${BLUE}https://platform.openai.com/api-keys${NC}"
echo ""

if parameter_exists "/totallifeai/openai-api-key"; then
    print_info "OpenAI API key already configured"
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -s -p "Enter your OpenAI API key: " OPENAI_API_KEY
        echo ""
        if [ ! -z "$OPENAI_API_KEY" ]; then
            set_parameter "/totallifeai/openai-api-key" "$OPENAI_API_KEY"
        else
            print_warning "Empty key provided, skipping update"
        fi
    fi
else
    read -s -p "Enter your OpenAI API key: " OPENAI_API_KEY
    echo ""
    if [ ! -z "$OPENAI_API_KEY" ]; then
        set_parameter "/totallifeai/openai-api-key" "$OPENAI_API_KEY"
    else
        print_warning "No OpenAI API key provided"
    fi
fi

echo ""

# Application Secret Key
echo -e "${CYAN}📝 Application Secret Key${NC}"
echo "This is used for JWT tokens and application security"
echo ""

if parameter_exists "/totallifeai/secret-key"; then
    print_info "Application secret key already configured"
    read -p "Do you want to regenerate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SECRET_KEY=$(generate_secret_key)
        set_parameter "/totallifeai/secret-key" "$SECRET_KEY"
        print_warning "New secret key generated - this will invalidate existing user sessions"
    fi
else
    print_step "Generating application secret key..."
    SECRET_KEY=$(generate_secret_key)
    set_parameter "/totallifeai/secret-key" "$SECRET_KEY"
fi

echo ""

# Additional configuration parameters
print_step "Setting up additional configuration..."

# Database configuration (if needed)
set_parameter "/totallifeai/database-url" "postgresql://totallifeai:password@localhost/totallifeai" "String"
set_parameter "/totallifeai/environment" "production" "String"
set_parameter "/totallifeai/debug" "false" "String"
set_parameter "/totallifeai/log-level" "INFO" "String"

# Performance configuration
set_parameter "/totallifeai/max-workers" "4" "String"
set_parameter "/totallifeai/timeout" "30" "String"
set_parameter "/totallifeai/max-connections" "100" "String"

print_info "✅ Additional configuration parameters set"

echo ""

# Verify configuration
print_step "Verifying configuration..."

echo ""
echo -e "${CYAN}📋 Configuration Summary:${NC}"

PARAMS=(
    "/totallifeai/together-api-key"
    "/totallifeai/openai-api-key"
    "/totallifeai/secret-key"
    "/totallifeai/environment"
    "/totallifeai/debug"
    "/totallifeai/log-level"
)

for param in "${PARAMS[@]}"; do
    if parameter_exists "$param"; then
        if [[ "$param" == *"key"* ]]; then
            print_info "✅ $param: [CONFIGURED]"
        else
            VALUE=$(aws ssm get-parameter --name "$param" --profile $AWS_PROFILE --query 'Parameter.Value' --output text 2>/dev/null)
            print_info "✅ $param: $VALUE"
        fi
    else
        print_warning "❌ $param: [NOT SET]"
    fi
done

echo ""

# Restart ECS service to pick up new configuration
read -p "Do you want to restart the ECS service to apply the new configuration? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Restarting ECS service..."

    CLUSTER_NAME=$(aws cloudformation describe-stacks \
        --stack-name $PROJECT_NAME \
        --profile $AWS_PROFILE \
        --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
        --output text 2>/dev/null)

    SERVICE_NAME=$(aws cloudformation describe-stacks \
        --stack-name $PROJECT_NAME \
        --profile $AWS_PROFILE \
        --query 'Stacks[0].Outputs[?OutputKey==`ServiceName`].OutputValue' \
        --output text 2>/dev/null)

    if [ ! -z "$CLUSTER_NAME" ] && [ ! -z "$SERVICE_NAME" ]; then
        aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service $SERVICE_NAME \
            --force-new-deployment \
            --profile $AWS_PROFILE > /dev/null

        print_info "✅ Service restart initiated"
        print_warning "It may take 3-5 minutes for the service to fully restart"
    else
        print_warning "Could not find ECS service details"
    fi
fi

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}🎉 CONFIGURATION SETUP COMPLETE!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo -e "${BLUE}🔐 All API keys and configuration parameters have been set${NC}"
echo -e "${BLUE}🔄 ECS service will use the new configuration on next deployment${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Test your configuration with: curl http://[your-alb-dns]/health"
echo "2. If you restarted the service, monitor: aws ecs describe-services --cluster [cluster] --services [service]"
echo "3. Deploy frontend: ./deploy-frontend.sh"
echo ""
echo -e "${GREEN}💰 Your system is now configured for 90% cost savings with Together AI!${NC}"
echo ""