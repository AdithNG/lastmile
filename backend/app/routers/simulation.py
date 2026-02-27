from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.simulator import generate_scenario, inject_traffic_event

router = APIRouter()


class SimulationConfig(BaseModel):
    city: str = "seattle"
    num_stops: int = 20
    num_vehicles: int = 3
    seed: Optional[int] = None


class TrafficInjectRequest(BaseModel):
    route_id: int
    delay_factor: float = 1.5


@router.post("/start")
async def start_simulation(config: SimulationConfig, db: AsyncSession = Depends(get_db)):
    """
    Generate a realistic scenario and return IDs ready for /routes/optimize.
    The frontend calls this first, then immediately calls /routes/optimize
    with the returned depot_id / vehicle_ids / stop_ids.
    """
    return await generate_scenario(
        city=config.city,
        num_stops=config.num_stops,
        num_vehicles=config.num_vehicles,
        seed=config.seed,
        db=db,
    )


@router.post("/inject-traffic")
async def inject_traffic(req: TrafficInjectRequest):
    """
    Emit a synthetic traffic event.
    The frontend passes this to POST /routes/{route_id}/reroute to trigger
    live rerouting and see the route update on the map.
    """
    return inject_traffic_event(req.route_id, req.delay_factor)
