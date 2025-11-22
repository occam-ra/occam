#!/bin/bash
set -e

echo "Starting OCCAM Web Server Container..."

# Ensure gunicorn config has correct permissions
chown occam:occam /var/www/occam/gunicorn_config.py

# Ensure log directory exists and has correct permissions
mkdir -p /var/www/occam/logs
chown -R occam:occam /var/www/occam/logs
chmod 775 /var/www/occam/logs

# Ensure data directory has correct permissions
chown -R occam:occam /var/www/occam/data
chmod 775 /var/www/occam/data

# Print startup information
echo "========================================"
echo "OCCAM Web Server Container Started"
echo "========================================"
echo ""
echo "Services:"
echo "  - Gunicorn (Flask): http://localhost:5000"
echo "  - Redis: localhost:6379"
echo "  - RQ Worker: Background job processing"
echo ""
echo "Environment Variables:"
echo "  REDIS_URL: ${REDIS_URL:-redis://127.0.0.1:6379/0}"
echo "  SMTP_HOST: ${SMTP_HOST:-localhost}"
echo "  SMTP_PORT: ${SMTP_PORT:-25}"
echo "  LOG_LEVEL: ${LOG_LEVEL:-info}"
echo "  GUNICORN_WORKERS: ${GUNICORN_WORKERS:-auto}"
echo ""
echo "Logs available at: /var/www/occam/logs/"
echo "========================================"
echo ""

# Execute the main command (supervisord)
exec "$@"
