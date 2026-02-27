from datetime import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.stop import Stop, StopStatus

router = APIRouter()


class StopCreate(BaseModel):
    address: str
    lat: float
    lng: float
    earliest_time: time
    latest_time: time
    package_weight_kg: float


class StopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    address: str
    lat: float
    lng: float
    earliest_time: time
    latest_time: time
    package_weight_kg: float
    status: StopStatus


@router.get("/", response_model=List[StopResponse])
async def list_stops(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stop))
    return result.scalars().all()


@router.post("/", response_model=StopResponse, status_code=201)
async def create_stop(stop: StopCreate, db: AsyncSession = Depends(get_db)):
    db_stop = Stop(**stop.model_dump())
    db.add(db_stop)
    await db.commit()
    await db.refresh(db_stop)
    return db_stop


@router.get("/{stop_id}", response_model=StopResponse)
async def get_stop(stop_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stop).where(Stop.id == stop_id))
    stop = result.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop
