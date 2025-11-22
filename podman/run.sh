#!/bin/bash
# Run script for OCCAM Web Server container
# Supports both Docker and Podman

set -e

CONTAINER_TOOL="${CONTAINER_TOOL:-podman}"
IMAGE_NAME="occam-web"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="occam-web"
PORT="${PORT:-5000}"

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

# Stop and remove existing container if it exists
if $CONTAINER_TOOL ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo "Stopping and removing existing container: $CONTAINER_NAME"
    $CONTAINER_TOOL stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    $CONTAINER_TOOL rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

echo "Starting OCCAM Web Server container..."
echo "Using container tool: $CONTAINER_TOOL"
echo "Image: $IMAGE_NAME:$IMAGE_TAG"
echo "Port: $PORT"

# Run container
$CONTAINER_TOOL run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:5000" \
    -e SMTP_HOST="${SMTP_HOST:-localhost}" \
    -e SMTP_PORT="${SMTP_PORT:-25}" \
    -e SMTP_FROM="${SMTP_FROM:-noreply@occam.local}" \
    -e LOG_LEVEL="${LOG_LEVEL:-info}" \
    "$IMAGE_NAME:$IMAGE_TAG"

echo ""
echo "Container started successfully!"
echo ""
echo "Access OCCAM at: http://localhost:$PORT"
echo ""
echo "Useful commands:"
echo "  View logs:        $CONTAINER_TOOL logs -f $CONTAINER_NAME"
echo "  Stop container:   $CONTAINER_TOOL stop $CONTAINER_NAME"
echo "  Start container:  $CONTAINER_TOOL start $CONTAINER_NAME"
echo "  Remove container: $CONTAINER_TOOL rm -f $CONTAINER_NAME"
echo "  Shell access:     $CONTAINER_TOOL exec -it $CONTAINER_NAME bash"
echo ""
