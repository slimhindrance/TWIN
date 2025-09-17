#!/bin/bash

# ============================================================================
# TotalLifeAI - Custom Domain Setup Script
# ============================================================================
# Sets up totallifeai.base2ml.com custom domain with SSL
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
DOMAIN_NAME="totallifeai.base2ml.com"
HOSTED_ZONE_ID="Z09099671VTWA1L2CL021"
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
    echo "🌐 SETTING UP CUSTOM DOMAIN: $DOMAIN_NAME"
    echo "============================================================================"
    echo -e "${NC}"
}

print_header

# Step 1: Request SSL Certificate
print_step "Requesting SSL certificate for $DOMAIN_NAME..."

# Check if certificate already exists
EXISTING_CERT=$(aws acm list-certificates \
    --region us-east-1 \
    --profile $AWS_PROFILE \
    --query "CertificateSummaryList[?DomainName=='$DOMAIN_NAME'].CertificateArn" \
    --output text 2>/dev/null || echo "")

if [ ! -z "$EXISTING_CERT" ] && [ "$EXISTING_CERT" != "None" ]; then
    print_info "✅ SSL certificate already exists: $EXISTING_CERT"
    CERTIFICATE_ARN=$EXISTING_CERT
else
    print_info "Requesting new SSL certificate..."
    CERTIFICATE_ARN=$(aws acm request-certificate \
        --domain-name $DOMAIN_NAME \
        --validation-method DNS \
        --region us-east-1 \
        --profile $AWS_PROFILE \
        --query 'CertificateArn' \
        --output text)

    print_info "✅ Certificate requested: $CERTIFICATE_ARN"

    # Wait for certificate details to be available
    print_info "Waiting for certificate validation details..."
    sleep 10
fi

# Step 2: Get DNS validation records
print_step "Getting DNS validation records..."

VALIDATION_RECORDS=$(aws acm describe-certificate \
    --certificate-arn $CERTIFICATE_ARN \
    --region us-east-1 \
    --profile $AWS_PROFILE \
    --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
    --output json)

if [ "$VALIDATION_RECORDS" = "null" ] || [ -z "$VALIDATION_RECORDS" ]; then
    print_warning "DNS validation records not yet available. Waiting..."
    sleep 30
    VALIDATION_RECORDS=$(aws acm describe-certificate \
        --certificate-arn $CERTIFICATE_ARN \
        --region us-east-1 \
        --profile $AWS_PROFILE \
        --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
        --output json)
fi

if [ "$VALIDATION_RECORDS" != "null" ] && [ ! -z "$VALIDATION_RECORDS" ]; then
    VALIDATION_NAME=$(echo $VALIDATION_RECORDS | jq -r '.Name')
    VALIDATION_VALUE=$(echo $VALIDATION_RECORDS | jq -r '.Value')
    VALIDATION_TYPE=$(echo $VALIDATION_RECORDS | jq -r '.Type')

    print_info "DNS Validation Record:"
    print_info "  Name: $VALIDATION_NAME"
    print_info "  Type: $VALIDATION_TYPE"
    print_info "  Value: $VALIDATION_VALUE"

    # Step 3: Create DNS validation record
    print_step "Creating DNS validation record in Route 53..."

    # Check if validation record already exists
    EXISTING_VALIDATION=$(aws route53 list-resource-record-sets \
        --hosted-zone-id $HOSTED_ZONE_ID \
        --profile $AWS_PROFILE \
        --query "ResourceRecordSets[?Name=='$VALIDATION_NAME' && Type=='$VALIDATION_TYPE'].Name" \
        --output text 2>/dev/null || echo "")

    if [ -z "$EXISTING_VALIDATION" ]; then
        aws route53 change-resource-record-sets \
            --hosted-zone-id $HOSTED_ZONE_ID \
            --profile $AWS_PROFILE \
            --change-batch "{
                \"Changes\": [{
                    \"Action\": \"CREATE\",
                    \"ResourceRecordSet\": {
                        \"Name\": \"$VALIDATION_NAME\",
                        \"Type\": \"$VALIDATION_TYPE\",
                        \"TTL\": 300,
                        \"ResourceRecords\": [{
                            \"Value\": \"$VALIDATION_VALUE\"
                        }]
                    }
                }]
            }" > /dev/null

        print_info "✅ DNS validation record created"
    else
        print_info "✅ DNS validation record already exists"
    fi
else
    print_warning "Could not get DNS validation records. Certificate may need manual validation."
fi

# Step 4: Get infrastructure details
print_step "Getting infrastructure details..."

# Get CloudFront distribution ID
CLOUDFRONT_DIST_ID=$(aws cloudfront list-distributions \
    --profile $AWS_PROFILE \
    --query "DistributionList.Items[?Comment=='Total Life AI Frontend Distribution'].Id" \
    --output text)

# Get ALB DNS name
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name $PROJECT_NAME \
    --profile $AWS_PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -z "$ALB_DNS" ] || [ "$ALB_DNS" = "None" ]; then
    ALB_DNS=$(aws elbv2 describe-load-balancers \
        --profile $AWS_PROFILE \
        --query 'LoadBalancers[0].DNSName' \
        --output text)
fi

print_info "✅ CloudFront Distribution: $CLOUDFRONT_DIST_ID"
print_info "✅ ALB DNS: $ALB_DNS"

# Step 5: Wait for certificate validation (if needed)
print_step "Checking certificate validation status..."

CERT_STATUS=$(aws acm describe-certificate \
    --certificate-arn $CERTIFICATE_ARN \
    --region us-east-1 \
    --profile $AWS_PROFILE \
    --query 'Certificate.Status' \
    --output text)

if [ "$CERT_STATUS" = "PENDING_VALIDATION" ]; then
    print_warning "Certificate is pending validation. This may take 5-10 minutes..."
    print_info "You can continue with the next steps while validation completes in the background."
elif [ "$CERT_STATUS" = "ISSUED" ]; then
    print_info "✅ Certificate is already validated and issued"
else
    print_warning "Certificate status: $CERT_STATUS"
fi

# Step 6: Create CloudFront distribution update script
print_step "Creating CloudFront update configuration..."

cat > /tmp/cloudfront-update-config.json << EOF
{
    "Id": "$CLOUDFRONT_DIST_ID",
    "IfMatch": "CURRENT_ETAG"
}
EOF

# Step 7: Create DNS records for the domain
print_step "Creating DNS records for $DOMAIN_NAME..."

# Create A record for the domain pointing to CloudFront
print_info "Creating A record for frontend (CloudFront)..."

# Get CloudFront distribution domain name
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
    --id $CLOUDFRONT_DIST_ID \
    --profile $AWS_PROFILE \
    --query 'Distribution.DomainName' \
    --output text)

# Check if A record already exists
EXISTING_A_RECORD=$(aws route53 list-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --profile $AWS_PROFILE \
    --query "ResourceRecordSets[?Name=='$DOMAIN_NAME.' && Type=='A'].Name" \
    --output text 2>/dev/null || echo "")

if [ -z "$EXISTING_A_RECORD" ]; then
    aws route53 change-resource-record-sets \
        --hosted-zone-id $HOSTED_ZONE_ID \
        --profile $AWS_PROFILE \
        --change-batch "{
            \"Changes\": [{
                \"Action\": \"CREATE\",
                \"ResourceRecordSet\": {
                    \"Name\": \"$DOMAIN_NAME\",
                    \"Type\": \"A\",
                    \"AliasTarget\": {
                        \"DNSName\": \"$CLOUDFRONT_DOMAIN\",
                        \"EvaluateTargetHealth\": false,
                        \"HostedZoneId\": \"Z2FDTNDATAQYW2\"
                    }
                }
            }]
        }" > /dev/null

    print_info "✅ A record created for $DOMAIN_NAME → CloudFront"
else
    print_info "✅ A record already exists for $DOMAIN_NAME"
fi

# Create CNAME record for API subdomain
API_DOMAIN="api.$DOMAIN_NAME"
print_info "Creating CNAME record for API subdomain..."

EXISTING_API_RECORD=$(aws route53 list-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --profile $AWS_PROFILE \
    --query "ResourceRecordSets[?Name=='$API_DOMAIN.' && Type=='CNAME'].Name" \
    --output text 2>/dev/null || echo "")

if [ -z "$EXISTING_API_RECORD" ]; then
    aws route53 change-resource-record-sets \
        --hosted-zone-id $HOSTED_ZONE_ID \
        --profile $AWS_PROFILE \
        --change-batch "{
            \"Changes\": [{
                \"Action\": \"CREATE\",
                \"ResourceRecordSet\": {
                    \"Name\": \"$API_DOMAIN\",
                    \"Type\": \"CNAME\",
                    \"TTL\": 300,
                    \"ResourceRecords\": [{
                        \"Value\": \"$ALB_DNS\"
                    }]
                }
            }]
        }" > /dev/null

    print_info "✅ CNAME record created for $API_DOMAIN → ALB"
else
    print_info "✅ CNAME record already exists for $API_DOMAIN"
fi

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}🎉 CUSTOM DOMAIN SETUP IN PROGRESS!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo -e "${BLUE}🌐 Domain: $DOMAIN_NAME${NC}"
echo -e "${BLUE}🔒 SSL Certificate: $CERTIFICATE_ARN${NC}"
echo -e "${BLUE}☁️  CloudFront: $CLOUDFRONT_DIST_ID${NC}"
echo -e "${BLUE}⚖️  Load Balancer: $ALB_DNS${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Wait for SSL certificate validation (5-10 minutes)"
echo "2. Update CloudFront distribution with custom domain"
echo "3. Update frontend configuration to use custom domain"
echo "4. Test the custom domain"
echo ""
echo -e "${CYAN}💡 Manual Steps Required:${NC}"
echo ""
echo -e "${YELLOW}🔐 Update CloudFront Distribution:${NC}"
echo "   aws cloudfront get-distribution-config --id $CLOUDFRONT_DIST_ID > /tmp/dist-config.json"
echo "   # Edit the config to add '$DOMAIN_NAME' to alternate domain names"
echo "   # Add certificate ARN: $CERTIFICATE_ARN"
echo "   aws cloudfront update-distribution --id $CLOUDFRONT_DIST_ID --distribution-config file:///tmp/dist-config.json"
echo ""
echo -e "${GREEN}✅ DNS records are configured and certificate validation is in progress!${NC}"
echo ""