# API guide

Interactive documentation is available at `/docs`; ReDoc is at `/redoc`.

## Start a streaming research job

```bash
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"topic":"How will solid-state batteries affect aviation?"}'
```

```json
{
  "job_id": "c832d1e4-...",
  "status": "queued",
  "stream_url": "/api/v1/research/c832d1e4-.../events",
  "websocket_url": "/api/v1/research/c832d1e4-.../ws"
}
```

Subscribe with `EventSource`:

```js
const stream = new EventSource(`/api/v1/research/${jobId}/events`);
stream.addEventListener("agent", event => {
  const update = JSON.parse(event.data);
  console.log(update.agent, update.status, update.progress);
});
stream.addEventListener("job", event => {
  const update = JSON.parse(event.data);
  if (["completed", "failed"].includes(update.status)) stream.close();
});
```

The WebSocket endpoint emits the same JSON event objects. Both transports replay
the durable timeline before sending live events.

## Compatibility endpoint

Existing clients can continue to call:

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic":"Retrieval-augmented generation"}'
```

It blocks until complete and returns the unchanged `topic`, `result`, and
`report_path` fields.

## Authentication

Register or log in through `/api/v1/auth/register` and
`/api/v1/auth/login`. Pass the returned token as:

```text
Authorization: Bearer <token>
```

Set `AUTH_REQUIRED=true` to require authentication for research and
configuration endpoints. Google and GitHub OAuth activate when their client ID
and secret environment variables are present.

## Important resources

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/research` | Start background research |
| `GET` | `/api/v1/research/{id}/events` | SSE event stream |
| `WS` | `/api/v1/research/{id}/ws` | WebSocket event stream |
| `GET` | `/api/v1/reports` | Search report history |
| `GET` | `/api/v1/reports/{id}` | Report, sources, citations, graph, timeline |
| `GET` | `/api/v1/reports/{id}/export/{format}` | Export artifact |
| `POST` | `/api/v1/knowledge/search` | Semantic history search |
| `GET` | `/api/v1/analytics` | Aggregate operational metrics |
| `GET/PUT` | `/api/v1/config` | User research configuration |
| `GET/POST` | `/api/v1/prompts` | Versioned prompt library |
| `POST` | `/api/v1/playground` | Run one agent independently |
