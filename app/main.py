from fastapi import FastAPI

from app.routers import genres, items, languages, platforms, search

app = FastAPI(title="MediaShelf")

app.include_router(items.router)
app.include_router(languages.router)
app.include_router(platforms.router)
app.include_router(genres.router)
app.include_router(search.router)


@app.get("/health")
def health():
    return {"status": "ok"}
