# OCCAM Web Server - Modern Flask Application Container
# Multi-stage build for efficient image size

# Build stage - compile OCCAM and build wheels
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    meson \
    ninja-build \
    libgmp-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create build directory
WORKDIR /build

# Copy source code
COPY .. /build/

# Build OCCAM C++ library and CLI
RUN meson setup builddir && \
    ninja -C builddir

# Build Python wheels
WORKDIR /build/pyoccam
RUN pip3 install --no-cache-dir build && \
    python3 -m build

WORKDIR /build/flask_app
RUN python3 -m build

# Runtime stage - minimal image with only runtime dependencies
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libgmp10 \
    redis-server \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 -s /bin/bash occam && \
    mkdir -p /var/www/occam /var/log/supervisor

# Install Python wheels from builder
COPY --from=builder /build/pyoccam/dist/*.whl /tmp/
COPY --from=builder /build/flask_app/dist/*.whl /tmp/

# Install Python packages
RUN pip3 install --no-cache-dir --break-system-packages \
    /tmp/*.whl \
    gunicorn \
    redis \
    rq \
    && rm -rf /tmp/*.whl

# Copy OCCAM CLI from builder
COPY --from=builder /build/builddir/occ /usr/local/bin/occ

# Copy Flask application
COPY flask_app/occam_server /var/www/occam/occam_server

# Create necessary directories
RUN mkdir -p /var/www/occam/data /var/www/occam/logs && \
    chown -R occam:occam /var/www/occam && \
    chmod 775 /var/www/occam/data

# Copy supervisor configuration
COPY podman/supervisord.conf /etc/supervisor/conf.d/occam.conf

# Copy entrypoint script
COPY podman/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Set working directory
WORKDIR /var/www/occam

# Use supervisor to manage processes
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
