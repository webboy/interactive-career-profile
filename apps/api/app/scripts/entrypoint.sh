#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

host="${DATABASE_HOST:-postgres}"
port="${DATABASE_PORT:-5432}"
user="${DATABASE_USER:-icp}"
database="${DATABASE_NAME:-icp}"

echo "Waiting for PostgreSQL at ${host}:${port}..."
until pg_isready -h "${host}" -p "${port}" -U "${user}" -d "${database}" >/dev/null 2>&1; do
  sleep 1
done

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
