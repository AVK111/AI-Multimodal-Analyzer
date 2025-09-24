#!/bin/bash

set -e

# Variables (update these)
REGION="ap-south-1"                 # Your AWS region
REPOSITORY="my-app-repo"            # Your ECR repo name
IMAGE_TAG="latest"                  # Image tag
CONTAINER_NAME="my-app"             # Container name
APP_PORT="5000"                     # Port your app runs inside the container

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "🚀 Deploying container from ECR: $ECR_REGISTRY/$REPOSITORY:$IMAGE_TAG"

# Ensure Docker is installed
if ! command -v docker &> /dev/null
then
  echo "🐳 Installing Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
fi

# Login to ECR
echo "🔑 Logging in to Amazon ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Pull latest image
echo "⬇️ Pulling latest image..."
docker pull $ECR_REGISTRY/$REPOSITORY:$IMAGE_TAG

# Stop old container if running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "🛑 Stopping old container..."
    docker stop $CONTAINER_NAME
fi

# Remove old container if exists
if [ "$(docker ps -aq -f status=exited -f name=$CONTAINER_NAME)" ]; then
    echo "🧹 Removing old container..."
    docker rm $CONTAINER_NAME
fi

# Run new container
echo "▶️ Starting new container..."
docker run -d --name $CONTAINER_NAME -p $APP_PORT:$APP_PORT $ECR_REGISTRY/$REPOSITORY:$IMAGE_TAG

# Restart Nginx
echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx

echo "✅ Deployment successful! Container is running on port $APP_PORT"
