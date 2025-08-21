#!/bin/bash
# Deployment script for Docker Dashboard to remote server

# Configuration
REMOTE_USER="logan"
REMOTE_HOST="logan-GL502VS"
REMOTE_PORT="22"
APP_NAME="docker-dashboard"
IMAGE_NAME="dashboard"
TARGET_PORT="100"

echo "Docker Dashboard - Deployment to Remote Server"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

print_status "Docker found, proceeding with deployment..."

# Build the Docker image
print_status "Building Docker image..."
if docker build -t $IMAGE_NAME:latest .; then
    print_status "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Save image to tar file for transfer
print_status "Saving Docker image to tar file..."
if docker save $IMAGE_NAME:latest -o dashboard.tar; then
    print_status "Docker image saved to dashboard.tar"
else
    print_error "Failed to save Docker image"
    exit 1
fi

# Transfer files to remote server
print_status "Transferring files to remote server..."
scp dashboard.tar docker-compose.yml $REMOTE_USER@$REMOTE_HOST:~/
if [ $? -eq 0 ]; then
    print_status "Files transferred successfully"
else
    print_error "Failed to transfer files"
    exit 1
fi

# SSH to remote server and deploy
print_status "Connecting to remote server and deploying..."
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
    echo "Loading Docker image on remote server..."
    docker load -i dashboard.tar
    
    echo "Stopping existing containers..."
    docker-compose down 2>/dev/null || true
    
    echo "Starting new containers..."
    docker-compose up -d
    
    echo "Cleaning up..."
    rm dashboard.tar
    
    echo "Deployment completed!"
    echo "Dashboard should be accessible at http://$(hostname -I | cut -d' ' -f1):100"
    
    # Show running containers
    echo "Running containers:"
    docker ps --filter "name=dashboard"
ENDSSH

if [ $? -eq 0 ]; then
    print_status "Deployment completed successfully!"
    print_status "Dashboard should be accessible at http://$REMOTE_HOST:$TARGET_PORT"
else
    print_error "Deployment failed"
    exit 1
fi

# Clean up local files
rm dashboard.tar

print_status "Deployment process completed!"
