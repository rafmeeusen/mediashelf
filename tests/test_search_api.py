import respx
from httpx import Response


@respx.mock
def test_search_books_proxies_open_library(client):
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
                        "isbn": ["9780571376490"],
                    }
                ]
            },
        )
    )

    resp = client.get("/search/books", params={"q": "Demon Copperhead"})
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["title"] == "Demon Copperhead"
    assert body[0]["isbn"] == "9780571376490"


@respx.mock
def test_search_podcasts_proxies_itunes(client):
    respx.get("https://itunes.apple.com/search").mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "collectionName": "Nerdland",
                        "artistName": "Lieven Scheire",
                        "feedUrl": "https://feeds.example.com/nerdland.rss",
                        "artworkUrl600": "https://example.com/cover.jpg",
                        "collectionId": 123,
                    }
                ]
            },
        )
    )

    resp = client.get("/search/podcasts", params={"q": "Nerdland"})
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["feed_url"] == "https://feeds.example.com/nerdland.rss"


@respx.mock
def test_search_movies_upstream_failure_returns_502(client):
    respx.get("https://api.themoviedb.org/3/search/movie").mock(
        return_value=Response(401, json={"status_message": "Invalid API key"})
    )

    resp = client.get("/search/movies", params={"q": "Interstellar"})
    assert resp.status_code == 502


@respx.mock
def test_create_item_from_search_resolves_imdb_id(client):
    respx.get("https://api.themoviedb.org/3/movie/603/external_ids").mock(
        return_value=Response(200, json={"imdb_id": "tt0133093"})
    )

    resp = client.post(
        "/items/from-search",
        json={
            "content_type": "movie",
            "title": "The Matrix",
            "external_metadata": {"tmdb_id": 603, "media_type": "movie"},
        },
    )
    assert resp.status_code == 201
    assert resp.json()["imdb_id"] == "tt0133093"
