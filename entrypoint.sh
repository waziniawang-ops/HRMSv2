#!/usr/bin/env bash
set -e

python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py seed_users

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2
