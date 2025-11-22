#!/bin/bash
# OCCAM Flask Web Server - Nginx Installation Script
# This script sets up the OCCAM web server with Nginx and Gunicorn

set -e  # Exit on error

# Configuration variables - EDIT THESE FOR YOUR DEPLOYMENT
DOMAIN="occam.example.com"
INSTALL_DIR="/var/www/occam"
APP_USER="www-data"
APP_GROUP="www-data"
PYTHON_BIN="/usr/bin/python3"
GUNICORN_WORKERS=4
GUNICORN_PORT=8000
ENABLE_SSL="no"  # Set to "yes" to enable SSL (requires certificate setup)
USE_CERTBOT="no"  # Set to "yes" to automatically obtain Let's Encrypt certificates
CERTBOT_EMAIL=""  # Email for Let's Encrypt notifications (required if USE_CERTBOT=yes)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}OCCAM Nginx Installation Script${NC}"
echo -e "${GREEN}====================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo bash install-nginx.sh"
    exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}>>> $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Validate certbot configuration
if [ "$USE_CERTBOT" = "yes" ]; then
    if [ "$ENABLE_SSL" != "yes" ]; then
        print_error "USE_CERTBOT requires ENABLE_SSL=yes"
        exit 1
    fi
    if [ -z "$CERTBOT_EMAIL" ]; then
        print_error "CERTBOT_EMAIL must be set when USE_CERTBOT=yes"
        exit 1
    fi
    if [ "$DOMAIN" = "occam.example.com" ] || [ "$DOMAIN" = "localhost" ]; then
        print_error "DOMAIN must be a valid public domain for Certbot (not $DOMAIN)"
        exit 1
    fi
fi

# Check if OCCAM is built
print_status "Checking OCCAM build..."
if [ ! -f "../builddir/occ" ]; then
    print_error "OCCAM not built. Please run 'meson setup builddir && ninja -C builddir' from project root first."
    exit 1
fi

# Install system dependencies
print_status "Installing Nginx and dependencies..."
apt update
if [ "$USE_CERTBOT" = "yes" ]; then
    apt install -y nginx python3-pip redis-server certbot python3-certbot-nginx
else
    apt install -y nginx python3-pip redis-server
fi

# Create installation directory
print_status "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/logs"

# Copy Flask application files
print_status "Copying Flask application..."
cp -r occam_server "$INSTALL_DIR/"

# Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install pyoccam Flask gunicorn redis rq

# Set permissions
print_status "Setting permissions..."
chown -R $APP_USER:$APP_GROUP "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"
chmod 775 "$INSTALL_DIR/data"

# Create Gunicorn configuration file
print_status "Creating Gunicorn configuration..."
cat > "$INSTALL_DIR/gunicorn_config.py" << 'GUNICORNEOF'
import multiprocessing
import os

# Server socket
bind = '127.0.0.1:8000'
backlog = 2048

# Worker processes
workers = 4
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Process naming
proc_name = 'occam-gunicorn'

# Logging
accesslog = '/var/www/occam/logs/gunicorn-access.log'
errorlog = '/var/www/occam/logs/gunicorn-error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Server mechanics
daemon = False
pidfile = '/var/www/occam/gunicorn.pid'
user = 'www-data'
group = 'www-data'
umask = 0o002

# SSL (if needed)
# keyfile = '/etc/ssl/private/occam.key'
# certfile = '/etc/ssl/certs/occam.crt'
GUNICORNEOF

# Update bind port in config
sed -i "s/bind = '127.0.0.1:8000'/bind = '127.0.0.1:$GUNICORN_PORT'/" "$INSTALL_DIR/gunicorn_config.py"
sed -i "s/workers = 4/workers = $GUNICORN_WORKERS/" "$INSTALL_DIR/gunicorn_config.py"

# Create systemd service for Gunicorn
print_status "Creating Gunicorn service..."
cat > /etc/systemd/system/occam-gunicorn.service << SERVICEEOF
[Unit]
Description=OCCAM Gunicorn WSGI Server
After=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_GROUP
RuntimeDirectory=gunicorn
WorkingDirectory=$INSTALL_DIR/occam_server
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=$PYTHON_BIN -m gunicorn -c $INSTALL_DIR/gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Create Nginx configuration
print_status "Creating Nginx configuration..."
NGINX_CONF="/etc/nginx/sites-available/occam"

if [ "$ENABLE_SSL" = "yes" ]; then
    # SSL configuration
    cat > "$NGINX_CONF" << 'NGINXEOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name DOMAIN_PLACEHOLDER;

    # Redirect all HTTP requests to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/DOMAIN_PLACEHOLDER.crt;
    ssl_certificate_key /etc/ssl/private/DOMAIN_PLACEHOLDER.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/www/occam/logs/nginx-access.log;
    error_log /var/www/occam/logs/nginx-error.log;

    # Max upload size (for data files)
    client_max_body_size 100M;

    # Static files
    location /static {
        alias /var/www/occam/occam_server/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:GUNICORN_PORT_PLACEHOLDER;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;

        # Timeouts for long-running requests
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
NGINXEOF

    print_warning "SSL enabled. Please ensure SSL certificates are installed at:"
    print_warning "  /etc/ssl/certs/$DOMAIN.crt"
    print_warning "  /etc/ssl/private/$DOMAIN.key"

else
    # HTTP-only configuration
    cat > "$NGINX_CONF" << 'NGINXEOF'
server {
    listen 80;
    listen [::]:80;
    server_name DOMAIN_PLACEHOLDER;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/www/occam/logs/nginx-access.log;
    error_log /var/www/occam/logs/nginx-error.log;

    # Max upload size (for data files)
    client_max_body_size 100M;

    # Static files
    location /static {
        alias /var/www/occam/occam_server/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:GUNICORN_PORT_PLACEHOLDER;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;

        # Timeouts for long-running requests
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
NGINXEOF
fi

# Replace placeholders in Nginx config
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" "$NGINX_CONF"
sed -i "s/GUNICORN_PORT_PLACEHOLDER/$GUNICORN_PORT/g" "$NGINX_CONF"

# Enable the Nginx site
print_status "Enabling OCCAM site in Nginx..."
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/occam
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
print_status "Testing Nginx configuration..."
if ! nginx -t; then
    print_error "Nginx configuration test failed!"
    exit 1
fi

# Obtain SSL certificates with Certbot
if [ "$USE_CERTBOT" = "yes" ]; then
    print_status "Obtaining SSL certificate from Let's Encrypt..."

    # Start Nginx and Gunicorn temporarily for certbot (needed for HTTP-01 challenge)
    systemctl start nginx

    # Run certbot
    if certbot --nginx \
        --non-interactive \
        --agree-tos \
        --email "$CERTBOT_EMAIL" \
        --domains "$DOMAIN" \
        --redirect; then

        echo -e "${GREEN}✓ SSL certificate obtained successfully${NC}"

        # Certbot automatically modifies the Nginx config, so we verify it again
        if ! nginx -t; then
            print_error "Nginx configuration test failed after Certbot modifications!"
            exit 1
        fi

        # Reload Nginx to apply certbot changes
        systemctl reload nginx
    else
        print_error "Certbot failed to obtain certificate!"
        print_error "Please check that:"
        print_error "  1. Domain $DOMAIN points to this server's public IP"
        print_error "  2. Port 80 is accessible from the internet"
        print_error "  3. No firewall is blocking Let's Encrypt servers"
        exit 1
    fi

    # Set up automatic renewal
    print_status "Setting up automatic certificate renewal..."
    systemctl enable certbot.timer
    systemctl start certbot.timer

    echo -e "${GREEN}✓ Certbot renewal timer enabled${NC}"
fi

# Start and enable Redis
print_status "Starting Redis server..."
systemctl start redis-server
systemctl enable redis-server

# Create systemd service for RQ worker
print_status "Creating RQ worker service..."
cat > /etc/systemd/system/occam-worker.service << WORKEREOF
[Unit]
Description=OCCAM RQ Background Worker
After=network.target redis-server.service
Requires=redis-server.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$INSTALL_DIR/occam_server
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="SMTP_HOST=localhost"
Environment="SMTP_PORT=25"
Environment="SMTP_FROM=noreply@$DOMAIN"
ExecStart=$PYTHON_BIN worker.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
WORKEREOF

# Reload systemd
print_status "Reloading systemd..."
systemctl daemon-reload

# Start services
print_status "Starting services..."
systemctl enable occam-gunicorn
systemctl start occam-gunicorn

systemctl enable occam-worker
systemctl start occam-worker

systemctl enable nginx
systemctl restart nginx

# Check service status
print_status "Checking service status..."
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    print_error "Nginx failed to start!"
    systemctl status nginx
    exit 1
fi

if systemctl is-active --quiet occam-gunicorn; then
    echo -e "${GREEN}✓ Gunicorn is running${NC}"
else
    print_error "Gunicorn failed to start!"
    systemctl status occam-gunicorn
    journalctl -u occam-gunicorn -n 50 --no-pager
    exit 1
fi

if systemctl is-active --quiet occam-worker; then
    echo -e "${GREEN}✓ RQ Worker is running${NC}"
else
    print_warning "RQ Worker failed to start (batch jobs will not work)"
    echo "Check logs with: journalctl -u occam-worker -n 50"
fi

if systemctl is-active --quiet redis-server; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    print_warning "Redis failed to start (batch jobs will not work)"
fi

# Print completion message
echo ""
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo "OCCAM web server has been installed and started."
echo ""
echo "Access the server at:"
if [ "$ENABLE_SSL" = "yes" ]; then
    echo "  https://$DOMAIN"
else
    echo "  http://$DOMAIN"
fi
echo ""
echo "Service Management:"
echo "  Nginx:      systemctl {start|stop|restart|status} nginx"
echo "  Gunicorn:   systemctl {start|stop|restart|status} occam-gunicorn"
echo "  RQ Worker:  systemctl {start|stop|restart|status} occam-worker"
echo "  Redis:      systemctl {start|stop|restart|status} redis-server"
echo ""
echo "Log Files:"
echo "  Nginx:      $INSTALL_DIR/logs/nginx-error.log"
echo "  Nginx:      $INSTALL_DIR/logs/nginx-access.log"
echo "  Gunicorn:   $INSTALL_DIR/logs/gunicorn-error.log"
echo "  Gunicorn:   $INSTALL_DIR/logs/gunicorn-access.log"
echo "  Gunicorn:   journalctl -u occam-gunicorn -f"
echo "  RQ Worker:  journalctl -u occam-worker -f"
echo ""
echo "Configuration:"
echo "  Nginx:      $NGINX_CONF"
echo "  Gunicorn:   $INSTALL_DIR/gunicorn_config.py"
echo "  Gunicorn:   /etc/systemd/system/occam-gunicorn.service"
echo "  Worker:     /etc/systemd/system/occam-worker.service"
if [ "$USE_CERTBOT" = "yes" ]; then
    echo "  SSL:        Managed by Certbot (auto-renewal enabled)"
fi
echo ""
echo "Next Steps:"
if [ "$USE_CERTBOT" = "yes" ]; then
    echo "  1. Verify HTTPS is working by visiting https://$DOMAIN"
    echo "  2. Configure email in /etc/systemd/system/occam-worker.service"
    echo "  3. Test batch job submission"
    echo ""
    echo "SSL Certificate Info:"
    echo "  - Certificates auto-renew via certbot.timer systemd service"
    echo "  - Manual renewal: sudo certbot renew"
    echo "  - Check renewal status: sudo certbot certificates"
elif [ "$ENABLE_SSL" = "yes" ]; then
    echo "  1. Edit /etc/hosts or DNS to point $DOMAIN to this server"
    echo "  2. Install SSL certificates in /etc/ssl/certs/ and /etc/ssl/private/"
    echo "  3. Restart Nginx: systemctl restart nginx"
    echo "  4. Configure email in /etc/systemd/system/occam-worker.service"
    echo "  5. Test the installation by visiting the URL above"
else
    echo "  1. Edit /etc/hosts or DNS to point $DOMAIN to this server"
    echo "  2. Configure email in /etc/systemd/system/occam-worker.service"
    echo "  3. Test the installation by visiting the URL above"
fi
echo ""
echo "Performance Tuning:"
echo "  - Adjust worker count in $INSTALL_DIR/gunicorn_config.py"
echo "  - Current: $GUNICORN_WORKERS workers"
echo "  - Recommended: 2-4 workers for limited resources"
echo ""
