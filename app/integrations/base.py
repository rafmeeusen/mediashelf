from typing import Protocol

from app.schemas import SearchResult


class MetadataProvider(Protocol):
    def search(self, query: str) -> list[SearchResult]: ...
