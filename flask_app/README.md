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
├── occam_server/          # Main package
│   ├── __init__.py       # Package initialization
│   ├── app.py            # Main Flask application
│   ├── occam_wrapper.py  # Compatibility wrapper for _pyoccam
│   ├── ocGraph.py        # Graph generation (Python 3 port)
│   ├── utils.py          # Utility functions (file handling, etc.)
│   ├── templates/        # Jinja2 templates
│   │   ├── base.html     # Base template with PSU branding
│   │   ├── index.html    # Landing page
│   │   ├── error.html    # Error display
│   │   ├── main_form.html # Main input form
│   │   └── ...           # Result templates (fit, search, sbfit, sbsearch)
│   └── static/           # Static assets (CSS, images)
│       ├── base.css
│       ├── style.css
│       ├── occam_logo.jpg
│       └── examples/
└── data/                  # Runtime data directory (created during setup)
```

The package is structured as a modern Python package using `pyproject.toml` for dependency management and build configuration.

## Status

### ✅ Completed
- Flask application structure with all core routes
- Variable-Based and State-Based modeling (VB and SB)
- Model fit and search operations
- Utility functions for file handling
- OccamManager wrapper providing ocutils.py-compatible API
- All Jinja2 templates (9 templates)
- Graph generation with SVG and Gephi export
- Job control functionality
- HTML and CSV output formats

### ❌ Not Implemented
- Batch job processing (requires background job queue)
- Email notifications (requires SMTP configuration)
- Cached data forms

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

### Production Deployment

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

## Known Issues

1. **Batch processing**: Requires background job queue (Celery/RQ) for async operations
2. **Email functionality**: Batch job email notifications need SMTP configuration
3. **Cached data forms**: Form for using cached data components not yet implemented

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

## Next Steps

Optional enhancements:
1. Implement Celery/RQ for background batch processing
2. Add email notification support via SMTP
3. Create cached data input forms
4. Add PDF graph download option
5. Implement CSRF protection for forms
6. Add session-based job tracking
