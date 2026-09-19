from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ContentType, Status
from app.schemas import (
    ItemCreate,
    ItemCreateFromSearch,
    ItemOut,
    ItemPlatformIn,
    ItemUpdate,
)
from app.services import items as items_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=list[ItemOut])
def list_items(
    content_type: ContentType | None = None,
    status_: Status | None = Query(default=None, alias="status"),
    genre: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    rows = items_service.list_items(db, content_type, status_, genre, limit, offset)
    return [ItemOut.from_item(row) for row in rows]


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(body: ItemCreate, db: Session = Depends(get_db)):
    return ItemOut.from_item(items_service.create_item(db, body))


@router.post("/from-search", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item_from_search(body: ItemCreateFromSearch, db: Session = Depends(get_db)):
    return ItemOut.from_item(items_service.create_item_from_search(db, body))


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    return ItemOut.from_item(items_service.get_item(db, item_id))


@router.patch("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, body: ItemUpdate, db: Session = Depends(get_db)):
    return ItemOut.from_item(items_service.update_item(db, item_id, body))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    items_service.delete_item(db, item_id)


@router.put("/{item_id}/platforms/{platform_id}", response_model=ItemOut)
def set_item_platform(
    item_id: int, platform_id: int, body: ItemPlatformIn, db: Session = Depends(get_db)
):
    return ItemOut.from_item(
        items_service.set_platform_link(db, item_id, platform_id, body.available)
    )


@router.delete("/{item_id}/platforms/{platform_id}", response_model=ItemOut)
def remove_item_platform(item_id: int, platform_id: int, db: Session = Depends(get_db)):
    return ItemOut.from_item(items_service.remove_platform_link(db, item_id, platform_id))


@router.post("/{item_id}/genres/{genre_id}", response_model=ItemOut)
def add_item_genre(item_id: int, genre_id: int, db: Session = Depends(get_db)):
    return ItemOut.from_item(items_service.add_genre(db, item_id, genre_id))


@router.delete("/{item_id}/genres/{genre_id}", response_model=ItemOut)
def remove_item_genre(item_id: int, genre_id: int, db: Session = Depends(get_db)):
    return ItemOut.from_item(items_service.remove_genre(db, item_id, genre_id))
