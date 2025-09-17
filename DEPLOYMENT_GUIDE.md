# 🚀 TotalLifeAI - AWS Deployment Guide

This guide walks you through the complete deployment process for TotalLifeAI to AWS production environment.

## 📋 Prerequisites

Before starting, ensure you have:

- **AWS CLI** installed and configured with appropriate permissions
- **Docker** installed and running
- **Node.js** (v16+) and npm installed
- **Python 3.8+** installed
- **Git** repository access
- **AWS Account** with sufficient permissions

## 🎯 Deployment Overview

The deployment process consists of 6 main stages:

```
1. Infrastructure → 2. Backend → 3. Configuration → 4. Frontend → 5. Verification → 6. Monitoring
```

## 📁 Available Scripts

| Script | Purpose | Stage |
|--------|---------|-------|
| `deploy-aws.sh` | **Complete end-to-end deployment** | All |
| `build-and-push-ecr.sh` | Build and push Docker image to ECR | 2 |
| `update-ecs-service.sh` | Update ECS service with new image | 2 |
| `setup-config.sh` | Configure API keys and parameters | 3 |
| `deploy-frontend.sh` | Build and deploy React frontend | 4 |
| `teardown-aws.sh` | Clean up all AWS resources | Cleanup |

## 🚀 Quick Start (Recommended)

### Option A: Complete Automated Deployment

For first-time deployment, use the all-in-one script:

```bash
# Make script executable
chmod +x deploy-aws.sh

# Run complete deployment
./deploy-aws.sh
```

This script will:
- ✅ Check prerequisites
- ✅ Deploy AWS infrastructure (10-15 min)
- ✅ Build and push Docker image
- ✅ Update ECS service
- ✅ Deploy frontend to S3/CloudFront
- ✅ Guide you through configuration setup

## 🔧 Manual Stage-by-Stage Deployment

### Stage 1: Infrastructure Deployment

**What it does:** Creates VPC, RDS, ECS, ALB, CloudFront, S3, ECR, IAM roles

```bash
# Navigate to infrastructure directory
cd aws-infrastructure

# Setup CDK environment
chmod +x setup-cdk.sh
./setup-cdk.sh

# Activate virtual environment
source .venv/bin/activate

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy infrastructure
cdk deploy --require-approval never

# Return to project root
cd ..
```

**Expected time:** 10-15 minutes
**Output:** ECR repository, RDS database, ECS cluster, Load balancer URLs

---

### Stage 2: Backend Deployment

**What it does:** Builds Docker image and deploys to ECS

```bash
# Make scripts executable
chmod +x build-and-push-ecr.sh update-ecs-service.sh

# Build and push Docker image
./build-and-push-ecr.sh

# Update ECS service
./update-ecs-service.sh
```

**Expected time:** 5-10 minutes
**Output:** Running backend service on ECS

---

### Stage 3: Configuration Setup

**What it does:** Sets up API keys and environment variables

```bash
# Make script executable
chmod +x setup-config.sh

# Configure API keys and parameters
./setup-config.sh
```

**Required inputs:**
- Together AI API key (primary - 90% cost savings)
- OpenAI API key (fallback)
- Auto-generated application secrets

**Expected time:** 2-3 minutes

---

### Stage 4: Frontend Deployment

**What it does:** Builds React app and deploys to S3/CloudFront

```bash
# Make script executable
chmod +x deploy-frontend.sh

# Deploy frontend
./deploy-frontend.sh
```

**Expected time:** 3-5 minutes
**Output:** Live frontend accessible via CloudFront URL

---

### Stage 5: Verification

**What it does:** Verify all services are running correctly

```bash
# Get deployment outputs
source deployment-outputs.env

# Test backend health
curl http://$ALB_DNS/health

# Test API documentation
curl http://$ALB_DNS/docs

# Test frontend
curl https://$CLOUDFRONT_DOMAIN
```

---

### Stage 6: Monitoring & Maintenance

```bash
# Monitor ECS service
aws ecs describe-services --cluster [cluster-name] --services [service-name]

# Check logs
aws logs tail /ecs/totallifeai --follow

# Monitor CloudFront
aws cloudfront get-distribution --id [distribution-id]
```

## 🔄 Update Workflows

### Backend Code Updates

```bash
# 1. Build and push new image
./build-and-push-ecr.sh

# 2. Update ECS service
./update-ecs-service.sh
```

### Frontend Updates

```bash
# Deploy updated frontend
./deploy-frontend.sh
```

### Configuration Updates

```bash
# Update API keys or settings
./setup-config.sh
```

### Infrastructure Updates

```bash
cd aws-infrastructure
cdk diff    # Review changes
cdk deploy  # Apply changes
cd ..
```

## 🐛 Troubleshooting

### Common Issues

#### 1. ECS Service Health Check Failures
```bash
# Check service status
aws ecs describe-services --cluster totallifeai-cluster --services [service-name]

# Check task logs
aws logs tail /ecs/totallifeai --follow

# Verify health endpoint
curl http://[alb-dns]/health
```

#### 2. Docker Build Failures
```bash
# Check Docker daemon
docker info

# Check Dockerfile syntax
docker build -t test .

# Clear Docker cache
docker system prune -a
```

#### 3. CloudFront Cache Issues
```bash
# Force cache invalidation
aws cloudfront create-invalidation --distribution-id [dist-id] --paths "/*"

# Check distribution status
aws cloudfront get-distribution --id [dist-id]
```

#### 4. API Key Configuration Issues
```bash
# Verify parameters are set
aws ssm get-parameter --name "/totallifeai/together-api-key"
aws ssm get-parameter --name "/totallifeai/openai-api-key"

# Update parameters
./setup-config.sh
```

### Log Locations

- **ECS Task Logs:** CloudWatch `/ecs/totallifeai`
- **ALB Access Logs:** S3 bucket (if enabled)
- **CloudFront Logs:** S3 bucket (if enabled)
- **CDK Deployment:** Local terminal output

## 💰 Cost Optimization

Your deployment is configured for cost optimization:

- **Together AI:** 90% cheaper than OpenAI for same quality
- **ECS Fargate:** Auto-scaling, pay-per-use
- **RDS:** Optimized instance sizes
- **CloudFront:** Edge caching reduces origin requests
- **S3:** Standard storage for static assets

**Estimated Monthly Costs:**
- **Light usage:** $50-80/month
- **Medium usage:** $80-120/month
- **Heavy usage:** $120-200/month

## 🔐 Security Features

- ✅ VPC with private subnets
- ✅ Security groups with minimal access
- ✅ RDS in private subnet
- ✅ SSL/TLS termination at ALB
- ✅ IAM roles with least privilege
- ✅ Secrets in AWS Systems Manager
- ✅ No hardcoded credentials

## 📊 Infrastructure Outputs

After successful deployment, you'll have:

| Resource | Purpose | Access |
|----------|---------|--------|
| **ALB DNS** | Backend API | `http://[alb-dns]` |
| **CloudFront** | Frontend | `https://[cloudfront-domain]` |
| **ECR Repository** | Docker images | AWS Console |
| **RDS Database** | Data storage | Private network only |
| **S3 Bucket** | Frontend files | Via CloudFront only |

## 🆘 Support & Resources

### AWS Resources Created

```
├── VPC (us-east-1)
│   ├── Public Subnets (2 AZs)
│   ├── Private Subnets (2 AZs)
│   ├── Internet Gateway
│   ├── NAT Gateways (2)
│   └── Route Tables
├── ECS Cluster
│   ├── Service (Fargate)
│   ├── Task Definition
│   └── Auto Scaling
├── RDS PostgreSQL
│   ├── Multi-AZ (optional)
│   └── Automated backups
├── Application Load Balancer
│   ├── Target Groups
│   └── Health Checks
├── CloudFront Distribution
├── S3 Bucket (Frontend)
├── ECR Repository
└── IAM Roles & Policies
```

### Getting Help

1. **Check AWS CloudFormation console** for stack events
2. **Review ECS service events** in AWS console
3. **Check application logs** in CloudWatch
4. **Verify security groups** and network ACLs
5. **Test API endpoints** manually with curl

### Cleanup

To remove all resources:

```bash
# Make script executable
chmod +x teardown-aws.sh

# Remove all AWS resources
./teardown-aws.sh
```

⚠️ **Warning:** This will delete all data and cannot be undone!

---

## 🎉 Success!

Once deployed, your TotalLifeAI system will be:

- 🌐 **Accessible worldwide** via CloudFront CDN
- 🔒 **Secure** with AWS best practices
- 📈 **Scalable** with auto-scaling capabilities
- 💰 **Cost-optimized** with Together AI integration
- 🛡️ **Production-ready** with monitoring and logging

Visit your frontend URL and start using your AI-powered application!