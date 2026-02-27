import asyncio

from celery import Celery
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings

celery_app = Celery(
    "lastmile",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="optimize_routes", bind=True)
def optimize_routes_task(
    self,
    depot_id: int,
    vehicle_ids: list,
    stop_ids: list,
    date: str,
):
    """
    Async optimization wrapped in a sync Celery task.
    Creates its own DB session because Celery workers run outside the
    FastAPI request/response lifecycle.
    """
    async def _run():
        engine = create_async_engine(settings.database_url)
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
        async with SessionLocal() as db:
            from app.services.optimizer import run_optimization
            result = await run_optimization(depot_id, vehicle_ids, stop_ids, date, db)
        await engine.dispose()
        return result

    return asyncio.run(_run())
