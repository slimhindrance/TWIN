#!/bin/bash
# Complete ECS Deployment Script
# Deploys Digital Twin to AWS ECS with all infrastructure

set -e

# Configuration
CLUSTER_NAME="digital-twin-cluster"
SERVICE_NAME="digital-twin-service"
TASK_DEFINITION_FAMILY="digital-twin-task"
AWS_REGION="us-east-1"
DESIRED_COUNT=2

echo "🚀 Deploying Digital Twin to AWS ECS"
echo "================================================"

# Check required tools
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ jq not found. Please install it first."
    exit 1
fi

# Load environment variables
if [ -f "../.env.images" ]; then
    source ../.env.images
else
    echo "❌ Image info not found. Run docker/build-and-push.sh first."
    exit 1
fi

# Step 1: Update task definition with actual values
echo "📝 Updating task definition..."

# Get current AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get infrastructure outputs from CloudFormation
VPC_ID=$(aws cloudformation describe-stacks \
    --stack-name digital-twin-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`VPCId`].OutputValue' \
    --output text)

PRIVATE_SUBNET_1=$(aws cloudformation describe-stacks \
    --stack-name digital-twin-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnet1Id`].OutputValue' \
    --output text)

PRIVATE_SUBNET_2=$(aws cloudformation describe-stacks \
    --stack-name digital-twin-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnet2Id`].OutputValue' \
    --output text)

EFS_ID=$(aws cloudformation describe-stacks \
    --stack-name digital-twin-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`EFSFileSystemId`].OutputValue' \
    --output text)

SECURITY_GROUP_ID=$(aws cloudformation describe-stacks \
    --stack-name digital-twin-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSSecurityGroupId`].OutputValue' \
    --output text)

EXECUTION_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name digital-twin-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSTaskExecutionRoleArn`].OutputValue' \
    --output text)

TASK_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name digital-twin-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSTaskRoleArn`].OutputValue' \
    --output text)

TARGET_GROUP_ARN=$(aws cloudformation describe-stacks \
    --stack-name digital-twin-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBTargetGroupArn`].OutputValue' \
    --output text)

# Update task definition
TASK_DEF_FILE="../aws/ecs-task-definition.json"
UPDATED_TASK_DEF=$(cat $TASK_DEF_FILE | \
    jq --arg image "$DIGITAL_TWIN_IMAGE" \
       --arg account "$AWS_ACCOUNT_ID" \
       --arg region "$AWS_REGION" \
       --arg efs_id "$EFS_ID" \
       --arg exec_role "$EXECUTION_ROLE_ARN" \
       --arg task_role "$TASK_ROLE_ARN" \
    '.containerDefinitions[0].image = $image |
     .executionRoleArn = $exec_role |
     .taskRoleArn = $task_role |
     .containerDefinitions[0].secrets[0].valueFrom = "arn:aws:secretsmanager:" + $region + ":" + $account + ":secret:digital-twin/openai-key" |
     .containerDefinitions[0].secrets[1].valueFrom = "arn:aws:secretsmanager:" + $region + ":" + $account + ":secret:digital-twin/secret-key" |
     .containerDefinitions[0].repositoryCredentials.credentialsParameter = "arn:aws:secretsmanager:" + $region + ":" + $account + ":secret:acr-credentials" |
     .containerDefinitions[0].logConfiguration.options."awslogs-region" = $region |
     .volumes[0].efsVolumeConfiguration.fileSystemId = $efs_id')

echo "$UPDATED_TASK_DEF" > "/tmp/task-definition.json"

# Step 2: Register task definition
echo "📋 Registering task definition..."
TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-definition.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "✅ Task definition registered: $TASK_DEF_ARN"

# Step 3: Create or update service
echo "🔄 Creating/updating ECS service..."

# Check if service exists
if aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --query 'services[0].status' \
    --output text 2>/dev/null | grep -q "ACTIVE"; then
    
    echo "📝 Updating existing service..."
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --task-definition "$TASK_DEF_ARN" \
        --desired-count "$DESIRED_COUNT" \
        > /dev/null
else
    echo "🆕 Creating new service..."
    aws ecs create-service \
        --cluster "$CLUSTER_NAME" \
        --service-name "$SERVICE_NAME" \
        --task-definition "$TASK_DEF_ARN" \
        --desired-count "$DESIRED_COUNT" \
        --launch-type "FARGATE" \
        --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=DISABLED}" \
        --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=digital-twin-container,containerPort=8000" \
        --health-check-grace-period-seconds 300 \
        --enable-execute-command \
        > /dev/null
fi

echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME"

# Step 4: Get application URL
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name digital-twin-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerDNS`].OutputValue' \
    --output text)

echo "✅ Deployment Complete!"
echo "================================================"
echo "🌐 Your Digital Twin is now running at:"
echo "   http://$ALB_DNS"
echo ""
echo "📊 Service Status:"
aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --query 'services[0].{Status:status,RunningCount:runningCount,DesiredCount:desiredCount,TaskDefinition:taskDefinition}' \
    --output table

echo ""
echo "🔍 To check logs:"
echo "   aws logs tail /ecs/digital-twin --follow"
echo ""
echo "🛠️  To update deployment:"
echo "   1. Push new image: cd deployment/docker && ./build-and-push.sh"
echo "   2. Deploy update: cd deployment/scripts && ./deploy-to-ecs.sh"

# Clean up
rm -f /tmp/task-definition.json
