from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Genre
from app.schemas import GenreCreate, GenreOut
from app.services import lookups

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=list[GenreOut])
def list_genres(db: Session = Depends(get_db)):
    return lookups.list_all(db, Genre)


@router.post("", response_model=GenreOut, status_code=status.HTTP_201_CREATED)
def create_genre(body: GenreCreate, db: Session = Depends(get_db)):
    return lookups.create(db, Genre, body.name)


@router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_genre(genre_id: int, db: Session = Depends(get_db)):
    lookups.delete(db, Genre, genre_id)
