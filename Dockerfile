FROM python:3.10.14-slim-bookworm AS app

LABEL maintainer="Gavin Mason gavin@rawcsav.com"

WORKDIR /rawcon

ARG UID=1000
ARG GID=1000

# Install system dependencies and create user
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libpq-dev \
    && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man \
    && apt-get clean \
    && groupadd -g "${GID}" rawcon \
    && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" rawcon \
    && chown rawcon:rawcon -R /rawcon

# Switch to non-root user
USER rawcon

# Copy requirements file and install dependencies
COPY --chown=rawcon:rawcon requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=wsgi.py \
    FLASK_DEBUG=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/rawcon/.local/bin:${PATH}" \
    USER="rawcon"

# Copy the rest of the application
COPY --chown=rawcon:rawcon . .

# Set proper permissions
RUN chmod -R 755 /rawcon

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8081/health || exit 1

# Set the command
CMD ["gunicorn", "--workers", "1", "--timeout", "90", "--bind", "0.0.0.0:8081", "wsgi:app", "--log-level=debug"]