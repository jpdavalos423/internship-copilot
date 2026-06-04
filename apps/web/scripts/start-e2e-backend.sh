#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
API_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../../api" && pwd)

cd "$API_DIR"

: "${DJANGO_DB_NAME:=$API_DIR/e2e.sqlite3}"
export DJANGO_DB_NAME

uv run python manage.py migrate --noinput
uv run python manage.py flush --no-input
exec uv run python manage.py runserver 127.0.0.1:8100
