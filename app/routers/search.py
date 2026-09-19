import httpx
from fastapi import APIRouter, HTTPException, Query

from app.integrations.itunes import ITunesPodcastProvider
from app.integrations.openlibrary import OpenLibraryProvider
from app.integrations.tmdb import TMDBMovieProvider, TMDBTVProvider
from app.schemas import SearchResult

router = APIRouter(prefix="/search", tags=["search"])

_movie_provider = TMDBMovieProvider()
_tv_provider = TMDBTVProvider()
_book_provider = OpenLibraryProvider()
_podcast_provider = ITunesPodcastProvider()


def _run(provider, q: str) -> list[SearchResult]:
    try:
        return provider.search(q)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream metadata search failed: {exc}")


@router.get("/movies", response_model=list[SearchResult])
def search_movies(q: str = Query(min_length=1)):
    return _run(_movie_provider, q)


@router.get("/tv", response_model=list[SearchResult])
def search_tv(q: str = Query(min_length=1)):
    return _run(_tv_provider, q)


@router.get("/books", response_model=list[SearchResult])
def search_books(q: str = Query(min_length=1)):
    return _run(_book_provider, q)


@router.get("/podcasts", response_model=list[SearchResult])
def search_podcasts(q: str = Query(min_length=1)):
    return _run(_podcast_provider, q)
