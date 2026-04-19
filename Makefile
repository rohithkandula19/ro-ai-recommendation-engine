.PHONY: up down migrate seed ingest-all test lint clean reset logs backup restore distroless e2e load

up:
	docker compose -f infra/docker-compose.yml up --build -d

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f --tail=100 api ml_service event_service

migrate:
	docker compose -f infra/docker-compose.yml run --rm --no-deps api alembic upgrade head

reset: down
	docker compose -f infra/docker-compose.yml down -v
	$(MAKE) up
	sleep 8
	$(MAKE) migrate

seed:
	docker cp scripts/seed.py infra-ml_service-1:/tmp/seed.py
	docker cp scripts/real_content.json infra-ml_service-1:/tmp/real_content.json
	docker cp scripts/trakt_ingested.json infra-ml_service-1:/tmp/trakt_ingested.json 2>/dev/null || true
	docker cp scripts/tvmaze_ingested.json infra-ml_service-1:/tmp/tvmaze_ingested.json 2>/dev/null || true
	docker exec -e SYNC_DATABASE_URL=postgresql://recuser:recpass@postgres:5432/recengine \
		infra-ml_service-1 python /tmp/seed.py --users 100 --interactions 15000 --reset --artifacts-dir /app/artifacts

ingest-tvmaze:
	docker cp scripts/ingest_tvmaze.py infra-api-1:/tmp/
	docker exec infra-api-1 python /tmp/ingest_tvmaze.py --count 400 --output /tmp/tvmaze_ingested.json
	docker cp infra-api-1:/tmp/tvmaze_ingested.json scripts/tvmaze_ingested.json

ingest-trakt:
	docker cp scripts/ingest_trakt.py infra-api-1:/tmp/
	docker exec -e TRAKT_CLIENT_ID=$${TRAKT_CLIENT_ID} infra-api-1 python /tmp/ingest_trakt.py --pages 8 --output /tmp/trakt_ingested.json
	docker cp infra-api-1:/tmp/trakt_ingested.json scripts/trakt_ingested.json

ingest-episodes:
	docker cp scripts/ingest_episodes.py infra-api-1:/tmp/
	docker exec -e SYNC_DATABASE_URL=postgresql://recuser:recpass@postgres:5432/recengine \
		infra-api-1 python /tmp/ingest_episodes.py

ingest-cast:
	docker cp scripts/ingest_cast.py infra-api-1:/tmp/
	docker exec -e SYNC_DATABASE_URL=postgresql://recuser:recpass@postgres:5432/recengine \
		infra-api-1 python /tmp/ingest_cast.py

ingest-all: ingest-tvmaze ingest-trakt seed ingest-episodes ingest-cast

test:
	cd backend/api && pytest -q
	cd backend/ml_service && pytest tests/ -q
	cd frontend && npm run typecheck

e2e:
	cd tests && npx playwright test

load:
	locust -f tests/locustfile.py --host=http://localhost:8000 --headless --users 30 --spawn-rate 5 -t 60s

lint:
	cd backend/api && ruff check . && black --check .
	cd frontend && npm run lint

backup:
	@mkdir -p backups
	docker exec infra-postgres-1 pg_dump -U recuser recengine | gzip > backups/db-$$(date +%Y%m%d-%H%M%S).sql.gz
	tar -czf backups/artifacts-$$(date +%Y%m%d-%H%M%S).tar.gz -C backend/ml_service artifacts
	@echo "Backup written to ./backups/"

restore:
	@read -p "path to db-*.sql.gz: " p; gunzip -c $$p | docker exec -i infra-postgres-1 psql -U recuser recengine

clean:
	docker compose -f infra/docker-compose.yml down -v
	rm -rf backend/ml_service/artifacts/* backups/*
