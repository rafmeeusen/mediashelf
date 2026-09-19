import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.integrations import tmdb as tmdb_integration
from app.models import ContentType, Genre, Item, ItemPlatform, Platform, Status
from app.schemas import ItemCreate, ItemCreateFromSearch, ItemUpdate

_EAGER = (
    selectinload(Item.language),
    selectinload(Item.platform_links).selectinload(ItemPlatform.platform),
    selectinload(Item.genres),
)


def _get_or_404(db: Session, item_id: int) -> Item:
    item = db.execute(
        select(Item).options(*_EAGER).where(Item.id == item_id)
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


def list_items(
    db: Session,
    content_type: ContentType | None,
    item_status: Status | None,
    genre: str | None,
    limit: int,
    offset: int,
) -> list[Item]:
    query = select(Item).options(*_EAGER)
    if content_type is not None:
        query = query.where(Item.content_type == content_type)
    if item_status is not None:
        query = query.where(Item.status == item_status)
    if genre is not None:
        query = query.where(Item.genres.any(func.lower(Genre.name) == genre.lower()))
    query = query.order_by(Item.id).limit(limit).offset(offset)
    return db.execute(query).scalars().all()


def get_item(db: Session, item_id: int) -> Item:
    return _get_or_404(db, item_id)


def create_item(db: Session, body: ItemCreate) -> Item:
    item = Item(**body.model_dump())
    db.add(item)
    db.commit()
    return _get_or_404(db, item.id)


def create_item_from_search(db: Session, body: ItemCreateFromSearch) -> Item:
    data = body.model_dump()

    if data["content_type"] in (ContentType.movie, ContentType.tv) and not data.get("imdb_id"):
        meta = data.get("external_metadata") or {}
        tmdb_id, media_type = meta.get("tmdb_id"), meta.get("media_type")
        if tmdb_id and media_type:
            try:
                data["imdb_id"] = tmdb_integration.get_imdb_id(tmdb_id, media_type)
            except httpx.HTTPError:
                pass  # best-effort enrichment — item is still created without it

    item = Item(**data, status=Status.to_consume)
    db.add(item)
    db.commit()
    return _get_or_404(db, item.id)


def update_item(db: Session, item_id: int, body: ItemUpdate) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    return _get_or_404(db, item_id)


def delete_item(db: Session, item_id: int) -> None:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    db.delete(item)
    db.commit()


def set_platform_link(db: Session, item_id: int, platform_id: int, available: bool) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    platform = db.get(Platform, platform_id)
    if platform is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found")

    link = db.get(ItemPlatform, (item_id, platform_id))
    if link is None:
        link = ItemPlatform(item_id=item_id, platform_id=platform_id, available=available)
        db.add(link)
    else:
        link.available = available
    db.commit()
    return _get_or_404(db, item_id)


def remove_platform_link(db: Session, item_id: int, platform_id: int) -> Item:
    link = db.get(ItemPlatform, (item_id, platform_id))
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform link not found")
    db.delete(link)
    db.commit()
    return _get_or_404(db, item_id)


def add_genre(db: Session, item_id: int, genre_id: int) -> Item:
    item = _get_or_404(db, item_id)
    genre = db.get(Genre, genre_id)
    if genre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found")
    if genre not in item.genres:
        item.genres.append(genre)
        db.commit()
    return _get_or_404(db, item_id)


def remove_genre(db: Session, item_id: int, genre_id: int) -> Item:
    item = _get_or_404(db, item_id)
    genre = db.get(Genre, genre_id)
    if genre is None or genre not in item.genres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre link not found")
    item.genres.remove(genre)
    db.commit()
    return _get_or_404(db, item_id)
