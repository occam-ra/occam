#!/bin/bash
# OCCAM Flask Web Server - Uninstall Script
# This script removes OCCAM web server installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
INSTALL_DIR="/var/www/occam"
REMOVE_DATA="ask"
REMOVE_PACKAGES="ask"
FORCE="no"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --remove-data)
            REMOVE_DATA="yes"
            shift
            ;;
        --keep-data)
            REMOVE_DATA="no"
            shift
            ;;
        --remove-packages)
            REMOVE_PACKAGES="yes"
            shift
            ;;
        --keep-packages)
            REMOVE_PACKAGES="no"
            shift
            ;;
        --force)
            FORCE="yes"
            shift
            ;;
        --help)
            echo "OCCAM Web Server Uninstall Script"
            echo ""
            echo "Usage: sudo bash uninstall.sh [options]"
            echo ""
            echo "Options:"
            echo "  --install-dir DIR     Installation directory (default: /var/www/occam)"
            echo "  --remove-data         Remove data directory without asking"
            echo "  --keep-data           Keep data directory without asking"
            echo "  --remove-packages     Remove system packages without asking"
            echo "  --keep-packages       Keep system packages without asking"
            echo "  --force               Skip all confirmation prompts"
            echo "  --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  sudo bash uninstall.sh"
            echo "  sudo bash uninstall.sh --force --remove-data"
            echo "  sudo bash uninstall.sh --install-dir /opt/occam"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}OCCAM Web Server Uninstall Script${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo bash uninstall.sh"
    exit 1
fi

# Confirmation prompt
if [ "$FORCE" != "yes" ]; then
    echo -e "${YELLOW}WARNING: This will remove the OCCAM web server installation.${NC}"
    echo ""
    echo "Installation directory: $INSTALL_DIR"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Uninstall cancelled."
        exit 0
    fi
    echo ""
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

# Detect what was installed
APACHE_INSTALLED=false
NGINX_INSTALLED=false

if systemctl is-active --quiet apache2 && [ -f /etc/apache2/sites-available/occam.conf ]; then
    APACHE_INSTALLED=true
fi

if systemctl is-active --quiet nginx && [ -f /etc/nginx/sites-available/occam ]; then
    NGINX_INSTALLED=true
fi

if systemctl list-unit-files | grep -q occam-gunicorn.service; then
    NGINX_INSTALLED=true
fi

# Stop services
print_status "Stopping OCCAM services..."

if systemctl is-active --quiet occam-worker 2>/dev/null; then
    systemctl stop occam-worker
    echo "  ✓ Stopped occam-worker"
fi

if systemctl is-active --quiet occam-gunicorn 2>/dev/null; then
    systemctl stop occam-gunicorn
    echo "  ✓ Stopped occam-gunicorn"
fi

if [ "$APACHE_INSTALLED" = true ]; then
    systemctl stop apache2
    echo "  ✓ Stopped apache2"
fi

if [ "$NGINX_INSTALLED" = true ]; then
    systemctl stop nginx
    echo "  ✓ Stopped nginx"
fi

# Disable services
print_status "Disabling OCCAM services..."

if systemctl is-enabled --quiet occam-worker 2>/dev/null; then
    systemctl disable occam-worker
    echo "  ✓ Disabled occam-worker"
fi

if systemctl is-enabled --quiet occam-gunicorn 2>/dev/null; then
    systemctl disable occam-gunicorn
    echo "  ✓ Disabled occam-gunicorn"
fi

# Remove systemd service files
print_status "Removing systemd service files..."

if [ -f /etc/systemd/system/occam-worker.service ]; then
    rm /etc/systemd/system/occam-worker.service
    echo "  ✓ Removed occam-worker.service"
fi

if [ -f /etc/systemd/system/occam-gunicorn.service ]; then
    rm /etc/systemd/system/occam-gunicorn.service
    echo "  ✓ Removed occam-gunicorn.service"
fi

# Reload systemd
systemctl daemon-reload

# Remove Apache configuration
if [ "$APACHE_INSTALLED" = true ]; then
    print_status "Removing Apache configuration..."

    if [ -f /etc/apache2/sites-enabled/occam.conf ]; then
        a2dissite occam.conf 2>/dev/null || true
        echo "  ✓ Disabled occam site"
    fi

    if [ -f /etc/apache2/sites-available/occam.conf ]; then
        rm /etc/apache2/sites-available/occam.conf
        echo "  ✓ Removed occam.conf"
    fi

    # Optionally restart Apache if other sites exist
    if systemctl is-active --quiet apache2; then
        systemctl reload apache2
        echo "  ✓ Reloaded Apache"
    fi
fi

# Remove Nginx configuration
if [ "$NGINX_INSTALLED" = true ]; then
    print_status "Removing Nginx configuration..."

    if [ -L /etc/nginx/sites-enabled/occam ]; then
        rm /etc/nginx/sites-enabled/occam
        echo "  ✓ Removed occam site link"
    fi

    if [ -f /etc/nginx/sites-available/occam ]; then
        rm /etc/nginx/sites-available/occam
        echo "  ✓ Removed occam configuration"
    fi

    # Optionally restart Nginx if other sites exist
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
        echo "  ✓ Reloaded Nginx"
    fi
fi

# Remove WSGI file (Apache)
if [ -f "$INSTALL_DIR/occam.wsgi" ]; then
    rm "$INSTALL_DIR/occam.wsgi"
    echo "  ✓ Removed WSGI file"
fi

# Handle data directory
if [ -d "$INSTALL_DIR/data" ]; then
    if [ "$REMOVE_DATA" = "ask" ]; then
        echo ""
        echo -e "${YELLOW}Data directory found: $INSTALL_DIR/data${NC}"
        read -p "Remove data directory? This will delete all uploaded files! (yes/no): " remove_data
        REMOVE_DATA="$remove_data"
    fi

    if [ "$REMOVE_DATA" = "yes" ]; then
        print_status "Removing data directory..."
        rm -rf "$INSTALL_DIR/data"
        echo "  ✓ Removed data directory"
    else
        print_warning "Keeping data directory: $INSTALL_DIR/data"
    fi
fi

# Handle logs directory
if [ -d "$INSTALL_DIR/logs" ]; then
    print_status "Removing logs directory..."
    rm -rf "$INSTALL_DIR/logs"
    echo "  ✓ Removed logs directory"
fi

# Remove application files
if [ -d "$INSTALL_DIR/occam_server" ]; then
    print_status "Removing application files..."
    rm -rf "$INSTALL_DIR/occam_server"
    echo "  ✓ Removed occam_server directory"
fi

if [ -f "$INSTALL_DIR/gunicorn_config.py" ]; then
    rm "$INSTALL_DIR/gunicorn_config.py"
    echo "  ✓ Removed gunicorn_config.py"
fi

if [ -f "$INSTALL_DIR/gunicorn.pid" ]; then
    rm "$INSTALL_DIR/gunicorn.pid"
fi

# Remove installation directory if empty or forced
if [ -d "$INSTALL_DIR" ]; then
    if [ -z "$(ls -A $INSTALL_DIR)" ] || [ "$REMOVE_DATA" = "yes" ]; then
        print_status "Removing installation directory..."
        rmdir "$INSTALL_DIR" 2>/dev/null || rm -rf "$INSTALL_DIR"
        echo "  ✓ Removed $INSTALL_DIR"
    else
        print_warning "Installation directory not empty, keeping: $INSTALL_DIR"
    fi
fi

# Ask about removing system packages
if [ "$REMOVE_PACKAGES" = "ask" ]; then
    echo ""
    echo -e "${YELLOW}System packages (Apache/Nginx, Redis, etc.) are still installed.${NC}"
    read -p "Remove system packages? (yes/no): " remove_pkgs
    REMOVE_PACKAGES="$remove_pkgs"
fi

if [ "$REMOVE_PACKAGES" = "yes" ]; then
    print_status "Removing system packages..."

    if [ "$APACHE_INSTALLED" = true ]; then
        apt remove -y apache2 libapache2-mod-wsgi-py3
        echo "  ✓ Removed Apache packages"
    fi

    if [ "$NGINX_INSTALLED" = true ]; then
        apt remove -y nginx
        echo "  ✓ Removed Nginx"
    fi

    # Ask before removing Redis (might be used by other apps)
    if systemctl is-active --quiet redis-server 2>/dev/null; then
        echo ""
        print_warning "Redis server is running and might be used by other applications."
        read -p "Remove Redis? (yes/no): " remove_redis
        if [ "$remove_redis" = "yes" ]; then
            systemctl stop redis-server
            apt remove -y redis-server
            echo "  ✓ Removed Redis"
        fi
    fi

    # Autoremove unnecessary packages
    apt autoremove -y
    echo "  ✓ Removed unnecessary packages"
else
    print_warning "Keeping system packages (Apache/Nginx, Redis)"
fi

# Remove Python packages (optional)
echo ""
echo -e "${YELLOW}Python packages (Flask, gunicorn, pyoccam, etc.) are still installed.${NC}"
read -p "Remove Python packages? (yes/no): " remove_python
if [ "$remove_python" = "yes" ]; then
    print_status "Removing Python packages..."
    pip3 uninstall -y Flask gunicorn redis rq pyoccam 2>/dev/null || true
    echo "  ✓ Removed Python packages"
fi

# Clean up Certbot if installed
if command -v certbot &> /dev/null; then
    echo ""
    read -p "Remove SSL certificates managed by Certbot? (yes/no): " remove_certs
    if [ "$remove_certs" = "yes" ]; then
        print_status "Removing SSL certificates..."
        certbot delete --cert-name occam.* 2>/dev/null || true
        echo "  ✓ Removed SSL certificates"
    fi
fi

# Print completion message
echo ""
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Uninstall Complete!${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""
echo "OCCAM web server has been removed from the system."
echo ""

if [ "$REMOVE_DATA" != "yes" ] && [ -d "$INSTALL_DIR/data" ]; then
    echo -e "${YELLOW}Note: Data directory preserved at: $INSTALL_DIR/data${NC}"
    echo ""
fi

if [ "$REMOVE_PACKAGES" != "yes" ]; then
    echo "System packages were NOT removed. To remove manually:"
    if [ "$APACHE_INSTALLED" = true ]; then
        echo "  sudo apt remove apache2 libapache2-mod-wsgi-py3"
    fi
    if [ "$NGINX_INSTALLED" = true ]; then
        echo "  sudo apt remove nginx"
    fi
    echo "  sudo apt remove redis-server"
    echo "  sudo apt autoremove"
    echo ""
fi

echo "To reinstall OCCAM web server, run:"
echo "  cd flask_app"
echo "  sudo bash install-apache.sh   # or install-nginx.sh"
echo ""
