#!/bin/bash

# ============================================================================
# TotalLifeAI - ECS Service Update Script
# ============================================================================
# Updates the ECS service with new Docker image and restarts tasks
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

print_step "Updating ECS service with latest Docker image..."

# Check prerequisites
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Get infrastructure details from CloudFormation
print_step "Getting infrastructure details..."

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

ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name $PROJECT_NAME \
    --profile $AWS_PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
    --output text 2>/dev/null)

# If outputs aren't available yet, try to get resources directly
if [ -z "$CLUSTER_NAME" ] || [ "$CLUSTER_NAME" = "None" ]; then
    print_warning "CloudFormation outputs not ready, trying to find cluster directly..."
    CLUSTER_NAME=$(aws cloudformation describe-stack-resources \
        --stack-name $PROJECT_NAME \
        --profile $AWS_PROFILE \
        --query 'StackResources[?ResourceType==`AWS::ECS::Cluster`].PhysicalResourceId' \
        --output text 2>/dev/null)
fi

if [ -z "$SERVICE_NAME" ] || [ "$SERVICE_NAME" = "None" ]; then
    print_warning "CloudFormation outputs not ready, trying to find service directly..."
    SERVICE_NAME=$(aws cloudformation describe-stack-resources \
        --stack-name $PROJECT_NAME \
        --profile $AWS_PROFILE \
        --query 'StackResources[?ResourceType==`AWS::ECS::Service`].PhysicalResourceId' \
        --output text 2>/dev/null | head -1)
fi

if [ -z "$ECR_URI" ] || [ "$ECR_URI" = "None" ]; then
    print_warning "CloudFormation outputs not ready, trying to find ECR directly..."
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

if [ -z "$CLUSTER_NAME" ] || [ "$CLUSTER_NAME" = "None" ]; then
    print_error "Could not find ECS cluster. Make sure infrastructure is deployed first."
    exit 1
fi

if [ -z "$SERVICE_NAME" ] || [ "$SERVICE_NAME" = "None" ]; then
    print_error "Could not find ECS service. Make sure infrastructure is deployed first."
    exit 1
fi

if [ -z "$ECR_URI" ] || [ "$ECR_URI" = "None" ]; then
    print_error "Could not find ECR repository. Make sure infrastructure is deployed first."
    exit 1
fi

print_info "✅ Cluster: $CLUSTER_NAME"
print_info "✅ Service: $SERVICE_NAME"
print_info "✅ ECR Repository: $ECR_URI"

# Get current task definition
print_step "Getting current task definition..."
CURRENT_TASK_DEF_ARN=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --profile $AWS_PROFILE \
    --query 'services[0].taskDefinition' \
    --output text)

if [ -z "$CURRENT_TASK_DEF_ARN" ]; then
    print_error "Could not get current task definition"
    exit 1
fi

print_info "Current task definition: $CURRENT_TASK_DEF_ARN"

# Get the task definition family and revision
TASK_DEF_FAMILY=$(echo $CURRENT_TASK_DEF_ARN | cut -d'/' -f2 | cut -d':' -f1)
CURRENT_REVISION=$(echo $CURRENT_TASK_DEF_ARN | cut -d':' -f2)

print_info "Task definition family: $TASK_DEF_FAMILY"
print_info "Current revision: $CURRENT_REVISION"

# Get current task definition JSON
TASK_DEF_JSON=$(aws ecs describe-task-definition \
    --task-definition $CURRENT_TASK_DEF_ARN \
    --profile $AWS_PROFILE \
    --query 'taskDefinition')

# Update the image in task definition
UPDATED_TASK_DEF=$(echo $TASK_DEF_JSON | jq -r \
    --arg new_image "$ECR_URI:latest" \
    '
    # Remove fields that cannot be included in new task definition
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy) |
    # Update the image
    .containerDefinitions[0].image = $new_image
    ')

# Write updated task definition to temp file
echo "$UPDATED_TASK_DEF" > /tmp/updated-task-def.json

# Register new task definition
print_step "Registering new task definition..."
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/updated-task-def.json \
    --profile $AWS_PROFILE \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

if [ -z "$NEW_TASK_DEF_ARN" ]; then
    print_error "Failed to register new task definition"
    rm -f /tmp/updated-task-def.json
    exit 1
fi

NEW_REVISION=$(echo $NEW_TASK_DEF_ARN | cut -d':' -f2)
print_info "✅ New task definition: $NEW_TASK_DEF_ARN"
print_info "✅ New revision: $NEW_REVISION"

# Update the service
print_step "Updating ECS service..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $NEW_TASK_DEF_ARN \
    --force-new-deployment \
    --profile $AWS_PROFILE \
    > /dev/null

print_info "✅ Service update initiated"

# Wait for deployment to complete
print_step "Waiting for deployment to stabilize (this may take 3-5 minutes)..."
print_warning "You can press Ctrl+C to exit early, but the deployment will continue in the background"

# Show deployment progress
echo ""
echo "Deployment progress:"
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --profile $AWS_PROFILE

# Check final status
print_step "Checking final deployment status..."
SERVICE_STATUS=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --profile $AWS_PROFILE \
    --query 'services[0].{
        status: status,
        runningCount: runningCount,
        pendingCount: pendingCount,
        desiredCount: desiredCount,
        taskDefinition: taskDefinition,
        deployments: deployments[0].{
            status: status,
            rolloutState: rolloutState,
            createdAt: createdAt
        }
    }')

echo ""
echo "Service Status:"
echo "$SERVICE_STATUS" | jq '.'

# Get load balancer URL
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name $PROJECT_NAME \
    --profile $AWS_PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
    --output text 2>/dev/null)

# Test health endpoint
if [ ! -z "$ALB_DNS" ]; then
    print_step "Testing health endpoint..."
    sleep 30  # Give time for tasks to start

    if curl -f "http://$ALB_DNS/health" > /dev/null 2>&1; then
        print_info "✅ Health check passed"
    else
        print_warning "Health check failed - service may still be starting"
        print_info "You can check status with: curl http://$ALB_DNS/health"
    fi
fi

# Clean up
rm -f /tmp/updated-task-def.json

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}🎉 ECS SERVICE UPDATE COMPLETE!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo -e "${BLUE}📋 Service Details:${NC}"
echo -e "${BLUE}   • Cluster: $CLUSTER_NAME${NC}"
echo -e "${BLUE}   • Service: $SERVICE_NAME${NC}"
echo -e "${BLUE}   • Task Definition: $NEW_TASK_DEF_ARN${NC}"
echo -e "${BLUE}   • Revision: $CURRENT_REVISION → $NEW_REVISION${NC}"
if [ ! -z "$ALB_DNS" ]; then
    echo -e "${BLUE}   • Health Check: http://$ALB_DNS/health${NC}"
    echo -e "${BLUE}   • API Docs: http://$ALB_DNS/docs${NC}"
fi
echo ""
echo -e "${YELLOW}🔍 Monitor deployment:${NC}"
echo -e "${YELLOW}   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME${NC}"
echo ""