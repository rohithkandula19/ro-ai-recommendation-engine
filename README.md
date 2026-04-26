<div align="center">

<img src="https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js" />
<img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi" />
<img src="https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=for-the-badge&logo=pytorch" />
<img src="https://img.shields.io/badge/Apache_Kafka-streaming-231F20?style=for-the-badge&logo=apachekafka" />
<img src="https://img.shields.io/badge/LightGBM-LTR-02569B?style=for-the-badge" />
<img src="https://img.shields.io/badge/FAISS-semantic_search-blue?style=for-the-badge" />
<img src="https://img.shields.io/badge/Docker-compose-2496ED?style=for-the-badge&logo=docker" />
<img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql" />

# RO RecEngine

**A full-stack, production-shaped AI recommendation system — Netflix without the subscription.**

*Collaborative filtering · Learning-to-rank · Semantic search · Real-time event streaming · AI chat assistant*

[Live Demo](#local-setup) · [API Docs](http://localhost:8000/docs) · [ML Service](http://localhost:8001/docs)

</div>

---

## What is RO RecEngine?

RO RecEngine is a Netflix-clone recommendation platform built from first principles — not a tutorial project, not a Jupyter notebook demo. It's a multi-service system that combines **collaborative filtering (ALS)**, **content embeddings (sentence-transformers + FAISS)**, **a LightGBM learning-to-rank pipeline**, and **real-time Kafka event streaming** behind a FastAPI gateway with a Next.js 14 frontend styled after Netflix.

Every recommendation shown in the UI is the result of a real ML pipeline: candidates are generated from multiple signals, reranked with a trained LTR model, diversity-reranked via MMR, and served with a latency budget. The system also ships an **AI chat assistant** ("Ask RO") powered by Claude that understands your taste and recommends films conversationally.

The goal: take every layer of a real recommendation system — data ingestion, model training, serving, event streaming, observability — and build it end to end.

---

## Features

| Area | What's built |
|---|---|
| **Recommendations** | ALS collaborative filtering · content-based cosine similarity · trending ZSET · session-based "continue watching" · multi-armed bandit exploration |
| **Ranking** | LightGBM LTR ranker trained on 50k+ interaction events with 20+ features; MMR diversity reranking |
| **Semantic Search** | sentence-transformers embeddings → FAISS IVF index; typo-tolerant full-text search fallback |
| **AI Chat** | Claude-powered "Ask RO" chat with slash commands, message threads, thinking badge, inline title cards |
| **Streaming** | Kafka topics: `user.events`, `retrain.trigger`, DLQ; auto-retrain after 10k new events |
| **Frontend** | Netflix-style UI: transparent→solid navbar, card hover expansion, fullscreen YouTube trailers, 3D tilt, scroll-reveal, shimmer skeletons |
| **Auth** | JWT access + rotating refresh tokens; bcrypt passwords; token revocation via Redis SET |
| **Data** | TMDB API integration: real posters, backdrops, YouTube trailer IDs for 891 titles |
| **Observability** | Prometheus metrics, Grafana dashboards, custom latency / cache-hit / event-lag metrics |
| **Admin** | Admin panel, feature flags, live WebSocket dashboard, A/B experiment management |
| **Infra** | Docker Compose locally; Kubernetes + Terraform (EKS + RDS + ElastiCache + MSK) for prod |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Next.js 14 Frontend                        │
│   /browse  /watch  /search  /chat  /profile  /admin  /pro       │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTPS + JWT
                           ▼
         ┌─────────────────────────────────────┐
         │         FastAPI Gateway             │
         │  auth · content · events · admin    │
         │  Prometheus /metrics  · rate-limit  │
         └────────┬──────────────┬─────────────┘
                  │              │
       ┌──────────▼───┐    ┌─────▼──────┐    ┌────────────┐
       │  PostgreSQL  │    │   Redis    │    │   Kafka    │
       │  (async SQLA)│    │  cache +   │    │ user.events│
       │  partitioned │    │  trending  │    │ retrain    │
       │  interactions│    │  seen sets │    │ DLQ topics │
       └──────────────┘    └────────────┘    └─────┬──────┘
                                                   │
     ┌─────────────────────────────────────────────┴──────────┐
     ▼                                                         ▼
┌──────────────────────────┐               ┌────────────────────────────┐
│       ML Service         │               │       Event Service         │
│  ALS + 2-tower + FAISS   │               │  user-event consumer → PG  │
│  LightGBM LTR ranker     │               │  cache-invalidation handler│
│  MMR reranker + rules    │               │  retrain trigger (10k evts)│
│  /ml/recommend           │               │  DLQ for malformed events  │
└──────────────────────────┘               └────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router) · React 18 · TypeScript · Tailwind CSS · React Query · Zustand |
| **API** | FastAPI · Pydantic v2 · SQLAlchemy 2 async · asyncpg · slowapi · python-jose · passlib |
| **ML** | PyTorch 2 · implicit (ALS) · sentence-transformers · FAISS · LightGBM · scikit-learn |
| **Data** | PostgreSQL 15 (partitioned interactions table) · Redis 7 (cache + ZSET + SET) |
| **Streaming** | Apache Kafka (confluent-kafka) · ZooKeeper |
| **AI** | Claude claude-sonnet-4-6 — chat, recommendations, slash commands, streaming |
| **Queue** | Celery + Redis broker |
| **Observability** | Prometheus · Grafana · custom request / latency / cache-hit metrics |
| **CI/CD** | GitHub Actions — test → build → ECR push → `kubectl apply` |
| **Infra** | Terraform (VPC + EKS + RDS + ElastiCache + MSK) · Kubernetes (HPA + Ingress) |
| **Container** | Docker Compose (local) · multi-stage Docker builds (prod) |

---

## ML Pipeline

```
User request
     │
     ▼
Candidate Generation (parallel)
  ├── ALS collaborative filtering      →  ~200 candidates
  ├── Content-based (FAISS cosine)     →  ~100 candidates
  ├── Trending ZSET (Redis)            →   ~50 candidates
  ├── Session-based (last 5 watched)   →   ~50 candidates
  └── Popularity fallback              →   ~50 candidates
                    │
                    ▼  (union, deduplicate)
             ~300 raw candidates
                    │
                    ▼
          Feature Engineering
    (user affinity · genre overlap · recency
     rating delta · watch-ratio · trending score)
                    │
                    ▼
        LightGBM LTR Ranker
        (trained on 50k interaction events,
         80 training groups, lambdarank objective)
                    │
                    ▼
          MMR Diversity Reranker
          (λ=0.7, deduplicates genres)
                    │
                    ▼
         Final N recommendations
         + match score + reason_text
```

---

## Engineering Challenges

### 1. Kafka broker crash on restart — ZooKeeper stale ephemeral node
Kafka stores its broker ID as an ephemeral node in ZooKeeper. When the container crashed mid-session, the node persisted until ZooKeeper's session timeout expired. The next startup threw `NodeExistsException` and Kafka never came up. The fix was two-fold: delete the stale volume (`infra_kafkadata`), and add a ZooKeeper healthcheck using `nc -z localhost 2181` — the `ruok` command was disabled in this ZooKeeper version. Kafka's `depends_on` now waits for `service_healthy` before starting.

### 2. 428 poster images stuck on picsum.photos
The original seed script ran before the TMDB API key was configured, so every title got a `picsum.photos` placeholder. Wrote a backfill script that queries all content with picsum thumbnails, searches TMDB by title + year, and updates `thumbnail_url`, `backdrop_url`, and `youtube_trailer_id` in one pass. Result: 428/428 matched, 515 items now have real TMDB images.

### 3. 742 YouTube trailer IDs from zero
The seed script hardcoded a Big Buck Bunny placeholder trailer URL for all 891 titles. Wrote a second backfill that NULLed out the old URL column and ran every title through TMDB's videos endpoint to find real YouTube trailer IDs. 742/891 titles now have real trailers; the rest gracefully hide the "Play Trailer" button.

### 4. LTR training stability — FAISS + LightGBM pipeline
Early training attempts produced NaN loss. Root cause: interaction weights included zero-division when normalizing sparse ALS output. Fixed by clipping item factors to a minimum L2-norm before cosine scoring. The final ranker trains on 80 query groups (one per user sample), 30 features, lambdarank objective. NDCG@10 ≈ 0.72 on held-out set.

### 5. Semantic search latency budget
Full FAISS flat-index search over 891 sentence-transformer embeddings took ~200ms cold. Switched to `IndexIVFFlat` with `nlist=32`, reducing search to ~18ms at the cost of ~2% recall. Cache layer in Redis (TTL 5m) drops repeat queries to <1ms.

### 6. Real-time streaming architecture without backpressure buildup
The event consumer initially wrote to Postgres synchronously, causing lag spikes when write volume exceeded ~500 events/s during load testing. Refactored to batch-insert with a 500ms flush window, reducing lag from 4s to <80ms at 2k events/s sustained.

---

## Local Setup

**Prerequisites:** Docker + Docker Compose v2, ~6 GB RAM

```bash
# 1. Clone and configure
git clone https://github.com/rohithkandula19/ro-ai-recommendation-engine.git
cd ro-ai-recommendation-engine
cp .env.example .env
# Add your TMDB_API_KEY and ANTHROPIC_API_KEY to .env

# 2. Start all services
docker compose -f infra/docker-compose.yml up --build

# 3. Run migrations (new terminal)
docker compose -f infra/docker-compose.yml exec api alembic upgrade head

# 4. Seed data — 1000 titles, 500 users, 50k events, trains ALS, builds FAISS
pip install -r scripts/requirements.txt
SYNC_DATABASE_URL=postgresql://recuser:recpass@localhost:5432/recengine \
  python scripts/seed.py

# 5. Open
open http://localhost:3000          # Frontend
open http://localhost:8000/docs     # API Swagger
open http://localhost:8001/docs     # ML service Swagger
open http://localhost:9090          # Prometheus
open http://localhost:3001          # Grafana (admin / admin)
```

**Default users:** `user0@example.com` … `user499@example.com` · password: `password123`  
`user0@example.com` has admin access.

---

## Key API Contracts

```
POST  /auth/register                →  { user_id, access_token, refresh_token }
POST  /auth/login                   →  { access_token, refresh_token, expires_in }
POST  /auth/refresh                 →  rotating token pair

GET   /recommendations/{surface}    →  { items[], model_version, generated_at }
      surface: home | trending | because_you_watched | continue_watching | new_releases

POST  /search/semantic              →  { results[] }  (sentence-transformers + FAISS)
GET   /search?q=...                 →  { results[] }  (full-text fallback)

POST  /events/ingest                →  { accepted, rejected } + Kafka publish

GET   /content/{id}                 →  full item with backdrop_url + youtube_trailer_id
GET   /content/genres               →  genre list

POST  /users/me/ratings/{id}        →  { rating: 1..5 }
POST  /users/me/watchlist/{id}      →  add to watchlist
GET   /users/me/history             →  watch history

GET   /health                       →  DB + Redis + Kafka status
GET   /metrics                      →  Prometheus scrape
```

---

## Repository Layout

```
ro-ai-recommendation-engine/
├── frontend/                  Next.js 14 app — pages, components, hooks, stores
│   ├── app/                   App Router pages (browse, watch, chat, profile, admin)
│   ├── components/            UI components (cards, navbar, chat, content, layout)
│   └── hooks/ lib/ types/     React Query hooks, API client, TypeScript types
├── backend/
│   ├── api/                   FastAPI — auth, content, recommendations, events, admin
│   │   ├── routers/           Route handlers
│   │   ├── models/            SQLAlchemy ORM models
│   │   ├── ml/                Recommendation orchestration layer
│   │   └── migrations/        Alembic migration versions
│   ├── ml_service/            Candidate gen, LTR ranker, MMR, training scripts
│   │   ├── training/          train_als.py, train_ranker.py, generate_embeddings.py
│   │   ├── ranker/            LightGBM inference
│   │   └── evaluation/        precision@k, recall@k, ndcg@k, map@k
│   └── event_service/         Kafka consumers
├── scripts/                   seed.py, backfill_tmdb_images.py, seed_availability_demo.py
├── infra/
│   ├── docker-compose.yml     Local dev stack
│   ├── k8s/                   Kubernetes manifests + HPA + Ingress
│   ├── terraform/             EKS + RDS + ElastiCache + MSK provisioning
│   ├── prometheus/            Scrape config
│   └── grafana/               Dashboard provisioning
└── .github/workflows/         CI (test → build → ECR) + CD (kubectl apply)
```

---

## Production Deployment (EKS)

```bash
# 1. Provision infra
cd infra/terraform
terraform init && terraform apply
# Creates: VPC · EKS cluster · RDS Postgres 15 · ElastiCache Redis 7 · MSK Kafka

# 2. Push images (CI handles this automatically on main branch)
# See .github/workflows/ci.yml

# 3. Apply manifests
aws eks update-kubeconfig --name ro-rec-engine --region us-east-1
kubectl apply -f infra/k8s/
```

The API deployment runs 3→10 pods with HPA at 70% CPU. The ML service runs on a tainted node group so heavy inference doesn't starve API pods.

---

<div align="center">

Built by **Rohith Kandula**

[GitHub](https://github.com/rohithkandula19) · [LinkedIn](https://linkedin.com/in/rohithkandula)

*Every recommendation is real ML — no hardcoded results.*

</div>
