from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response

from core.config import settings
from core.database import check_db_health
from core.kafka import check_kafka_health
from core.redis import check_redis_health, close_redis
from core.telemetry import init_sentry, init_telemetry
from middleware.metrics_middleware import MetricsMiddleware
from middleware.request_id import RequestIDMiddleware
from routers import admin, agent, auth, batch, catalog, chat, chat_v2, compliance, content, dna_timeline, events, extras, history, mega, mega2, queues, recommendations, search, unique, users, ws


limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"API starting, model_version={settings.MODEL_VERSION}")
    yield
    await close_redis()
    logger.info("API shutdown complete")


app = FastAPI(
    title="RO AI Recommendation Engine",
    version="1.0.0",
    description="Netflix-style recommendation engine API",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestIDMiddleware)
init_sentry()
init_telemetry(app)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(unique.router)  # must come before content/recommendations to win /recommendations/anti-recs etc.
app.include_router(catalog.router)
app.include_router(content.router)
app.include_router(recommendations.router)
app.include_router(events.router)
app.include_router(search.router)
app.include_router(history.router)
app.include_router(queues.router)
app.include_router(dna_timeline.router)
app.include_router(chat.router)
app.include_router(chat_v2.router)
app.include_router(mega.router)
app.include_router(mega2.router)
app.include_router(batch.router)
app.include_router(ws.router)
app.include_router(agent.router)
app.include_router(compliance.router)
app.include_router(extras.router)
app.include_router(admin.router)


@app.get("/health", tags=["system"])
async def health():
    db_ok = await check_db_health()
    redis_ok = await check_redis_health()
    kafka_ok = check_kafka_health()
    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "db": db_ok,
        "redis": redis_ok,
        "kafka": kafka_ok,
        "model_version": settings.MODEL_VERSION,
    }


@app.get("/metrics", tags=["system"])
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/", tags=["system"])
async def root():
    return {"name": "RO AI Recommendation Engine API", "version": "1.0.0", "docs": "/docs"}
