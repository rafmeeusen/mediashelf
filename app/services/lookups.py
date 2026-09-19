from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def list_all(db: Session, model):
    return db.execute(select(model).order_by(model.name)).scalars().all()


def create(db: Session, model, name: str):
    obj = model(name=name)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{model.__name__} with this name already exists",
        )
    db.refresh(obj)
    return obj


def delete(db: Session, model, obj_id: int):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    db.delete(obj)
    db.commit()
