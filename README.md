# RO AI Recommendation Engine

A Netflix-style, production-shaped recommendation system: multi-source candidate generation (ALS + content-based + trending + session), LightGBM learning-to-rank, and MMR diversity reranking, served behind a FastAPI gateway with a Next.js 14 frontend.

## Architecture

```
                         ┌──────────────────────────────────────────────┐
                         │                Frontend (Next.js)            │
                         │  /browse  /watch  /search  /profile  /login  │
                         └───────────────┬──────────────────────────────┘
                                         │ HTTPS + JWT
                                         ▼
                   ┌─────────────────────────────────────────┐
                   │          API Gateway (FastAPI)          │
                   │  auth / users / content / events / ... │
                   │  Prometheus /metrics   rate-limit 100/m │
                   └─────┬───────────────┬───────────────┬───┘
                         │               │               │
                 ┌───────▼──────┐  ┌─────▼──────┐  ┌─────▼──────────┐
                 │  PostgreSQL  │  │   Redis    │  │     Kafka      │
                 │  async SQLA  │  │  cache +   │  │  user.events   │
                 │  partitioned │  │  trending  │  │  retrain.trig  │
                 │  interactions│  │  seen sets │  │  dlq topics    │
                 └──────────────┘  └────────────┘  └────┬───────────┘
                                                        │
      ┌─────────────────────────────────────────────────┴──────────────────┐
      ▼                                                                    ▼
┌───────────────────────────┐                           ┌───────────────────────────────┐
│       ML Service          │                           │       Event Service           │
│  ALS + 2-tower + FAISS    │                           │  user-event consumer → PG+CH  │
│  LightGBM LTR ranker      │                           │  cache-invalidation consumer  │
│  MMR reranker + rules     │                           │  retrain-trigger (10k events) │
│  /ml/recommend            │                           │  DLQ for malformed events     │
└───────────────────────────┘                           └───────────────────────────────┘
```

## Prerequisites

- Docker + Docker Compose v2
- Python 3.11 (for running the seed script on host, if not using compose)
- Node 20 (for frontend dev without docker)
- ~6 GB RAM free for the full stack

## Local setup

```bash
cp .env.example .env

# Bring the whole stack up
docker compose -f infra/docker-compose.yml up --build

# In a second terminal: run migrations
docker compose -f infra/docker-compose.yml exec api alembic upgrade head

# Seed data (optional but recommended — generates 1000 titles, 500 users, 50k events,
# trains initial ALS, builds FAISS index, precomputes snapshots)
pip install -r scripts/requirements.txt
SYNC_DATABASE_URL=postgresql://recuser:recpass@localhost:5432/recengine python scripts/seed.py

# Visit
open http://localhost:3000          # Frontend
open http://localhost:8000/docs     # Swagger UI
open http://localhost:8001/docs     # ML service Swagger
open http://localhost:9090          # Prometheus
open http://localhost:3001          # Grafana (admin/admin)
```

Default seeded users: `user0@example.com` … `user499@example.com` (password `password123`). `user0` is admin.

## Environment variables

See `.env.example`. Key vars:

| Name | Purpose |
|---|---|
| `DATABASE_URL` | Async Postgres URL (`postgresql+asyncpg://…`) |
| `SYNC_DATABASE_URL` | Sync URL (Alembic, seed script) |
| `REDIS_URL` | Redis for cache, trending ZSET, refresh tokens, seen sets |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers for event stream |
| `SECRET_KEY` | JWT signing key — **must be ≥32 chars in prod** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime (stored in Redis) |
| `ML_SERVICE_URL` | URL the API uses to call the ML service |
| `MODEL_VERSION` | Version stamp embedded in responses |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Celery backend (Redis) |

## Running training scripts

Training scripts live in `backend/ml_service/training/` and operate on parquet files in `data/`. The seed script writes the same artifacts that training produces.

```bash
cd backend/ml_service

python training/train_als.py \
  --interactions-path ../../data/interactions.parquet \
  --output-path artifacts/als

python training/generate_embeddings.py \
  --content-path ../../data/content.csv \
  --output-path artifacts/faiss

python training/train_two_tower.py \
  --interactions-path ../../data/interactions.parquet \
  --output-path artifacts/two_tower

python training/train_ranker.py \
  --features-path ../../data/ranker_features.parquet \
  --output-path artifacts/ranker/ltr.txt
```

Evaluation: `python -m evaluation.metrics` or call `evaluate_all(...)` from your own script against a held-out set. Printed metrics include `precision@k`, `recall@k`, `ndcg@k`, `map@k`.

## Running tests

```bash
# API
cd backend/api && pytest --cov=. --cov-report=term

# ML service
cd backend/ml_service && pytest tests/ -q

# Frontend
cd frontend && npm run typecheck && npm run lint && npm test
```

## Key API contracts

```
POST /auth/register              →  { user_id, access_token, refresh_token }
POST /auth/login                 →  { access_token, refresh_token, expires_in }
POST /auth/refresh               →  new token pair (rotating, old refresh revoked)

GET  /users/me                   →  current user
GET  /users/me/preferences       →  onboarding-aware preferences
PUT  /users/me/preferences       →  upsert

GET  /content?limit=20&offset=0  →  active content (by popularity)
GET  /content/{id}               →  single item
POST /content                    →  admin only
PATCH /content/{id}              →  admin only
GET  /content/genres             →  all genres

GET  /recommendations/{surface}?limit=20  →  { surface, items, generated_at, model_version }
     surface ∈ {home, trending, because_you_watched, continue_watching, new_releases}

POST /events/ingest              →  { accepted, rejected } + Kafka publish

GET  /search?q=...&limit=20      →  { query, results[] }
GET  /users/me/history           →  watch history
GET  /users/me/watchlist         →  user watchlist
POST /users/me/watchlist/{id}    →  add
POST /users/me/ratings/{id}      →  { rating: 1..5 }

GET  /admin/metrics              →  admin-only Prometheus scrape
POST /admin/model/retrain        →  enqueue Celery retrain
GET  /health                     →  DB + Redis + Kafka status
GET  /metrics                    →  public Prometheus scrape
```

## Production deployment (EKS)

1. Provision infra via Terraform:
   ```bash
   cd infra/terraform
   terraform init
   terraform apply
   ```
   Creates VPC, EKS cluster (general + ml node groups), RDS Postgres 15, ElastiCache Redis 7, MSK Kafka cluster.

2. Build + push images to ECR (see `.github/workflows/ci.yml`).

3. Deploy manifests — done automatically via `.github/workflows/deploy.yml` on successful `main` CI, or manually:
   ```bash
   aws eks update-kubeconfig --name ro-rec-engine --region us-east-1
   kubectl apply -f infra/k8s/
   ```

The API deployment includes an HPA scaling 3→10 pods at 70% CPU utilization. The ML service has its own tainted node group so heavy inference doesn't starve the API pods.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind, React Query, Zustand |
| API | FastAPI, Pydantic v2, SQLAlchemy 2 async, asyncpg, slowapi, python-jose, passlib |
| ML | PyTorch 2, implicit (ALS), sentence-transformers, FAISS, LightGBM, scikit-learn |
| Data | PostgreSQL 15 (partitioned interactions), Redis 7 (cache + ZSET + SET), ClickHouse (event analytics) |
| Streaming | Apache Kafka (confluent-kafka), user.events + retrain.trigger + DLQ topics |
| Queue | Celery + Redis broker |
| Observability | Prometheus client, Grafana, custom request/latency/cache metrics |
| CI/CD | GitHub Actions (test → build → ECR → kubectl apply) |
| Infra | Terraform (VPC + EKS + RDS + ElastiCache + MSK), k8s manifests + HPA + Ingress |
| Container | Docker + docker-compose for local; standalone Next.js + multi-stage builds for prod |

## Repository layout

```
ro-ai-recommendation-engine/
├── frontend/                  Next.js app (app router, TS, Tailwind)
├── backend/
│   ├── api/                   FastAPI: auth, content, recommendations, events, admin, Celery
│   ├── ml_service/            Candidate gen, LTR ranker, MMR reranker, training scripts
│   └── event_service/         Kafka consumers (event write, cache inval, retrain trigger)
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── k8s/                   Deployments, Services, HPA, Ingress
│   ├── terraform/             EKS + RDS + ElastiCache + MSK
│   ├── prometheus/            scrape config
│   └── grafana/               provisioning
├── scripts/
│   └── seed.py                Faker data, trains ALS, builds FAISS, precomputes snapshots
└── .github/workflows/         CI + deploy
```
