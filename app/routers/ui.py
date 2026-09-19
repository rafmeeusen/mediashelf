from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ContentType, Genre, Language, Status
from app.schemas import ItemUpdate
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
