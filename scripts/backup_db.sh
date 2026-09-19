#!/usr/bin/env bash
# Back up the MediaShelf Postgres database using a disposable postgres
# container (avoids needing pg_dump installed on the host).
#
# Usage: scripts/backup_db.sh
# Reads DATABASE_URL from .env in the repo root.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${MEDIASHELF_BACKUP_DIR:-$HOME/backups/mediashelf}"
RETENTION_DAYS="${MEDIASHELF_BACKUP_RETENTION_DAYS:-30}"
PG_IMAGE="postgres:16-alpine"

# shellcheck disable=SC1091
set -a; source "$REPO_DIR/.env"; set +a

# Parse postgresql+psycopg://user:pass@host:port/dbname
url="${DATABASE_URL#postgresql+psycopg://}"
DB_USER="${url%%:*}"; rest="${url#*:}"
DB_PASSWORD="${rest%%@*}"; rest="${rest#*@}"
DB_HOST="${rest%%:*}"; rest="${rest#*:}"
DB_PORT="${rest%%/*}"
DB_NAME="${rest#*/}"
SCHEMA="${DB_SCHEMA:-mediashelf}"

mkdir -p "$BACKUP_DIR"
timestamp="$(date +%Y%m%d_%H%M%S)"
dump_file="$BACKUP_DIR/${DB_NAME}_${timestamp}.dump"

echo "Backing up schema '$SCHEMA' of $DB_NAME to $dump_file ..."
docker run --rm \
  --network host \
  --user "$(id -u):$(id -g)" \
  -e PGPASSWORD="$DB_PASSWORD" \
  -v "$BACKUP_DIR:/backup" \
  "$PG_IMAGE" \
  pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -n "$SCHEMA" -F c -f "/backup/$(basename "$dump_file")" "$DB_NAME"

echo "Backup written: $dump_file ($(du -h "$dump_file" | cut -f1))"

echo "Pruning backups older than $RETENTION_DAYS days ..."
find "$BACKUP_DIR" -name "${DB_NAME}_*.dump" -mtime +"$RETENTION_DAYS" -print -delete

echo "Done. $(find "$BACKUP_DIR" -name "${DB_NAME}_*.dump" | wc -l) backup(s) retained in $BACKUP_DIR."
