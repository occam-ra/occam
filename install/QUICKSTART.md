# OCCAM Web Server - Quick Start Guide

Get your OCCAM web server running with HTTPS in minutes!

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- Root/sudo access
- A domain name pointing to your server (e.g., occam.example.com)
- Ports 80 and 443 open in firewall

## 5-Minute Setup with Apache + HTTPS

### Step 1: Build OCCAM

```bash
cd /path/to/occam
sudo apt install build-essential meson ninja-build libgmp-dev python3-dev python3-pip
meson setup builddir
ninja -C builddir
```

### Step 2: Configure Installation Script

```bash
cd flask_app
nano install-apache.sh
```

Edit these lines:
```bash
DOMAIN="occam.yourdomain.com"        # Your actual domain
ENABLE_SSL="yes"
USE_CERTBOT="yes"
CERTBOT_EMAIL="admin@yourdomain.com" # Your email
```

Save and exit (Ctrl+X, Y, Enter).

### Step 3: Verify DNS

Make sure your domain points to this server:
```bash
dig +short occam.yourdomain.com
# Should show your server's IP address
```

### Step 4: Run Installation

```bash
sudo bash install-apache.sh
```

The script will automatically:
- Install all dependencies
- Obtain free SSL certificate from Let's Encrypt
- Configure Apache with HTTPS
- Set up automatic certificate renewal
- Start all services

### Step 5: Test

Visit `https://occam.yourdomain.com` - You should see the OCCAM landing page with a valid SSL certificate!

## 5-Minute Setup with Nginx + HTTPS

Same steps as Apache, but use `install-nginx.sh` instead:

```bash
cd flask_app
nano install-nginx.sh

# Edit same variables:
DOMAIN="occam.yourdomain.com"
ENABLE_SSL="yes"
USE_CERTBOT="yes"
CERTBOT_EMAIL="admin@yourdomain.com"

# Run installation
sudo bash install-nginx.sh
```

## Quick Start without HTTPS

For testing or internal networks:

```bash
cd flask_app
nano install-apache.sh  # or install-nginx.sh

# Edit:
DOMAIN="localhost"     # or internal hostname
ENABLE_SSL="no"
USE_CERTBOT="no"

sudo bash install-apache.sh
```

Access at: `http://your-server-ip:80` or `http://localhost`

## Next Steps

### Configure Email Notifications

Edit the worker service to enable batch job email notifications:

```bash
sudo nano /etc/systemd/system/occam-worker.service
```

Update these lines:
```ini
Environment="SMTP_HOST=smtp.gmail.com"
Environment="SMTP_PORT=587"
Environment="SMTP_USER=youruser@gmail.com"
Environment="SMTP_PASSWORD=your-app-password"
Environment="SMTP_FROM=noreply@yourdomain.com"
```

Restart the worker:
```bash
sudo systemctl daemon-reload
sudo systemctl restart occam-worker
```

### Test Batch Processing

1. Visit `https://occam.yourdomain.com/batch`
2. Upload an example file (from `/static/examples/`)
3. Enter your email address
4. Submit the job
5. Check your email for notification when complete

## Common Issues

### DNS Not Resolving

If `dig` doesn't show your IP:
- Wait for DNS propagation (can take up to 48 hours)
- Check your domain registrar's DNS settings
- Use `nslookup occam.yourdomain.com` to verify

### Certbot Fails

If Let's Encrypt certificate fails:
```bash
# Check port 80 is accessible
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check Apache/Nginx is listening
sudo netstat -tlnp | grep :80

# Try manual certbot
sudo certbot --apache -d occam.yourdomain.com  # or --nginx
```

### Services Not Starting

Check service status:
```bash
# Apache setup
sudo systemctl status apache2
sudo systemctl status occam-worker
sudo tail -f /var/www/occam/logs/error.log

# Nginx setup
sudo systemctl status nginx
sudo systemctl status occam-gunicorn
sudo systemctl status occam-worker
sudo journalctl -u occam-gunicorn -n 50
```

## Advanced Configuration

### Adjust Performance

For servers with limited resources:

**Nginx:**
```bash
sudo nano /var/www/occam/gunicorn_config.py
# Change: workers = 2  # instead of 4
sudo systemctl restart occam-gunicorn
```

**Apache:**
```bash
sudo nano /etc/apache2/sites-available/occam.conf
# Change: threads=2  # in WSGIDaemonProcess line
sudo systemctl restart apache2
```

### Multiple Domains

To add more domains to your certificate:

```bash
sudo certbot --apache -d occam.yourdomain.com -d www.occam.yourdomain.com
# or for Nginx:
sudo certbot --nginx -d occam.yourdomain.com -d www.occam.yourdomain.com
```

### Check Certificate Renewal

Certificates auto-renew every 60 days via systemd timer:

```bash
# Check renewal timer
systemctl status certbot.timer

# Test renewal (doesn't actually renew)
sudo certbot renew --dry-run

# View certificate info
sudo certbot certificates
```

## Uninstall

To completely remove the installation:

```bash
# Stop services
sudo systemctl stop apache2 nginx occam-gunicorn occam-worker redis-server
sudo systemctl disable occam-worker occam-gunicorn

# Remove files
sudo rm -rf /var/www/occam
sudo rm /etc/systemd/system/occam-*.service
sudo rm /etc/apache2/sites-*/occam.conf
sudo rm /etc/nginx/sites-*/occam

# Reload systemd
sudo systemctl daemon-reload

# Optionally remove packages
sudo apt remove apache2 nginx redis-server
sudo apt autoremove
```

## Getting Help

- **Documentation**: See [INSTALL.md](INSTALL.md) for detailed instructions
- **GitHub**: https://github.com/occam-ra/occam
- **Issues**: Report bugs at https://github.com/occam-ra/occam/issues
- **Email**: zwick@pdx.edu

## Quick Reference

| Task | Command |
|------|---------|
| Restart web server | `sudo systemctl restart apache2` (or `nginx`) |
| Restart app server | `sudo systemctl restart occam-gunicorn` (Nginx only) |
| Restart worker | `sudo systemctl restart occam-worker` |
| View logs | `sudo tail -f /var/www/occam/logs/*.log` |
| Check SSL cert | `sudo certbot certificates` |
| Renew SSL manually | `sudo certbot renew` |
| Test SSL renewal | `sudo certbot renew --dry-run` |
| View worker logs | `sudo journalctl -u occam-worker -f` |

---

**Pro Tip**: Bookmark your installation for easy access:
- Main page: `https://occam.yourdomain.com`
- Interactive analysis: `https://occam.yourdomain.com/occam`
- Batch jobs: `https://occam.yourdomain.com/batch`
