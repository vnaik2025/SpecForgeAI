#!/usr/bin/env bash
# Build script for Vercel deployment
set -e

# Detect python executable
if command -v python3 &>/dev/null; then
    PY="python3"
else
    PY="python"
fi

echo "Installing project dependencies using $PY..."
$PY -m pip install -r requirements.txt

echo "Collecting static files..."
$PY manage.py collectstatic --noinput --clear

echo "Static files build complete."
