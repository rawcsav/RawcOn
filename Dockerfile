FROM python:3.10.14-slim-bookworm AS app

LABEL maintainer="Gavin Mason gavin@rawcsav.com"

WORKDIR /appuser

ARG UID=1000
ARG GID=1000

# Install system dependencies and create user
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libpq-dev \
    && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man \
    && apt-get clean \
    && groupadd -g "${GID}" appuser \
    && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" appuser \
    && chown appuser:appuser -R /appuser \

RUN mkdir -p /rawcon/celerybeat-schedule && \
    chown appuser:appuser /rawcon/celerybeat-schedule && \
    chmod 755 /rawcon/celerybeat-schedule \

# Switch to non-root user


ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copy requirements file and install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=wsgi.py \
    FLASK_DEBUG=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    USER="appuser"

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Set proper permissions
RUN chmod -R 755 /appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8081/health || exit 1

# Create directory for celerybeat schedule with correct permissions

# Set the command
CMD ["gunicorn", "--workers", "1", "--timeout", "90", "--bind", "0.0.0.0:8081", "wsgi:app"]