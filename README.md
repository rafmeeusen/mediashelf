# MediaShelf

Books, films, series all on one shelf.

A self-hosted, single-user app for tracking movies, books, TV series, and
podcasts you still want to consume or have already consumed — with ratings,
notes, and metadata enrichment from TMDB, Open Library, and iTunes.

Open `/` for the web UI (live search + filters, mobile and desktop
friendly), or browse the JSON API directly via the auto-generated docs at
`/docs`.

## Prerequisites

- An existing PostgreSQL database and role, e.g.:
  ```sql
  CREATE USER media_user WITH PASSWORD 'choose-a-password';
  CREATE DATABASE media_db OWNER media_user;
  ```
- Docker and Docker Compose.

## Setup

1. Copy `.env.example` to `.env` and fill in `DATABASE_URL` (pointing at your
   Postgres instance), `DB_SCHEMA` (the app lives in its own schema, not
   `public` — see below), `PORT` (which port the app listens on), and,
   optionally, `TMDB_API_KEY` (needed for movie/TV search — get one free at
   https://www.themoviedb.org/settings/api). Open Library and iTunes need no
   key.
2. Build the image:
   ```
   docker compose build
   ```
3. Apply database migrations:
   ```
   docker compose run --rm app uv run --no-sync alembic upgrade head
   ```
4. Start the app:
   ```
   docker compose up -d
   ```
5. Open http://localhost:8087/docs (or whichever `PORT` you set) for the
   interactive API docs — also reachable from other machines on your LAN at
   `http://<this-machine's-IP>:8087/docs`.

The app runs with `network_mode: host` so the same `DATABASE_URL` (e.g.
`localhost`) works whether Postgres is reached from inside the container or
from a native/local run — no separate hostname needed. Because of
`network_mode: host`, the app binds directly to `PORT` on every network
interface (LAN included) — put it behind a firewall/VPN if that's not what
you want.

### Why a dedicated schema

All of MediaShelf's tables live in the `DB_SCHEMA` schema (default
`mediashelf`) inside your database, not in Postgres's default `public`
schema — so it stays cleanly separated from anything else you keep in that
database, and can be dumped/restored independently (see Backups below). The
app's engine sets the connection's `search_path` to this schema
(`app/db.py`), and Alembic (`migrations/env.py`) reuses that same engine so
migrations always target the same place the app reads from. Nothing on the
model layer hardcodes a schema name — moving to a different `DB_SCHEMA`
later only means updating `.env` and physically moving the tables (see
`scripts/move_to_mediashelf_schema.sql` for the one-time move this project
itself went through, using Postgres's `ALTER ... SET SCHEMA`, which
relocates existing tables/data/sequences/types in place — no dump/restore
needed for that).

## Local development (without Docker)

```
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run pytest
```

Tests run against the same database as `DATABASE_URL`, but inside an
isolated `test` Postgres schema (dropped and recreated automatically each
test session) — no separate test database needed.

## Web UI

`/` is a server-rendered page (`app/templates/`) using [htmx](https://htmx.org)
for interactivity, vendored locally at `app/static/htmx.min.js` (no CDN
dependency, no build step, no npm). The search box and type/status/genre
filters live-update the results via `GET /ui/items`, which renders just the
`app/templates/_item_list.html` fragment and htmx swaps it into the page —
debounced 300ms while typing, faster on dropdown changes (see the
`hx-trigger` on the `<form>` in `app/templates/index.html`).

This pattern is what future pieces (add a new item, edit a field in place)
should follow: a small route in `app/routers/ui.py` that accepts form input,
calls the existing `app/services/` functions (same ones the JSON API uses),
and returns a small HTML fragment to swap in — no new frontend framework or
duplicated business logic needed as the UI grows.

Styling is a single plain stylesheet (`app/static/style.css`), mobile-first
with a breakpoint at 640px for wider screens — no CSS framework.

## API overview

- `GET/POST /items`, `GET/PATCH/DELETE /items/{id}` — manage tracked items
  (movies, books, TV, podcasts). `PATCH` is how you mark something done,
  set a rating (1-10), or add notes.
- `POST /items/from-search` — create an item directly from a metadata
  search result.
- `PUT/DELETE /items/{id}/platforms/{platform_id}` — record whether an item
  is available on a given platform (e.g. a library or streaming service),
  mainly useful for items you haven't consumed yet.
- `POST/DELETE /items/{id}/genres/{genre_id}` — tag an item with a genre
  (e.g. "Documentary", "Comedy") — orthogonal to `content_type`: a movie can
  be a Documentary, a Comedy, both, or neither. Mirrors how IMDb separates
  title type (movie/tvSeries/...) from its genre list.
- `GET/POST/DELETE /languages`, `GET/POST/DELETE /platforms`,
  `GET/POST/DELETE /genres` — manage the lookup lists referenced by items.
  All start empty; add entries as you need them.
- `GET /items?genre=documentary` — filter items by genre (also filterable
  by `content_type` and `status`).
- `GET /search/movies|tv|books|podcasts?q=...` — search external metadata
  providers (TMDB, Open Library, iTunes) to enrich a new item.

Example: create a book, mark it as available at two platforms, then mark it
read.

```
curl -X POST localhost:8087/items -H "Content-Type: application/json" -d \
  '{"content_type": "book", "title": "Mislukte staten", "creator": "Noam Chomsky"}'

curl -X PUT localhost:8087/items/1/platforms/1 -d '{"available": true}'
curl -X PUT localhost:8087/items/1/platforms/2 -d '{"available": false}'

curl -X PATCH localhost:8087/items/1 -d \
  '{"status": "done", "rating": 8, "completed_date": "2026-09-19"}'
```

## Bulk importing your backlog

Write your list into `data/import.txt` (see `data/import.example.txt` for
the field reference — it's a lightweight `key: value` block format, one
entry per block). Then:

```
uv run python scripts/import_items.py data/import.txt            # dry run / preview
uv run python scripts/import_items.py data/import.txt --apply    # actually import
```

The dry run parses the file, prints a full preview with any warnings, and
writes nothing — review it before re-running with `--apply`. Referenced
languages/platforms/genres are created automatically if they don't exist
yet.

## Backups

`scripts/backup_db.sh` dumps only the `DB_SCHEMA` schema (custom `pg_dump`
format — compressed, supports selective restore) via a disposable
`postgres:16-alpine` container, so no Postgres client tools need to be
installed on the host, and nothing else that might live in the same
database gets swept in. It reads `DATABASE_URL`/`DB_SCHEMA` from `.env`.

```
scripts/backup_db.sh
```

- Writes to `~/backups/mediashelf/<dbname>_<timestamp>.dump` (override with
  `MEDIASHELF_BACKUP_DIR`).
- Prunes dumps older than 30 days automatically (override with
  `MEDIASHELF_BACKUP_RETENTION_DAYS`).
- Scheduled via cron, daily at 3am:
  ```
  0 3 * * * /home/raf/repo/mediashelf/scripts/backup_db.sh >> /home/raf/backups/mediashelf/backup.log 2>&1
  ```
  Check/edit with `crontab -e`; view history in `~/backups/mediashelf/backup.log`.

These backups only live on this machine — copy them elsewhere (another
disk, a NAS, cloud storage) for real disaster recovery; a single-host copy
doesn't protect against disk/host failure.

**Restore** (into an existing, empty-or-overwritable database):

```
docker run --rm -v ~/backups/mediashelf:/backup --network host \
  -e PGPASSWORD=<password> postgres:16-alpine \
  pg_restore -h localhost -p 5432 -U media_user -d media_db --clean --if-exists \
  /backup/<dump-file>.dump
```

`--clean --if-exists` drops existing objects before recreating them, so this
is safe to run against the live database to roll back to a backup.

### Testing a restore without touching production

`scripts/restore_test.sh` proves a backup is actually restorable, without a
second database (`media_user` has no `CREATEDB` privilege — but schema-level
`CREATE` already works, the same trick the test suite uses). It restores the
most recent backup into a throwaway `mediashelf_restore_test` schema in the
same database, verifies every table's row count matches the live schema
exactly, then drops the test schema again:

```
scripts/restore_test.sh              # uses the newest backup, cleans up after itself
scripts/restore_test.sh --keep       # leaves mediashelf_restore_test in place to inspect manually
scripts/restore_test.sh path/to/some-older-backup.dump
```

A `pg_dump` archive always bakes in the exact schema name it came from —
there's no `pg_restore` flag to remap it — so this works by converting the
dump to plain SQL and substituting the schema name before applying it.
