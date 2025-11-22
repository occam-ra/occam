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
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create build directory
WORKDIR /build

# Copy source code
COPY .. /build/

# Build OCCAM C++ library and CLI
RUN meson setup builddir && \
    ninja -C builddir

# Build Python wheels using pip wheel (avoids sdist issue with parent directory refs)
WORKDIR /build
RUN pip3 wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels ./pyoccam && \
    pip3 wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels ./flask_app

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

# Create app user (use UID 1001 to avoid conflict with ubuntu user)
RUN useradd -m -u 1001 -s /bin/bash occam && \
    mkdir -p /var/www/occam /var/log/supervisor

# Install Python wheels from builder
COPY --from=builder /tmp/wheels/*.whl /tmp/

# Install Python packages
RUN pip3 install --no-cache-dir --break-system-packages \
    /tmp/*.whl \
    gunicorn \
    redis \
    rq \
    && rm -rf /tmp/*.whl

# Copy OCCAM CLI from builder
COPY --from=builder /build/builddir/cpp/occ /usr/local/bin/occ

# Copy Flask application
COPY flask_app/occam_server /var/www/occam/occam_server

# Create necessary directories
RUN mkdir -p /var/www/occam/data /var/www/occam/logs && \
    chown -R occam:occam /var/www/occam && \
    chmod 775 /var/www/occam/data

# Copy supervisor configuration
COPY podman/supervisord.conf /etc/supervisor/conf.d/occam.conf

# Copy gunicorn configuration
COPY podman/gunicorn_config.py /var/www/occam/gunicorn_config.py

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
