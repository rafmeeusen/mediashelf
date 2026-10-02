from app.integrations.base import CombinedProvider
from app.integrations.google_books import GoogleBooksProvider
from app.integrations.itunes import ITunesPodcastProvider
from app.integrations.openlibrary import OpenLibraryProvider
from app.integrations.tmdb import TMDBMovieProvider, TMDBTVProvider

# One shared provider instance per content type, reused by both the JSON
# /search/* endpoints and the "add new item" UI flow.
#
# Books combine two sources: Open Library (good for English-language and
# public-domain works, no key needed) and Google Books (much better
# coverage of non-English/translated editions, e.g. Dutch/Flemish -- see
# app/integrations/google_books.py). Results from both are concatenated.
PROVIDERS = {
    "movie": TMDBMovieProvider(),
    "tv": TMDBTVProvider(),
    "book": CombinedProvider([OpenLibraryProvider(), GoogleBooksProvider()], per_provider_limit=6),
    "podcast": ITunesPodcastProvider(),
}
