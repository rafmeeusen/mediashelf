import httpx

from app.integrations.base import CombinedProvider
from app.schemas import SearchResult


class _FakeProvider:
    def __init__(self, results=None, raises=False):
        self._results = results or []
        self._raises = raises

    def search(self, query: str) -> list[SearchResult]:
        if self._raises:
            raise httpx.HTTPError("boom")
        return self._results


def _result(title: str) -> SearchResult:
    return SearchResult(title=title)


def test_concatenates_results_from_all_providers():
    a = _FakeProvider([_result("From A")])
    b = _FakeProvider([_result("From B1"), _result("From B2")])

    results = CombinedProvider([a, b]).search("query")

    assert [r.title for r in results] == ["From A", "From B1", "From B2"]


def test_one_provider_failing_does_not_break_the_others():
    working = _FakeProvider([_result("Still here")])
    broken = _FakeProvider(raises=True)

    results = CombinedProvider([broken, working]).search("query")

    assert [r.title for r in results] == ["Still here"]


def test_all_providers_failing_returns_empty_list():
    results = CombinedProvider([_FakeProvider(raises=True), _FakeProvider(raises=True)]).search("query")
    assert results == []


def test_per_provider_limit_prevents_one_noisy_source_from_crowding_out_another():
    # A high-volume, loosely-relevant source (like Open Library often is)
    # must not be able to push a more relevant second source's results past
    # whatever cap a caller applies downstream (e.g. showing only the first
    # 12 combined results in the UI).
    noisy = _FakeProvider([_result(f"Noise {i}") for i in range(20)])
    relevant = _FakeProvider([_result("The one you wanted")])

    results = CombinedProvider([noisy, relevant], per_provider_limit=6).search("query")

    assert len(results) == 7  # 6 from noisy + 1 from relevant
    assert "The one you wanted" in [r.title for r in results]
