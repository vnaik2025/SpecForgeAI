#!/usr/bin/env bash
# Build script for Vercel deployment
set -e

echo "Building static files for Vercel..."
python manage.py collectstatic --noinput --clear
echo "Static collection complete."
