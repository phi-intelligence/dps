#!/bin/sh
set -e

# Default: persistent volume path (override with DATABASE_URL)
export DATABASE_URL="${DATABASE_URL:-file:/data/dev.db}"

# Path on disk after stripping file: prefix
db_path="${DATABASE_URL#file:}"

if [ ! -f "$db_path" ]; then
  parent=$(dirname "$db_path")
  if [ "$parent" != "." ] && [ "$parent" != "/" ]; then
    mkdir -p "$parent" 2>/dev/null || true
  fi
  if [ -f /app/db-init/dev.db ]; then
    echo "[entrypoint] Creating SQLite database at $db_path (schema from image)."
    cp /app/db-init/dev.db "$db_path"
  else
    echo "[entrypoint] Warning: missing /app/db-init/dev.db — create the DB or mount one."
  fi
fi

exec node server.js
