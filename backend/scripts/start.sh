#!/usr/bin/env bash
set -euo pipefail

echo "Aplicando migraciones..."
alembic upgrade head

echo "Iniciando API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
