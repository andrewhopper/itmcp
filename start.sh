#!/bin/bash

set -e

# Create necessary directories
mkdir -p config logs secrets/keys

# Make sure secrets directory has proper permissions
chmod 700 secrets
chmod 700 secrets/keys

# Create credentials file if it doesn't exist
if [ ! -f "secrets/ssh_credentials.json" ]; then
  echo "Creating empty SSH credentials file"
  echo '{}' > secrets/ssh_credentials.json
  chmod 600 secrets/ssh_credentials.json
fi

echo "Checking if Docker is running..."
if ! docker info > /dev/null 2>&1; then
  echo "Docker is not running. Please start Docker first."
  exit 1
fi

echo "Building and starting the itmcp container..."
docker-compose up -d --build

echo "Waiting for container to start..."
sleep 3

# Check if container is running
if ! docker ps | grep -q itmcp_container; then
  echo "Container failed to start. Check logs with 'docker-compose logs'."
  exit 1
fi

echo "Container is running. Starting MCP server with Docker execution enabled..."

# Set environment variables
export USE_DOCKER=true
export DOCKER_CONTAINER=itmcp_container

# Start the MCP server locally (connecting to the Docker container)
echo "Starting MCP server..."
python3 src/itmcp/executor.py

echo "MCP server stopped." 