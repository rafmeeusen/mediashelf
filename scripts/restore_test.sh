#!/usr/bin/env bash
# Restore a MediaShelf backup into a throwaway schema in the SAME database,
# for testing/verifying backups actually work, without needing a second
# database (media_user has no CREATEDB privilege, but schema-level CREATE
# already works -- the same trick our test suite uses).
#
# A pg_dump archive always bakes in the exact schema name it was dumped
# from (pg_restore has no "restore into a different schema" flag), so this
# converts the dump to plain SQL and text-substitutes the schema name
# before applying it.
#
# Usage: scripts/restore_test.sh [dump-file] [--keep]
#   dump-file   defaults to the most recent backup in $MEDIASHELF_BACKUP_DIR
#   --keep      don't drop the test schema afterwards (for manual inspection)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${MEDIASHELF_BACKUP_DIR:-$HOME/backups/mediashelf}"
PG_IMAGE="postgres:16-alpine"
TEST_SCHEMA="mediashelf_restore_test"

KEEP=false
DUMP_FILE=""
for arg in "$@"; do
  if [ "$arg" = "--keep" ]; then KEEP=true; else DUMP_FILE="$arg"; fi
done

if [ -z "$DUMP_FILE" ]; then
  DUMP_FILE="$(ls -t "$BACKUP_DIR"/*.dump | head -1)"
fi
echo "Using dump file: $DUMP_FILE"

# shellcheck disable=SC1091
set -a; source "$REPO_DIR/.env"; set +a

url="${DATABASE_URL#postgresql+psycopg://}"
DB_USER="${url%%:*}"; rest="${url#*:}"
DB_PASSWORD="${rest%%@*}"; rest="${rest#*@}"
DB_HOST="${rest%%:*}"; rest="${rest#*:}"
DB_PORT="${rest%%/*}"
DB_NAME="${rest#*/}"
SOURCE_SCHEMA="${DB_SCHEMA:-mediashelf}"

pg() {
  docker run --rm -i --network host -e PGPASSWORD="$DB_PASSWORD" "$PG_IMAGE" \
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 "$@"
}

echo "Dropping any leftover $TEST_SCHEMA ..."
echo "DROP SCHEMA IF EXISTS $TEST_SCHEMA CASCADE;" | pg

echo "Converting dump to plain SQL and remapping $SOURCE_SCHEMA -> $TEST_SCHEMA ..."
docker run --rm -v "$BACKUP_DIR:/backup" "$PG_IMAGE" \
  pg_restore --no-owner -f - "/backup/$(basename "$DUMP_FILE")" \
  | sed -E "s/\b${SOURCE_SCHEMA}\b/${TEST_SCHEMA}/g" \
  | pg

echo
echo "Restored into schema '$TEST_SCHEMA'. Verifying row counts against '$SOURCE_SCHEMA' ..."
for table in languages platforms genres items item_platforms item_genres; do
  counts=$(echo "SELECT
      (SELECT count(*) FROM ${SOURCE_SCHEMA}.${table}),
      (SELECT count(*) FROM ${TEST_SCHEMA}.${table});" | pg -t -A -F' ')
  original=$(echo "$counts" | cut -d' ' -f1)
  restored=$(echo "$counts" | cut -d' ' -f2)
  if [ "$original" = "$restored" ]; then
    echo "  OK    $table: $original rows in both"
  else
    echo "  MISMATCH  $table: $original in $SOURCE_SCHEMA vs $restored in $TEST_SCHEMA"
  fi
done

if [ "$KEEP" = true ]; then
  echo
  echo "Kept schema '$TEST_SCHEMA' for inspection. Drop it later with:"
  echo "  echo 'DROP SCHEMA $TEST_SCHEMA CASCADE;' | <psql as above>"
else
  echo
  echo "Cleaning up: dropping $TEST_SCHEMA ..."
  echo "DROP SCHEMA IF EXISTS $TEST_SCHEMA CASCADE;" | pg
fi
