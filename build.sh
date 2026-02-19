#!/bin/bash
# Build cookbook images locally on the NAS.
# Run this via SSH whenever source code changes.
# Container Station (and docker compose) will pick up the updated images.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Building cookbook-backend:latest"
docker build -t cookbook-backend:latest "$SCRIPT_DIR/backend"

echo "==> Building cookbook-frontend:latest"
docker build -t cookbook-frontend:latest "$SCRIPT_DIR/frontend"

echo ""
echo "Done. Restart the stack to apply:"
echo "  docker compose -f $SCRIPT_DIR/docker-compose.yml up -d"
