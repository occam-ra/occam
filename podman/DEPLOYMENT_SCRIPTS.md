# OCCAM Container - Deployment Scripts

Automated scripts for deploying the OCCAM container on remote servers with Apache2 or Nginx reverse proxy.

## Quick Start

### 1. Transfer Container to Remote Server

**Save the container image:**
```bash
sudo podman save -o occam-web.tar localhost/occam-web:latest
```

**Transfer to remote server:**
```bash
scp occam-web.tar user@remote-server:/tmp/
scp podman/*.sh user@remote-server:/tmp/
```

**On the remote server, load the image:**
```bash
sudo podman load -i /tmp/occam-web.tar
```

### 2. Deploy Container

```bash
cd /tmp
sudo bash deploy-container.sh
```

This will:
- Create persistent volumes for data and logs
- Run the container on port 5000
- Configure auto-restart
- Display management commands

### 3. Setup Reverse Proxy

**Option A: Nginx (Recommended)**
```bash
sudo DOMAIN=occam.yourdomain.com bash setup-nginx-proxy.sh
```

**Option B: Apache2**
```bash
sudo DOMAIN=occam.yourdomain.com bash setup-apache-proxy.sh
```

## Deployment Scripts

### `deploy-container.sh`

Loads and runs the OCCAM container with persistent storage.

**Environment Variables:**
```bash
CONTAINER_NAME=occam-web        # Container name (default: occam-web)
IMAGE_NAME=occam-web:latest     # Image name (default: localhost/occam-web:latest)
HTTP_PORT=5000                  # Container port (default: 5000)
DATA_VOLUME=occam-data          # Data volume name
LOGS_VOLUME=occam-logs          # Logs volume name

# SMTP Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com
```

**Example with email:**
```bash
sudo SMTP_HOST=smtp.gmail.com \
     SMTP_PORT=587 \
     SMTP_USER=occam@yourdomain.com \
     SMTP_PASSWORD=your-app-password \
     bash deploy-container.sh
```

### `setup-nginx-proxy.sh`

Configures Nginx as a reverse proxy with optional SSL.

**Environment Variables:**
```bash
DOMAIN=occam.example.com        # Your domain name (required)
ENABLE_SSL=yes                  # Enable HTTPS (default: no)
USE_CERTBOT=yes                 # Use Let's Encrypt (default: no)
CERTBOT_EMAIL=admin@example.com # Email for Let's Encrypt
CONTAINER_PORT=5000             # Backend port (default: 5000)
```

**Example - HTTP only:**
```bash
sudo DOMAIN=occam.yourdomain.com bash setup-nginx-proxy.sh
```

**Example - HTTPS with Let's Encrypt:**
```bash
sudo DOMAIN=occam.yourdomain.com \
     ENABLE_SSL=yes \
     USE_CERTBOT=yes \
     CERTBOT_EMAIL=admin@yourdomain.com \
     bash setup-nginx-proxy.sh
```

**Example - HTTPS with manual certificates:**
```bash
# First, place your certificates:
sudo cp your-cert.crt /etc/ssl/certs/occam.yourdomain.com.crt
sudo cp your-key.key /etc/ssl/private/occam.yourdomain.com.key

# Then run the script:
sudo DOMAIN=occam.yourdomain.com \
     ENABLE_SSL=yes \
     bash setup-nginx-proxy.sh
```

### `setup-apache-proxy.sh`

Configures Apache2 as a reverse proxy with optional SSL.

**Environment Variables:**
```bash
DOMAIN=occam.example.com        # Your domain name (required)
ENABLE_SSL=yes                  # Enable HTTPS (default: no)
USE_CERTBOT=yes                 # Use Let's Encrypt (default: no)
CERTBOT_EMAIL=admin@example.com # Email for Let's Encrypt
CONTAINER_PORT=5000             # Backend port (default: 5000)
```

**Example - HTTP only:**
```bash
sudo DOMAIN=occam.yourdomain.com bash setup-apache-proxy.sh
```

**Example - HTTPS with Let's Encrypt:**
```bash
sudo DOMAIN=occam.yourdomain.com \
     ENABLE_SSL=yes \
     USE_CERTBOT=yes \
     CERTBOT_EMAIL=admin@yourdomain.com \
     bash setup-apache-proxy.sh
```

## Complete Deployment Example

Full deployment with Nginx and Let's Encrypt SSL:

```bash
# 1. On build machine: Save container
sudo podman save -o occam-web.tar localhost/occam-web:latest

# 2. Transfer to remote server
scp occam-web.tar podman/*.sh user@remote-server:/tmp/

# 3. On remote server: Load container
ssh user@remote-server
cd /tmp
sudo podman load -i occam-web.tar

# 4. Deploy container with email configuration
sudo SMTP_HOST=smtp.gmail.com \
     SMTP_PORT=587 \
     SMTP_USER=occam@yourdomain.com \
     SMTP_PASSWORD=app-password \
     bash deploy-container.sh

# 5. Setup Nginx with SSL
sudo DOMAIN=occam.yourdomain.com \
     ENABLE_SSL=yes \
     USE_CERTBOT=yes \
     CERTBOT_EMAIL=admin@yourdomain.com \
     bash setup-nginx-proxy.sh

# 6. Done! Access at https://occam.yourdomain.com
```

## TLS/HTTPS Termination

The reverse proxy handles TLS termination:
- Client connects via HTTPS to Nginx/Apache
- Nginx/Apache decrypts the connection
- Nginx/Apache proxies to container via HTTP on localhost:5000
- Flask app receives `X-Forwarded-Proto: https` header
- Flask app correctly generates HTTPS URLs and redirects

This is secure because:
- The unencrypted traffic never leaves the server (localhost only)
- The Flask app uses `ProxyFix` middleware to trust proxy headers
- All external traffic is encrypted

## Management Commands

### Container Management

```bash
# View logs
sudo podman logs -f occam-web

# View service status
sudo podman exec occam-web supervisorctl status

# Restart container
sudo podman restart occam-web

# Stop container
sudo podman stop occam-web

# Start container
sudo podman start occam-web

# Shell access
sudo podman exec -it occam-web bash

# View application logs
sudo podman exec occam-web tail -f /var/www/occam/logs/gunicorn-stdout.log
```

### Web Server Management

**Nginx:**
```bash
# Status
sudo systemctl status nginx

# Restart
sudo systemctl restart nginx

# Test configuration
sudo nginx -t

# View logs
sudo tail -f /var/log/nginx/occam-error.log
sudo tail -f /var/log/nginx/occam-access.log
```

**Apache:**
```bash
# Status
sudo systemctl status apache2

# Restart
sudo systemctl restart apache2

# Test configuration
sudo apache2ctl configtest

# View logs
sudo tail -f /var/log/apache2/occam-error.log
sudo tail -f /var/log/apache2/occam-access.log
```

### SSL Certificate Renewal

With Let's Encrypt/Certbot, certificates auto-renew. To manually renew:

```bash
# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal

# List certificates
sudo certbot certificates
```

## Updating the Container

To deploy a new version:

```bash
# 1. Transfer new image to server
scp occam-web.tar user@remote-server:/tmp/

# 2. On remote server: Stop and remove old container
sudo podman stop occam-web
sudo podman rm occam-web

# 3. Remove old image (optional)
sudo podman rmi localhost/occam-web:latest

# 4. Load new image
sudo podman load -i /tmp/occam-web.tar

# 5. Redeploy (data is preserved in volumes)
sudo bash deploy-container.sh

# Web server configuration is unchanged
```

## Backup and Restore

### Backup

```bash
# Backup data volume
sudo podman run --rm \
  -v occam-data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/occam-data-$(date +%Y%m%d).tar.gz -C /data .

# Backup logs volume
sudo podman run --rm \
  -v occam-logs:/logs \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/occam-logs-$(date +%Y%m%d).tar.gz -C /logs .
```

### Restore

```bash
# Restore data
sudo podman run --rm \
  -v occam-data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/occam-data-20241122.tar.gz -C /data

# Restore logs
sudo podman run --rm \
  -v occam-logs:/logs \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/occam-logs-20241122.tar.gz -C /logs
```

## Troubleshooting

### Container won't start

```bash
# Check container logs
sudo podman logs occam-web

# Check if port is in use
sudo lsof -i :5000

# Check systemd service (if enabled)
sudo journalctl -u occam-web.service -f
```

### Web server returns 502 Bad Gateway

1. Check container is running: `sudo podman ps | grep occam-web`
2. Check container responds: `curl http://localhost:5000`
3. Check web server logs: `sudo tail -f /var/log/nginx/occam-error.log`
4. Test proxy: `curl -H "Host: occam.yourdomain.com" http://localhost:5000`

### SSL certificate errors

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Restart web server
sudo systemctl restart nginx  # or apache2
```

### Permissions issues

```bash
# Check volume permissions
sudo podman volume inspect occam-data
sudo podman volume inspect occam-logs

# Fix permissions inside container
sudo podman exec occam-web chown -R occam:occam /var/www/occam/data
sudo podman exec occam-web chown -R occam:occam /var/www/occam/logs
```

## Security Recommendations

1. **Always use HTTPS in production** - Use the `ENABLE_SSL=yes` and `USE_CERTBOT=yes` options
2. **Keep system updated** - Regularly update the host OS and container runtime
3. **Update container regularly** - Rebuild and redeploy container for security updates
4. **Use strong SMTP passwords** - Use app-specific passwords for email
5. **Configure firewall** - Only allow ports 80, 443, and SSH
6. **Monitor logs** - Set up log monitoring and alerting
7. **Backup regularly** - Schedule automated backups of data volumes

## Firewall Configuration

**UFW (Ubuntu/Debian):**
```bash
sudo ufw allow 'Nginx Full'    # or 'Apache Full'
sudo ufw allow 'OpenSSH'
sudo ufw enable
```

**Firewalld (RHEL/CentOS):**
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

## DNS Configuration

Before running the scripts, configure DNS:

```
A record:  occam.yourdomain.com → your-server-ip
```

Verify DNS is working:
```bash
dig occam.yourdomain.com
nslookup occam.yourdomain.com
```

## Support

For issues:
1. Check the troubleshooting section above
2. Review logs (container and web server)
3. See complete documentation in `docs/CONTAINER_DEPLOYMENT.md`
4. Report issues on GitHub
