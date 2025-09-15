#!/bin/bash
# Azure Container Registry Setup Script
# Run this to create and configure ACR for your Digital Twin

set -e

# Configuration
RESOURCE_GROUP="digital-twin-rg"
ACR_NAME="digitaltwinacr$(date +%s)"  # Unique name with timestamp
LOCATION="eastus"
SUBSCRIPTION_ID=""  # Add your Azure subscription ID

echo "🚀 Setting up Azure Container Registry for Digital Twin"
echo "================================================"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure
echo "🔐 Logging into Azure..."
az login

# Set subscription if provided
if [ ! -z "$SUBSCRIPTION_ID" ]; then
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Create resource group
echo "📦 Creating resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

# Create ACR
echo "🏗️  Creating Azure Container Registry..."
az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --location "$LOCATION" \
    --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer --output tsv)

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value --output tsv)

echo "✅ ACR Setup Complete!"
echo "================================================"
echo "📝 Save these credentials for ECS deployment:"
echo "ACR_LOGIN_SERVER: $ACR_LOGIN_SERVER"
echo "ACR_USERNAME: $ACR_USERNAME"
echo "ACR_PASSWORD: $ACR_PASSWORD"
echo "================================================"

# Create environment file
cat > ../deployment/.env.acr << EOF
ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER
ACR_USERNAME=$ACR_USERNAME
ACR_PASSWORD=$ACR_PASSWORD
ACR_NAME=$ACR_NAME
RESOURCE_GROUP=$RESOURCE_GROUP
EOF

echo "✅ ACR credentials saved to deployment/.env.acr"
echo "🚀 Next: Run docker-build-push.sh to build and push your images"
