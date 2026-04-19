# Secrets

This folder is **gitignored**. Before `docker compose up` with prod overlay, create:

```bash
mkdir -p secrets
openssl rand -base64 32 > secrets/db_password.txt
openssl rand -base64 48 > secrets/jwt_secret.txt
echo "sk-or-v1-xxx" > secrets/openrouter_key.txt
chmod 600 secrets/*.txt
```

Then: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml up -d`

Secrets are mounted into containers at `/run/secrets/<name>` and read via
`SECRET_KEY_FILE` / `DB_PASSWORD_FILE` / `OPENROUTER_API_KEY_FILE` env patterns.
