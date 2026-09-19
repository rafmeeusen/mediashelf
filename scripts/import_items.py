#!/usr/bin/env python3
"""Parse a MediaShelf import file and, optionally, create the items via the API.

See data/import.example.txt for the file format.

Usage:
    uv run python scripts/import_items.py data/import.txt            # dry run, prints a preview
    uv run python scripts/import_items.py data/import.txt --apply    # actually creates the items
"""

import argparse
import re
import sys
from datetime import datetime

import httpx

TYPE_ALIASES = {
    "movie": "movie",
    "film": "movie",
    "book": "book",
    "boek": "book",
    "tv": "tv",
    "serie": "tv",
    "series": "tv",
    "podcast": "podcast",
}

STATUS_ALIASES = {
    "done": "done",
    "gelezen": "done",
    "gezien": "done",
    "beluisterd": "done",
    "to_consume": "to_consume",
    "nog te lezen": "to_consume",
    "nog te zien": "to_consume",
    "te lezen": "to_consume",
    "te zien": "to_consume",
}

AVAILABLE_TRUE = {"ja", "yes", "true", "available", "beschikbaar"}
AVAILABLE_FALSE = {"nee", "no", "false", "unavailable", "niet beschikbaar"}

DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y")

SIMPLE_FIELDS = (
    "title", "type", "status", "creator", "language", "notes", "source",
    "rating", "completed_date", "imdb", "isbn", "feed_url",
)

IMDB_ID_RE = re.compile(r"(tt\d{7,10})")


def parse_date(value: str) -> str:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()  # noqa: DTZ007 (calendar date, not a timestamp)
        except ValueError:
            continue
    raise ValueError(f"unrecognized date format: {value!r}")


def parse_platform_line(value: str) -> tuple[str, bool]:
    if "=" in value:
        name, avail = value.split("=", 1)
        name, avail = name.strip(), avail.strip().lower()
        if avail in AVAILABLE_TRUE:
            return name, True
        if avail in AVAILABLE_FALSE:
            return name, False
        raise ValueError(f"unrecognized availability {avail!r} for platform {name!r}")
    return value.strip(), True


def parse_file(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    blocks = re.split(r"\n\s*\n+", text)
    entries = []
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        if not lines:
            continue
        raw: dict = {"platforms": [], "genres": []}
        warnings: list[str] = []
        for line in lines:
            if ":" not in line:
                warnings.append(f"ignoring line without ':': {line!r}")
                continue
            key, value = (part.strip() for part in line.split(":", 1))
            key = key.lower()
            if key == "platform":
                try:
                    raw["platforms"].append(parse_platform_line(value))
                except ValueError as exc:
                    warnings.append(str(exc))
            elif key == "genre":
                raw["genres"].append(value)
            elif key in SIMPLE_FIELDS:
                if key in raw:
                    warnings.append(f"duplicate key {key!r}, keeping last value")
                raw[key] = value
            else:
                warnings.append(f"unrecognized field: {key!r}")
        entries.append(normalize(raw, warnings))
    return entries


def normalize(raw: dict, warnings: list[str]) -> dict:
    result: dict = {"platforms": raw["platforms"], "genres": raw["genres"], "warnings": warnings}

    title = raw.get("title")
    if not title:
        warnings.append("missing required field: title")
    result["title"] = title

    raw_type = raw.get("type")
    content_type = TYPE_ALIASES.get((raw_type or "").lower())
    if raw_type and not content_type:
        warnings.append(f"unrecognized type: {raw_type!r}")
    elif not raw_type:
        warnings.append("missing required field: type")
    result["content_type"] = content_type

    raw_status = raw.get("status")
    if raw_status:
        status = STATUS_ALIASES.get(raw_status.lower())
        if not status:
            warnings.append(f"unrecognized status: {raw_status!r}, defaulting to to_consume")
            status = "to_consume"
    else:
        status = "to_consume"
    result["status"] = status

    result["creator"] = raw.get("creator")
    result["language"] = raw.get("language")
    result["notes"] = raw.get("notes")
    result["source"] = raw.get("source")

    rating = None
    rating_raw = raw.get("rating")
    if rating_raw:
        try:
            rating = int(rating_raw)
            if not (1 <= rating <= 10):
                warnings.append(f"rating out of range 1-10: {rating}")
                rating = None
        except ValueError:
            warnings.append(f"unparseable rating: {rating_raw!r}")
    result["rating"] = rating

    completed_date = None
    date_raw = raw.get("completed_date")
    if date_raw:
        try:
            completed_date = parse_date(date_raw)
        except ValueError as exc:
            warnings.append(str(exc))
    result["completed_date"] = completed_date

    imdb_id = None
    imdb_raw = raw.get("imdb")
    if imdb_raw:
        match = IMDB_ID_RE.search(imdb_raw)
        if match:
            imdb_id = match.group(1)
        else:
            warnings.append(f"could not extract an imdb id from: {imdb_raw!r}")
    result["imdb_id"] = imdb_id
    result["isbn"] = raw.get("isbn")
    result["feed_url"] = raw.get("feed_url")

    return result


def print_preview(entries: list[dict]) -> int:
    warning_count = 0
    for i, entry in enumerate(entries, start=1):
        print(f"[{i}] {entry['title'] or '(missing title)'}  ({entry['content_type'] or '?'})")
        print(f"    status: {entry['status']}", end="")
        if entry["creator"]:
            print(f"  creator: {entry['creator']}", end="")
        if entry["language"]:
            print(f"  language: {entry['language']}", end="")
        if entry["rating"]:
            print(f"  rating: {entry['rating']}", end="")
        if entry["completed_date"]:
            print(f"  completed: {entry['completed_date']}", end="")
        if entry["imdb_id"]:
            print(f"  imdb: {entry['imdb_id']}", end="")
        if entry["isbn"]:
            print(f"  isbn: {entry['isbn']}", end="")
        if entry["feed_url"]:
            print(f"  feed_url: {entry['feed_url']}", end="")
        print()
        if entry["source"]:
            print(f"    source: {entry['source']}")
        if entry["notes"]:
            print(f"    notes: {entry['notes']}")
        for name, available in entry["platforms"]:
            print(f"    platform: {name} ({'available' if available else 'not available'})")
        if entry["genres"]:
            print(f"    genres: {', '.join(entry['genres'])}")
        for warning in entry["warnings"]:
            print(f"    !! WARNING: {warning}")
            warning_count += 1
        print()
    print(f"{len(entries)} entries, {warning_count} warning(s).")
    return warning_count


def get_or_create_lookup(client: httpx.Client, endpoint: str, name: str, cache: dict) -> int:
    key = name.strip().lower()
    if key in cache:
        return cache[key]
    resp = client.post(endpoint, json={"name": name.strip()})
    if resp.status_code == 409:
        existing = {row["name"].strip().lower(): row["id"] for row in client.get(endpoint).json()}
        item_id = existing[key]
    else:
        resp.raise_for_status()
        item_id = resp.json()["id"]
    cache[key] = item_id
    return item_id


def apply_entries(entries: list[dict], base_url: str) -> None:
    language_cache: dict = {}
    platform_cache: dict = {}
    genre_cache: dict = {}
    with httpx.Client(base_url=base_url, timeout=10) as client:
        for entry in entries:
            if entry["warnings"] or not entry["content_type"] or not entry["title"]:
                print(f"SKIPPING (has warnings): {entry['title']!r}")
                continue

            body = {
                "content_type": entry["content_type"],
                "title": entry["title"],
                "creator": entry["creator"],
                "status": entry["status"],
                "rating": entry["rating"],
                "notes": entry["notes"],
                "source": entry["source"],
                "completed_date": entry["completed_date"],
                "imdb_id": entry["imdb_id"],
                "isbn": entry["isbn"],
                "feed_url": entry["feed_url"],
            }
            if entry["language"]:
                body["language_id"] = get_or_create_lookup(client, "/languages", entry["language"], language_cache)

            resp = client.post("/items", json=body)
            resp.raise_for_status()
            item = resp.json()
            print(f"created item {item['id']}: {item['title']}")

            for name, available in entry["platforms"]:
                platform_id = get_or_create_lookup(client, "/platforms", name, platform_cache)
                client.put(f"/items/{item['id']}/platforms/{platform_id}", json={"available": available}).raise_for_status()

            for name in entry["genres"]:
                genre_id = get_or_create_lookup(client, "/genres", name, genre_cache)
                client.post(f"/items/{item['id']}/genres/{genre_id}").raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="path to the import text file")
    parser.add_argument("--apply", action="store_true", help="actually create the items (default: dry run)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8087", help="MediaShelf API base URL")
    args = parser.parse_args()

    entries = parse_file(args.file)
    warning_count = print_preview(entries)

    if not args.apply:
        print("\nDry run only — nothing was written. Re-run with --apply to import.")
        return

    if warning_count:
        print(f"\n{warning_count} warning(s) found — entries with warnings will be skipped.")
        if input("Continue with --apply anyway? [y/N] ").strip().lower() != "y":
            sys.exit(1)

    apply_entries(entries, args.base_url)


if __name__ == "__main__":
    main()
