#!/bin/sh
set -e
python manage.py migrate --noinput 2>/dev/null || true
python scripts/init_admin.py 2>/dev/null || true
exec "$@"
