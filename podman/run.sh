#!/bin/bash
podman run -d -p 8080:80 occam_local
echo "You can now connect at http://localhost:8080/"
