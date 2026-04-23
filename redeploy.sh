#!/bin/bash
# Auto redeploy script for chatbot

set -e

echo "=========================================="
echo "Starting redeploy process..."
echo "=========================================="

# Pull latest code
echo "Pulling latest code from git..."
git pull origin main

# Rebuild and restart containers
echo "Rebuilding Docker images..."
docker compose build

echo "Restarting containers..."
docker compose up -d

# Show status
echo "Checking container status..."
docker compose ps

echo "=========================================="
echo "Redeploy completed successfully!"
echo "=========================================="

# Show logs
echo "Showing recent logs..."
docker compose logs --tail=50
