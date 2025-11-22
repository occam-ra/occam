# OCCAM Flask Web Server

Modern Python 3 Flask replacement for the legacy Python 2 CGI web server.

## Quick Start

```bash
cd flask_app
pip install .
occam-server --port 5000
```

## Documentation

For complete documentation, installation instructions, and deployment guides, see:

- **[docs/FLASK_README.md](../docs/FLASK_README.md)** - Complete Flask app documentation
- **[install/INSTALL.md](../install/INSTALL.md)** - Production installation guide
- **[install/QUICKSTART.md](../install/QUICKSTART.md)** - 5-minute setup guide
- **[docs/INSTALL.md](../docs/INSTALL.md)** - General OCCAM installation

## Installation Scripts

Automated installation scripts for production deployment:

```bash
cd install

# Apache2 + mod_wsgi
sudo bash install-apache.sh

# OR Nginx + Gunicorn
sudo bash install-nginx.sh

# Uninstall
sudo bash uninstall.sh
```

See [install/INSTALL.md](../install/INSTALL.md) for detailed instructions.

## Development

```bash
cd flask_app
pip install -e ".[dev]"
cd occam_server
python3 app.py
```

Access at: http://localhost:5000

## Features

- Variable-Based Modeling (VBM): fit and search operations
- State-Based Modeling (SBM): fit and search operations
- File upload (txt, zip)
- Graph generation (SVG, Gephi export)
- Batch job processing with Redis Queue
- Email notifications for batch jobs

## License

GPL v3 or later. See [LICENSE](../LICENSE) for details.
