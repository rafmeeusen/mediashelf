import httpx

from app.config import settings
from app.schemas import SearchResult

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def _year_from_date(value: str | None) -> int | None:
    if value and len(value) >= 4 and value[:4].isdigit():
        return int(value[:4])
    return None


class TMDBMovieProvider:
    media_type = "movie"
    _search_path = "/search/movie"
    _title_key = "title"
    _date_key = "release_date"

    def search(self, query: str) -> list[SearchResult]:
        response = httpx.get(
            f"{BASE_URL}{self._search_path}",
            params={"api_key": settings.tmdb_api_key, "query": query},
            timeout=10,
        )
        response.raise_for_status()
        return [self._normalize(item) for item in response.json().get("results", [])]

    def _normalize(self, item: dict) -> SearchResult:
        poster_path = item.get("poster_path")
        return SearchResult(
            title=item.get(self._title_key, ""),
            release_year=_year_from_date(item.get(self._date_key)),
            description=item.get("overview"),
            cover_url=f"{IMAGE_BASE_URL}{poster_path}" if poster_path else None,
            external_metadata={"tmdb_id": item["id"], "media_type": self.media_type},
        )


class TMDBTVProvider(TMDBMovieProvider):
    media_type = "tv"
    _search_path = "/search/tv"
    _title_key = "name"
    _date_key = "first_air_date"


def get_imdb_id(tmdb_id: int, media_type: str) -> str | None:
    """Resolve the IMDb id for a TMDB movie/tv record.

    TMDB's search endpoints don't return imdb_id, so this is called once,
    per selected search result, when creating an item from search.
    """
    response = httpx.get(
        f"{BASE_URL}/{media_type}/{tmdb_id}/external_ids",
        params={"api_key": settings.tmdb_api_key},
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("imdb_id") or None
