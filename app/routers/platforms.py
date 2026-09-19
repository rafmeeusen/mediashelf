from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Platform
from app.schemas import PlatformCreate, PlatformOut
from app.services import lookups

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("", response_model=list[PlatformOut])
def list_platforms(db: Session = Depends(get_db)):
    return lookups.list_all(db, Platform)


@router.post("", response_model=PlatformOut, status_code=status.HTTP_201_CREATED)
def create_platform(body: PlatformCreate, db: Session = Depends(get_db)):
    return lookups.create(db, Platform, body.name)


@router.delete("/{platform_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform(platform_id: int, db: Session = Depends(get_db)):
    lookups.delete(db, Platform, platform_id)
