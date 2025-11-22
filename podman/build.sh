#!/bin/bash
# Build script for OCCAM Web Server container
# Supports both Docker and Podman

set -e

CONTAINER_TOOL="${CONTAINER_TOOL:-podman}"
IMAGE_NAME="occam-web"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Detect container runtime if not specified
if ! command -v "$CONTAINER_TOOL" &> /dev/null; then
    if command -v podman &> /dev/null; then
        CONTAINER_TOOL="podman"
    elif command -v docker &> /dev/null; then
        CONTAINER_TOOL="docker"
    else
        echo "Error: Neither podman nor docker found in PATH"
        exit 1
    fi
fi

echo "Using container tool: $CONTAINER_TOOL"
echo "Building image: $IMAGE_NAME:$IMAGE_TAG"

# Build from parent directory
cd "$(dirname "$0")/.."

$CONTAINER_TOOL build \
    -t "$IMAGE_NAME:$IMAGE_TAG" \
    -f podman/Dockerfile \
    . \
    "$@"

echo ""
echo "Build complete!"
echo "Image: $IMAGE_NAME:$IMAGE_TAG"
echo ""
echo "To run the container:"
echo "  $CONTAINER_TOOL run -d -p 5000:5000 --name occam-web $IMAGE_NAME:$IMAGE_TAG"
echo ""
echo "Or use docker-compose:"
echo "  cd podman && docker-compose up -d"
echo ""
