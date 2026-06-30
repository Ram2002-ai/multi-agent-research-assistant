# Developer guide

## Local setup

```bash
cp .env.example .env
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn backend.api:app --reload
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:4173`. Vite proxies `/api/*` to FastAPI.

## Quality checks

```bash
pytest
ruff check app backend agents tasks tests
cd frontend && npm run build
```

The API tests replace CrewAI with a deterministic fake crew. They never make
provider or search calls.

## Adding a service

1. Put domain logic under `app/services`.
2. Depend on `Repository` or another small interface—not FastAPI globals.
3. Add the service to `Container` in `app/factory.py`.
4. Keep HTTP validation in Pydantic schemas and route handlers.
5. Cover behavior with unit tests, then add one API integration test.

## Changing the agent pipeline

The public compatibility boundary is `build_crew(topic)`. Optional keyword
arguments are permitted, but the positional topic and returned Crew must remain
stable. Keep each task's dependency explicit and preserve the core order:

`Researcher → Teacher → Simplifier → Student → Examiner`

The report compiler is an aggregation stage, not a replacement for an agent.

## Prompt workflow

Prompt records are append-only versions: posting the same name creates the next
version. Test candidate prompts in Agent Playground before copying them into an
agent/task definition. See [PROMPTS.md](PROMPTS.md).
