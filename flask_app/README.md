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
├── app.py                 # Main Flask application
├── occam_wrapper.py       # Compatibility wrapper for _pyoccam
├── ocGraph.py             # Graph generation (Python 3 port)
├── utils.py               # Utility functions (file handling, etc.)
├── requirements.txt       # Python dependencies
├── templates/             # Jinja2 templates
│   ├── base.html         # Base template with PSU branding
│   ├── index.html        # Landing page
│   ├── error.html        # Error display
│   ├── main_form.html    # Main input form
│   └── ...               # Result templates (fit, search, sbfit, sbsearch)
└── static/               # Static assets (CSS, images)
    ├── base.css
    ├── style.css
    ├── occam_logo.jpg
    └── examples/
```

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

1. Install Python 3 and dependencies:
   ```bash
   cd flask_app
   pip install -r requirements.txt
   ```

   Note: Graph generation requires `python-igraph` and `pycairo`. If these fail to install, graph generation will be disabled but all other features will work.

2. Install pyoccam module:
   ```bash
   # Option A: Install from prebuilt wheel
   pip install ../pyoccam/wheels/pyoccam-0.1.0-cp3*-linux_x86_64.whl

   # Option B: Build from source (requires pybind11, GMP, etc.)
   cd ../pyoccam
   # TODO: Add build instructions
   ```

3. Copy static assets:
   ```bash
   mkdir -p static
   cp ../html/base.css static/
   cp ../html/occam_logo.jpg static/
   cp -r ../examples static/
   ```

4. Create data directory:
   ```bash
   mkdir data
   chmod 775 data
   ```

## Running

### Development Server
```bash
python3 app.py
```

Access at: http://localhost:5000

### Production Deployment

#### Option 1: Gunicorn (Recommended)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

#### Option 2: Apache + mod_wsgi
1. Install mod_wsgi:
   ```bash
   apt install libapache2-mod-wsgi-py3
   a2enmod wsgi
   ```

2. Create WSGI file (`occam.wsgi`):
   ```python
   import sys
   sys.path.insert(0, '/path/to/flask_app')
   from app import app as application
   ```

3. Configure Apache virtual host:
   ```apache
   <VirtualHost *:80>
       ServerName occam.example.com
       WSGIDaemonProcess occam python-path=/path/to/flask_app
       WSGIScriptAlias / /path/to/flask_app/occam.wsgi

       <Directory /path/to/flask_app>
           WSGIProcessGroup occam
           WSGIApplicationGroup %{GLOBAL}
           Require all granted
       </Directory>
   </VirtualHost>
   ```

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

## Testing

TODO: Add testing instructions once basic functionality is working

## Known Issues

1. **SBMManager not implemented**: State-based modeling requires pybind11 implementation
2. **Job control**: Background job management needs adaptation for Flask
3. **Email functionality**: Batch job email needs SMTP configuration
4. **Graph generation**: ocGraph.py integration pending

## Next Steps

See [../pyoccam/PORTING_STATUS.md](../pyoccam/PORTING_STATUS.md) for pybind11 binding completion status.

Priority tasks:
1. Add SBMManager to pyoccam_pybind11.cpp
2. Complete all Jinja2 templates
3. Implement all route handlers
4. Test with real OCCAM data files
5. Deploy and performance test
