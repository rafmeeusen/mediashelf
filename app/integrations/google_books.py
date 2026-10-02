import httpx

from app.config import settings
from app.schemas import SearchResult

SEARCH_URL = "https://www.googleapis.com/books/v1/volumes"


class GoogleBooksProvider:
    """Broader/international book catalog than Open Library -- notably much
    better coverage of non-English (e.g. Dutch/Flemish) translated editions,
    since it indexes publisher catalogs worldwide rather than mainly
    English-language and public-domain library records.
    """

    def search(self, query: str) -> list[SearchResult]:
        params = {"q": query, "maxResults": 20}
        if settings.google_books_api_key:
            params["key"] = settings.google_books_api_key
        response = httpx.get(SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        return [self._normalize(item) for item in response.json().get("items", [])]

    def _normalize(self, item: dict) -> SearchResult:
        info = item.get("volumeInfo", {})
        authors = info.get("authors") or []
        published = info.get("publishedDate") or ""
        year = int(published[:4]) if published[:4].isdigit() else None

        isbn = None
        identifiers = info.get("industryIdentifiers") or []
        for preferred_type in ("ISBN_13", "ISBN_10"):
            match = next((i["identifier"] for i in identifiers if i.get("type") == preferred_type), None)
            if match:
                isbn = match
                break

        cover_url = (info.get("imageLinks") or {}).get("thumbnail")
        if cover_url:
            cover_url = cover_url.replace("http://", "https://")

        return SearchResult(
            title=info.get("title", ""),
            creator=", ".join(authors) if authors else None,
            release_year=year,
            description=info.get("description"),
            cover_url=cover_url,
            isbn=isbn,
            external_metadata={
                "google_books_id": item.get("id"),
                "language": info.get("language"),
            },
        )
