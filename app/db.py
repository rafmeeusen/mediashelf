from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Sets the connection's default schema so table DDL/queries (which never
# hardcode a schema on the SQLAlchemy models) resolve against `db_schema`
# instead of Postgres's default "public".
engine = create_engine(
    settings.database_url,
    connect_args={"options": f"-c search_path={settings.db_schema}"},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
