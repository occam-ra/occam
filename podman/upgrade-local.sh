#!/bin/bash
# OCCAM Container - Local Upgrade Script
# Upgrades container on the local machine (run this on your cloud box)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="${CONTAINER_NAME:-occam-web}"
IMAGE_TAR="${1:-occam-web.tar}"

echo "========================================"
echo "OCCAM Container - Local Upgrade"
echo "========================================"
echo ""

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo -e "${RED}Error: Neither podman nor docker found.${NC}"
    exit 1
fi

echo "Using container runtime: $CONTAINER_CMD"

# Determine sudo requirement
SUDO=""
if [ "$CONTAINER_CMD" = "podman" ]; then
    if ! podman info 2>/dev/null | grep -q "rootless: true"; then
        if [ "$EUID" -ne 0 ]; then
            SUDO="sudo"
        fi
    fi
else
    if ! docker ps &>/dev/null 2>&1; then
        if [ "$EUID" -ne 0 ]; then
            SUDO="sudo"
        fi
    fi
fi

# Check if tar file exists
if [ ! -f "$IMAGE_TAR" ]; then
    echo -e "${RED}Error: Container image file not found: $IMAGE_TAR${NC}"
    echo ""
    echo "Usage: $0 [path-to-image.tar]"
    echo ""
    echo "Transfer the image file first:"
    echo "  scp occam-web.tar user@cloudbox:/tmp/"
    echo ""
    exit 1
fi

echo "Image file: $IMAGE_TAR"
echo ""

# Step 1: Stop old container
echo -e "${BLUE}[1/4]${NC} Stopping old container..."
if $SUDO $CONTAINER_CMD ps -a | grep -q "$CONTAINER_NAME"; then
    $SUDO $CONTAINER_CMD stop "$CONTAINER_NAME" 2>/dev/null || true
    $SUDO $CONTAINER_CMD rm "$CONTAINER_NAME" 2>/dev/null || true
    echo "Old container stopped and removed"
else
    echo "No existing container found"
fi

# Step 2: Remove old image (optional)
echo ""
echo -e "${BLUE}[2/4]${NC} Removing old image..."
if $SUDO $CONTAINER_CMD images | grep -q "occam-web"; then
    $SUDO $CONTAINER_CMD rmi localhost/occam-web:latest 2>/dev/null || true
    echo "Old image removed"
else
    echo "No existing image found"
fi

# Step 3: Load new image
echo ""
echo -e "${BLUE}[3/4]${NC} Loading new container image..."
$SUDO $CONTAINER_CMD load -i "$IMAGE_TAR"

# Step 4: Start new container
echo ""
echo -e "${BLUE}[4/4]${NC} Starting new container..."
$SUDO $CONTAINER_CMD run -d \
    --name "$CONTAINER_NAME" \
    -p 5000:5000 \
    -v occam-data:/var/www/occam/data \
    -v occam-logs:/var/www/occam/logs \
    --restart unless-stopped \
    localhost/occam-web:latest

sleep 3

# Verify
if $SUDO $CONTAINER_CMD ps | grep -q "$CONTAINER_NAME"; then
    echo ""
    echo -e "${GREEN}✓ Upgrade complete!${NC}"
    echo ""
    echo "Container status:"
    $SUDO $CONTAINER_CMD exec "$CONTAINER_NAME" supervisorctl status || true
    echo ""
    echo "Management commands:"
    echo "  View logs:   $SUDO $CONTAINER_CMD logs -f $CONTAINER_NAME"
    echo "  Restart:     $SUDO $CONTAINER_CMD restart $CONTAINER_NAME"
    echo "  Shell:       $SUDO $CONTAINER_CMD exec -it $CONTAINER_NAME bash"
else
    echo ""
    echo -e "${RED}Error: Container failed to start${NC}"
    echo ""
    echo "Check logs:"
    echo "  $SUDO $CONTAINER_CMD logs $CONTAINER_NAME"
    exit 1
fi
