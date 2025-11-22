# OCCAM Container - Remote Deployment Guide

Complete guide for deploying the OCCAM container on a remote server with Apache2 or Nginx as a reverse proxy.

## Step 1: Transfer Container to Remote Machine

### Option A: Save/Transfer/Load (Recommended for offline transfer)

**On the build machine:**
```bash
# Save the container image to a tar file
sudo podman save -o occam-web.tar localhost/occam-web:latest

# The file will be approximately 544 MB
ls -lh occam-web.tar
```

**Transfer to remote machine:**
```bash
# Using scp
scp occam-web.tar user@remote-server:/tmp/

# Or using rsync (resumes on interruption)
rsync -avP occam-web.tar user@remote-server:/tmp/
```

**On the remote machine:**
```bash
# Load the image
sudo podman load -i /tmp/occam-web.tar

# Verify it loaded
sudo podman images | grep occam-web

# Clean up tar file
rm /tmp/occam-web.tar
```

### Option B: Direct Transfer via SSH (No intermediate file)

**From build machine directly to remote:**
```bash
sudo podman save localhost/occam-web:latest | \
  ssh user@remote-server 'sudo podman load'
```

### Option C: Container Registry (Best for multiple deployments)

**On build machine:**
```bash
# Tag for registry (use Docker Hub, quay.io, or private registry)
sudo podman tag localhost/occam-web:latest docker.io/yourusername/occam-web:latest

# Login and push
sudo podman login docker.io
sudo podman push docker.io/yourusername/occam-web:latest
```

**On remote machine:**
```bash
sudo podman pull docker.io/yourusername/occam-web:latest
```

## Step 2: Install Podman on Remote Machine (if needed)

### Debian/Ubuntu:
```bash
sudo apt update
sudo apt install podman
```

### RHEL/CentOS/Fedora:
```bash
sudo dnf install podman
```

### Verify installation:
```bash
podman --version
```

## Step 3: Run Container on Remote Machine

### Basic Run (for testing):
```bash
sudo podman run -d \
  -p 5000:5000 \
  --name occam-web \
  localhost/occam-web:latest

# Test it works
curl http://localhost:5000
```

### Run with Persistent Data (Recommended):
```bash
sudo podman run -d \
  -p 5000:5000 \
  -v occam-data:/var/www/occam/data \
  -v occam-logs:/var/www/occam/logs \
  --name occam-web \
  --restart unless-stopped \
  localhost/occam-web:latest
```

### Run with Email Configuration:
```bash
sudo podman run -d \
  -p 5000:5000 \
  -v occam-data:/var/www/occam/data \
  -v occam-logs:/var/www/occam/logs \
  -e SMTP_HOST=smtp.gmail.com \
  -e SMTP_PORT=587 \
  -e SMTP_USER=your-email@gmail.com \
  -e SMTP_PASSWORD=your-app-password \
  -e SMTP_FROM=noreply@yourdomain.com \
  --name occam-web \
  --restart unless-stopped \
  localhost/occam-web:latest
```

## Step 4: Configure Reverse Proxy

The container runs on port 5000. Use Apache or Nginx as a reverse proxy to:
- Serve on standard HTTP/HTTPS ports (80/443)
- Add SSL/TLS encryption
- Handle static files efficiently
- Add authentication if needed

### Option A: Apache2 Reverse Proxy

**Install Apache2:**
```bash
sudo apt update
sudo apt install apache2
```

**Enable required modules:**
```bash
sudo a2enmod proxy proxy_http headers ssl
sudo systemctl restart apache2
```

**Create virtual host configuration:**
```bash
sudo nano /etc/apache2/sites-available/occam.conf
```

**Paste this configuration:**
```apache
<VirtualHost *:80>
    ServerName occam.example.com
    ServerAdmin admin@example.com

    # Proxy to container
    ProxyPreserveHost On
    ProxyPass / http://localhost:5000/
    ProxyPassReverse / http://localhost:5000/

    # Set headers
    RequestHeader set X-Forwarded-Proto "http"
    RequestHeader set X-Forwarded-Port "80"

    # Logging
    ErrorLog ${APACHE_LOG_DIR}/occam-error.log
    CustomLog ${APACHE_LOG_DIR}/occam-access.log combined
</VirtualHost>
```

**For HTTPS (with Let's Encrypt):**
```apache
<VirtualHost *:80>
    ServerName occam.example.com

    # Redirect to HTTPS
    Redirect permanent / https://occam.example.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName occam.example.com
    ServerAdmin admin@example.com

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/occam.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/occam.example.com/privkey.pem

    # Modern SSL settings
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5
    SSLHonorCipherOrder on

    # Proxy to container
    ProxyPreserveHost On
    ProxyPass / http://localhost:5000/
    ProxyPassReverse / http://localhost:5000/

    # Set headers for HTTPS
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"

    # Logging
    ErrorLog ${APACHE_LOG_DIR}/occam-ssl-error.log
    CustomLog ${APACHE_LOG_DIR}/occam-ssl-access.log combined
</VirtualHost>
```

**Enable site and restart Apache:**
```bash
sudo a2ensite occam.conf
sudo systemctl restart apache2
```

**Get SSL certificate with Certbot:**
```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d occam.example.com
```

### Option B: Nginx Reverse Proxy

**Install Nginx:**
```bash
sudo apt update
sudo apt install nginx
```

**Create configuration:**
```bash
sudo nano /etc/nginx/sites-available/occam
```

**Paste this configuration:**
```nginx
# HTTP - redirect to HTTPS (if using SSL)
server {
    listen 80;
    listen [::]:80;
    server_name occam.example.com;

    # For HTTP-only deployment, use this instead:
    # location / {
    #     proxy_pass http://localhost:5000;
    #     proxy_set_header Host $host;
    #     proxy_set_header X-Real-IP $remote_addr;
    #     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #     proxy_set_header X-Forwarded-Proto $scheme;
    #     proxy_redirect off;
    # }

    # For SSL deployment, redirect to HTTPS:
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name occam.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/occam.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/occam.example.com/privkey.pem;

    # Modern SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Proxy to container
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_redirect off;

        # Increase timeouts for long-running analyses
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
    }

    # Logging
    access_log /var/log/nginx/occam-access.log;
    error_log /var/log/nginx/occam-error.log;
}
```

**For HTTP-only (no SSL), use this simpler config:**
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name occam.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Increase timeouts for long-running analyses
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
    }

    access_log /var/log/nginx/occam-access.log;
    error_log /var/log/nginx/occam-error.log;
}
```

**Enable site and restart Nginx:**
```bash
sudo ln -s /etc/nginx/sites-available/occam /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

**Get SSL certificate with Certbot:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d occam.example.com
```

## Step 5: Configure Firewall

**Allow HTTP/HTTPS through firewall:**
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 'Apache Full'    # or 'Nginx Full'
sudo ufw status

# Firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Step 6: Enable Container Auto-Start

**Make container start on boot:**
```bash
# Generate systemd service file
sudo podman generate systemd --new --name occam-web \
  > /etc/systemd/system/occam-web.service

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable occam-web.service
sudo systemctl start occam-web.service

# Check status
sudo systemctl status occam-web.service
```

## Step 7: Verify Deployment

**Check container is running:**
```bash
sudo podman ps | grep occam-web
sudo podman exec occam-web supervisorctl status
```

**Test from localhost:**
```bash
curl http://localhost:5000
```

**Test through web server:**
```bash
curl http://occam.example.com
# or
curl https://occam.example.com
```

**Check logs:**
```bash
# Container logs
sudo podman logs occam-web

# Application logs
sudo podman exec occam-web tail -f /var/www/occam/logs/gunicorn-stdout.log

# Web server logs
sudo tail -f /var/log/apache2/occam-access.log  # Apache
sudo tail -f /var/log/nginx/occam-access.log    # Nginx
```

## Management Commands

### Container Management:
```bash
# View status
sudo podman ps -a | grep occam-web
sudo podman exec occam-web supervisorctl status

# View logs
sudo podman logs -f occam-web

# Stop container
sudo podman stop occam-web

# Start container
sudo podman start occam-web

# Restart container
sudo podman restart occam-web

# Update container (after transferring new image)
sudo podman stop occam-web
sudo podman rm occam-web
# Load new image, then run with same command as before
```

### Backup Data:
```bash
# Backup uploaded data
sudo podman run --rm \
  -v occam-data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/occam-data-$(date +%Y%m%d).tar.gz -C /data .

# Backup logs
sudo podman run --rm \
  -v occam-logs:/logs \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/occam-logs-$(date +%Y%m%d).tar.gz -C /logs .
```

### Restore Data:
```bash
sudo podman run --rm \
  -v occam-data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/occam-data-20241122.tar.gz -C /data
```

## Troubleshooting

### Container won't start:
```bash
sudo podman logs occam-web
sudo journalctl -u occam-web.service -f
```

### Port 5000 already in use:
```bash
sudo lsof -i :5000
# Kill conflicting process or use different port:
# -p 8080:5000
```

### Web server returns 502 Bad Gateway:
- Check container is running: `sudo podman ps`
- Check container responds: `curl http://localhost:5000`
- Check web server proxy settings
- Check firewall isn't blocking localhost connections

### SSL certificate errors:
```bash
# Renew certificate
sudo certbot renew
sudo systemctl restart apache2  # or nginx
```

## Security Considerations

1. **Always use HTTPS in production** - Use Let's Encrypt for free SSL certificates
2. **Keep container updated** - Rebuild and redeploy regularly
3. **Restrict access** - Use firewall rules, IP allowlists, or authentication
4. **Monitor logs** - Set up log rotation and monitoring
5. **Backup data** - Schedule regular backups of the data volume
6. **Use strong passwords** - For SMTP and any additional auth

## Quick Reference

**Full deployment in one script:**
```bash
#!/bin/bash
# Quick deployment script

# 1. Load container
sudo podman load -i occam-web.tar

# 2. Run container
sudo podman run -d \
  -p 5000:5000 \
  -v occam-data:/var/www/occam/data \
  -v occam-logs:/var/www/occam/logs \
  --name occam-web \
  --restart unless-stopped \
  localhost/occam-web:latest

# 3. Generate and enable systemd service
sudo podman generate systemd --new --name occam-web \
  > /etc/systemd/system/occam-web.service
sudo systemctl daemon-reload
sudo systemctl enable occam-web.service

# 4. Configure nginx (example)
sudo tee /etc/nginx/sites-available/occam > /dev/null <<'EOF'
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
EOF

sudo ln -s /etc/nginx/sites-available/occam /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "Deployment complete! Access at http://occam.example.com"
```
