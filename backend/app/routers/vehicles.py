from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.vehicle import Vehicle

router = APIRouter()


class VehicleCreate(BaseModel):
    depot_id: int
    capacity_kg: float
    driver_name: str


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    depot_id: int
    capacity_kg: float
    driver_name: str


@router.get("/", response_model=List[VehicleResponse])
async def list_vehicles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle))
    return result.scalars().all()


@router.post("/", response_model=VehicleResponse, status_code=201)
async def create_vehicle(vehicle: VehicleCreate, db: AsyncSession = Depends(get_db)):
    db_vehicle = Vehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    await db.commit()
    await db.refresh(db_vehicle)
    return db_vehicle


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle
