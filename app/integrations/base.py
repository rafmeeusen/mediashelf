from typing import Protocol

import httpx

from app.schemas import SearchResult


class MetadataProvider(Protocol):
    def search(self, query: str) -> list[SearchResult]: ...


class CombinedProvider:
    """Queries several providers and concatenates their results, so one
    source's gaps (e.g. Open Library's weak non-English coverage) don't
    limit what can be found. A single source failing doesn't break the
    others -- their results still come back.

    `per_provider_limit` caps each source's contribution *before*
    concatenating -- without it, a noisy/high-volume source (e.g. Open
    Library often returns many loosely-relevant matches) can crowd out a
    more relevant source entirely once the combined list is truncated
    downstream (callers typically only show/use the first N results).
    """

    def __init__(self, providers: list[MetadataProvider], per_provider_limit: int | None = None):
        self._providers = providers
        self._per_provider_limit = per_provider_limit

    def search(self, query: str) -> list[SearchResult]:
        results = []
        for provider in self._providers:
            try:
                provider_results = provider.search(query)
            except httpx.HTTPError:
                continue
            if self._per_provider_limit is not None:
                provider_results = provider_results[: self._per_provider_limit]
            results.extend(provider_results)
        return results
