import respx
from httpx import Response

from app.integrations.tmdb import TMDBMovieProvider, TMDBTVProvider, get_imdb_id


@respx.mock
def test_movie_provider_normalizes_result():
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

    result = TMDBMovieProvider().search("Matrix")[0]

    assert result.title == "The Matrix"
    assert result.release_year == 1999
    assert result.cover_url == "https://image.tmdb.org/t/p/w500/poster.jpg"
    assert result.external_metadata == {"tmdb_id": 603, "media_type": "movie"}


@respx.mock
def test_tv_provider_uses_name_and_first_air_date():
    respx.get("https://api.themoviedb.org/3/search/tv").mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {"id": 1, "name": "Chernobyl", "first_air_date": "2019-05-06"}
                ]
            },
        )
    )

    result = TMDBTVProvider().search("Chernobyl")[0]

    assert result.title == "Chernobyl"
    assert result.release_year == 2019
    assert result.external_metadata == {"tmdb_id": 1, "media_type": "tv"}


@respx.mock
def test_get_imdb_id():
    respx.get("https://api.themoviedb.org/3/movie/603/external_ids").mock(
        return_value=Response(200, json={"imdb_id": "tt0133093"})
    )

    assert get_imdb_id(603, "movie") == "tt0133093"
