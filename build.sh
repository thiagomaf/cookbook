#!/bin/bash
# build.sh — Pull latest source and rebuild Docker images on the NAS.
# Run via SSH from /share/Container/cookbook/ whenever you want to update the app.
#
# One-time setup (run once after creating the folder and placing backend/.env):
#   cd /share/Container/cookbook
#   git init
#   git remote add origin https://github.com/USER/REPO.git
#   git pull origin main
#
# Subsequent updates: just run this script.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Pulling latest source..."
git -C "$SCRIPT_DIR" pull

echo "==> Building cookbook-backend:latest..."
docker build -t cookbook-backend:latest "$SCRIPT_DIR/backend"

echo "==> Building cookbook-frontend:latest..."
docker build -t cookbook-frontend:latest "$SCRIPT_DIR/frontend"

echo ""
echo "Done. Restart the stack in Container Station to apply the update."
