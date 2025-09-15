# 🚀 **Digital Twin - Production Deployment Guide**

**Complete guide to deploy your Digital Twin to Azure Container Registry + Amazon ECS**

---

## 📋 **Prerequisites**

### **Required Tools:**
- **Azure CLI**: `az` command ([Install Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- **AWS CLI**: `aws` command ([Install Guide](https://aws.amazon.com/cli/))
- **Docker**: Latest version ([Install Guide](https://docs.docker.com/get-docker/))
- **Git**: For version control
- **jq**: JSON processor (`apt-get install jq` or `brew install jq`)

### **Required Accounts:**
- ✅ **Azure Account** with Container Registry permissions
- ✅ **AWS Account** with ECS/CloudFormation permissions  
- ✅ **OpenAI API Key** with sufficient credits

---

## 🎯 **Deployment Overview**

**Architecture:**
- **Azure Container Registry (ACR)**: Stores your Docker images
- **Amazon ECS Fargate**: Runs your containerized application
- **Application Load Balancer**: Distributes traffic and provides HTTPS
- **Amazon EFS**: Persistent storage for vector database
- **AWS Secrets Manager**: Secure storage for API keys

**Benefits:**
- ✅ **Zero-downtime deployments**
- ✅ **Auto-scaling** based on traffic
- ✅ **High availability** across multiple AZs
- ✅ **Secure secret management**
- ✅ **Persistent data storage**

---

## 🚀 **Step-by-Step Deployment**

### **Step 1: Setup Azure Container Registry**

```bash
# Navigate to deployment directory
cd deployment

# Make scripts executable (Linux/Mac)
chmod +x azure/acr-setup.sh docker/build-and-push.sh scripts/*.sh

# Run ACR setup
./azure/acr-setup.sh
```

**What this does:**
- Creates Azure resource group
- Sets up Container Registry
- Saves credentials to `.env.acr`

### **Step 2: Build and Push Docker Image**

```bash
# Build and push your Digital Twin image
cd docker
./build-and-push.sh
```

**What this does:**
- Builds multi-stage Docker image (frontend + backend)
- Tags with latest and git commit hash
- Pushes to your Azure Container Registry
- Saves image info for ECS deployment

### **Step 3: Setup AWS Infrastructure**

```bash
# Create complete AWS infrastructure
cd ../scripts
./setup-aws-infrastructure.sh
```

**You'll be prompted for:**
- Azure Container Registry details (from Step 1)
- OpenAI API key
- Your domain name (optional)

**What this creates:**
- VPC with public/private subnets
- Application Load Balancer
- ECS Fargate cluster
- EFS file system for data persistence
- Security groups and IAM roles
- AWS Secrets Manager for secure API key storage

### **Step 4: Deploy to ECS**

```bash
# Deploy your Digital Twin to ECS
./deploy-to-ecs.sh
```

**What this does:**
- Updates ECS task definition with your image
- Creates/updates ECS service
- Configures load balancer integration
- Waits for deployment to complete

---

## ✅ **Verification & Testing**

### **1. Check Deployment Status**
```bash
# Check ECS service status
aws ecs describe-services \
  --cluster digital-twin-cluster \
  --services digital-twin-service

# Get your application URL
aws cloudformation describe-stacks \
  --stack-name digital-twin-infrastructure \
  --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerDNS`].OutputValue' \
  --output text
```

### **2. Test Your Application**
```bash
# Test health endpoint
curl http://your-alb-dns/health

# Test API
curl http://your-alb-dns/api/v1/sources/supported
```

### **3. View Logs**
```bash
# View application logs
aws logs tail /ecs/digital-twin --follow
```

---

## 🔧 **Post-Deployment Configuration**

### **1. Custom Domain (Optional)**
```bash
# Add SSL certificate for your domain
aws acm request-certificate \
  --domain-name your-domain.com \
  --subject-alternative-names www.your-domain.com \
  --validation-method DNS
```

### **2. Monitoring & Alerts**
- Set up CloudWatch dashboards
- Configure scaling policies
- Create health check alarms

### **3. Backup Strategy**
- EFS automatic backups are enabled
- Consider database backups if using RDS

---

## 🔄 **Updates & Maintenance**

### **Deploy Updates**
```bash
# 1. Build new image
cd deployment/docker
./build-and-push.sh

# 2. Deploy to ECS
cd ../scripts
./deploy-to-ecs.sh
```

### **Scale Your Application**
```bash
# Scale to more instances
aws ecs update-service \
  --cluster digital-twin-cluster \
  --service digital-twin-service \
  --desired-count 5
```

### **View Resource Usage**
- **ECS Console**: Monitor CPU/Memory usage
- **CloudWatch**: View detailed metrics
- **Cost Explorer**: Track spending

---

## 💰 **Cost Optimization**

### **Estimated Monthly Costs (US East):**
- **ECS Fargate** (2 tasks): ~$30-50
- **Application Load Balancer**: ~$20
- **EFS Storage**: ~$5-15 (based on usage)
- **CloudWatch Logs**: ~$2-5
- **ACR Storage**: ~$1-5
- **Total**: **~$60-100/month** for production workload

### **Cost Saving Tips:**
- Use Fargate Spot for non-critical workloads
- Set up auto-scaling to scale down during low traffic
- Use CloudWatch to monitor and optimize resource usage
- Consider Reserved Instances for predictable workloads

---

## 🛡️ **Security Best Practices**

### **Already Implemented:**
- ✅ **Secrets in AWS Secrets Manager** (not in environment variables)
- ✅ **VPC with private subnets** for application security
- ✅ **Security groups** restricting network access
- ✅ **EFS encryption** at rest and in transit
- ✅ **IAM roles** with least privilege access

### **Additional Recommendations:**
- Enable **AWS GuardDuty** for threat detection
- Set up **AWS Config** for compliance monitoring
- Use **AWS WAF** with ALB for additional protection
- Enable **VPC Flow Logs** for network monitoring

---

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **"Task failed to start"**
```bash
# Check task definition
aws ecs describe-task-definition --task-definition digital-twin-task

# Check service events
aws ecs describe-services --cluster digital-twin-cluster --services digital-twin-service
```

#### **"Health check failing"**
```bash
# Check logs
aws logs tail /ecs/digital-twin --follow

# Verify container is running
aws ecs list-tasks --cluster digital-twin-cluster --service-name digital-twin-service
```

#### **"Cannot pull image"**
- Verify ACR credentials in AWS Secrets Manager
- Check repository permissions in Azure

#### **"Application not responding"**
- Check security group rules
- Verify target group health
- Review application logs

---

## 🎊 **Success! Your Digital Twin is Live**

### **What You've Accomplished:**
- ✅ **Enterprise-grade deployment** with high availability
- ✅ **Secure secret management** with AWS Secrets Manager
- ✅ **Auto-scaling infrastructure** that handles traffic spikes
- ✅ **Persistent data storage** that survives restarts
- ✅ **Zero-downtime deployments** for continuous updates
- ✅ **Production monitoring** with CloudWatch integration

### **Your URLs:**
- **Application**: `http://your-alb-dns-name.us-east-1.elb.amazonaws.com`
- **Health Check**: `http://your-alb-dns/health`
- **API Docs**: `http://your-alb-dns/docs`

---

## 🚀 **Next Steps**

### **Immediate:**
1. **Test all functionality** with real Notion/Obsidian data
2. **Set up custom domain** with SSL certificate
3. **Configure monitoring** and alerting

### **Growth Phase:**
1. **Add CDN** (CloudFront) for better global performance
2. **Set up CI/CD pipeline** for automated deployments
3. **Add database** (RDS) for user management and analytics
4. **Implement caching** (Redis) for improved performance

### **Enterprise Features:**
1. **Multi-region deployment** for disaster recovery
2. **Advanced monitoring** with APM tools
3. **Security scanning** and compliance monitoring
4. **Team collaboration** features

---

**🎯 Your Digital Twin is now running in production with enterprise-grade infrastructure!**

**Ready to handle thousands of users and scale to millions!** 🚀
