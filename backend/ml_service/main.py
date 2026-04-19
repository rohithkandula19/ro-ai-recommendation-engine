import os
import time
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException
from loguru import logger
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field
from starlette.responses import Response

from core.config import settings
from core.faiss_index import FaissIndex
from models.als_model import ALSRecommender
from models.ranking_model import LtrRanker
from models.embeddings import TextEmbedder
from pipeline.candidate_generator import CandidateGenerator
from pipeline.feature_builder import FeatureBuilder
from pipeline.ranker import Ranker
from pipeline.reranker import Reranker


ML_REQUESTS = Counter("ml_requests_total", "ML requests", ["surface"])
ML_LATENCY = Histogram("ml_latency_seconds", "ML end-to-end latency", ["surface"])


class MLRecommendRequest(BaseModel):
    user_id: str
    surface: str = "home"
    limit: int = Field(default=20, ge=1, le=200)
    context: dict[str, Any] = Field(default_factory=dict)


class MLRecommendItem(BaseModel):
    content_id: str
    score: float
    sources: list[str]


class MLRecommendResponse(BaseModel):
    items: list[MLRecommendItem]
    latency_ms: float


class MLState:
    def __init__(self):
        self.als: ALSRecommender | None = None
        self.faiss: FaissIndex | None = None
        self.ltr: LtrRanker | None = None
        self.embedder: TextEmbedder | None = None
        self.redis: aioredis.Redis | None = None

    async def load(self):
        als = ALSRecommender()
        als_path = os.path.join(settings.ARTIFACTS_DIR, "als")
        if als.load(als_path):
            self.als = als
            logger.info(f"Loaded ALS from {als_path}")
        else:
            logger.warning(f"No ALS model at {als_path}")

        faiss_idx = FaissIndex()
        faiss_path = os.path.join(settings.ARTIFACTS_DIR, "faiss")
        if faiss_idx.load(faiss_path):
            self.faiss = faiss_idx
            logger.info(f"Loaded FAISS from {faiss_path}")
        else:
            logger.warning(f"No FAISS index at {faiss_path}")

        ltr = LtrRanker()
        ltr_path = os.path.join(settings.ARTIFACTS_DIR, "ranker", "ltr.txt")
        if ltr.load(ltr_path):
            self.ltr = ltr
            logger.info(f"Loaded LTR ranker from {ltr_path}")

        try:
            self.embedder = TextEmbedder(settings.EMBED_MODEL)
            logger.info("Loaded embedder for semantic search")
        except Exception as e:
            logger.warning(f"Embedder load failed: {e}")

        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


state = MLState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await state.load()
    yield
    if state.redis is not None:
        await state.redis.close()


app = FastAPI(title="RO ML Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    redis_ok = False
    try:
        if state.redis is not None:
            redis_ok = await state.redis.ping()
    except Exception:
        pass
    return {
        "status": "ok",
        "als_loaded": state.als is not None,
        "faiss_loaded": state.faiss is not None,
        "ltr_loaded": state.ltr is not None,
        "redis": bool(redis_ok),
        "model_version": settings.MODEL_VERSION,
    }


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/ml/recommend", response_model=MLRecommendResponse)
async def recommend(req: MLRecommendRequest):
    start = time.perf_counter()
    ML_REQUESTS.labels(surface=req.surface).inc()

    top_watched = req.context.get("top_watched", []) or []
    session_items = req.context.get("session_items", []) or []
    seen_ids = set(req.context.get("seen_ids", []) or [])
    content_by_id = req.context.get("content_by_id", {}) or {}
    user_genre_prefs = set(req.context.get("user_genre_prefs", []) or [])
    user_maturity = req.context.get("maturity_rating", "R")

    cg = CandidateGenerator(state.als, state.faiss, state.redis)
    candidates = await cg.generate(req.user_id, top_watched, session_items, k=settings.CANDIDATE_K)

    fb = FeatureBuilder()
    user_features = fb.build_user_features(req.context.get("user", {}) or {})
    item_features = [
        fb.build_item_features(c, content_by_id.get(c["content_id"], {}), user_genre_prefs)
        for c in candidates
    ]

    ranker = Ranker(state.ltr)
    ranked = ranker.rank(candidates, user_features, item_features)

    reranker = Reranker(state.faiss, lambda_=settings.MMR_LAMBDA)
    final = reranker.rerank(ranked, n=req.limit, seen_ids=seen_ids,
                            content_by_id=content_by_id, user_maturity=user_maturity)

    items = [
        MLRecommendItem(
            content_id=it["content_id"],
            score=float(it.get("ranker_score", it.get("score", 0.0))),
            sources=it.get("sources", []),
        )
        for it in final
    ]
    latency_ms = (time.perf_counter() - start) * 1000
    ML_LATENCY.labels(surface=req.surface).observe(latency_ms / 1000.0)
    return MLRecommendResponse(items=items, latency_ms=latency_ms)


@app.post("/ml/retrain")
async def retrain_trigger():
    logger.info("Retrain endpoint hit — in production this enqueues a job")
    return {"status": "queued", "message": "Use training/* scripts to retrain models"}


@app.get("/ml/similar/{content_id}")
async def similar(content_id: str, k: int = 20):
    if state.faiss is None:
        raise HTTPException(status_code=503, detail="FAISS index not loaded")
    if content_id not in state.faiss.id_map:
        raise HTTPException(status_code=404, detail="content not in index")
    import numpy as np
    idx = state.faiss.id_map.index(content_id)
    vec = state.faiss.index.reconstruct(idx)
    return {"results": state.faiss.search(np.array(vec), k=k)}


class SemanticSearchRequest(BaseModel):
    query: str
    k: int = 20


@app.post("/ml/semantic-search")
async def semantic_search(req: SemanticSearchRequest):
    if state.faiss is None or state.embedder is None:
        raise HTTPException(status_code=503, detail="FAISS/embedder not loaded")
    emb = state.embedder.encode([req.query])
    hits = state.faiss.search(emb[0], k=req.k)
    return {"query": req.query, "ids": [h[0] for h in hits]}
