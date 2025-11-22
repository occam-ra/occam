# OCCAM Flask Web Server - Installation Guide

Quick installation guide for production deployments of the OCCAM web server.

## Prerequisites

### System Requirements
- Ubuntu 20.04+ or Debian 11+ (or compatible Linux distribution)
- Sudo/root access
- Internet connection for package installation
- 2GB+ RAM recommended for production use
- Redis server (installed automatically by scripts)

### Build OCCAM First

Before running installation scripts, build OCCAM from the project root:

```bash
cd /path/to/occam
sudo apt install build-essential meson ninja-build libgmp-dev python3-dev python3-pip
meson setup builddir
ninja -C builddir
```

## Automated Installation (Recommended)

Automated scripts are provided for both Apache2 and Nginx. Choose one based on your preference.

### Option 1: Apache2 + mod_wsgi

```bash
cd flask_app

# Edit configuration (optional)
nano install-apache.sh
# Change DOMAIN, INSTALL_DIR, ENABLE_SSL as needed

# Run installation
sudo bash install-apache.sh
```

**What it installs:**
- Apache2 with mod_wsgi
- Redis server for job queue
- All Python dependencies (Flask, pyoccam, redis, rq)
- Systemd service for RQ worker
- Complete Apache virtual host configuration

**Post-installation:**
- Access: http://your-domain (or https:// if SSL enabled)
- Logs: `/var/www/occam/logs/`
- Configuration: `/etc/apache2/sites-available/occam.conf`

### Option 2: Nginx + Gunicorn

```bash
cd flask_app

# Edit configuration (optional)
nano install-nginx.sh
# Change DOMAIN, INSTALL_DIR, ENABLE_SSL, GUNICORN_WORKERS as needed

# Run installation
sudo bash install-nginx.sh
```

**What it installs:**
- Nginx web server
- Gunicorn WSGI server (4 workers by default)
- Redis server for job queue
- All Python dependencies (Flask, pyoccam, redis, rq, gunicorn)
- Systemd services for Gunicorn and RQ worker
- Complete Nginx configuration

**Post-installation:**
- Access: http://your-domain (or https:// if SSL enabled)
- Logs: `/var/www/occam/logs/`
- Configuration: `/etc/nginx/sites-available/occam`

## Configuration Options

Both scripts support these configuration variables (edit at top of script):

| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAIN` | occam.example.com | Server domain name |
| `INSTALL_DIR` | /var/www/occam | Installation directory |
| `APP_USER` | www-data | Application user |
| `ENABLE_SSL` | no | Enable HTTPS (requires certificates) |
| `USE_CERTBOT` | no | Automatically obtain Let's Encrypt certificates |
| `CERTBOT_EMAIL` | (empty) | Email for Let's Encrypt notifications (required if USE_CERTBOT=yes) |
| `GUNICORN_WORKERS` | 4 | Number of Gunicorn workers (Nginx only) |

## SSL/HTTPS Setup

### Option 1: Automatic SSL with Let's Encrypt (Recommended)

The easiest way to enable HTTPS is to use the built-in Certbot support for automatic certificate management:

1. Edit the installation script:
   ```bash
   nano install-apache.sh  # or install-nginx.sh
   ```

2. Configure SSL settings:
   ```bash
   DOMAIN="occam.yourdomain.com"  # Must be a valid public domain
   ENABLE_SSL="yes"
   USE_CERTBOT="yes"
   CERTBOT_EMAIL="admin@yourdomain.com"  # For renewal notifications
   ```

3. Ensure your domain points to the server:
   ```bash
   # DNS must be configured before running the script
   # Check with: dig +short occam.yourdomain.com
   ```

4. Run the installation script:
   ```bash
   sudo bash install-apache.sh  # or install-nginx.sh
   ```

The script will automatically:
- Install Certbot and required plugins
- Obtain SSL certificates from Let's Encrypt
- Configure HTTPS with HTTP→HTTPS redirect
- Set up automatic certificate renewal (every 60 days)

**Certbot auto-renewal** runs via systemd timer. Check status with:
```bash
systemctl status certbot.timer
sudo certbot renew --dry-run  # Test renewal
```

### Option 2: Manual SSL Certificate Installation

If you already have SSL certificates or prefer manual management:

1. Edit the installation script:
   ```bash
   nano install-apache.sh  # or install-nginx.sh
   # Change: ENABLE_SSL="yes"
   # Keep: USE_CERTBOT="no"
   ```

2. Install SSL certificates before running the script:
   ```bash
   sudo mkdir -p /etc/ssl/certs /etc/ssl/private
   sudo cp your-domain.crt /etc/ssl/certs/
   sudo cp your-domain.key /etc/ssl/private/
   sudo chmod 600 /etc/ssl/private/your-domain.key
   ```

3. Run the installation script:
   ```bash
   sudo bash install-apache.sh  # or install-nginx.sh
   ```

### Manual Certbot Setup (Alternative)

If you prefer to run Certbot manually after installation:

```bash
# For Apache
sudo certbot --apache -d your-domain.com

# For Nginx
sudo certbot --nginx -d your-domain.com
```

## Email Configuration for Batch Jobs

To enable email notifications for batch job completion:

1. Edit the worker service configuration:
   ```bash
   sudo nano /etc/systemd/system/occam-worker.service
   ```

2. Update environment variables:
   ```ini
   Environment="SMTP_HOST=smtp.example.com"
   Environment="SMTP_PORT=587"
   Environment="SMTP_USER=username"
   Environment="SMTP_PASSWORD=password"
   Environment="SMTP_FROM=noreply@your-domain.com"
   ```

3. Reload and restart the worker:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart occam-worker
   ```

## Service Management

### Apache2 Installation

```bash
# Control web server
sudo systemctl {start|stop|restart|status} apache2

# Control background worker
sudo systemctl {start|stop|restart|status} occam-worker

# Control Redis
sudo systemctl {start|stop|restart|status} redis-server

# View logs
sudo tail -f /var/www/occam/logs/error.log
sudo journalctl -u occam-worker -f
```

### Nginx Installation

```bash
# Control web server
sudo systemctl {start|stop|restart|status} nginx

# Control application server
sudo systemctl {start|stop|restart|status} occam-gunicorn

# Control background worker
sudo systemctl {start|stop|restart|status} occam-worker

# Control Redis
sudo systemctl {start|stop|restart|status} redis-server

# View logs
sudo tail -f /var/www/occam/logs/nginx-error.log
sudo tail -f /var/www/occam/logs/gunicorn-error.log
sudo journalctl -u occam-worker -f
```

## Testing Installation

1. **Check services are running:**
   ```bash
   sudo systemctl status apache2  # or nginx and occam-gunicorn
   sudo systemctl status occam-worker
   sudo systemctl status redis-server
   ```

2. **Test web access:**
   ```bash
   curl http://localhost/
   # Should return HTML page
   ```

3. **Test batch processing:**
   - Visit http://your-domain/batch
   - Submit a test job with example data
   - Check email is received
   - Verify job completes successfully

## Troubleshooting

### Web server not accessible

**Apache:**
```bash
sudo apache2ctl configtest
sudo systemctl status apache2
sudo tail -f /var/www/occam/logs/error.log
```

**Nginx:**
```bash
sudo nginx -t
sudo systemctl status nginx
sudo systemctl status occam-gunicorn
sudo tail -f /var/www/occam/logs/nginx-error.log
```

### Batch jobs not processing

```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Check worker is running
sudo systemctl status occam-worker
sudo journalctl -u occam-worker -n 50

# Check worker logs
sudo journalctl -u occam-worker -f
```

### Email not sending

```bash
# Check SMTP configuration
sudo systemctl cat occam-worker | grep SMTP

# Test SMTP connection
telnet smtp.example.com 25  # or 587

# Check worker logs for errors
sudo journalctl -u occam-worker | grep -i email
```

### Permission errors

```bash
# Fix permissions
sudo chown -R www-data:www-data /var/www/occam
sudo chmod 775 /var/www/occam/data
```

## Performance Tuning

### For servers with limited resources:

**Nginx (adjust workers):**
```bash
sudo nano /var/www/occam/gunicorn_config.py
# Change: workers = 2  # Reduce from 4
sudo systemctl restart occam-gunicorn
```

**Apache (adjust processes):**
```bash
sudo nano /etc/apache2/sites-available/occam.conf
# Change: WSGIDaemonProcess occam ... threads=2  # Reduce from 5
sudo systemctl restart apache2
```

### For high-traffic servers:

**Nginx:**
```bash
sudo nano /var/www/occam/gunicorn_config.py
# Change: workers = 8  # Increase based on CPU cores
# Formula: (2 x CPU cores) + 1
sudo systemctl restart occam-gunicorn
```

## Uninstallation

### Automated Uninstall (Recommended)

Use the automated uninstall script:

```bash
cd flask_app
sudo bash uninstall.sh
```

The script will:
- Detect what was installed (Apache or Nginx)
- Stop and disable all services
- Remove configuration files
- Ask about removing data directory
- Ask about removing system packages
- Provide options for keeping or removing components

**Command-line options:**
```bash
# Interactive (asks for confirmation)
sudo bash uninstall.sh

# Force removal without prompts, keep data
sudo bash uninstall.sh --force --keep-data

# Remove everything including data
sudo bash uninstall.sh --force --remove-data --remove-packages

# Custom installation directory
sudo bash uninstall.sh --install-dir /opt/occam

# Show all options
sudo bash uninstall.sh --help
```

### Manual Uninstall

If you prefer to remove components manually:

```bash
# Stop and disable services
sudo systemctl stop occam-worker occam-gunicorn apache2 nginx
sudo systemctl disable occam-worker occam-gunicorn

# Remove files
sudo rm -rf /var/www/occam
sudo rm /etc/systemd/system/occam-worker.service
sudo rm /etc/systemd/system/occam-gunicorn.service
sudo rm /etc/apache2/sites-available/occam.conf
sudo rm /etc/nginx/sites-available/occam
sudo rm /etc/nginx/sites-enabled/occam

# Reload systemd
sudo systemctl daemon-reload

# Optionally remove packages
sudo apt remove apache2 libapache2-mod-wsgi-py3  # or nginx
sudo apt remove redis-server
sudo apt autoremove
```

## Manual Installation

For manual installation or customization, see the detailed instructions in [README.md](README.md).

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/occam-ra/occam
- Email: zwick@pdx.edu
