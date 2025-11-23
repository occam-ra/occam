# OCCAM Web Server - Container Quick Start

## Quick Build and Run

### Option 1: Using Build/Run Scripts (Simplest)

```bash
# From the podman/ directory
cd podman

# Build the container
./build.sh

# Run the container
./run.sh

# Visit http://localhost:5000
```


### Option 2: Using Compose (Recommended for Production)

```bash
# From the podman/ directory
cd podman

# Auto-detects docker/podman and uses appropriate compose tool
./compose.sh up -d

# View logs
./compose.sh logs -f

# Stop
./compose.sh down

# Visit http://localhost:5000
```


### Option 3: Manual Commands

**With Podman (from podman/ directory):**
```bash
cd podman
BUILDAH_ISOLATION=chroot sudo -E podman build -t occam-web:latest -f Dockerfile ..
sudo podman run -d -p 5000:5000 --name occam-web occam-web:latest
```

**With Docker (from podman/ directory):**
```bash
cd podman
docker build -t occam-web:latest -f Dockerfile ..
docker run -d -p 5000:5000 --name occam-web occam-web:latest
```

**Note:** Use `./build.sh` instead of manual commands - it handles permission issues automatically.


## Container Management

# View logs
podman logs -f occam-web          # or: docker logs -f occam-web

# Stop container
podman stop occam-web             # or: docker stop occam-web

# Start container
podman start occam-web            # or: docker start occam-web

# Remove container
podman rm -f occam-web            # or: docker rm -f occam-web

# Shell access
podman exec -it occam-web bash   # or: docker exec -it occam-web bash

# Check service status (inside container)
podman exec occam-web supervisorctl status


## Configuration

### Using environment variables:

SMTP_HOST=smtp.gmail.com \
SMTP_PORT=587 \
SMTP_USER=user@gmail.com \
SMTP_PASSWORD=password \
./run.sh

### Using .env file (for compose):

cp .env.example .env
# Edit .env with your settings
./compose.sh up -d


## Docker vs Podman - Which Should I Use?

Both work! The scripts auto-detect which you have installed.

**Podman (Recommended for Linux):**
- Daemonless (more secure)
- Rootless by default
- Drop-in replacement for Docker
- Use: podman, podman compose (3.0+), or podman-compose

**Docker:**
- Most widely used
- Better Windows/Mac support
- Use: docker, docker compose, or docker-compose

**Our scripts support all of these automatically!**


## Compose Tool Differences

| Tool | Command | Notes |
|------|---------|-------|
| podman compose | `podman compose up -d` | Built-in Podman 3.0+ (recommended) |
| podman-compose | `podman-compose up -d` | Separate tool, older method |
| docker compose | `docker compose up -d` | Built-in Docker (recommended) |
| docker-compose | `docker-compose up -d` | Legacy standalone tool |

**Just use `./compose.sh` and it handles all of this for you!**


## For Complete Documentation

- **CONTAINER_README.md** - Full container reference and configuration
- **CONTAINER_DEPLOYMENT.md** - Production deployment with Apache/Nginx reverse proxy
- **podman/DEPLOYMENT_SCRIPTS.md** - Automated deployment scripts documentation

All documentation is in the `docs/` directory.
