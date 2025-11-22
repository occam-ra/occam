# OCCAM Flask Web Server

Modern Python 3 Flask replacement for the legacy Python 2 CGI web server.

## Overview

This Flask application provides the same user interface and functionality as the original OCCAM CGI web server (`weboccam.py`), but using:
- **Python 3** instead of Python 2
- **Flask** web framework instead of CGI
- **pybind11** bindings (`_pyoccam`) instead of old Python C API
- **Jinja2** templates instead of simple string replacement

## Architecture

```
flask_app/
├── pyproject.toml         # Modern Python packaging (PEP 518)
├── README.md              # This file
├── requirements.txt       # Runtime dependencies
├── occam_server/          # Main package
│   ├── __init__.py       # Package initialization
│   ├── app.py            # Main Flask application
│   ├── occam_wrapper.py  # Compatibility wrapper for _pyoccam
│   ├── jobs.py           # Batch job manager (Redis Queue)
│   ├── worker.py         # Background worker for batch jobs
│   ├── ocGraph.py        # Graph generation (Python 3 port)
│   ├── utils.py          # Utility functions (file handling, etc.)
│   ├── templates/        # Jinja2 templates
│   │   ├── base.html     # Base template with PSU branding
│   │   ├── index.html    # Landing page
│   │   ├── error.html    # Error display
│   │   ├── main_form.html     # Main input form
│   │   ├── batch_form.html    # Batch job submission form
│   │   ├── batch_jobs.html    # Batch job list view
│   │   ├── batch_result.html  # Batch job status/results
│   │   └── ...           # Result templates (fit, search, sbfit, sbsearch)
│   └── static/           # Static assets (CSS, images)
│       ├── base.css
│       ├── style.css
│       ├── occam_logo.jpg
│       ├── occam-manual.pdf
│       └── examples/
└── data/                  # Runtime data directory (created during setup)
```

The package is structured as a modern Python package using `pyproject.toml` for dependency management and build configuration.

## Status

### ✅ Core Functionality Complete

**All essential OCCAM features are implemented:**
- Flask application with modern Python 3 architecture
- Variable-Based Modeling (VBM): fit and search operations
- State-Based Modeling (SBM): fit and search operations
- File upload and processing (supports .txt and .zip files)
- Data validation and error handling
- OccamManager wrapper providing compatibility with legacy API
- Complete set of Jinja2 templates with PSU branding
- Graph generation with SVG and Gephi export (requires python-igraph)
- HTML and CSV output formats
- PDF manual and example files included
- All links verified and working
- **Batch job processing** with Redis Queue (RQ) for background analysis
- **Email notifications** for batch job completion/failure

**The web server is production-ready for both interactive and batch OCCAM analysis.**

### 🔧 Optional Enhancements (Not Currently Implemented)

These features from the legacy CGI system are not essential for core functionality:
- **Cached data forms** - Legacy optimization; modern browsers and connections make this unnecessary

For most use cases, the current implementation provides all needed functionality.

## Installation

### Quick Start

From the project root directory:

```bash
# 1. Install system dependencies
sudo apt install build-essential meson ninja-build libgmp-dev python3-dev python3-pip

# 2. Build everything (C++ library, CLI, and Python extension)
meson setup builddir
ninja -C builddir

# 3. Install the Flask server
cd flask_app
pip install -e .

# 4. Create data directory
mkdir -p data
chmod 775 data
```

The Flask server should now be ready to run.

### Detailed Installation Steps

#### 1. System Dependencies

**Required:**
```bash
sudo apt install build-essential meson ninja-build libgmp-dev python3-dev python3-pip
```

**Optional (for graph generation):**
```bash
pip install python-igraph pycairo
```

Note: If graph dependencies fail to install, graph generation will be disabled but all other features will work.

#### 2. Build OCCAM Components

The project uses Meson/Ninja for cross-platform building:

```bash
# From project root
meson setup builddir
ninja -C builddir
```

This builds:
- C++ library (`liboccam3.a`)
- Command-line tool (`occ`)
- Python extension (`_pyoccam`)

#### 3. Install Flask Server

**Option A: Editable Install (Development)**
```bash
cd flask_app
pip install -e .
```

**Option B: Regular Install**
```bash
cd flask_app
pip install .
```

**Option C: Build Wheel**
```bash
cd flask_app
pip install build
python -m build
pip install dist/occam_server-*.whl
```

#### 4. Setup Data Directory

```bash
cd flask_app
mkdir -p data
chmod 775 data
```

### Building Python Wheels

To build distributable wheels for Python 3.9-3.13:

```bash
# From project root
pip install build

# Build pyoccam wheel
cd pyoccam
python -m build
ls dist/  # pyoccam-*.whl

# Build Flask server wheel
cd ../flask_app
python -m build
ls dist/  # occam_server-*.whl
```

### Verifying Installation

Test that everything is installed correctly:

```bash
# Test C++ CLI
./builddir/occ --help

# Test Python extension
python3 -c "from pyoccam import _pyoccam; print('pyoccam OK')"

# Test Flask server
cd flask_app
python3 -c "from occam_server import app; print('Flask app OK')"
```

### Alternative: Using Requirements Files

Instead of using `pip install -e .`, you can install dependencies using requirements files:

**Basic Installation:**
```bash
cd flask_app
pip install -r requirements.txt
```

**With Graph Generation Support:**
```bash
cd flask_app
pip install -r requirements-graphs.txt
```

**For Development:**
```bash
cd flask_app
pip install -r requirements-dev.txt
```

**Requirements Files Available:**

- `requirements.txt` - Core runtime dependencies (Flask, pyoccam, etc.)
- `requirements-graphs.txt` - Adds graph generation libraries (python-igraph, pycairo)
- `requirements-dev.txt` - Development tools (pytest, black, gunicorn, etc.)

Note: `pyoccam` must be built and installed first (from the project root with Meson), or installed from a wheel.

## Running

### Development Server

**Important:** You must run the server from the `flask_app/occam_server` directory so it can find the `static/` and `templates/` directories.

```bash
cd flask_app/occam_server
python3 app.py
```

Access at: http://localhost:5000

**Configuration:** The development server runs with `debug=True` by default. Edit `app.py` to change settings.

**Note:** You may see "Bad request version" errors in the server log if someone tries to access the server via HTTPS (e.g., https://localhost:5000). This is normal - the development server only supports HTTP. The errors show TLS handshake bytes and can be safely ignored. For production with HTTPS support, use Gunicorn behind a reverse proxy (Apache/Nginx) or deploy with proper SSL certificates.

### Automated Installation Scripts

For production deployments, automated installation scripts are provided for both Apache2 and Nginx. These scripts handle all setup steps including dependencies, configuration, and service management.

**Apache2 Installation:**
```bash
cd flask_app
sudo bash install-apache.sh
```

**Nginx Installation:**
```bash
cd flask_app
sudo bash install-nginx.sh
```

Both scripts support SSL configuration with automatic Let's Encrypt certificates. Edit the configuration variables at the top of each script before running:
- `DOMAIN` - Your server domain name
- `INSTALL_DIR` - Installation directory (default: /var/www/occam)
- `ENABLE_SSL` - Set to "yes" for HTTPS
- `USE_CERTBOT` - Set to "yes" for automatic Let's Encrypt SSL certificates
- `CERTBOT_EMAIL` - Email for certificate renewal notifications (required if using Certbot)

The scripts will:
- Install all required system packages
- Install Python dependencies
- Copy application files
- Configure web server (Apache/Nginx)
- Set up systemd services for Gunicorn/Worker
- Configure and start Redis
- Set proper permissions
- Enable and start all services

See the scripts for full configuration options and customization.

**To uninstall:**
```bash
cd flask_app
sudo bash uninstall.sh
```

The uninstall script will safely remove all components with options to keep or remove data, packages, and SSL certificates.

### Manual Production Deployment

For manual installation or customization:

#### Option 1: Gunicorn (Recommended)
```bash
pip install gunicorn

# Run from flask_app/occam_server directory
cd flask_app/occam_server

# Run with 4 worker processes
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Or with auto-reload for development
gunicorn -w 4 -b 0.0.0.0:8000 --reload app:app
```

#### Option 2: Apache + mod_wsgi
1. Install mod_wsgi:
   ```bash
   sudo apt install libapache2-mod-wsgi-py3
   sudo a2enmod wsgi
   ```

2. Create WSGI file (`/var/www/occam/occam.wsgi`):
   ```python
   import sys
   import os

   # Ensure data directory exists
   data_dir = '/var/www/occam/data'
   os.makedirs(data_dir, exist_ok=True)

   from occam_server.app import app as application
   ```

3. Configure Apache virtual host:
   ```apache
   <VirtualHost *:80>
       ServerName occam.example.com

       WSGIDaemonProcess occam user=www-data group=www-data threads=5
       WSGIScriptAlias / /var/www/occam/occam.wsgi

       <Directory /var/www/occam>
           WSGIProcessGroup occam
           WSGIApplicationGroup %{GLOBAL}
           Require all granted
       </Directory>

       # Static files
       Alias /static /var/www/occam/static
       <Directory /var/www/occam/static>
           Require all granted
       </Directory>

       # Data directory (write access needed)
       <Directory /var/www/occam/data>
           Require all denied
       </Directory>
   </VirtualHost>
   ```

4. Set permissions:
   ```bash
   sudo chown -R www-data:www-data /var/www/occam/data
   sudo chmod 775 /var/www/occam/data
   ```

#### Option 3: Docker (Future)

See `../podman/` directory for containerization setup.

## Batch Processing

The Flask server supports batch job processing for long-running OCCAM analyses with email notifications when jobs complete. This uses Redis Queue (RQ) for background job management.

### Setup Requirements

**1. Install Redis Server**
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# macOS
brew install redis
brew services start redis
```

**2. Install Python Dependencies**
```bash
cd flask_app
pip install redis rq
# Or use requirements.txt which includes these
pip install -r requirements.txt
```

**3. Configure Email (Optional)**

Set environment variables for SMTP email notifications:
```bash
export SMTP_HOST=localhost
export SMTP_PORT=25
export SMTP_USER=your_email@example.com
export SMTP_PASSWORD=your_password
export SMTP_FROM=noreply@occam.example.com
```

Or create a `.env` file:
```bash
# Email configuration for batch job notifications
SMTP_HOST=localhost
SMTP_PORT=25
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@occam.local

# Redis configuration (optional, defaults to localhost)
REDIS_URL=redis://localhost:6379/0
```

**4. Start RQ Worker**

The RQ worker processes batch jobs in the background:
```bash
cd flask_app/occam_server
python3 worker.py
```

For production, run the worker as a service or use a process manager:
```bash
# Using systemd (example service file)
# /etc/systemd/system/occam-worker.service
[Unit]
Description=OCCAM RQ Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/occam
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="SMTP_HOST=localhost"
ExecStart=/usr/bin/python3 worker.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Using Batch Processing

**Submit a Batch Job:**
1. Navigate to http://localhost:5000/batch
2. Select action (fit, search, SBfit, SBsearch)
3. Upload data file (.txt or .zip)
4. Enter model specification (optional for fit, required for search)
5. **Enter your email address** (required for notifications)
6. Configure advanced options (separator, alpha, search levels, etc.)
7. Click "Submit Batch Job"

**Monitor Jobs:**
- View all jobs: http://localhost:5000/batch/jobs
- View specific job: http://localhost:5000/batch/job/<job_id>
- Jobs show status: Queued → Running → Completed/Failed
- Refresh the page to see updated status

**Email Notifications:**
- Receive email when job completes or fails
- Email includes job ID, action, timestamps, and status
- For completed jobs, results are available via the web interface

**Job Results:**
- Results are kept for 24 hours after completion
- Access via job status page or job list
- Download or view results directly in browser

### Architecture

The batch processing system uses:
- **Redis**: In-memory data store for job queue and metadata
- **RQ (Redis Queue)**: Lightweight Python job queue
- **Worker Process**: Separate Python process that executes jobs
- **SMTP**: Email notifications (optional but recommended)

Jobs are processed asynchronously, allowing the web server to handle multiple requests while long-running analyses execute in the background.

### Troubleshooting

**Worker Not Processing Jobs:**
- Check Redis is running: `redis-cli ping` (should return PONG)
- Check worker is running: `ps aux | grep worker.py`
- Check worker logs for errors

**Email Not Sending:**
- Verify SMTP configuration in environment variables
- Check SMTP server is accessible
- Review worker logs for email errors
- Email failures don't affect job processing

**Jobs Stuck in Queued:**
- Ensure worker is running
- Check Redis connection: `redis-cli` then `KEYS job:*`
- Restart worker if needed

## Migration Notes

### Differences from CGI Version

1. **No stdout printing**: Use Flask's `return` instead of `print`
2. **File uploads**: Use `request.files` instead of `cgi.FieldStorage()`
3. **Form data**: Use `request.form` instead of form fields dictionary
4. **Templates**: Jinja2 replaces OpagCGI string replacement
5. **Sessions**: Can use Flask sessions for batch jobs instead of files

### API Compatibility

The `OccamManager` class in `occam_wrapper.py` provides compatibility with the old `ocutils.ocUtils` API:

| Old API (ocutils.py) | New API (occam_wrapper.py) | Notes |
|---------------------|---------------------------|-------|
| `ocUtils("VB")` | `OccamManager("VB")` | Same interface |
| `initFromCommandLine()` | `init_from_command_line()` | Python naming |
| `setReportSeparator()` | `set_report_separator()` | Python naming |
| `doAction()` | `do_fit()` / `do_search()` | Explicit methods |

## Known Limitations

The current implementation provides full OCCAM functionality for both interactive and batch processing. The following legacy CGI features are not implemented as they're not essential for modern usage:

1. **Cached data forms**: Legacy browser optimization; modern connections and caching make this unnecessary.

## Testing

### Manual Testing

Test the Flask server with example data:
```bash
# Start development server
cd flask_app/occam_server
python3 app.py

# In browser, navigate to http://localhost:5000
# 1. Upload an example file from static/examples/ (e.g., fit.in, search.in)
# 2. Test VB fit operation
# 3. Test VB search operation
# 4. Test SB fit operation
# 5. Test SB search operation
# 6. Test graph generation (if python-igraph installed)
```

### Example Test Sequence

```bash
# Start server
cd flask_app/occam_server
python3 app.py &

# Test basic functionality
curl http://localhost:5000/  # Should return landing page

# Test with example data (in browser)
# 1. Visit http://localhost:5000
# 2. Click "Choose File" and select one of the example files (e.g., fit.in)
# 3. Select action (fit, search, etc.)
# 4. Click "Submit"
# 5. Verify output shows analysis results
```

### Unit Tests (Future)

Future enhancements could include:
- pytest tests for route handlers
- Mock tests for _pyoccam integration
- Integration tests for file upload/processing
- Template rendering tests

## Future Enhancements

**Production Hardening:**
1. Implement CSRF protection for forms
2. Add rate limiting for API endpoints
3. Implement user authentication (if needed for private deployments)

**Analysis Features:**
4. PDF export for graph visualizations
5. Session-based analysis history
6. Comparison tools for multiple models

**Advanced (Low Priority):**
7. API endpoints for programmatic access
8. WebSocket support for real-time progress updates on batch jobs
9. Database backend for persistent job history (replace Redis TTL)

**Note:** The core OCCAM functionality including batch processing is complete. These enhancements are optional and depend on specific deployment needs.
