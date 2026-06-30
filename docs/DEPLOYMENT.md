# Deployment guide

## Docker Compose

1. Copy `.env.example` to `.env`.
2. Set provider keys, a random `JWT_SECRET`, and `POSTGRES_PASSWORD`.
3. Run `docker compose up --build -d`.
4. Check `http://localhost:8000/health`.

Compose builds the React application into the FastAPI image, starts PostgreSQL,
and mounts reports and logs into durable volumes. Run Qdrant as an optional
profile with `docker compose --profile qdrant up -d`.

## Production checklist

- Set `APP_ENV=production` and a 32+ byte random `JWT_SECRET`.
- Set `AUTH_REQUIRED=true` unless anonymous research is intentional.
- Use HTTPS at the ingress and forward proxy headers.
- Restrict `CORS_ORIGINS` to deployed UI origins.
- Store API keys in the deployment secret manager.
- Back up PostgreSQL and the artifact/object-storage target.
- Set CPU/memory limits; CrewAI jobs are provider-latency heavy.
- Ship `logs/*.log` to the platform log collector.
- Add a distributed worker/broker before scaling beyond one API replica.
- Apply request quotas and provider budget alerts.

## Database

Set:

```text
DATABASE_URL=postgresql+psycopg://user:password@host:5432/research
```

The application creates missing tables on startup. For a long-lived production
deployment, introduce Alembic migrations before making schema changes.

## OAuth callbacks

Configure these callbacks at the provider:

- `https://your-host/api/v1/auth/oauth/google/callback`
- `https://your-host/api/v1/auth/oauth/github/callback`

Set `OAUTH_SUCCESS_URL` to the deployed frontend origin.
