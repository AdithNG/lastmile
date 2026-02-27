from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import routes, stops, vehicles, simulation

app = FastAPI(title="LastMile", version="1.0.0", description="Real-time delivery route optimization engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/routes", tags=["routes"])
app.include_router(stops.router, prefix="/stops", tags=["stops"])
app.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
app.include_router(simulation.router, prefix="/simulation", tags=["simulation"])


@app.on_event("startup")
async def startup():
    from app.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status": "ok"}
