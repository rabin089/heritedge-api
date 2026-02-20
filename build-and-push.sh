#!/bin/bash

# Build and Push Docker Image to Docker Hub
# Run this locally to build and push your image

set -e

# Configuration
IMAGE_NAME="heritedge-backend"
DOCKER_HUB_USERNAME="rabin089"  # CHANGE THIS
TAG="latest"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker Hub username
if [ "$DOCKER_HUB_USERNAME" = "your-dockerhub-username" ]; then
    print_error "Please update DOCKER_HUB_USERNAME in this script"
    exit 1
fi

# Check if logged in to Docker Hub
print_status "Checking Docker Hub login..."
if ! docker info | grep -q "Username"; then
    print_warning "You're not logged in to Docker Hub"
    print_status "Please run: docker login"
    exit 1
fi

# Build the image
print_status "Building Docker image: ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG}"
docker build -t ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG} .

if [ $? -ne 0 ]; then
    print_error "Docker build failed"
    exit 1
fi

# Push to Docker Hub
print_status "Pushing image to Docker Hub..."
docker push ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG}

if [ $? -ne 0 ]; then
    print_error "Docker push failed"
    exit 1
fi

print_status "✅ Image successfully pushed to Docker Hub!"
echo ""
echo "🐳 Image: ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG}"
echo ""
echo "🚀 On your server, run:"
echo "   docker pull ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG}"
echo "   docker run -d --name heritedge-backend -p 8000:8000 ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG}"
