# 🚀 Total Life AI - AWS Production Deployment

Complete Infrastructure as Code deployment for your cost-optimized RAG system with **90% AI cost savings** using Together AI!

## 📋 **WHAT THIS CREATES**

### **🏗️ Complete AWS Infrastructure**
- **VPC** with public/private subnets across 2 Availability Zones
- **RDS PostgreSQL** database with automated backups
- **ECS Fargate** cluster with auto-scaling (2-10 instances)
- **Application Load Balancer** with health checks
- **CloudFront CDN** + **S3** for global frontend delivery
- **ECR Repository** for Docker image management
- **IAM Roles** with least-privilege security
- **Systems Manager** for secure parameter storage
- **CloudWatch** logging and monitoring

### **💰 Cost-Optimized AI Stack**
- **Together AI** (Primary): ~$0.20 per 1M tokens (90% savings!)
- **AWS Bedrock** (Fallback): Claude Haiku for complex queries
- **OpenAI** (Emergency): GPT-4o-mini for maximum reliability
- Smart routing based on query complexity
- Built-in cost controls and usage limits

### **🔒 Production-Ready Features**
- Multi-user authentication with JWT
- Auto-scaling based on CPU/memory
- Database connection pooling
- CORS protection
- Rate limiting
- Health checks
- Automated deployments
- Zero-downtime updates

---

## 🎯 **DEPLOYMENT OPTIONS**

### **Option 1: One-Command Deployment (Linux/macOS)**
```bash
chmod +x deploy-aws.sh
./deploy-aws.sh
```

### **Option 2: PowerShell Deployment (Windows)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deploy-aws.ps1
```

### **Option 3: Custom Deployment**
```bash
# Deploy only infrastructure
./deploy-aws.sh --only-infrastructure

# Update code only (skip infrastructure)
./deploy-aws.sh --skip-infrastructure

# Use different AWS profile/region
./deploy-aws.ps1 -AWSProfile myprofile -AWSRegion us-west-2
```

---

## 📋 **PREREQUISITES**

### **Required Tools**
```bash
# Install these on your deployment machine:

# 1. AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# 2. Docker
sudo apt update && sudo apt install docker.io

# 3. Node.js & npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 4. AWS CDK
npm install -g aws-cdk

# 5. Python 3.8+
sudo apt install python3 python3-pip python3-venv
```

### **AWS Account Setup**
```bash
# Configure AWS credentials
aws configure

# Required AWS permissions:
# - CloudFormation (full access)
# - ECS (full access)
# - RDS (full access)
# - EC2 (full access)
# - S3 (full access)
# - CloudFront (full access)
# - IAM (full access)
# - Systems Manager (full access)
```

---

## 🔧 **CONFIGURATION**

### **Step 1: Get API Keys**

#### **Together AI (RECOMMENDED - 90% Cost Savings)**
1. Visit: https://api.together.xyz/settings/api-keys
2. Create account and get free API key
3. **Cost**: ~$0.20 per 1M tokens vs $2.00+ for OpenAI!

#### **OpenAI (Fallback)**
1. Visit: https://platform.openai.com/api-keys  
2. Create API key with billing enabled
3. **Cost**: ~$0.50 per 1M tokens for GPT-4o-mini

#### **AWS Bedrock (Auto-configured)**
- Automatically configured in your AWS region
- **Cost**: ~$0.25 per 1M tokens for Claude Haiku
- No separate setup required

### **Step 2: Set Configuration Parameters**
After deployment, run these commands:

```bash
# Set Together AI key (PRIMARY - saves 90%!)
aws ssm put-parameter \
  --name '/totallifeai/together-api-key' \
  --value 'YOUR_TOGETHER_AI_API_KEY' \
  --type 'SecureString' \
  --overwrite

# Set OpenAI key (fallback)
aws ssm put-parameter \
  --name '/totallifeai/openai-api-key' \
  --value 'YOUR_OPENAI_API_KEY' \
  --type 'SecureString' \
  --overwrite

# Generate secure app secret
aws ssm put-parameter \
  --name '/totallifeai/secret-key' \
  --value "$(openssl rand -base64 32)" \
  --type 'SecureString' \
  --overwrite
```

---

## 🚀 **DEPLOYMENT PROCESS**

### **What The Script Does**
1. **Validates prerequisites** and AWS credentials
2. **Bootstraps CDK** in your AWS account (one-time)
3. **Deploys infrastructure** using CloudFormation
4. **Builds Docker image** for your backend
5. **Pushes image to ECR** repository
6. **Updates ECS service** with new image
7. **Builds and deploys frontend** to S3/CloudFront
8. **Configures parameters** and performs health checks

### **Deployment Timeline**
- **Infrastructure**: 10-15 minutes
- **Docker build/push**: 3-5 minutes  
- **Service update**: 2-3 minutes
- **Frontend deployment**: 1-2 minutes
- **Total**: ~20 minutes

### **Live Progress Example**
```
🚀 TOTAL LIFE AI - AWS PRODUCTION DEPLOYMENT
============================================================================
💰 Cost-Optimized RAG System with Together AI (90% savings!)
🏗️  Complete AWS infrastructure with ECS, RDS, CloudFront
🔒 Production-ready security and auto-scaling

▶ Checking prerequisites...
ℹ️  ✅ All prerequisites satisfied
▶ Checking AWS configuration...
ℹ️  ✅ AWS Account: 123456789012
ℹ️  ✅ AWS User: arn:aws:iam::123456789012:user/deployer
ℹ️  ✅ AWS Region: us-east-1
▶ Deploying AWS infrastructure...
...
🎉 DEPLOYMENT COMPLETE!
============================================================================
🌐 Frontend URL: https://d1234567890.cloudfront.net
🔧 Backend API: http://totallifeai-alb-1234567890.us-east-1.elb.amazonaws.com
📚 API Docs: http://totallifeai-alb-1234567890.us-east-1.elb.amazonaws.com/docs
```

---

## 🏗️ **ARCHITECTURE OVERVIEW**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CloudFront    │    │ Application      │    │    ECS Fargate  │
│   Distribution  │◄───┤ Load Balancer    │◄───┤    Service      │
│   (Frontend)    │    │ (Backend Proxy)  │    │   (Auto-Scaling)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   S3 Bucket     │    │  Route 53 DNS    │    │  ECR Repository │
│ (Static Assets) │    │  (Optional)       │    │ (Docker Images) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                 │
                                 ▼
         ┌─────────────────────────────────────────┐
         │              VPC Network                │
         │  ┌─────────────────┐ ┌─────────────────┐│
         │  │ Public Subnets  │ │ Private Subnets ││
         │  │   (ALB, NAT)    │ │  (ECS, RDS)     ││
         │  └─────────────────┘ └─────────────────┘│
         └─────────────────────────────────────────┘
                                 │
                                 ▼
         ┌─────────────────┐    ┌─────────────────┐
         │ RDS PostgreSQL  │    │ Systems Manager │
         │   (Database)    │    │  (Config/Secrets)│
         └─────────────────┘    └─────────────────┘
```

---

## 💰 **COST ESTIMATION**

### **Monthly AWS Costs**
| Service | Configuration | Est. Cost |
|---------|--------------|-----------|
| **ECS Fargate** | 2x 0.5 vCPU, 1GB RAM | $30 |
| **RDS PostgreSQL** | t3.micro, 20GB SSD | $18 |
| **Application Load Balancer** | Standard ALB | $18 |
| **CloudFront** | 1TB transfer | $8 |
| **S3** | 10GB storage | $0.25 |
| **ECR** | 5GB images | $0.50 |
| **Other** | NAT, logs, etc. | $5 |
| **TOTAL** | | **~$80/month** |

### **AI Model Costs (Per 1M Tokens)**
| Provider | Model | Cost | Savings |
|----------|-------|------|---------|
| **Together AI** | Llama 3.1 8B | $0.20 | **90%** ✅ |
| **AWS Bedrock** | Claude Haiku | $0.25 | **87%** |
| **OpenAI** | GPT-4o-mini | $0.50 | **75%** |
| ~~OpenAI~~ | ~~GPT-4~~ | ~~$2.00~~ | ~~Baseline~~ |

### **Total Cost Projection**
- **Light usage** (10K tokens/day): **~$90/month**
- **Moderate usage** (50K tokens/day): **~$120/month**  
- **Heavy usage** (200K tokens/day): **~$200/month**

---

## 🔒 **SECURITY FEATURES**

### **Network Security**
- VPC with private subnets for database and application
- Security groups with minimal required permissions
- NAT Gateway for outbound internet access only
- No direct internet access to database or application

### **Application Security**
- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- CORS protection
- Rate limiting per user
- SQL injection prevention with parameterized queries

### **AWS Security**
- IAM roles with least-privilege permissions
- Encrypted storage for databases and logs
- Secrets stored in Systems Manager Parameter Store
- VPC Flow Logs for network monitoring
- CloudWatch for audit logging

### **AI Security**
- API key rotation capability
- Cost limits and usage monitoring
- Query sanitization
- Response content filtering

---

## 📊 **MONITORING & SCALING**

### **Auto-Scaling Configuration**
```yaml
# ECS Service Auto-Scaling
Min Capacity: 2 tasks
Max Capacity: 10 tasks
Target CPU: 70%
Target Memory: 80%
Scale Out Cooldown: 2 minutes
Scale In Cooldown: 5 minutes

# Database Auto-Scaling
Storage: 20GB → 100GB (auto-expand)
Backup Retention: 7 days
Multi-AZ: Optional
```

### **Health Checks**
- **ECS Health Check**: `/health` endpoint every 60 seconds
- **Database Health**: Connection pool monitoring
- **Load Balancer Health**: HTTP 200 response required
- **Application Metrics**: Response time, error rate, throughput

### **Monitoring Dashboards**
- **CloudWatch Metrics**: CPU, memory, network, errors
- **Application Logs**: Structured JSON logging
- **Cost Monitoring**: Daily spend alerts
- **Usage Tracking**: API calls per user/tier

---

## 🔧 **CUSTOMIZATION OPTIONS**

### **Environment Variables**
See `backend/prod.env` for full configuration options:

```bash
# Scale configuration
MIN_REPLICAS=2
MAX_REPLICAS=10
TARGET_CPU_UTILIZATION=70

# Database configuration  
DB_POOL_SIZE=10
DB_MAX_CONNECTIONS=50

# AI provider priorities
AI_PRIMARY_PROVIDER=together
AI_FALLBACK_PROVIDER=bedrock
AI_EMERGENCY_PROVIDER=openai
```

### **Resource Sizing**
Edit `aws-infrastructure/app.py`:

```python
# Increase ECS task resources
memory_limit_mib=2048,  # Default: 1024
cpu=1024,              # Default: 512

# Upgrade database instance
ec2.InstanceType.of(
    ec2.InstanceClass.T3,
    ec2.InstanceSize.SMALL  # Default: MICRO
)
```

---

## 🛠️ **MAINTENANCE OPERATIONS**

### **Update Application Code**
```bash
# Push new code and redeploy
git push origin main
./deploy-aws.sh --skip-infrastructure
```

### **Scale Resources**
```bash
# Scale ECS service manually
aws ecs update-service \
  --cluster totallifeai-cluster \
  --service totallifeai-service \
  --desired-count 5
```

### **Database Maintenance**
```bash
# Create database backup
aws rds create-db-snapshot \
  --db-instance-identifier totallifeai-database \
  --db-snapshot-identifier manual-backup-$(date +%Y%m%d)

# Apply database updates (during maintenance window)
aws rds modify-db-instance \
  --db-instance-identifier totallifeai-database \
  --apply-immediately
```

### **Update Configuration**
```bash
# Update API keys without downtime
aws ssm put-parameter \
  --name '/totallifeai/together-api-key' \
  --value 'NEW_API_KEY' \
  --type 'SecureString' \
  --overwrite

# Restart ECS service to pick up new config
aws ecs update-service \
  --cluster totallifeai-cluster \
  --service totallifeai-service \
  --force-new-deployment
```

---

## 🔥 **TEARDOWN / CLEANUP**

### **Complete Infrastructure Removal**
```bash
# ⚠️ WARNING: This deletes EVERYTHING!
chmod +x teardown-aws.sh
./teardown-aws.sh
```

### **What Gets Deleted**
- All ECS services and tasks
- RDS database (including all data!)
- S3 buckets and files
- CloudFront distribution
- Load balancers and networking
- IAM roles and security groups
- CloudWatch logs
- All configuration parameters

### **Partial Cleanup**
```bash
# Stop ECS services only (keep database)
aws ecs update-service \
  --cluster totallifeai-cluster \
  --service totallifeai-service \
  --desired-count 0

# Delete specific resources via CloudFormation
aws cloudformation delete-stack \
  --stack-name TotalLifeAI-Production
```

---

## 🆘 **TROUBLESHOOTING**

### **Common Issues**

#### **"Import 'constructs' could not be resolved"**
This means the CDK environment isn't properly set up:

```bash
# Linux/macOS
cd aws-infrastructure
chmod +x setup-cdk.sh
./setup-cdk.sh

# Windows PowerShell
cd aws-infrastructure
.\setup-cdk.ps1

# Verify installation
python -c "import constructs; print('✅ Constructs imported successfully')"
```

#### **"CDK Bootstrap Required"**
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

#### **"Docker Image Not Found"**
```bash
# Rebuild and push Docker image
docker build -t totallifeai-backend .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ECR-URI
docker tag totallifeai-backend:latest ECR-URI:latest
docker push ECR-URI:latest
```

#### **"Database Connection Failed"**
```bash
# Check database security groups
aws ec2 describe-security-groups --filters "Name=group-name,Values=*Database*"

# Verify database status
aws rds describe-db-instances --db-instance-identifier totallifeai-database
```

#### **"Frontend Not Loading"**
```bash
# Check S3 bucket contents
aws s3 ls s3://FRONTEND-BUCKET-NAME/

# Check CloudFront distribution
aws cloudfront list-distributions --query 'DistributionList.Items[*].DomainName'

# Create cache invalidation
aws cloudfront create-invalidation --distribution-id DISTRIBUTION-ID --paths "/*"
```

### **Logs and Debugging**
```bash
# View ECS service logs
aws logs tail /aws/ecs/totallifeai --follow

# Check ECS service status
aws ecs describe-services --cluster totallifeai-cluster --services totallifeai-service

# View CloudFormation stack events
aws cloudformation describe-stack-events --stack-name TotalLifeAI-Production
```

---

## 📚 **ADDITIONAL RESOURCES**

### **Documentation**
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [AWS RDS Security](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.html)
- [CDK Developer Guide](https://docs.aws.amazon.com/cdk/v2/guide/)

### **AI Provider Documentation**
- [Together AI Docs](https://docs.together.ai/)
- [AWS Bedrock User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

### **Support**
- AWS Support (for infrastructure issues)
- GitHub Issues (for application bugs)
- Discord/Slack (for community support)

---

## 🎉 **CONGRATULATIONS!**

Your Total Life AI system is now running on production-grade AWS infrastructure with:

✅ **90% AI cost savings** with Together AI  
✅ **Auto-scaling** from 2 to 10 instances  
✅ **Multi-region** disaster recovery ready  
✅ **Enterprise security** with VPC isolation  
✅ **Zero-downtime deployments**  
✅ **Automated backups** and monitoring  
✅ **Global CDN** for fast frontend delivery  

**Your personal AI is ready to help you organize your entire life!** 🧠✨

---

*Generated by Total Life AI Deployment System v1.0*
