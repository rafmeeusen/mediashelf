import httpx

from app.schemas import SearchResult

SEARCH_URL = "https://openlibrary.org/search.json"
COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
FIELDS = "key,title,author_name,first_publish_year,cover_i,isbn,subject"


class OpenLibraryProvider:
    def search(self, query: str) -> list[SearchResult]:
        response = httpx.get(
            SEARCH_URL, params={"q": query, "limit": 20, "fields": FIELDS}, timeout=10
        )
        response.raise_for_status()
        return [self._normalize(doc) for doc in response.json().get("docs", [])]

    def _normalize(self, doc: dict) -> SearchResult:
        authors = doc.get("author_name") or []
        isbns = doc.get("isbn") or []
        cover_id = doc.get("cover_i")
        subjects = doc.get("subject") or []
        return SearchResult(
            title=doc.get("title", ""),
            creator=authors[0] if authors else None,
            release_year=doc.get("first_publish_year"),
            cover_url=COVER_URL.format(cover_id=cover_id) if cover_id else None,
            isbn=isbns[0] if isbns else None,
            external_metadata={
                "openlibrary_work_key": doc.get("key"),
                "subjects": subjects[:10] or None,
            },
        )
