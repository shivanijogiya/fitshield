#!/bin/sh
# entrypoint.sh – runs inside the Django container on every start.
# Waits for the database, applies migrations, seeds data, then starts the server.

set -e

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Seeding database (skipped if data already exists)..."
python manage.py seed_meals

echo "==> Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
