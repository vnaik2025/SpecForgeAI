#!/bin/sh
set -e

echo "==> [SpecForge AI] Applying database migrations..."
python manage.py migrate --noinput

echo "==> [SpecForge AI] Seeding initial production user accounts..."
python manage.py seed_users || true

PORT="${PORT:-8000}"
echo "==> [SpecForge AI] Launching Gunicorn on 0.0.0.0:$PORT..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:$PORT" --workers 2 --timeout 120
