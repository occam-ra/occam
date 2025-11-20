# OCCAM Python 2 → Python 3 Flask Migration Summary

## Overview

This document summarizes the work done to migrate the OCCAM web server from Python 2 CGI to Python 3 Flask, using the modern pybind11 bindings from the `pyoccam-port` branch.

## Project Structure

```
occam/
├── cpp/pyoccam.cpp              # Original Python 2 C API bindings
├── pyoccam/
│   ├── pyoccam_pybind11.cpp    # New Python 3 pybind11 bindings ✅
│   ├── wheels/                  # Prebuilt wheels for multiple platforms
│   ├── PORTING_STATUS.md        # Detailed status of C++ bindings
│   └── README.md
├── py/
│   ├── weboccam.py              # Original Python 2 CGI server
│   ├── ocutils.py               # Original OCCAM wrapper
│   └── OpagCGI.py               # Original template engine
├── html/                        # Original HTML templates
└── flask_app/                   # NEW: Python 3 Flask server ✅
    ├── app.py                   # Main Flask application
    ├── occam_wrapper.py         # Compatibility wrapper for _pyoccam
    ├── utils.py                 # Utility functions
    ├── requirements.txt
    ├── templates/               # Jinja2 templates
    └── README.md
```

## What Was Completed ✅

### 1. Analyzed Existing Codebase
- Mapped all routes and actions from original weboccam.py
- Identified dependencies and functionality
- Documented valid actions:
  - Common: `fit`, `search`, `SBsearch`, `SBfit`
  - Form: `compare`, `log`, `fitbatch`
  - Control: `jobcontrol`

### 2. Reviewed Python 3 Bindings
- Analyzed `pyoccam_pybind11.cpp` (872 lines)
- Documented what's implemented:
  - ✅ PyVBMManager with full functionality
  - ✅ PyModel with test data support
  - ✅ Beam search implementation
  - ✅ Fit and search report generation
- Created `pyoccam/PORTING_STATUS.md` documenting gaps

### 3. Created Flask Application Structure
**File: `flask_app/app.py`**
- Route handling for all OCCAM actions
- File upload processing
- Security validation (action allowlist)
- Error handling
- Development and production server support

**Features:**
- Uses Flask instead of CGI
- Werkzeug for secure file handling
- Jinja2 templating
- Proper MIME types and file downloads
- Session management ready

### 4. Built Compatibility Wrapper
**File: `flask_app/occam_wrapper.py`**
- `OccamManager` class providing ocutils.py-compatible API
- Wraps `_pyoccam.VBMManager` with familiar interface
- Configuration methods matching old API
- `do_fit()` and `do_search()` operations
- Constants (TABSEP, COMMASEP, HTMLFORMAT)

This allows minimal changes to port existing code:
```python
# Old way (Python 2)
from ocutils import ocUtils
oc = ocUtils("VB")

# New way (Python 3)
from occam_wrapper import OccamManager
oc = OccamManager("VB")
```

### 5. Created Utility Functions
**File: `flask_app/utils.py`**
- `get_unique_filename()` - tempfile-based unique names
- `get_timestamped_filename()` - timestamp-based naming
- `unzip_data_file()` - handle zip uploads
- `prepare_cached_data()` - cached data assembly
- `get_data_filename()` - filename extraction

### 6. Started Jinja2 Templates
**Files in `flask_app/templates/`:**
- `base.html` - Base template with PSU branding
- `index.html` - Landing page
- `error.html` - Error display

Templates use:
- Template inheritance (`{% extends %}`)
- Variable substitution (`{{ variable }}`)
- URL generation (`{{ url_for() }}`)
- Conditional rendering (`{% if %}`)

### 7. Documentation
- `flask_app/README.md` - Complete setup and deployment guide
- `pyoccam/PORTING_STATUS.md` - C++ bindings status
- Installation instructions
- Testing guidelines
- Migration notes

## What Still Needs Work ❌

### High Priority

#### 1. Add SBMManager to pybind11 Bindings
**File to modify: `pyoccam/pyoccam_pybind11.cpp`**

The original `cpp/pyoccam.cpp` exposes both VBMManager and SBMManager. Currently, only VBMManager is in pybind11.

**What's needed:**
```cpp
// Add to pyoccam_pybind11.cpp

class PySBMManager {
    private:
        SBMManager manager;
    public:
        // Similar methods to PyVBMManager
        bool init_from_command_line(const std::vector<std::string>& args);
        std::string generate_search_report(...);
        std::string generate_fit_report(...);
        // ... etc
};

// Add to module definition
PYBIND11_MODULE(_pyoccam, m) {
    // ... existing code ...

    py::class_<PySBMManager>(m, "SBMManager")
        .def(py::init<>())
        .def("init_from_command_line", &PySBMManager::init_from_command_line)
        // ... etc
        ;
}
```

**Impact:** Without this, SBfit and SBsearch actions won't work.

#### 2. Complete Flask Route Handlers
**File to complete: `flask_app/app.py`**

Currently stubbed out:
- `handle_fit_text()` - CSV output for fit
- `handle_search()` - Model search
- `handle_sb_fit()` - State-based fit
- `handle_sb_search()` - State-based search
- `handle_fit_batch()` - Batch processing
- `handle_batch_compare()` - Batch comparison
- `handle_show_log()` - Log display
- `handle_job_control()` - Job management

#### 3. Convert HTML Templates to Jinja2
**Files to create in `flask_app/templates/`:**

From `html/`:
- `main_form.html` (from switchform.html + formheader.html)
- `fit_form.html` (from fit.template.html)
- `search_form.html` (from search.template.html)
- `sbfit_form.html` (from SBfit.template.html)
- `sbsearch_form.html` (from SBsearch.template.html)
- `compare_form.html` (from compareform.html)
- `log_form.html` (from logform.html)
- `fitbatch_form.html` (from fitbatchform.html)
- `fit_result.html` (result display)
- `search_result.html` (result display)

Template conversion pattern:
```html
<!-- Old (OpagCGI) -->
<input name="model" value="{model}">

<!-- New (Jinja2) -->
<input name="model" value="{{ model }}">
```

### Medium Priority

#### 4. Graph Generation Integration
- Port `ocGraph.py` to Python 3
- Integrate SVG/PDF generation
- Gephi export functionality
- Graph options in forms

#### 5. Job Control
- Background job management for Flask
- Process listing and killing
- Job status tracking
- Adapt from current ps-based approach

#### 6. Batch Processing
- Email integration
- Background task queue (Celery?)
- Log file management
- Progress tracking

### Lower Priority

#### 7. Testing
- Unit tests for utils and wrapper
- Integration tests for routes
- Test with real OCCAM data files
- Performance testing

#### 8. Deployment
- Production WSGI configuration
- Apache/Nginx setup
- Docker containerization
- Security hardening

## Quick Start for Continuation

### 1. Add SBMManager to C++ Bindings

```bash
cd /usr/local/src/occam
git checkout pyoccam-port
cd pyoccam

# Edit pyoccam_pybind11.cpp
# Add PySBMManager class (copy pattern from PyVBMManager)
# Add to PYBIND11_MODULE definition

# Build (requires pybind11, GMP, etc.)
# TODO: Add build instructions
```

### 2. Test Current Flask App

```bash
cd /usr/local/src/occam/flask_app

# Install dependencies
pip3 install -r requirements.txt

# Install pyoccam from wheel
pip3 install ../pyoccam/wheels/pyoccam-0.1.0-cp3*-linux_x86_64.whl

# Copy static assets
mkdir -p static
cp ../html/base.css static/
cp ../html/occam_logo.jpg static/

# Create data directory
mkdir -p data

# Run development server
python3 app.py

# Access at http://localhost:5000
```

### 3. Complete Route Handlers

Edit `flask_app/app.py` and implement the stubbed functions following the pattern in `handle_fit_html()`.

### 4. Convert Templates

For each HTML template in `html/`, create a Jinja2 version in `flask_app/templates/`:

1. Replace `{variable}` with `{{ variable }}`
2. Add `{% extends "base.html" %}` and `{% block content %}`
3. Use `{{ url_for('route_name') }}` for URLs
4. Replace form action with Flask route

## Architecture Decisions

### Why Flask?
- Modern, well-supported Python 3 framework
- Much simpler than Django for this use case
- Easy deployment options (Gunicorn, mod_wsgi)
- Built-in development server
- Excellent documentation

### Why Wrapper Class?
- Minimizes changes to business logic
- Provides migration path
- Can swap implementations easily
- Familiar API for existing code

### Why pybind11?
- Modern C++11 bindings
- Automatic type conversion
- Better error messages
- Python 3 native
- Active development

## Success Criteria

The Flask server will be complete when:
1. ✅ All routes handle GET and POST correctly
2. ✅ File uploads work (data, zip files)
3. ✅ VB fit and search operations work
4. ✅ SB fit and search operations work (requires SBMManager)
5. ✅ Reports generate in HTML and CSV formats
6. ✅ Graphs generate (SVG, PDF, Gephi)
7. ✅ User interface matches original exactly
8. ✅ All example files process correctly
9. ✅ Batch operations work
10. ✅ Job control works

## References

- Original web server: `py/weboccam.py`
- Original wrapper: `py/ocutils.py`
- Original bindings: `cpp/pyoccam.cpp`
- New bindings: `pyoccam/pyoccam_pybind11.cpp`
- Flask docs: https://flask.palletsprojects.com/
- pybind11 docs: https://pybind11.readthedocs.io/

## Contact

For questions about this migration:
- Review the code in `flask_app/`
- Check `pyoccam/PORTING_STATUS.md` for C++ binding status
- See original weboccam.py for reference implementation
