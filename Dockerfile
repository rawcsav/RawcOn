# Stage 1: Build dependencies
FROM python:3.10.14-slim-bookworm as builder

# Set build arguments
ARG UID=1000
ARG GID=1000

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app directory and user
RUN groupadd -g "${GID}" appuser && \
    useradd --create-home --no-log-init -u "${UID}" -g "${GID}" appuser

# Switch to non-root user
USER appuser
WORKDIR /build

# Install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN python -m venv /home/appuser/venv && \
    . /home/appuser/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.10.14-slim-bookworm

# Set build arguments
ARG UID=1000
ARG GID=1000

# Set environment variables
ENV FLASK_APP=wsgi.py \
    FLASK_DEBUG=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/venv/bin:${PATH}" \
    USER="appuser"

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean && \
    groupadd -g "${GID}" appuser && \
    useradd --create-home --no-log-init -u "${UID}" -g "${GID}" appuser && \
    mkdir -p /rawcon/celerybeat-schedule && \
    chown -R appuser:appuser /rawcon

# Switch to non-root user
USER appuser
WORKDIR /rawcon

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /home/appuser/venv /home/appuser/venv

# Copy application code
COPY --chown=appuser:appuser . .

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

LABEL maintainer="Gavin Mason gavin@rawcsav.com" \
      org.opencontainers.image.authors="Gavin Mason" \
      org.opencontainers.image.vendor="rawcsav"