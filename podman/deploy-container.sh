#!/bin/bash
# OCCAM Container Deployment Script
# Loads and runs the OCCAM container with persistent volumes

set -e

# Configuration
CONTAINER_NAME="${CONTAINER_NAME:-occam-web}"
IMAGE_NAME="${IMAGE_NAME:-localhost/occam-web:latest}"
HTTP_PORT="${HTTP_PORT:-5000}"
DATA_VOLUME="${DATA_VOLUME:-occam-data}"
LOGS_VOLUME="${LOGS_VOLUME:-occam-logs}"

# SMTP Configuration (optional)
SMTP_HOST="${SMTP_HOST:-localhost}"
SMTP_PORT="${SMTP_PORT:-25}"
SMTP_USER="${SMTP_USER:-}"
SMTP_PASSWORD="${SMTP_PASSWORD:-}"
SMTP_FROM="${SMTP_FROM:-noreply@occam.local}"

# Redis URL
REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "OCCAM Container Deployment"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Warning: Not running as root. Using rootless podman.${NC}"
    SUDO=""
else
    SUDO="sudo"
fi

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo -e "${RED}Error: Neither podman nor docker found. Please install one.${NC}"
    exit 1
fi

echo "Using container runtime: $CONTAINER_CMD"
echo ""

# Check if image exists
if ! $SUDO $CONTAINER_CMD images | grep -q "occam-web"; then
    echo -e "${RED}Error: Container image 'occam-web:latest' not found.${NC}"
    echo ""
    echo "Please load the container image first:"
    echo "  $SUDO $CONTAINER_CMD load -i occam-web.tar"
    echo ""
    echo "Or build it:"
    echo "  cd podman && $SUDO $CONTAINER_CMD build -t occam-web:latest -f Dockerfile .."
    exit 1
fi

# Stop and remove existing container if it exists
if $SUDO $CONTAINER_CMD ps -a | grep -q "$CONTAINER_NAME"; then
    echo "Stopping existing container..."
    $SUDO $CONTAINER_CMD stop "$CONTAINER_NAME" 2>/dev/null || true
    echo "Removing existing container..."
    $SUDO $CONTAINER_CMD rm "$CONTAINER_NAME" 2>/dev/null || true
fi

# Create volumes if they don't exist
echo "Creating persistent volumes..."
$SUDO $CONTAINER_CMD volume create "$DATA_VOLUME" 2>/dev/null || true
$SUDO $CONTAINER_CMD volume create "$LOGS_VOLUME" 2>/dev/null || true

# Build environment variables
ENV_VARS=""
if [ -n "$SMTP_HOST" ]; then
    ENV_VARS="$ENV_VARS -e SMTP_HOST=$SMTP_HOST"
fi
if [ -n "$SMTP_PORT" ]; then
    ENV_VARS="$ENV_VARS -e SMTP_PORT=$SMTP_PORT"
fi
if [ -n "$SMTP_USER" ]; then
    ENV_VARS="$ENV_VARS -e SMTP_USER=$SMTP_USER"
fi
if [ -n "$SMTP_PASSWORD" ]; then
    ENV_VARS="$ENV_VARS -e SMTP_PASSWORD=$SMTP_PASSWORD"
fi
if [ -n "$SMTP_FROM" ]; then
    ENV_VARS="$ENV_VARS -e SMTP_FROM=$SMTP_FROM"
fi
if [ -n "$REDIS_URL" ]; then
    ENV_VARS="$ENV_VARS -e REDIS_URL=$REDIS_URL"
fi

# Run container
echo "Starting OCCAM container..."
$SUDO $CONTAINER_CMD run -d \
    --name "$CONTAINER_NAME" \
    -p "$HTTP_PORT:5000" \
    -v "$DATA_VOLUME:/var/www/occam/data" \
    -v "$LOGS_VOLUME:/var/www/occam/logs" \
    --restart unless-stopped \
    $ENV_VARS \
    "$IMAGE_NAME"

# Wait for container to start
echo "Waiting for container to start..."
sleep 3

# Check if container is running
if ! $SUDO $CONTAINER_CMD ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}Error: Container failed to start!${NC}"
    echo ""
    echo "Check logs with:"
    echo "  $SUDO $CONTAINER_CMD logs $CONTAINER_NAME"
    exit 1
fi

# Check service status
echo ""
echo "Checking services..."
$SUDO $CONTAINER_CMD exec "$CONTAINER_NAME" supervisorctl status || true

echo ""
echo -e "${GREEN}✓ Container deployed successfully!${NC}"
echo ""
echo "Container Details:"
echo "  Name: $CONTAINER_NAME"
echo "  Port: $HTTP_PORT"
echo "  Data Volume: $DATA_VOLUME"
echo "  Logs Volume: $LOGS_VOLUME"
echo ""
echo "Access OCCAM at: http://localhost:$HTTP_PORT"
echo ""
echo "Management Commands:"
echo "  View logs:   $SUDO $CONTAINER_CMD logs -f $CONTAINER_NAME"
echo "  Stop:        $SUDO $CONTAINER_CMD stop $CONTAINER_NAME"
echo "  Start:       $SUDO $CONTAINER_CMD start $CONTAINER_NAME"
echo "  Restart:     $SUDO $CONTAINER_CMD restart $CONTAINER_NAME"
echo "  Shell:       $SUDO $CONTAINER_CMD exec -it $CONTAINER_NAME bash"
echo ""
echo "To enable auto-start on boot:"
echo "  $SUDO $CONTAINER_CMD generate systemd --new --name $CONTAINER_NAME > /etc/systemd/system/$CONTAINER_NAME.service"
echo "  $SUDO systemctl daemon-reload"
echo "  $SUDO systemctl enable $CONTAINER_NAME.service"
echo ""
