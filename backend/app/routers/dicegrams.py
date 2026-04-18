from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db import get_session
from ..deps import current_user
from ..models import Dicegram, User

router = APIRouter(prefix="/api/dicegrams", tags=["dicegrams"])


class DicegramIn(BaseModel):
    name: str
    source: str = ""


class DicegramOut(BaseModel):
    id: int
    name: str
    source: str
    created_at: datetime
    updated_at: datetime


def _to_out(d: Dicegram) -> DicegramOut:
    return DicegramOut.model_validate(d, from_attributes=True)


@router.get("", response_model=list[DicegramOut])
def list_dicegrams(
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(Dicegram)
        .where(Dicegram.owner_id == user.id)
        .order_by(Dicegram.updated_at.desc())
    ).all()
    return [_to_out(d) for d in rows]


@router.post("", response_model=DicegramOut, status_code=status.HTTP_201_CREATED)
def create_dicegram(
    data: DicegramIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    d = Dicegram(owner_id=user.id, name=data.name, source=data.source)
    session.add(d)
    session.commit()
    session.refresh(d)
    return _to_out(d)


@router.get("/{dicegram_id}", response_model=DicegramOut)
def get_dicegram(
    dicegram_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    d = session.get(Dicegram, dicegram_id)
    if not d or d.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return _to_out(d)


@router.put("/{dicegram_id}", response_model=DicegramOut)
def update_dicegram(
    dicegram_id: int,
    data: DicegramIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    d = session.get(Dicegram, dicegram_id)
    if not d or d.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    d.name = data.name
    d.source = data.source
    d.updated_at = datetime.now(timezone.utc)
    session.add(d)
    session.commit()
    session.refresh(d)
    return _to_out(d)


@router.delete("/{dicegram_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dicegram(
    dicegram_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    d = session.get(Dicegram, dicegram_id)
    if not d or d.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    session.delete(d)
    session.commit()
