import httpx
from loguru import logger

from core.config import settings
from tasks.celery_app import celery_app


@celery_app.task(name="tasks.retrain_task.retrain_all")
def retrain_all() -> dict:
    logger.info("Triggering ML service retrain")
    try:
        resp = httpx.post(f"{settings.ML_SERVICE_URL}/ml/retrain", timeout=30)
        return {"status": resp.status_code, "body": resp.json() if resp.status_code == 200 else None}
    except Exception as e:
        logger.error(f"retrain trigger failed: {e}")
        return {"status": "error", "error": str(e)}
