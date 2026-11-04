#!/usr/bin/env bash
# Ejecuta manage.py check y check --deploy (SCRUM-32 / review PR #17).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export USE_SQLITE_DEMO=True
export SECRET_KEY="${SECRET_KEY:-ci-check-only-not-for-production}"
export DEBUG=False

echo "== manage.py check (SQLite demo) =="
python manage.py check

export DJANGO_USE_HTTPS=True
export TRUST_X_FORWARDED_PROTO=True
export CSRF_TRUSTED_ORIGINS=https://example.com
export ALLOWED_HOSTS=example.com

echo "== manage.py check --deploy (HTTPS + proxy) =="
python manage.py check --deploy

echo "OK: check y check --deploy completados."

# Desarrollado por: hcastro
