from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Language
from app.schemas import LanguageCreate, LanguageOut
from app.services import lookups

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("", response_model=list[LanguageOut])
def list_languages(db: Session = Depends(get_db)):
    return lookups.list_all(db, Language)


@router.post("", response_model=LanguageOut, status_code=status.HTTP_201_CREATED)
def create_language(body: LanguageCreate, db: Session = Depends(get_db)):
    return lookups.create(db, Language, body.name)


@router.delete("/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_language(language_id: int, db: Session = Depends(get_db)):
    lookups.delete(db, Language, language_id)
