#!/usr/bin/env bash
set -e

python manage.py collectstatic --no-input

# Same rationale as the main HRMSv2 app: migrations run once per deploy via
# a dedicated step, not on every replica's startup, so a rolling restart
# during a deploy can't race a schema change. Set RUN_MIGRATIONS_ON_START=1
# for local/dev containers where there's no separate migrate step.
if [ "${RUN_MIGRATIONS_ON_START:-0}" = "1" ]; then
  echo "RUN_MIGRATIONS_ON_START=1 — applying migrations from the entrypoint"
  python manage.py migrate --no-input
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2
