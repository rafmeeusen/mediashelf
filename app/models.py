import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ContentType(str, enum.Enum):
    movie = "movie"
    book = "book"
    tv = "tv"
    podcast = "podcast"


class Status(str, enum.Enum):
    to_consume = "to_consume"
    done = "done"


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


item_genres = Table(
    "item_genres",
    Base.metadata,
    Column("item_id", ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, name="content_type_enum"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Enrichment metadata (nullable — manual entry may skip these)
    creator: Mapped[str | None] = mapped_column(String(500))
    release_year: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(1000))

    # Natural/business keys — unique when present, at most one populated per
    # item depending on content_type. Postgres allows multiple NULLs in a
    # unique column, so manual entries without one are unaffected.
    isbn: Mapped[str | None] = mapped_column(String(20), unique=True)
    imdb_id: Mapped[str | None] = mapped_column(String(20), unique=True)
    feed_url: Mapped[str | None] = mapped_column(String(1000), unique=True)

    external_metadata: Mapped[dict | None] = mapped_column(JSONB)

    language_id: Mapped[int | None] = mapped_column(
        ForeignKey("languages.id", ondelete="SET NULL")
    )
    language: Mapped["Language | None"] = relationship()

    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status_enum"),
        nullable=False,
        default=Status.to_consume,
        server_default="to_consume",
    )
    rating: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(500))
    completed_date: Mapped[date | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    platform_links: Mapped[list["ItemPlatform"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    genres: Mapped[list["Genre"]] = relationship(secondary=item_genres, order_by="Genre.name")

    __table_args__ = (
        Index("ix_items_status", "status"),
        CheckConstraint("rating IS NULL OR (rating BETWEEN 1 AND 10)", name="ck_items_rating_range"),
    )


class ItemPlatform(Base):
    __tablename__ = "item_platforms"

    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    platform_id: Mapped[int] = mapped_column(
        ForeignKey("platforms.id", ondelete="CASCADE"), primary_key=True
    )
    available: Mapped[bool | None] = mapped_column(Boolean)

    item: Mapped["Item"] = relationship(back_populates="platform_links")
    platform: Mapped["Platform"] = relationship()
