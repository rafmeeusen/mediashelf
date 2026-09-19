from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ContentType, Genre, Status
from app.services import items as items_service
from app.services import lookups

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


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
