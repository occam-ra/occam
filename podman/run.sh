#!/bin/bash
# OCCAM Container - Run Script
# Simple script to run the container for development/testing

set -e

# Configuration
CONTAINER_NAME="${CONTAINER_NAME:-occam-web}"
HTTP_PORT="${HTTP_PORT:-5000}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "OCCAM Container - Run"
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
    if podman info 2>/dev/null | grep -q "rootless: true"; then
        echo "Using rootless podman"
    else
        if [ "$EUID" -ne 0 ]; then
            SUDO="sudo"
            echo "Using rootful podman (requires sudo)"
        fi
    fi
else
    # Docker usually requires sudo unless user is in docker group
    if ! docker ps &>/dev/null 2>&1; then
        if [ "$EUID" -ne 0 ]; then
            SUDO="sudo"
            echo "Docker requires sudo (or add your user to docker group)"
        fi
    fi
fi

# Check if image exists
if ! $SUDO $CONTAINER_CMD images | grep -q "occam-web"; then
    echo -e "${RED}Error: Container image 'occam-web:latest' not found.${NC}"
    echo ""
    echo "Build the image first:"
    echo "  ./build.sh"
    exit 1
fi

# Stop and remove existing container if running
if $SUDO $CONTAINER_CMD ps -a | grep -q "$CONTAINER_NAME"; then
    echo "Removing existing container..."
    $SUDO $CONTAINER_CMD stop "$CONTAINER_NAME" 2>/dev/null || true
    $SUDO $CONTAINER_CMD rm "$CONTAINER_NAME" 2>/dev/null || true
fi

echo ""
echo "Starting container..."
$SUDO $CONTAINER_CMD run -d \
    --name "$CONTAINER_NAME" \
    -p "$HTTP_PORT:5000" \
    occam-web:latest

# Wait for startup
sleep 2

# Check if running
if $SUDO $CONTAINER_CMD ps | grep -q "$CONTAINER_NAME"; then
    echo ""
    echo -e "${GREEN}✓ Container started successfully!${NC}"
    echo ""
    echo "Access OCCAM at: http://localhost:$HTTP_PORT"
    echo ""
    echo "Management commands:"
    echo "  View logs:   $SUDO $CONTAINER_CMD logs -f $CONTAINER_NAME"
    echo "  Stop:        $SUDO $CONTAINER_CMD stop $CONTAINER_NAME"
    echo "  Restart:     $SUDO $CONTAINER_CMD restart $CONTAINER_NAME"
    echo "  Shell:       $SUDO $CONTAINER_CMD exec -it $CONTAINER_NAME bash"
    echo "  Status:      $SUDO $CONTAINER_CMD exec $CONTAINER_NAME supervisorctl status"
    echo ""
else
    echo -e "${RED}Error: Container failed to start${NC}"
    echo "Check logs: $SUDO $CONTAINER_CMD logs $CONTAINER_NAME"
    exit 1
fi
