#!/bin/bash
# OCCAM Container - Remote Upgrade Script
# Upgrades container on remote server by transferring and loading new image

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REMOTE_HOST="${1}"
REMOTE_USER="${2:-$(whoami)}"
CONTAINER_NAME="${CONTAINER_NAME:-occam-web}"
IMAGE_NAME="${IMAGE_NAME:-localhost/occam-web:latest}"
TEMP_TAR="/tmp/occam-web-$(date +%Y%m%d-%H%M%S).tar"

if [ -z "$REMOTE_HOST" ]; then
    echo -e "${RED}Error: Remote host not specified${NC}"
    echo ""
    echo "Usage: $0 <remote-host> [remote-user]"
    echo ""
    echo "Examples:"
    echo "  $0 myserver.com"
    echo "  $0 192.168.1.100 ubuntu"
    echo "  $0 myserver.com root"
    echo ""
    exit 1
fi

echo "========================================"
echo "OCCAM Container - Remote Upgrade"
echo "========================================"
echo ""
echo "Remote host: $REMOTE_USER@$REMOTE_HOST"
echo "Container: $CONTAINER_NAME"
echo ""

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo -e "${RED}Error: Neither podman nor docker found locally.${NC}"
    exit 1
fi

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

# Check if local image exists
if ! $SUDO $CONTAINER_CMD images | grep -q "occam-web"; then
    echo -e "${RED}Error: Local container image 'occam-web:latest' not found.${NC}"
    echo ""
    echo "Build the image first:"
    echo "  ./build.sh"
    exit 1
fi

# Step 1: Save container image locally
echo -e "${BLUE}[1/5]${NC} Saving container image..."
$SUDO $CONTAINER_CMD save -o "$TEMP_TAR" "$IMAGE_NAME"
IMAGE_SIZE=$(du -h "$TEMP_TAR" | cut -f1)
echo "Saved to: $TEMP_TAR ($IMAGE_SIZE)"

# Step 2: Transfer to remote server
echo ""
echo -e "${BLUE}[2/5]${NC} Transferring image to remote server..."
scp "$TEMP_TAR" "$REMOTE_USER@$REMOTE_HOST:/tmp/" || {
    echo -e "${RED}Error: Failed to transfer image${NC}"
    rm -f "$TEMP_TAR"
    exit 1
}

# Step 3: Stop and backup old container on remote
echo ""
echo -e "${BLUE}[3/5]${NC} Stopping old container on remote..."
ssh "$REMOTE_USER@$REMOTE_HOST" bash -s << 'REMOTE_SCRIPT'
set -e

# Detect container runtime on remote
if command -v podman &> /dev/null; then
    RCMD="podman"
elif command -v docker &> /dev/null; then
    RCMD="docker"
else
    echo "Error: No container runtime found on remote server"
    exit 1
fi

# Determine sudo on remote
RSUDO=""
if [ "$RCMD" = "podman" ]; then
    if ! podman info 2>/dev/null | grep -q "rootless: true"; then
        if [ "$EUID" -ne 0 ]; then
            RSUDO="sudo"
        fi
    fi
else
    if ! docker ps &>/dev/null 2>&1; then
        if [ "$EUID" -ne 0 ]; then
            RSUDO="sudo"
        fi
    fi
fi

# Check if container exists
if $RSUDO $RCMD ps -a | grep -q "occam-web"; then
    echo "Stopping occam-web container..."
    $RSUDO $RCMD stop occam-web 2>/dev/null || true
    
    echo "Removing old container..."
    $RSUDO $RCMD rm occam-web 2>/dev/null || true
fi

# Remove old image (optional - saves space)
if $RSUDO $RCMD images | grep -q "occam-web"; then
    echo "Removing old image..."
    $RSUDO $RCMD rmi localhost/occam-web:latest 2>/dev/null || true
fi

echo "Old container stopped and removed"
REMOTE_SCRIPT

# Step 4: Load new image on remote
echo ""
echo -e "${BLUE}[4/5]${NC} Loading new image on remote..."
REMOTE_TAR_NAME=$(basename "$TEMP_TAR")
ssh "$REMOTE_USER@$REMOTE_HOST" bash -s << REMOTE_LOAD
set -e

# Detect container runtime
if command -v podman &> /dev/null; then
    RCMD="podman"
else
    RCMD="docker"
fi

# Determine sudo
RSUDO=""
if [ "\$RCMD" = "podman" ]; then
    if ! podman info 2>/dev/null | grep -q "rootless: true"; then
        if [ "\$EUID" -ne 0 ]; then
            RSUDO="sudo"
        fi
    fi
else
    if ! docker ps &>/dev/null 2>&1; then
        if [ "\$EUID" -ne 0 ]; then
            RSUDO="sudo"
        fi
    fi
fi

echo "Loading new container image..."
\$RSUDO \$RCMD load -i "/tmp/$REMOTE_TAR_NAME"

echo "Cleaning up tar file..."
rm -f "/tmp/$REMOTE_TAR_NAME"
REMOTE_LOAD

# Step 5: Start new container
echo ""
echo -e "${BLUE}[5/5]${NC} Starting new container on remote..."
ssh "$REMOTE_USER@$REMOTE_HOST" bash -s << 'REMOTE_START'
set -e

# Detect container runtime
if command -v podman &> /dev/null; then
    RCMD="podman"
else
    RCMD="docker"
fi

# Determine sudo
RSUDO=""
if [ "$RCMD" = "podman" ]; then
    if ! podman info 2>/dev/null | grep -q "rootless: true"; then
        if [ "$EUID" -ne 0 ]; then
            RSUDO="sudo"
        fi
    fi
else
    if ! docker ps &>/dev/null 2>&1; then
        if [ "$EUID" -ne 0 ]; then
            RSUDO="sudo"
        fi
    fi
fi

echo "Starting occam-web container..."
$RSUDO $RCMD run -d \
    --name occam-web \
    -p 5000:5000 \
    -v occam-data:/var/www/occam/data \
    -v occam-logs:/var/www/occam/logs \
    --restart unless-stopped \
    localhost/occam-web:latest

sleep 3

# Check if running
if $RSUDO $RCMD ps | grep -q occam-web; then
    echo ""
    echo "Container started successfully!"
    $RSUDO $RCMD exec occam-web supervisorctl status || true
else
    echo ""
    echo "Error: Container failed to start"
    $RSUDO $RCMD logs occam-web
    exit 1
fi
REMOTE_START

# Clean up local tar file
rm -f "$TEMP_TAR"

echo ""
echo -e "${GREEN}✓ Upgrade complete!${NC}"
echo ""
echo "The container on $REMOTE_HOST has been upgraded to the latest version."
echo ""
echo "Verify the upgrade:"
echo "  ssh $REMOTE_USER@$REMOTE_HOST '$CONTAINER_CMD exec occam-web supervisorctl status'"
echo ""
echo "View logs:"
echo "  ssh $REMOTE_USER@$REMOTE_HOST '$CONTAINER_CMD logs -f occam-web'"
echo ""
