import json
from datetime import date

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.integrations.registry import PROVIDERS
from app.models import ContentType, Genre, Language, Status
from app.schemas import ItemCreate, ItemCreateFromSearch, ItemUpdate
from app.services import items as items_service
from app.services import lookups

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")

EDITABLE_FIELDS = {"status", "rating", "language_id", "source", "completed_date", "notes"}


def _search(
    db: Session,
    q: str | None,
    content_type: str | None,
    status: str | None,
    genre: str | None,
):
    # HTML <select> submits "" for the placeholder option ("All types" etc.),
    # not an absent param, so blank strings must be treated as "no filter".
    content_type_enum = ContentType(content_type) if content_type else None
    status_enum = Status(status) if status else None
    genre = genre or None
    q = q or None

    items = items_service.list_items(db, content_type_enum, status_enum, genre, limit=200, offset=0, q=q)
    count = items_service.count_items(db, content_type_enum, status_enum, genre, q)
    return items, count


@router.get("/")
def index(
    request: Request,
    q: str | None = None,
    content_type: str | None = None,
    status: str | None = None,
    genre: str | None = None,
    db: Session = Depends(get_db),
):
    items, count = _search(db, q, content_type, status, genre)
    genres = lookups.list_all(db, Genre)
    return templates.TemplateResponse(
        request, "index.html", {"items": items, "count": count, "genres": genres}
    )


@router.get("/ui/items")
def search_items(
    request: Request,
    q: str | None = None,
    content_type: str | None = None,
    status: str | None = None,
    genre: str | None = None,
    db: Session = Depends(get_db),
):
    items, count = _search(db, q, content_type, status, genre)
    return templates.TemplateResponse(request, "_item_list.html", {"items": items, "count": count})


@router.get("/ui/items/new")
def new_item_page(request: Request, db: Session = Depends(get_db)):
    languages = lookups.list_all(db, Language)
    return templates.TemplateResponse(request, "new.html", {"languages": languages})


@router.get("/ui/items/new/search")
def new_item_search(request: Request, content_type: str = "movie", q: str = ""):
    provider = PROVIDERS.get(content_type)
    results = []
    error = None
    q = q.strip()
    if provider and q:
        try:
            for result in provider.search(q)[:12]:
                results.append(
                    {**result.model_dump(), "external_metadata_json": json.dumps(result.external_metadata or {})}
                )
        except httpx.HTTPError:
            error = "Zoeken mislukt. Probeer het later opnieuw of voeg handmatig toe."
    return templates.TemplateResponse(
        request,
        "_new_search_results.html",
        {"results": results, "content_type": content_type, "query": q, "error": error},
    )


@router.get("/ui/items/new/confirm")
def new_item_confirm(
    request: Request,
    content_type: str,
    title: str,
    creator: str = "",
    release_year: str = "",
    description: str = "",
    cover_url: str = "",
    isbn: str = "",
    feed_url: str = "",
    external_metadata_json: str = "{}",
    db: Session = Depends(get_db),
):
    languages = lookups.list_all(db, Language)
    return templates.TemplateResponse(
        request,
        "_new_confirm.html",
        {
            "content_type": content_type,
            "title": title,
            "creator": creator or None,
            "release_year": int(release_year) if release_year else None,
            "description": description or None,
            "cover_url": cover_url or None,
            "isbn": isbn or None,
            "feed_url": feed_url or None,
            "external_metadata_json": external_metadata_json,
            "languages": languages,
        },
    )


@router.post("/ui/items/new/from-search")
def new_item_from_search(
    content_type: str = Form(...),
    title: str = Form(...),
    creator: str = Form(""),
    release_year: str = Form(""),
    description: str = Form(""),
    cover_url: str = Form(""),
    isbn: str = Form(""),
    feed_url: str = Form(""),
    external_metadata_json: str = Form("{}"),
    language_id: str = Form(""),
    source: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        external_metadata = json.loads(external_metadata_json) or None
    except json.JSONDecodeError:
        external_metadata = None

    body = ItemCreateFromSearch(
        content_type=ContentType(content_type),
        title=title,
        creator=creator or None,
        release_year=int(release_year) if release_year else None,
        description=description or None,
        cover_url=cover_url or None,
        isbn=isbn or None,
        feed_url=feed_url or None,
        external_metadata=external_metadata,
        language_id=int(language_id) if language_id else None,
        source=source or None,
    )
    item = items_service.create_item_from_search(db, body)
    return RedirectResponse(f"/ui/items/{item.id}", status_code=303)


@router.post("/ui/items/new/manual")
def new_item_manual(
    content_type: str = Form(...),
    title: str = Form(...),
    creator: str = Form(""),
    language_id: str = Form(""),
    db: Session = Depends(get_db),
):
    body = ItemCreate(
        content_type=ContentType(content_type),
        title=title,
        creator=creator or None,
        language_id=int(language_id) if language_id else None,
    )
    item = items_service.create_item(db, body)
    return RedirectResponse(f"/ui/items/{item.id}", status_code=303)


@router.get("/ui/items/{item_id}")
def item_detail(request: Request, item_id: int, db: Session = Depends(get_db)):
    item = items_service.get_item(db, item_id)
    return templates.TemplateResponse(request, "detail.html", {"item": item})


def _field_template(field: str) -> str:
    return "_field_notes.html" if field == "notes" else "_field_row.html"


def _field_context(db: Session, item, field: str, mode: str) -> dict:
    context = {"item": item, "field": field, "mode": mode}
    if field == "language_id":
        context["languages"] = lookups.list_all(db, Language)
    return context


def _parse_field_value(field: str, raw: str):
    raw = (raw or "").strip()
    if field == "status":
        return Status(raw)
    if field == "rating":
        return float(raw) if raw else None
    if field == "language_id":
        return int(raw) if raw else None
    if field == "completed_date":
        return date.fromisoformat(raw) if raw else None
    return raw or None  # source, notes: blank clears the field


@router.get("/ui/items/{item_id}/fields/{field}")
def view_field(request: Request, item_id: int, field: str, db: Session = Depends(get_db)):
    if field not in EDITABLE_FIELDS:
        raise HTTPException(status_code=404, detail="Unknown field")
    item = items_service.get_item(db, item_id)
    return templates.TemplateResponse(
        request, _field_template(field), _field_context(db, item, field, "view")
    )


@router.get("/ui/items/{item_id}/fields/{field}/edit")
def edit_field(request: Request, item_id: int, field: str, db: Session = Depends(get_db)):
    if field not in EDITABLE_FIELDS:
        raise HTTPException(status_code=404, detail="Unknown field")
    item = items_service.get_item(db, item_id)
    return templates.TemplateResponse(
        request, _field_template(field), _field_context(db, item, field, "edit")
    )


@router.post("/ui/items/{item_id}/fields/{field}")
def save_field(
    request: Request,
    item_id: int,
    field: str,
    value: str = Form(default=""),
    db: Session = Depends(get_db),
):
    if field not in EDITABLE_FIELDS:
        raise HTTPException(status_code=404, detail="Unknown field")
    try:
        parsed = _parse_field_value(field, value)
        item = items_service.update_item(db, item_id, ItemUpdate(**{field: parsed}))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return templates.TemplateResponse(
        request, _field_template(field), _field_context(db, item, field, "view")
    )
