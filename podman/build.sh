#!/bin/bash
# OCCAM Container - Build Script
# Handles permission issues and builds the container image

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "OCCAM Container - Build"
echo "========================================"
echo ""

# Change to podman directory
cd "$(dirname "$0")"

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo -e "${RED}Error: Neither podman nor docker found.${NC}"
    echo "Please install podman or docker first:"
    echo "  sudo apt install podman"
    exit 1
fi

echo "Using container runtime: $CONTAINER_CMD"
echo ""

# For podman, we need special handling due to permission issues
if [ "$CONTAINER_CMD" = "podman" ]; then
    # Check if we can use rootless build
    if podman info 2>/dev/null | grep -q "rootless: true"; then
        echo -e "${YELLOW}Using rootless podman with chroot isolation...${NC}"
        # Rootless build requires chroot isolation to avoid permission issues
        BUILDAH_ISOLATION=chroot podman build -t occam-web:latest -f Dockerfile ..
    else
        echo "Using rootful podman..."
        # Running as root or with sudo
        if [ "$EUID" -eq 0 ]; then
            BUILDAH_ISOLATION=chroot podman build -t occam-web:latest -f Dockerfile ..
        else
            echo "Rootful podman requires sudo..."
            BUILDAH_ISOLATION=chroot sudo -E podman build -t occam-web:latest -f Dockerfile ..
        fi
    fi
else
    # Docker doesn't have this issue
    echo "Building with docker..."
    if [ "$EUID" -eq 0 ]; then
        docker build -t occam-web:latest -f Dockerfile ..
    else
        sudo docker build -t occam-web:latest -f Dockerfile ..
    fi
fi

echo ""
echo -e "${GREEN}✓ Build complete!${NC}"
echo ""
echo "Container Details:"
$CONTAINER_CMD images | grep occam-web | head -1
echo ""
echo "Next steps:"
echo "  Run container:  ./run.sh"
echo "  Or use compose: ./compose.sh up -d"
echo ""
