from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.route import Route, RouteStop
from app.models.stop import Stop
from app.workers.celery_tasks import celery_app, optimize_routes_task

router = APIRouter()


# ---------------------------------------------------------------------------
# WebSocket connection manager — broadcast route updates to connected clients
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, route_id: str, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(route_id, []).append(ws)

    def disconnect(self, route_id: str, ws: WebSocket):
        if route_id in self._connections:
            self._connections[route_id].discard(ws) if hasattr(self._connections[route_id], "discard") else None
            try:
                self._connections[route_id].remove(ws)
            except ValueError:
                pass

    async def broadcast(self, route_id: str, payload: dict):
        dead = []
        for ws in self._connections.get(route_id, []):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(route_id, ws)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class OptimizeRequest(BaseModel):
    depot_id: int
    vehicle_ids: List[int]
    stop_ids: List[int]
    date: date


class RerouteRequest(BaseModel):
    traffic_events: List[dict]  # [{"from_idx": int, "to_idx": int, "delay_factor": float}]


class RouteStopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stop_id: int
    sequence: int
    planned_arrival: str | None


class RouteStopDetail(BaseModel):
    """Full stop data including coordinates — used by the map."""
    stop_id: int
    sequence: int
    planned_arrival: str | None
    lat: float
    lng: float
    address: str
    earliest_time: str
    latest_time: str
    package_weight_kg: float


class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    total_distance_km: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/optimize")
async def optimize(req: OptimizeRequest):
    """
    Submit a routing job. Returns a job_id for polling.
    Route computation runs asynchronously in a Celery worker so the API
    stays responsive while the solver (and ORS API call) run in the background.
    """
    task = optimize_routes_task.delay(
        depot_id=req.depot_id,
        vehicle_ids=req.vehicle_ids,
        stop_ids=req.stop_ids,
        date=str(req.date),
    )
    return {"job_id": task.id, "status": "queued"}


@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """Poll for optimization result. Status: queued → started → done / failed."""
    result = celery_app.AsyncResult(job_id)
    if result.ready():
        if result.successful():
            return {"status": "done", "result": result.get()}
        return {"status": "failed", "error": str(result.result)}
    return {"status": result.status.lower()}


@router.get("/{route_id}/stops", response_model=List[RouteStopResponse])
async def get_route_stops(route_id: int, db: AsyncSession = Depends(get_db)):
    """Return the ordered stop list for a persisted route."""
    result = await db.execute(
        select(RouteStop)
        .where(RouteStop.route_id == route_id)
        .order_by(RouteStop.sequence)
    )
    stops = result.scalars().all()
    if not stops:
        raise HTTPException(status_code=404, detail="Route not found")
    return stops


@router.get("/{route_id}/detail", response_model=List[RouteStopDetail])
async def get_route_detail(route_id: int, db: AsyncSession = Depends(get_db)):
    """
    Return ordered stops with full coordinates and stop metadata.
    Used by the frontend to build map polylines and marker popups.
    """
    route_stops = (
        await db.execute(
            select(RouteStop)
            .where(RouteStop.route_id == route_id)
            .order_by(RouteStop.sequence)
        )
    ).scalars().all()

    if not route_stops:
        raise HTTPException(status_code=404, detail="Route not found")

    detail = []
    for rs in route_stops:
        stop = (await db.execute(select(Stop).where(Stop.id == rs.stop_id))).scalar_one()
        detail.append(RouteStopDetail(
            stop_id=rs.stop_id,
            sequence=rs.sequence,
            planned_arrival=rs.planned_arrival,
            lat=stop.lat,
            lng=stop.lng,
            address=stop.address,
            earliest_time=str(stop.earliest_time),
            latest_time=str(stop.latest_time),
            package_weight_kg=stop.package_weight_kg,
        ))
    return detail


@router.post("/{route_id}/reroute")
async def reroute(route_id: int, req: RerouteRequest, db: AsyncSession = Depends(get_db)):
    """
    Trigger rerouting for an active route given new traffic data.
    Broadcasts the updated route to all WebSocket clients watching this route.
    """
    from app.services.rerouter import reroute_active

    updated = await reroute_active(route_id, req.traffic_events, db)
    await manager.broadcast(str(route_id), {"event": "rerouted", "route": updated})
    return updated


@router.websocket("/ws/{route_id}")
async def websocket_route(websocket: WebSocket, route_id: str):
    """
    WebSocket endpoint — frontend connects here to receive live route updates.
    The rerouter broadcasts to this channel whenever a route changes.
    """
    await manager.connect(route_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive ping from client
    except WebSocketDisconnect:
        manager.disconnect(route_id, websocket)
