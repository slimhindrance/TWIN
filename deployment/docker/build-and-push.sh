#!/bin/bash
# Docker Build and Push Script for ACR
# Builds and pushes Digital Twin images to Azure Container Registry

set -e

# Load ACR credentials
if [ -f "../.env.acr" ]; then
    source ../.env.acr
else
    echo "❌ ACR credentials not found. Run azure/acr-setup.sh first."
    exit 1
fi

echo "🚀 Building and Pushing Digital Twin to ACR"
echo "================================================"
echo "🏗️  Registry: $ACR_LOGIN_SERVER"

# Navigate to project root
cd ../..

# Login to ACR
echo "🔐 Logging into ACR..."
docker login "$ACR_LOGIN_SERVER" --username "$ACR_USERNAME" --password "$ACR_PASSWORD"

# Build and tag the image
IMAGE_NAME="digital-twin"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

echo "🔨 Building Docker image..."
docker build -t "$FULL_IMAGE_NAME" .

# Also tag with commit hash if in git repo
if [ -d ".git" ]; then
    COMMIT_HASH=$(git rev-parse --short HEAD)
    COMMIT_IMAGE_NAME="$ACR_LOGIN_SERVER/$IMAGE_NAME:$COMMIT_HASH"
    docker tag "$FULL_IMAGE_NAME" "$COMMIT_IMAGE_NAME"
    
    echo "📦 Pushing image with commit hash: $COMMIT_HASH"
    docker push "$COMMIT_IMAGE_NAME"
fi

# Push the image
echo "📦 Pushing image to ACR..."
docker push "$FULL_IMAGE_NAME"

echo "✅ Build and Push Complete!"
echo "================================================"
echo "🎯 Image Available:"
echo "   Latest: $FULL_IMAGE_NAME"
if [ ! -z "$COMMIT_HASH" ]; then
    echo "   Commit: $COMMIT_IMAGE_NAME"
fi
echo "================================================"
echo "🚀 Next: Deploy to ECS using the ECS task definition"

# Save image info for ECS deployment
cat > ../deployment/.env.images << EOF
DIGITAL_TWIN_IMAGE=$FULL_IMAGE_NAME
ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER
ACR_USERNAME=$ACR_USERNAME
ACR_PASSWORD=$ACR_PASSWORD
EOF

echo "✅ Image info saved to deployment/.env.images"
