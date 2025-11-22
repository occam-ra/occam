#!/bin/bash
# Compose wrapper for OCCAM - works with both Docker and Podman
# Auto-detects and uses the appropriate compose tool

set -e

COMPOSE_TOOL=""

# Detect which compose tool to use
if command -v podman &> /dev/null && command -v podman-compose &> /dev/null; then
    # Podman with podman-compose (older method)
    COMPOSE_TOOL="podman-compose"
    COMPOSE_FILE="docker-compose.yml"
elif command -v podman &> /dev/null; then
    # Podman 3.0+ with built-in compose support
    if podman compose version &> /dev/null; then
        COMPOSE_TOOL="podman compose"
        COMPOSE_FILE="docker-compose.yml"
    else
        echo "Error: Podman found but no compose support detected"
        echo ""
        echo "Options:"
        echo "  1. Install podman-compose: pip3 install podman-compose"
        echo "  2. Upgrade Podman to 3.0+ for built-in compose support"
        echo ""
        exit 1
    fi
elif command -v docker &> /dev/null; then
    # Docker with docker-compose or docker compose
    if docker compose version &> /dev/null; then
        COMPOSE_TOOL="docker compose"
        COMPOSE_FILE="docker-compose.yml"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_TOOL="docker-compose"
        COMPOSE_FILE="docker-compose.yml"
    else
        echo "Error: Docker found but no compose support detected"
        echo "Install docker-compose: sudo apt install docker-compose"
        exit 1
    fi
else
    echo "Error: Neither Podman nor Docker found in PATH"
    exit 1
fi

echo "Using: $COMPOSE_TOOL"
echo "Compose file: $COMPOSE_FILE"
echo ""

# Pass all arguments to the compose tool
$COMPOSE_TOOL -f "$COMPOSE_FILE" "$@"
