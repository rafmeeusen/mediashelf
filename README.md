# MediaShelf

Books, films, series all on one shelf.

A self-hosted, single-user API for tracking movies, books, TV series, and
podcasts you still want to consume or have already consumed — with ratings,
notes, and metadata enrichment from TMDB, Open Library, and iTunes.

No UI yet: browse and try the API via the auto-generated docs at `/docs`.

## Prerequisites

- An existing PostgreSQL database and role, e.g.:
  ```sql
  CREATE USER media_user WITH PASSWORD 'choose-a-password';
  CREATE DATABASE media_db OWNER media_user;
  ```
- Docker and Docker Compose.

## Setup

1. Copy `.env.example` to `.env` and fill in `DATABASE_URL` (pointing at your
   Postgres instance) and, optionally, `TMDB_API_KEY` (needed for movie/TV
   search — get one free at https://www.themoviedb.org/settings/api). Open
   Library and iTunes need no key.
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
5. Open http://localhost:8000/docs for the interactive API docs.

The app runs with `network_mode: host` so the same `DATABASE_URL` (e.g.
`localhost`) works whether Postgres is reached from inside the container or
from a native/local run — no separate hostname needed.

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

## API overview

- `GET/POST /items`, `GET/PATCH/DELETE /items/{id}` — manage tracked items
  (movies, books, TV, podcasts). `PATCH` is how you mark something done,
  set a rating (1-10), or add notes.
- `POST /items/from-search` — create an item directly from a metadata
  search result.
- `PUT/DELETE /items/{id}/platforms/{platform_id}` — record whether an item
  is available on a given platform (e.g. a library or streaming service),
  mainly useful for items you haven't consumed yet.
- `GET/POST/DELETE /languages`, `GET/POST/DELETE /platforms` — manage the
  lookup lists referenced by items. Both start empty; add entries as you
  need them.
- `GET /search/movies|tv|books|podcasts?q=...` — search external metadata
  providers (TMDB, Open Library, iTunes) to enrich a new item.

Example: create a book, mark it as available at two platforms, then mark it
read.

```
curl -X POST localhost:8000/items -H "Content-Type: application/json" -d \
  '{"content_type": "book", "title": "Mislukte staten", "creator": "Noam Chomsky"}'

curl -X PUT localhost:8000/items/1/platforms/1 -d '{"available": true}'
curl -X PUT localhost:8000/items/1/platforms/2 -d '{"available": false}'

curl -X PATCH localhost:8000/items/1 -d \
  '{"status": "done", "rating": 8, "completed_date": "2026-09-19"}'
```
