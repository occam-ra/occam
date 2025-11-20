#!/bin/bash
# Setup script to copy static assets from html/ directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_DIR="$(dirname "$SCRIPT_DIR")/html"
STATIC_DIR="$SCRIPT_DIR/static"
EXAMPLES_DIR="$HTML_DIR/../examples"

echo "Setting up static assets for Flask app..."

# Create static directory if it doesn't exist
mkdir -p "$STATIC_DIR"
mkdir -p "$STATIC_DIR/examples"

# Copy CSS
if [ -f "$HTML_DIR/base.css" ]; then
    echo "Copying base.css..."
    cp "$HTML_DIR/base.css" "$STATIC_DIR/"
else
    echo "Warning: base.css not found in $HTML_DIR"
fi

# Copy logo
if [ -f "$HTML_DIR/occam_logo.jpg" ]; then
    echo "Copying occam_logo.jpg..."
    cp "$HTML_DIR/occam_logo.jpg" "$STATIC_DIR/"
else
    echo "Warning: occam_logo.jpg not found in $HTML_DIR"
fi

# Copy example files
if [ -d "$EXAMPLES_DIR" ]; then
    echo "Copying example data files..."
    cp "$EXAMPLES_DIR"/*.in "$STATIC_DIR/examples/" 2>/dev/null || echo "No .in files found"
else
    echo "Warning: examples directory not found at $EXAMPLES_DIR"
fi

# Verify style.css exists
if [ ! -f "$STATIC_DIR/style.css" ]; then
    echo "Warning: style.css not found in static directory"
fi

echo "Static assets setup complete!"
echo "Static directory: $STATIC_DIR"
ls -la "$STATIC_DIR"
