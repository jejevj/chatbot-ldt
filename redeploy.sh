#!/bin/bash
# Smart redeploy script - only rebuild if necessary

set -e

echo "=========================================="
echo "Starting redeploy process..."
echo "=========================================="

# Pull latest code
echo "Pulling latest code from git..."
git pull origin main

# Check if rebuild is needed
REBUILD_API=false
REBUILD_FRONTEND=false

# Check if requirements.txt changed (API needs rebuild)
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q "api/requirements.txt"; then
    echo "requirements.txt changed - API will be rebuilt"
    REBUILD_API=true
fi

# Check if Dockerfile changed
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q "api/Dockerfile"; then
    echo "API Dockerfile changed - API will be rebuilt"
    REBUILD_API=true
fi

# Check if frontend dependencies changed
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q "frontend/package.json"; then
    echo "package.json changed - Frontend will be rebuilt"
    REBUILD_FRONTEND=true
fi

# Check if frontend Dockerfile changed
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q "frontend/Dockerfile"; then
    echo "Frontend Dockerfile changed - Frontend will be rebuilt"
    REBUILD_FRONTEND=true
fi

# Check if vite config or env changed (affects build output)
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -qE "frontend/vite.config.js|frontend/.env.production"; then
    echo "Frontend config changed - Frontend will be rebuilt"
    REBUILD_FRONTEND=true
fi

# Rebuild only what's needed
if [ "$REBUILD_API" = true ]; then
    echo "Rebuilding API image..."
    docker compose build api
fi

if [ "$REBUILD_FRONTEND" = true ]; then
    echo "Rebuilding Frontend image..."
    docker compose build frontend
fi

if [ "$REBUILD_API" = false ] && [ "$REBUILD_FRONTEND" = false ]; then
    echo "No rebuild needed - restarting containers only..."
fi

# Restart containers
echo "Restarting containers..."
docker compose up -d

# Show status
echo "Checking container status..."
docker compose ps

echo "=========================================="
echo "Redeploy completed!"
echo "=========================================="
