import respx
from httpx import Response

from app.integrations.openlibrary import OpenLibraryProvider


@respx.mock
def test_normalizes_result_fields():
    respx.get("https://openlibrary.org/search.json").mock(
        return_value=Response(
            200,
            json={
                "docs": [
                    {
                        "key": "/works/OL1W",
                        "title": "Demon Copperhead",
                        "author_name": ["Barbara Kingsolver"],
                        "first_publish_year": 2022,
                        "cover_i": 13141227,
                        "isbn": ["9780571376490", "0063267462"],
                        "subject": ["Fiction", "Poverty"],
                    }
                ]
            },
        )
    )

    results = OpenLibraryProvider().search("Demon Copperhead")

    assert len(results) == 1
    result = results[0]
    assert result.title == "Demon Copperhead"
    assert result.creator == "Barbara Kingsolver"
    assert result.release_year == 2022
    assert result.isbn == "9780571376490"
    assert result.cover_url == "https://covers.openlibrary.org/b/id/13141227-M.jpg"
    assert result.external_metadata["openlibrary_work_key"] == "/works/OL1W"


@respx.mock
def test_missing_optional_fields_default_to_none():
    respx.get("https://openlibrary.org/search.json").mock(
        return_value=Response(200, json={"docs": [{"title": "Mystery Book"}]})
    )

    result = OpenLibraryProvider().search("Mystery Book")[0]

    assert result.creator is None
    assert result.isbn is None
    assert result.cover_url is None
