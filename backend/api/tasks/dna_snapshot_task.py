import asyncio

from loguru import logger

from core.database import AsyncSessionLocal
from services.dna_snapshot_service import DNASnapshotService
from tasks.celery_app import celery_app


async def _run() -> int:
    async with AsyncSessionLocal() as s:
        return await DNASnapshotService(s).snapshot_all()


@celery_app.task(name="tasks.dna_snapshot_task.snapshot_all_users")
def snapshot_all_users() -> dict:
    count = asyncio.run(_run())
    logger.info(f"Snapshotted DNA for {count} users")
    return {"snapshotted": count}
