import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base, get_db
from app.main import app

TEST_SCHEMA = "test"

engine = create_engine(
    settings.database_url,
    connect_args={"options": f"-csearch_path={TEST_SCHEMA}"},
)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    yield

    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.commit()


@pytest.fixture(autouse=True)
def _clean_tables():
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(
                text(f'TRUNCATE TABLE "{TEST_SCHEMA}"."{table.name}" RESTART IDENTITY CASCADE')
            )
        conn.commit()
    yield


@pytest.fixture()
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
