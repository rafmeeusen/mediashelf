import httpx
from fastapi import APIRouter, HTTPException, Query

from app.integrations.registry import PROVIDERS
from app.schemas import SearchResult

router = APIRouter(prefix="/search", tags=["search"])


def _run(provider, q: str) -> list[SearchResult]:
    try:
        return provider.search(q)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream metadata search failed: {exc}")


@router.get("/movies", response_model=list[SearchResult])
def search_movies(q: str = Query(min_length=1)):
    return _run(PROVIDERS["movie"], q)


@router.get("/tv", response_model=list[SearchResult])
def search_tv(q: str = Query(min_length=1)):
    return _run(PROVIDERS["tv"], q)


@router.get("/books", response_model=list[SearchResult])
def search_books(q: str = Query(min_length=1)):
    return _run(PROVIDERS["book"], q)


@router.get("/podcasts", response_model=list[SearchResult])
def search_podcasts(q: str = Query(min_length=1)):
    return _run(PROVIDERS["podcast"], q)
