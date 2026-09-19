import respx
from httpx import Response

from app.integrations.itunes import ITunesPodcastProvider


@respx.mock
def test_normalizes_podcast_result():
    respx.get("https://itunes.apple.com/search").mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "collectionName": "Nerdland",
                        "artistName": "Lieven Scheire",
                        "releaseDate": "2019-03-01T00:00:00Z",
                        "artworkUrl600": "https://example.com/cover.jpg",
                        "feedUrl": "https://feeds.example.com/nerdland.rss",
                        "primaryGenreName": "Science",
                        "trackCount": 131,
                        "collectionId": 123,
                    }
                ]
            },
        )
    )

    result = ITunesPodcastProvider().search("Nerdland")[0]

    assert result.title == "Nerdland"
    assert result.creator == "Lieven Scheire"
    assert result.release_year == 2019
    assert result.feed_url == "https://feeds.example.com/nerdland.rss"
    assert result.external_metadata["itunes_collection_id"] == 123
