#!/bin/bash
# OCCAM Flask Web Server - Apache2 Installation Script
# This script sets up the OCCAM web server with Apache2 and mod_wsgi

set -e  # Exit on error

# Configuration variables - EDIT THESE FOR YOUR DEPLOYMENT
DOMAIN="occam.example.com"
INSTALL_DIR="/var/www/occam"
APACHE_USER="www-data"
APACHE_GROUP="www-data"
PYTHON_BIN="/usr/bin/python3"
ENABLE_SSL="no"  # Set to "yes" to enable SSL (requires certificate setup)
USE_CERTBOT="no"  # Set to "yes" to automatically obtain Let's Encrypt certificates
CERTBOT_EMAIL=""  # Email for Let's Encrypt notifications (required if USE_CERTBOT=yes)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}OCCAM Apache2 Installation Script${NC}"
echo -e "${GREEN}====================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo bash install-apache.sh"
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
print_status "Installing Apache2 and dependencies..."
apt update
if [ "$USE_CERTBOT" = "yes" ]; then
    apt install -y apache2 libapache2-mod-wsgi-py3 python3-pip redis-server certbot python3-certbot-apache
else
    apt install -y apache2 libapache2-mod-wsgi-py3 python3-pip redis-server
fi

# Enable Apache modules
print_status "Enabling Apache modules..."
a2enmod wsgi
a2enmod rewrite
a2enmod headers

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
pip3 install pyoccam Flask redis rq

# Create WSGI file
print_status "Creating WSGI file..."
cat > "$INSTALL_DIR/occam.wsgi" << 'WSGIEOF'
#!/usr/bin/python3
import sys
import os
import logging

# Set up logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Add application directory to Python path
sys.path.insert(0, '/var/www/occam/occam_server')

# Ensure data directory exists
data_dir = '/var/www/occam/data'
os.makedirs(data_dir, exist_ok=True)

# Import Flask application
try:
    from app import app as application
    logging.info('OCCAM Flask application loaded successfully')
except Exception as e:
    logging.error(f'Failed to load OCCAM application: {e}')
    raise
WSGIEOF

# Set permissions
print_status "Setting permissions..."
chown -R $APACHE_USER:$APACHE_GROUP "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"
chmod 775 "$INSTALL_DIR/data"
chmod 755 "$INSTALL_DIR/occam.wsgi"

# Create Apache virtual host configuration
print_status "Creating Apache virtual host configuration..."
VHOST_FILE="/etc/apache2/sites-available/occam.conf"

if [ "$ENABLE_SSL" = "yes" ]; then
    # SSL configuration
    cat > "$VHOST_FILE" << VHOSTEOF
<VirtualHost *:80>
    ServerName $DOMAIN

    # Redirect HTTP to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}\$1 [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName $DOMAIN
    ServerAdmin admin@$DOMAIN

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/$DOMAIN.crt
    SSLCertificateKeyFile /etc/ssl/private/$DOMAIN.key
    # SSLCertificateChainFile /etc/ssl/certs/$DOMAIN-chain.crt

    # WSGI Configuration
    WSGIDaemonProcess occam user=$APACHE_USER group=$APACHE_GROUP threads=5 python-path=$INSTALL_DIR/occam_server
    WSGIScriptAlias / $INSTALL_DIR/occam.wsgi
    WSGIPassAuthorization On

    <Directory $INSTALL_DIR>
        WSGIProcessGroup occam
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>

    # Static files
    Alias /static $INSTALL_DIR/occam_server/static
    <Directory $INSTALL_DIR/occam_server/static>
        Require all granted
        # Enable caching for static files
        ExpiresActive On
        ExpiresDefault "access plus 1 month"
    </Directory>

    # Data directory (no web access)
    <Directory $INSTALL_DIR/data>
        Require all denied
    </Directory>

    # Logging
    ErrorLog $INSTALL_DIR/logs/error.log
    CustomLog $INSTALL_DIR/logs/access.log combined
    LogLevel info

    # Security headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
</VirtualHost>
VHOSTEOF

    print_warning "SSL enabled. Please ensure SSL certificates are installed at:"
    print_warning "  /etc/ssl/certs/$DOMAIN.crt"
    print_warning "  /etc/ssl/private/$DOMAIN.key"

else
    # HTTP-only configuration
    cat > "$VHOST_FILE" << VHOSTEOF
<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAdmin admin@$DOMAIN

    # WSGI Configuration
    WSGIDaemonProcess occam user=$APACHE_USER group=$APACHE_GROUP threads=5 python-path=$INSTALL_DIR/occam_server
    WSGIScriptAlias / $INSTALL_DIR/occam.wsgi
    WSGIPassAuthorization On

    <Directory $INSTALL_DIR>
        WSGIProcessGroup occam
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>

    # Static files
    Alias /static $INSTALL_DIR/occam_server/static
    <Directory $INSTALL_DIR/occam_server/static>
        Require all granted
        # Enable caching for static files
        ExpiresActive On
        ExpiresDefault "access plus 1 month"
    </Directory>

    # Data directory (no web access)
    <Directory $INSTALL_DIR/data>
        Require all denied
    </Directory>

    # Logging
    ErrorLog $INSTALL_DIR/logs/error.log
    CustomLog $INSTALL_DIR/logs/access.log combined
    LogLevel info

    # Security headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
</VirtualHost>
VHOSTEOF
fi

# Enable the site
print_status "Enabling OCCAM site..."
a2dissite 000-default.conf 2>/dev/null || true
a2ensite occam.conf

# Test Apache configuration
print_status "Testing Apache configuration..."
if ! apache2ctl configtest; then
    print_error "Apache configuration test failed!"
    exit 1
fi

# Obtain SSL certificates with Certbot
if [ "$USE_CERTBOT" = "yes" ]; then
    print_status "Obtaining SSL certificate from Let's Encrypt..."

    # Start Apache temporarily for certbot (needed for HTTP-01 challenge)
    systemctl start apache2

    # Run certbot
    if certbot --apache \
        --non-interactive \
        --agree-tos \
        --email "$CERTBOT_EMAIL" \
        --domains "$DOMAIN" \
        --redirect; then

        echo -e "${GREEN}✓ SSL certificate obtained successfully${NC}"

        # Certbot automatically modifies the Apache config, so we verify it again
        if ! apache2ctl configtest; then
            print_error "Apache configuration test failed after Certbot modifications!"
            exit 1
        fi
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
cat > /etc/systemd/system/occam-worker.service << SERVICEEOF
[Unit]
Description=OCCAM RQ Background Worker
After=network.target redis-server.service
Requires=redis-server.service

[Service]
Type=simple
User=$APACHE_USER
Group=$APACHE_GROUP
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
SERVICEEOF

# Reload systemd and start worker
print_status "Starting RQ worker..."
systemctl daemon-reload
systemctl enable occam-worker
systemctl start occam-worker

# Restart Apache
print_status "Restarting Apache..."
systemctl restart apache2

# Check service status
print_status "Checking service status..."
if systemctl is-active --quiet apache2; then
    echo -e "${GREEN}✓ Apache2 is running${NC}"
else
    print_error "Apache2 failed to start!"
    systemctl status apache2
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
echo "  Apache2:    systemctl {start|stop|restart|status} apache2"
echo "  RQ Worker:  systemctl {start|stop|restart|status} occam-worker"
echo "  Redis:      systemctl {start|stop|restart|status} redis-server"
echo ""
echo "Log Files:"
echo "  Apache:     $INSTALL_DIR/logs/error.log"
echo "  Apache:     $INSTALL_DIR/logs/access.log"
echo "  RQ Worker:  journalctl -u occam-worker -f"
echo ""
echo "Configuration:"
echo "  Apache:     $VHOST_FILE"
echo "  WSGI:       $INSTALL_DIR/occam.wsgi"
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
    echo "  3. Restart Apache: systemctl restart apache2"
    echo "  4. Configure email in /etc/systemd/system/occam-worker.service"
    echo "  5. Test the installation by visiting the URL above"
else
    echo "  1. Edit /etc/hosts or DNS to point $DOMAIN to this server"
    echo "  2. Configure email in /etc/systemd/system/occam-worker.service"
    echo "  3. Test the installation by visiting the URL above"
fi
echo ""
