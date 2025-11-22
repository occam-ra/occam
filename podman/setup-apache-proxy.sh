#!/bin/bash
# OCCAM Container - Apache2 Reverse Proxy Setup
# Configures Apache2 as a reverse proxy to the OCCAM container

set -e

# Configuration - Edit these as needed
DOMAIN="${DOMAIN:-occam.example.com}"
ENABLE_SSL="${ENABLE_SSL:-no}"
USE_CERTBOT="${USE_CERTBOT:-no}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"
CONTAINER_PORT="${CONTAINER_PORT:-5000}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "OCCAM - Apache2 Reverse Proxy Setup"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    exit 1
fi

# Check if container is running
CONTAINER_CMD=""
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
fi

if [ -n "$CONTAINER_CMD" ]; then
    if ! $CONTAINER_CMD ps | grep -q "occam-web"; then
        echo -e "${YELLOW}Warning: OCCAM container doesn't appear to be running${NC}"
        echo "Make sure to run the container before configuring the proxy:"
        echo "  ./deploy-container.sh"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Install Apache2
echo "Installing Apache2..."
apt-get update
apt-get install -y apache2

# Enable required modules
echo "Enabling Apache2 modules..."
a2enmod proxy
a2enmod proxy_http
a2enmod headers
a2enmod rewrite

if [ "$ENABLE_SSL" = "yes" ]; then
    a2enmod ssl
fi

# Create Apache configuration
APACHE_CONF="/etc/apache2/sites-available/occam.conf"
echo "Creating Apache configuration: $APACHE_CONF"

if [ "$ENABLE_SSL" = "yes" ] && [ "$USE_CERTBOT" = "no" ]; then
    # HTTPS with manual certificates
    cat > "$APACHE_CONF" <<EOF
# HTTP - Redirect to HTTPS
<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAdmin admin@$DOMAIN

    # Redirect all HTTP to HTTPS
    Redirect permanent / https://$DOMAIN/
</VirtualHost>

# HTTPS
<VirtualHost *:443>
    ServerName $DOMAIN
    ServerAdmin admin@$DOMAIN

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/$DOMAIN.crt
    SSLCertificateKeyFile /etc/ssl/private/$DOMAIN.key

    # Modern SSL settings
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5
    SSLHonorCipherOrder on

    # Proxy to OCCAM container
    ProxyPreserveHost On
    ProxyPass / http://localhost:$CONTAINER_PORT/
    ProxyPassReverse / http://localhost:$CONTAINER_PORT/

    # Forward headers for HTTPS
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"

    # Logging
    ErrorLog \${APACHE_LOG_DIR}/occam-ssl-error.log
    CustomLog \${APACHE_LOG_DIR}/occam-ssl-access.log combined
</VirtualHost>
EOF

    echo ""
    echo -e "${YELLOW}Note: You need to provide SSL certificates at:${NC}"
    echo "  Certificate: /etc/ssl/certs/$DOMAIN.crt"
    echo "  Private Key: /etc/ssl/private/$DOMAIN.key"
    echo ""

elif [ "$ENABLE_SSL" = "yes" ] && [ "$USE_CERTBOT" = "yes" ]; then
    # Initial HTTP config for Certbot validation
    cat > "$APACHE_CONF" <<EOF
<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAdmin admin@$DOMAIN

    # Proxy to OCCAM container
    ProxyPreserveHost On
    ProxyPass / http://localhost:$CONTAINER_PORT/
    ProxyPassReverse / http://localhost:$CONTAINER_PORT/

    # Forward headers
    RequestHeader set X-Forwarded-Proto "http"
    RequestHeader set X-Forwarded-Port "80"

    # Logging
    ErrorLog \${APACHE_LOG_DIR}/occam-error.log
    CustomLog \${APACHE_LOG_DIR}/occam-access.log combined
</VirtualHost>
EOF

else
    # HTTP only
    cat > "$APACHE_CONF" <<EOF
<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAdmin admin@$DOMAIN

    # Proxy to OCCAM container
    ProxyPreserveHost On
    ProxyPass / http://localhost:$CONTAINER_PORT/
    ProxyPassReverse / http://localhost:$CONTAINER_PORT/

    # Forward headers
    RequestHeader set X-Forwarded-Proto "http"
    RequestHeader set X-Forwarded-Port "80"

    # Logging
    ErrorLog \${APACHE_LOG_DIR}/occam-error.log
    CustomLog \${APACHE_LOG_DIR}/occam-access.log combined
</VirtualHost>
EOF
fi

# Enable site
echo "Enabling OCCAM site..."
a2ensite occam.conf

# Disable default site if it exists
if [ -f /etc/apache2/sites-enabled/000-default.conf ]; then
    echo "Disabling default Apache site..."
    a2dissite 000-default.conf
fi

# Test Apache configuration
echo "Testing Apache configuration..."
if ! apache2ctl configtest; then
    echo -e "${RED}Error: Apache configuration test failed${NC}"
    exit 1
fi

# Restart Apache
echo "Restarting Apache..."
systemctl restart apache2

# Setup SSL with Certbot if requested
if [ "$ENABLE_SSL" = "yes" ] && [ "$USE_CERTBOT" = "yes" ]; then
    echo ""
    echo "Setting up SSL with Let's Encrypt..."

    if [ -z "$CERTBOT_EMAIL" ]; then
        echo -e "${RED}Error: CERTBOT_EMAIL must be set when USE_CERTBOT=yes${NC}"
        exit 1
    fi

    # Install Certbot
    apt-get install -y certbot python3-certbot-apache

    # Get certificate
    certbot --apache -d "$DOMAIN" --non-interactive --agree-tos --email "$CERTBOT_EMAIL"

    echo -e "${GREEN}✓ SSL certificate obtained and configured${NC}"
fi

# Enable Apache on boot
systemctl enable apache2

echo ""
echo -e "${GREEN}✓ Apache2 reverse proxy configured successfully!${NC}"
echo ""
echo "Configuration Details:"
echo "  Domain: $DOMAIN"
echo "  SSL: $ENABLE_SSL"
if [ "$ENABLE_SSL" = "yes" ] && [ "$USE_CERTBOT" = "yes" ]; then
    echo "  Certificate: Let's Encrypt (auto-renews)"
fi
echo "  Backend: http://localhost:$CONTAINER_PORT"
echo ""

if [ "$ENABLE_SSL" = "yes" ]; then
    echo "Access OCCAM at: https://$DOMAIN"
else
    echo "Access OCCAM at: http://$DOMAIN"
fi

echo ""
echo "Apache Management:"
echo "  Status:  systemctl status apache2"
echo "  Restart: systemctl restart apache2"
echo "  Logs:    tail -f /var/log/apache2/occam-error.log"
echo ""

if [ "$ENABLE_SSL" = "yes" ] && [ "$USE_CERTBOT" = "yes" ]; then
    echo "SSL Certificate Auto-Renewal:"
    echo "  Certbot automatic renewal is enabled via systemd timer"
    echo "  Test renewal: certbot renew --dry-run"
    echo ""
fi

echo -e "${BLUE}Next steps:${NC}"
echo "1. Update DNS to point $DOMAIN to this server"
echo "2. Test the site in a browser"
echo "3. Monitor logs for any issues"
echo ""
