from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import genres, items, languages, platforms, search, ui

app = FastAPI(title="MediaShelf")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(ui.router)
app.include_router(items.router)
app.include_router(languages.router)
app.include_router(platforms.router)
app.include_router(genres.router)
app.include_router(search.router)


@app.get("/health")
def health():
    return {"status": "ok"}
