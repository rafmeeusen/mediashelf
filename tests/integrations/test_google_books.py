import respx
from httpx import Response

from app.integrations.google_books import GoogleBooksProvider


@respx.mock
def test_normalizes_result_fields():
    respx.get("https://www.googleapis.com/books/v1/volumes").mock(
        return_value=Response(
            200,
            json={
                "items": [
                    {
                        "id": "abc123",
                        "volumeInfo": {
                            "title": "De Officier",
                            "authors": ["Robert Harris"],
                            "publishedDate": "2019-03-01",
                            "description": "Een Nederlandse vertaling.",
                            "language": "nl",
                            "imageLinks": {"thumbnail": "http://books.google.com/cover.jpg"},
                            "industryIdentifiers": [
                                {"type": "ISBN_10", "identifier": "1234567890"},
                                {"type": "ISBN_13", "identifier": "9781234567897"},
                            ],
                        },
                    }
                ]
            },
        )
    )

    result = GoogleBooksProvider().search("Robert Harris De Officier")[0]

    assert result.title == "De Officier"
    assert result.creator == "Robert Harris"
    assert result.release_year == 2019
    assert result.isbn == "9781234567897"  # prefers ISBN_13 over ISBN_10
    assert result.cover_url == "https://books.google.com/cover.jpg"  # http upgraded to https
    assert result.external_metadata == {"google_books_id": "abc123", "language": "nl"}


@respx.mock
def test_missing_optional_fields_default_to_none():
    respx.get("https://www.googleapis.com/books/v1/volumes").mock(
        return_value=Response(200, json={"items": [{"id": "x", "volumeInfo": {"title": "Mystery"}}]})
    )

    result = GoogleBooksProvider().search("Mystery")[0]

    assert result.creator is None
    assert result.isbn is None
    assert result.cover_url is None
    assert result.release_year is None
