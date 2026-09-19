from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ContentType, Status


class LanguageCreate(BaseModel):
    name: str


class LanguageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class PlatformCreate(BaseModel):
    name: str


class PlatformOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ItemPlatformIn(BaseModel):
    available: bool


class ItemPlatformOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    platform_id: int
    platform: str
    available: bool | None

    @classmethod
    def from_link(cls, link) -> "ItemPlatformOut":
        return cls(
            platform_id=link.platform_id,
            platform=link.platform.name,
            available=link.available,
        )


class ItemBase(BaseModel):
    content_type: ContentType
    title: str
    creator: str | None = None
    release_year: int | None = None
    description: str | None = None
    cover_url: str | None = None
    isbn: str | None = None
    imdb_id: str | None = None
    feed_url: str | None = None
    external_metadata: dict | None = None
    language_id: int | None = None
    source: str | None = None
    notes: str | None = None


class ItemCreate(ItemBase):
    status: Status = Status.to_consume
    rating: int | None = Field(default=None, ge=1, le=10)
    completed_date: date | None = None


class ItemCreateFromSearch(BaseModel):
    content_type: ContentType
    title: str
    creator: str | None = None
    release_year: int | None = None
    description: str | None = None
    cover_url: str | None = None
    isbn: str | None = None
    imdb_id: str | None = None
    feed_url: str | None = None
    external_metadata: dict | None = None
    language_id: int | None = None
    source: str | None = None


class ItemUpdate(BaseModel):
    title: str | None = None
    creator: str | None = None
    release_year: int | None = None
    description: str | None = None
    cover_url: str | None = None
    language_id: int | None = None
    status: Status | None = None
    rating: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = None
    source: str | None = None
    completed_date: date | None = None


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_type: ContentType
    title: str
    creator: str | None
    release_year: int | None
    description: str | None
    cover_url: str | None
    isbn: str | None
    imdb_id: str | None
    feed_url: str | None
    external_metadata: dict | None
    language: LanguageOut | None
    status: Status
    rating: int | None
    notes: str | None
    source: str | None
    completed_date: date | None
    created_at: datetime
    updated_at: datetime
    platforms: list[ItemPlatformOut]

    @classmethod
    def from_item(cls, item) -> "ItemOut":
        return cls(
            id=item.id,
            content_type=item.content_type,
            title=item.title,
            creator=item.creator,
            release_year=item.release_year,
            description=item.description,
            cover_url=item.cover_url,
            isbn=item.isbn,
            imdb_id=item.imdb_id,
            feed_url=item.feed_url,
            external_metadata=item.external_metadata,
            language=item.language,
            status=item.status,
            rating=item.rating,
            notes=item.notes,
            source=item.source,
            completed_date=item.completed_date,
            created_at=item.created_at,
            updated_at=item.updated_at,
            platforms=[ItemPlatformOut.from_link(link) for link in item.platform_links],
        )


class SearchResult(BaseModel):
    title: str
    creator: str | None = None
    release_year: int | None = None
    description: str | None = None
    cover_url: str | None = None
    isbn: str | None = None
    imdb_id: str | None = None
    feed_url: str | None = None
    external_metadata: dict | None = None
