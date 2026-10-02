import respx
from httpx import Response


def test_new_item_page_renders(client):
    resp = client.get("/ui/items/new")
    assert resp.status_code == 200
    assert "Nieuw item toevoegen" in resp.text
    assert "Handmatig toevoegen" in resp.text


@respx.mock
def test_search_movies_shows_clickable_result(client):
    respx.get("https://api.themoviedb.org/3/search/movie").mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "id": 603,
                        "title": "The Matrix",
                        "release_date": "1999-03-30",
                        "overview": "A hacker learns the truth.",
                        "poster_path": "/poster.jpg",
                    }
                ]
            },
        )
    )

    resp = client.get("/ui/items/new/search", params={"content_type": "movie", "q": "Matrix"})
    assert resp.status_code == 200
    assert "The Matrix" in resp.text
    assert 'name="content_type" value="movie"' in resp.text
    assert "tmdb_id" in resp.text  # external_metadata_json carried through


def test_search_with_no_query_shows_nothing(client):
    resp = client.get("/ui/items/new/search", params={"content_type": "movie", "q": ""})
    assert resp.status_code == 200
    assert "search-results" not in resp.text
    assert "Geen resultaten" not in resp.text  # only shown once a query was actually made


def test_confirm_prefills_title_and_year(client):
    resp = client.get(
        "/ui/items/new/confirm",
        params={
            "content_type": "movie",
            "title": "The Matrix",
            "creator": "",
            "release_year": "1999",
            "external_metadata_json": '{"tmdb_id": 603, "media_type": "movie"}',
        },
    )
    assert resp.status_code == 200
    assert 'value="The Matrix"' in resp.text
    assert 'value="1999"' in resp.text


@respx.mock
def test_from_search_creates_item_and_resolves_imdb_id(client):
    respx.get("https://api.themoviedb.org/3/movie/603/external_ids").mock(
        return_value=Response(200, json={"imdb_id": "tt0133093"})
    )

    resp = client.post(
        "/ui/items/new/from-search",
        data={
            "content_type": "movie",
            "title": "The Matrix",
            "release_year": "1999",
            "external_metadata_json": '{"tmdb_id": 603, "media_type": "movie"}',
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    location = resp.headers["location"]
    assert location.startswith("/ui/items/")

    item_id = int(location.rsplit("/", 1)[-1])
    item = client.get(f"/items/{item_id}").json()
    assert item["title"] == "The Matrix"
    assert item["release_year"] == 1999
    assert item["imdb_id"] == "tt0133093"
    assert item["status"] == "to_consume"


def test_new_item_manual_creates_item(client):
    resp = client.post(
        "/ui/items/new/manual",
        data={"content_type": "book", "title": "Schitterend gebrek", "creator": "Arthur Japin"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    item_id = int(resp.headers["location"].rsplit("/", 1)[-1])
    item = client.get(f"/items/{item_id}").json()
    assert item["title"] == "Schitterend gebrek"
    assert item["creator"] == "Arthur Japin"
    assert item["content_type"] == "book"


def test_new_item_path_does_not_collide_with_item_detail(client):
    # "/ui/items/new" must not be swallowed by the "/ui/items/{item_id}" route
    resp = client.get("/ui/items/new")
    assert resp.status_code == 200
