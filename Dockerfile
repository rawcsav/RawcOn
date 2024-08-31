# Use Python image as the base image
FROM python:3.10

# Set the working directory
WORKDIR /rawcon

RUN chown -R www-data:www-data /rawcon

COPY requirements.txt /rawcon/

RUN apt-get update && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /rawcon

ENV FLASK_APP=wsgi.py

# Set the entrypoint
ENTRYPOINT ["gunicorn", "--workers", "1", "-t", "90", "--bind", "0.0.0.0:8081", "wsgi:app", "--log-level=debug"]