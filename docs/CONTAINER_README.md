# OCCAM Web Server - Container Deployment

This directory contains container configuration for running the OCCAM web server with Docker or Podman.

## Docker vs Podman - Which Should I Use?

**TL;DR: Use whichever you have installed - our scripts auto-detect and work with both!**

### Podman (Recommended for Linux servers)
- **Daemonless:** More secure, no background daemon required
- **Rootless:** Runs without root privileges by default
- **Compatible:** Drop-in replacement for Docker commands
- **Tools:** `podman`, `podman compose` (3.0+), or `podman-compose`

### Docker (Recommended for Windows/Mac, widely supported)
- **Most popular:** Largest community and ecosystem
- **Better desktop support:** Docker Desktop for Windows/Mac
- **Mature:** Well-established in production environments
- **Tools:** `docker`, `docker compose`, or `docker-compose` (legacy)

### Our Scripts Support Both!

All scripts in this directory auto-detect which container runtime you have:
- `./build.sh` - Builds with docker or podman
- `./run.sh` - Runs with docker or podman
- `./compose.sh` - Uses docker compose, docker-compose, podman compose, or podman-compose

**You don't need to choose - just use the scripts!**

## Quick Start

### Option 1: Using Scripts (Simplest)

**Build:**
```bash
cd podman
./build.sh
```

**Run:**
```bash
./run.sh
```

Access at: http://localhost:5000

### Option 2: Using Compose (Recommended for Production)

**Start:**
```bash
cd podman
./compose.sh up -d
```

**View logs:**
```bash
./compose.sh logs -f
```

**Stop:**
```bash
./compose.sh down
```

Access at: http://localhost:5000

### Option 3: Manual Commands (Advanced)

**Using Podman or Docker

**Podman:**
```bash
cd podman
podman build -t occam-web:latest -f Dockerfile ..
podman run -d -p 5000:5000 --name occam-web occam-web:latest
```

**Docker:**
```bash
cd podman
docker build -t occam-web:latest -f Dockerfile ..
docker run -d -p 5000:5000 --name occam-web occam-web:latest
```

Access at: http://localhost:5000

## What's Included

The container includes:
- **OCCAM C++ library and CLI** (`occ` command)
- **PyOCCAM Python bindings**
- **Flask web server** with Gunicorn WSGI server
- **Redis** for job queue management
- **RQ Worker** for background batch job processing
- **Supervisor** for process management

All services run inside a single container and are managed by supervisord.

## Container Architecture

```
Container: occam-web
├── Gunicorn (Flask app)      :5000
├── Redis                      :6379 (internal)
├── RQ Worker                  (background)
└── Supervisor                 (process manager)
```

## Configuration

### Environment Variables

Configure the container with environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | redis://127.0.0.1:6379/0 | Redis connection string |
| `SMTP_HOST` | localhost | SMTP server for email notifications |
| `SMTP_PORT` | 25 | SMTP port |
| `SMTP_USER` | (empty) | SMTP username |
| `SMTP_PASSWORD` | (empty) | SMTP password |
| `SMTP_FROM` | noreply@occam.local | From address for emails |
| `GUNICORN_WORKERS` | auto | Number of Gunicorn workers |
| `GUNICORN_RELOAD` | false | Auto-reload on code changes |
| `LOG_LEVEL` | info | Logging level |

### Example with Environment Variables

**Using run.sh:**
```bash
SMTP_HOST=smtp.gmail.com \
SMTP_PORT=587 \
SMTP_USER=user@gmail.com \
SMTP_PASSWORD=app-password \
PORT=8080 \
./run.sh
```

**Using docker-compose:**

Create `.env` file in the `podman/` directory:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=user@gmail.com
SMTP_PASSWORD=app-password
SMTP_FROM=noreply@example.com
GUNICORN_WORKERS=4
LOG_LEVEL=info
```

Then run:
```bash
docker-compose up -d
```

## Usage

### Build and Run

**Podman:**
```bash
# Build
cd podman
./build.sh

# Run
./run.sh

# Or manually:
podman run -d -p 5000:5000 --name occam-web occam-web:latest
```

**Docker:**
```bash
# Build
CONTAINER_TOOL=docker ./build.sh

# Run
CONTAINER_TOOL=docker ./run.sh

# Or manually:
docker run -d -p 5000:5000 --name occam-web occam-web:latest
```

**Using Compose (works with both Docker and Podman):**
```bash
# Use our wrapper script (auto-detects compose tool)
./compose.sh up -d          # Start
./compose.sh logs -f        # View logs
./compose.sh down           # Stop and remove
./compose.sh restart        # Restart

# Or use compose directly:
# - docker compose up -d    (Docker with built-in compose)
# - docker-compose up -d    (Docker with legacy compose)
# - podman compose up -d    (Podman 3.0+ with built-in compose)
# - podman-compose up -d    (Podman with podman-compose tool)
```

### Access the Application

Once running:
- **Main page:** http://localhost:5000
- **Interactive analysis:** http://localhost:5000/occam
- **Batch jobs:** http://localhost:5000/batch

### Container Management

**View logs:**
```bash
# All logs
podman logs -f occam-web

# Specific service logs (from inside container)
podman exec occam-web tail -f /var/www/occam/logs/gunicorn-stdout.log
podman exec occam-web tail -f /var/www/occam/logs/worker-stdout.log
```

**Shell access:**
```bash
podman exec -it occam-web bash
```

**Stop container:**
```bash
podman stop occam-web
```

**Start container:**
```bash
podman start occam-web
```

**Remove container:**
```bash
podman rm -f occam-web
```

**Inspect container:**
```bash
podman inspect occam-web
```

## Persistent Data

The container stores uploaded data files in `/var/www/occam/data`.

### Using Volumes

**Podman/Docker:**
```bash
podman run -d \
  -p 5000:5000 \
  -v occam-data:/var/www/occam/data \
  -v occam-logs:/var/www/occam/logs \
  --name occam-web \
  occam-web:latest
```

**Using Compose:**

Volumes are automatically created and managed when using `./compose.sh` (see `docker-compose.yml`).

List volumes:
```bash
# Docker
docker volume ls | grep occam

# Podman
podman volume ls | grep occam
```

Backup data:
```bash
docker run --rm -v occam-data:/data -v $(pwd):/backup ubuntu tar czf /backup/occam-data-backup.tar.gz -C /data .
```

Restore data:
```bash
docker run --rm -v occam-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/occam-data-backup.tar.gz -C /data
```

## Advanced Configuration

### Custom Gunicorn Workers

Set the number of workers based on your server resources:

```bash
# Run with 2 workers (for limited resources)
podman run -d \
  -p 5000:5000 \
  -e GUNICORN_WORKERS=2 \
  --name occam-web \
  occam-web:latest
```

Formula: `(2 x CPU cores) + 1`

### Development Mode

Enable auto-reload for development:

```bash
podman run -d \
  -p 5000:5000 \
  -e GUNICORN_RELOAD=true \
  -e LOG_LEVEL=debug \
  -v $(pwd)/../flask_app/occam_server:/var/www/occam/occam_server \
  --name occam-web \
  occam-web:latest
```

### Running Behind a Reverse Proxy

If running behind nginx or Apache:

**Nginx example:**
```nginx
server {
    listen 80;
    server_name occam.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Apache2 example:**
```apache
<VirtualHost *:80>
    ServerName occam.example.com

    ProxyPreserveHost On
    ProxyPass / http://localhost:5000/
    ProxyPassReverse / http://localhost:5000/

    RequestHeader set X-Forwarded-Proto "http"
</VirtualHost>
```

**For complete deployment instructions with SSL/HTTPS, see:** `CONTAINER_DEPLOYMENT.md`

## Troubleshooting

### Container won't start

Check logs:
```bash
podman logs occam-web
```

Common issues:
- Port 5000 already in use: Use `-p 8080:5000` to map to different port
- Permission denied: Make sure you have permission to run containers

### Services not responding

Check supervisor status inside container:
```bash
podman exec occam-web supervisorctl status
```

Restart specific service:
```bash
podman exec occam-web supervisorctl restart gunicorn
podman exec occam-web supervisorctl restart rq-worker
```

### Batch jobs not processing

Check RQ worker is running:
```bash
podman exec occam-web supervisorctl status rq-worker
```

Check worker logs:
```bash
podman exec occam-web tail -f /var/www/occam/logs/worker-stdout.log
```

Check Redis is running:
```bash
podman exec occam-web redis-cli ping
```

### Email notifications not sending

Verify SMTP settings:
```bash
podman exec occam-web env | grep SMTP
```

Check worker logs for email errors:
```bash
podman exec occam-web grep -i email /var/www/occam/logs/worker-stdout.log
```

## Multi-Container Setup (Optional)

For production deployments, you can split services into separate containers:

```yaml
# docker-compose-multi.yml (example)
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

  occam-web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  occam-worker:
    build: .
    command: python3 worker.py
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
```

## Security Considerations

For production deployments:

1. **Don't expose Redis port** - Keep it internal to the container
2. **Use secrets for SMTP credentials** - Don't hardcode passwords
3. **Run behind HTTPS** - Use a reverse proxy with SSL
4. **Limit resource usage** - Set memory and CPU limits:
   ```bash
   podman run -d \
     -p 5000:5000 \
     --memory=2g \
     --cpus=2 \
     --name occam-web \
     occam-web:latest
   ```
5. **Keep image updated** - Rebuild regularly for security patches
6. **Use read-only root filesystem** - Add `--read-only` flag (advanced)

## Building for Different Architectures

**AMD64 (x86_64):**
```bash
podman build --platform linux/amd64 -t occam-web:amd64 -f Dockerfile ..
```

**ARM64:**
```bash
podman build --platform linux/arm64 -t occam-web:arm64 -f Dockerfile ..
```

**Multi-architecture:**
```bash
podman buildx build --platform linux/amd64,linux/arm64 -t occam-web:latest -f Dockerfile ..
```

## Deployment to Container Registries

**Docker Hub:**
```bash
docker tag occam-web:latest yourusername/occam-web:latest
docker push yourusername/occam-web:latest
```

**GitHub Container Registry:**
```bash
docker tag occam-web:latest ghcr.io/occam-ra/occam-web:latest
docker push ghcr.io/occam-ra/occam-web:latest
```

## Support

For issues or questions:
- **GitHub Issues:** https://github.com/occam-ra/occam/issues
- **Email:** zwick@pdx.edu
- **Documentation:** See parent directory README.md files
