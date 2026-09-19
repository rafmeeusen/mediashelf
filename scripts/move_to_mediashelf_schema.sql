-- One-time move of MediaShelf's tables out of "public" into a dedicated
-- "mediashelf" schema. Uses ALTER ... SET SCHEMA, which relocates objects
-- (and all their data) in place -- no dump/restore needed, no data loss.
-- Safe to run only once against a database whose MediaShelf tables still
-- live in "public".

BEGIN;

CREATE SCHEMA IF NOT EXISTS mediashelf AUTHORIZATION media_user;

ALTER TABLE public.items SET SCHEMA mediashelf;
ALTER TABLE public.languages SET SCHEMA mediashelf;
ALTER TABLE public.platforms SET SCHEMA mediashelf;
ALTER TABLE public.genres SET SCHEMA mediashelf;
ALTER TABLE public.item_platforms SET SCHEMA mediashelf;
ALTER TABLE public.item_genres SET SCHEMA mediashelf;
ALTER TABLE public.alembic_version SET SCHEMA mediashelf;

-- Note: sequences owned by a column (SERIAL/IDENTITY, e.g. items_id_seq)
-- move automatically with their owning table above; no separate
-- ALTER SEQUENCE needed (and would error with "does not exist" if attempted,
-- since it has already relocated).

ALTER TYPE public.content_type_enum SET SCHEMA mediashelf;
ALTER TYPE public.status_enum SET SCHEMA mediashelf;

COMMIT;
