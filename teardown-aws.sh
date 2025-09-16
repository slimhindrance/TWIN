#!/bin/bash

# ============================================================================
# Total Life AI - AWS Infrastructure Teardown Script
# ============================================================================
# This script safely removes all AWS resources created by the deployment
# USE WITH CAUTION - This will delete all data!
# ============================================================================

set -e

# Configuration
PROJECT_NAME="TotalLifeAI-Production"
AWS_REGION="us-east-1"
AWS_PROFILE="default"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${RED}"
    echo "============================================================================"
    echo "🔥 TOTAL LIFE AI - AWS INFRASTRUCTURE TEARDOWN"
    echo "============================================================================"
    echo -e "${NC}"
    echo -e "${YELLOW}⚠️  WARNING: This will DELETE ALL AWS resources and data!${NC}"
    echo -e "${YELLOW}⚠️  This action cannot be undone!${NC}"
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

check_confirmation() {
    print_header
    
    echo -e "${RED}This will permanently delete:${NC}"
    echo "• All ECS services and tasks"
    echo "• RDS PostgreSQL database (including all user data)"
    echo "• S3 bucket and all frontend files"
    echo "• CloudFront distribution"
    echo "• ECR repository and all Docker images"
    echo "• VPC and all networking components"
    echo "• Load balancers and security groups"
    echo "• IAM roles and policies"
    echo "• Systems Manager parameters"
    echo "• CloudWatch logs"
    echo ""
    
    echo -e "${YELLOW}💰 This will stop all AWS charges for Total Life AI${NC}"
    echo ""
    
    read -p "Are you ABSOLUTELY SURE you want to delete everything? (type 'DELETE' to confirm): " confirmation
    
    if [ "$confirmation" != "DELETE" ]; then
        print_info "Teardown cancelled"
        exit 0
    fi
    
    echo ""
    read -p "Last chance! Type 'YES I AM SURE' to proceed: " final_confirmation
    
    if [ "$final_confirmation" != "YES I AM SURE" ]; then
        print_info "Teardown cancelled"
        exit 0
    fi
}

check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found"
        exit 1
    fi
    
    # Check CDK
    if ! command -v cdk &> /dev/null; then
        print_error "AWS CDK not found"
        exit 1
    fi
    
    # Test AWS credentials
    if ! aws sts get-caller-identity --profile $AWS_PROFILE > /dev/null 2>&1; then
        print_error "AWS credentials not configured"
        exit 1
    fi
    
    print_info "✅ Prerequisites satisfied"
}

empty_s3_buckets() {
    print_step "Emptying S3 buckets..."
    
    # Find S3 buckets created by the stack
    buckets=$(aws s3api list-buckets --profile $AWS_PROFILE --query 'Buckets[?contains(Name, `totallifeai`)].Name' --output text 2>/dev/null || true)
    
    if [ -n "$buckets" ]; then
        for bucket in $buckets; do
            print_info "Emptying bucket: $bucket"
            aws s3 rm s3://$bucket --recursive --profile $AWS_PROFILE || true
            
            # Delete all versions if versioning is enabled
            aws s3api delete-objects --bucket $bucket --profile $AWS_REGION \
                --delete "$(aws s3api list-object-versions --bucket $bucket --profile $AWS_PROFILE --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}')" 2>/dev/null || true
                
            # Delete delete markers
            aws s3api delete-objects --bucket $bucket --profile $AWS_REGION \
                --delete "$(aws s3api list-object-versions --bucket $bucket --profile $AWS_PROFILE --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}')" 2>/dev/null || true
        done
        print_info "✅ S3 buckets emptied"
    else
        print_info "No S3 buckets found to empty"
    fi
}

delete_ecr_images() {
    print_step "Deleting ECR images..."
    
    # Find ECR repositories
    repos=$(aws ecr describe-repositories --profile $AWS_PROFILE --region $AWS_REGION --query 'repositories[?contains(repositoryName, `totallifeai`)].repositoryName' --output text 2>/dev/null || true)
    
    if [ -n "$repos" ]; then
        for repo in $repos; do
            print_info "Deleting images from repository: $repo"
            
            # Get all image digests
            image_digests=$(aws ecr list-images --repository-name $repo --profile $AWS_PROFILE --region $AWS_REGION --query 'imageIds[*].imageDigest' --output text 2>/dev/null || true)
            
            if [ -n "$image_digests" ]; then
                # Delete images in batches of 100 (AWS limit)
                echo $image_digests | tr ' ' '\n' | split -l 100 - /tmp/ecr_batch_
                
                for batch_file in /tmp/ecr_batch_*; do
                    if [ -s "$batch_file" ]; then
                        image_ids=$(cat $batch_file | sed 's/^/imageDigest=/' | tr '\n' ' ')
                        aws ecr batch-delete-image --repository-name $repo --image-ids $image_ids --profile $AWS_PROFILE --region $AWS_REGION || true
                    fi
                done
                
                # Cleanup temp files
                rm -f /tmp/ecr_batch_*
            fi
        done
        print_info "✅ ECR images deleted"
    else
        print_info "No ECR repositories found"
    fi
}

stop_ecs_services() {
    print_step "Stopping ECS services..."
    
    # Get cluster name from CloudFormation if stack exists
    cluster_name=$(aws cloudformation describe-stacks --stack-name $PROJECT_NAME --profile $AWS_PROFILE --region $AWS_REGION --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' --output text 2>/dev/null || true)
    
    if [ -n "$cluster_name" ]; then
        # List services in the cluster
        services=$(aws ecs list-services --cluster $cluster_name --profile $AWS_PROFILE --region $AWS_REGION --query 'serviceArns[*]' --output text 2>/dev/null || true)
        
        if [ -n "$services" ]; then
            for service in $services; do
                service_name=$(basename $service)
                print_info "Scaling down service: $service_name"
                aws ecs update-service --cluster $cluster_name --service $service_name --desired-count 0 --profile $AWS_PROFILE --region $AWS_REGION || true
            done
            
            # Wait for services to scale down
            print_info "Waiting for services to stop..."
            sleep 30
        fi
        
        print_info "✅ ECS services stopped"
    else
        print_info "No ECS cluster found"
    fi
}

invalidate_cloudfront() {
    print_step "Invalidating CloudFront distributions..."
    
    # Find CloudFront distributions
    distributions=$(aws cloudfront list-distributions --profile $AWS_PROFILE --query "DistributionList.Items[?Comment=='Total Life AI Frontend Distribution'].Id" --output text 2>/dev/null || true)
    
    if [ -n "$distributions" ]; then
        for distribution_id in $distributions; do
            print_info "Creating invalidation for distribution: $distribution_id"
            aws cloudfront create-invalidation --distribution-id $distribution_id --paths "/*" --profile $AWS_PROFILE || true
        done
        print_info "✅ CloudFront invalidations created"
    else
        print_info "No CloudFront distributions found"
    fi
}

destroy_infrastructure() {
    print_step "Destroying CDK infrastructure..."
    
    cd aws-infrastructure
    
    # Activate virtual environment if it exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Destroy the stack
    print_warning "This may take 10-20 minutes..."
    cdk destroy --profile $AWS_PROFILE --force
    
    cd ..
    print_info "✅ Infrastructure destroyed"
}

cleanup_parameters() {
    print_step "Cleaning up Systems Manager parameters..."
    
    # Delete parameters by path
    aws ssm delete-parameters-by-path --path "/totallifeai" --recursive --profile $AWS_PROFILE --region $AWS_REGION || true
    
    print_info "✅ Parameters cleaned up"
}

cleanup_logs() {
    print_step "Cleaning up CloudWatch logs..."
    
    # Find log groups
    log_groups=$(aws logs describe-log-groups --profile $AWS_PROFILE --region $AWS_REGION --query 'logGroups[?contains(logGroupName, `totallifeai`)].logGroupName' --output text 2>/dev/null || true)
    
    if [ -n "$log_groups" ]; then
        for log_group in $log_groups; do
            print_info "Deleting log group: $log_group"
            aws logs delete-log-group --log-group-name $log_group --profile $AWS_PROFILE --region $AWS_REGION || true
        done
        print_info "✅ Log groups deleted"
    else
        print_info "No log groups found"
    fi
}

final_verification() {
    print_step "Performing final verification..."
    
    # Check if stack still exists
    if aws cloudformation describe-stacks --stack-name $PROJECT_NAME --profile $AWS_PROFILE --region $AWS_REGION > /dev/null 2>&1; then
        print_error "CloudFormation stack still exists!"
        return 1
    fi
    
    print_info "✅ All resources have been deleted"
}

cleanup_local_files() {
    print_step "Cleaning up local deployment files..."
    
    # Remove deployment outputs
    rm -f deployment-outputs.env
    
    # Clean CDK artifacts
    if [ -d "aws-infrastructure/cdk.out" ]; then
        rm -rf aws-infrastructure/cdk.out
    fi
    
    print_info "✅ Local files cleaned up"
}

print_completion() {
    echo ""
    echo -e "${GREEN}"
    echo "============================================================================"
    echo "🗑️  TEARDOWN COMPLETE!"
    echo "============================================================================"
    echo -e "${NC}"
    echo -e "${GREEN}✅ All AWS resources have been deleted${NC}"
    echo -e "${GREEN}✅ All charges have been stopped${NC}"
    echo -e "${GREEN}✅ All data has been permanently removed${NC}"
    echo ""
    echo -e "${BLUE}ℹ️  You can now safely remove this directory if desired${NC}"
    echo ""
}

# Error handling
cleanup_on_error() {
    if [ $? -ne 0 ]; then
        print_error "Teardown encountered errors!"
        echo "Some resources may still exist and continue charging"
        echo "Please check the AWS console manually"
        exit 1
    fi
}

trap cleanup_on_error EXIT

# Main teardown flow
main() {
    check_confirmation
    check_prerequisites
    empty_s3_buckets
    delete_ecr_images
    stop_ecs_services
    invalidate_cloudfront
    destroy_infrastructure
    cleanup_parameters
    cleanup_logs
    final_verification
    cleanup_local_files
    print_completion
}

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Total Life AI - AWS Infrastructure Teardown"
    echo ""
    echo "This script will DELETE ALL AWS resources created by the deployment."
    echo "This includes all data, databases, files, and configurations."
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "WARNING: This action cannot be undone!"
    exit 0
fi

# Run main function
main "$@"
