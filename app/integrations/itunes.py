import httpx

from app.schemas import SearchResult

SEARCH_URL = "https://itunes.apple.com/search"


class ITunesPodcastProvider:
    def search(self, query: str) -> list[SearchResult]:
        response = httpx.get(SEARCH_URL, params={"term": query, "media": "podcast"}, timeout=10)
        response.raise_for_status()
        return [self._normalize(item) for item in response.json().get("results", [])]

    def _normalize(self, item: dict) -> SearchResult:
        release_date = item.get("releaseDate") or ""
        year = int(release_date[:4]) if release_date[:4].isdigit() else None
        return SearchResult(
            title=item.get("collectionName") or item.get("trackName") or "",
            creator=item.get("artistName"),
            release_year=year,
            cover_url=item.get("artworkUrl600"),
            feed_url=item.get("feedUrl"),
            external_metadata={
                "genre": item.get("primaryGenreName"),
                "episode_count": item.get("trackCount"),
                "itunes_collection_id": item.get("collectionId"),
            },
        )
