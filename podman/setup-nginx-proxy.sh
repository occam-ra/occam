#!/bin/bash
# OCCAM Container - Nginx Reverse Proxy Setup
# Configures Nginx as a reverse proxy to the OCCAM container

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
echo "OCCAM - Nginx Reverse Proxy Setup"
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

# Install Nginx
echo "Installing Nginx..."
apt-get update
apt-get install -y nginx

# Create Nginx configuration
NGINX_CONF="/etc/nginx/sites-available/occam"
echo "Creating Nginx configuration: $NGINX_CONF"

if [ "$ENABLE_SSL" = "yes" ] && [ "$USE_CERTBOT" = "no" ]; then
    # HTTPS with manual certificates
    cat > "$NGINX_CONF" <<EOF
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Redirect all HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/$DOMAIN.crt;
    ssl_certificate_key /etc/ssl/private/$DOMAIN.key;

    # Modern SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy to OCCAM container
    location / {
        proxy_pass http://localhost:$CONTAINER_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_redirect off;

        # Increase timeouts for long-running analyses
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;

        # Increase buffer sizes for large responses
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Logging
    access_log /var/log/nginx/occam-access.log;
    error_log /var/log/nginx/occam-error.log;
}
EOF

    echo ""
    echo -e "${YELLOW}Note: You need to provide SSL certificates at:${NC}"
    echo "  Certificate: /etc/ssl/certs/$DOMAIN.crt"
    echo "  Private Key: /etc/ssl/private/$DOMAIN.key"
    echo ""

elif [ "$ENABLE_SSL" = "yes" ] && [ "$USE_CERTBOT" = "yes" ]; then
    # Initial HTTP config for Certbot validation
    cat > "$NGINX_CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Proxy to OCCAM container
    location / {
        proxy_pass http://localhost:$CONTAINER_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
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
EOF

else
    # HTTP only
    cat > "$NGINX_CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Proxy to OCCAM container
    location / {
        proxy_pass http://localhost:$CONTAINER_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_redirect off;

        # Increase timeouts for long-running analyses
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;

        # Increase buffer sizes for large responses
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Logging
    access_log /var/log/nginx/occam-access.log;
    error_log /var/log/nginx/occam-error.log;
}
EOF
fi

# Enable site
echo "Enabling OCCAM site..."
ln -sf /etc/nginx/sites-available/occam /etc/nginx/sites-enabled/

# Disable default site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "Disabling default Nginx site..."
    rm -f /etc/nginx/sites-enabled/default
fi

# Test Nginx configuration
echo "Testing Nginx configuration..."
if ! nginx -t; then
    echo -e "${RED}Error: Nginx configuration test failed${NC}"
    exit 1
fi

# Restart Nginx
echo "Restarting Nginx..."
systemctl restart nginx

# Setup SSL with Certbot if requested
if [ "$ENABLE_SSL" = "yes" ] && [ "$USE_CERTBOT" = "yes" ]; then
    echo ""
    echo "Setting up SSL with Let's Encrypt..."

    if [ -z "$CERTBOT_EMAIL" ]; then
        echo -e "${RED}Error: CERTBOT_EMAIL must be set when USE_CERTBOT=yes${NC}"
        exit 1
    fi

    # Install Certbot
    apt-get install -y certbot python3-certbot-nginx

    # Get certificate and auto-configure Nginx
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$CERTBOT_EMAIL"

    echo -e "${GREEN}✓ SSL certificate obtained and configured${NC}"
fi

# Enable Nginx on boot
systemctl enable nginx

echo ""
echo -e "${GREEN}✓ Nginx reverse proxy configured successfully!${NC}"
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
echo "Nginx Management:"
echo "  Status:  systemctl status nginx"
echo "  Restart: systemctl restart nginx"
echo "  Logs:    tail -f /var/log/nginx/occam-error.log"
echo "  Test:    nginx -t"
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
