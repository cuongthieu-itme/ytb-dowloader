#!/bin/bash
set -e

# Use Docker-specific settings
export DJANGO_SETTINGS_MODULE=ytb_downloader.settings_docker

# Create necessary directories
mkdir -p /app/media
mkdir -p /app/static

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Django application
echo "Starting application..."
exec "$@"
