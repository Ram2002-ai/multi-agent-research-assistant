"""FastAPI application factory and versioned API surface."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

import jwt
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

from app.core.logging import close_logging_handlers, configure_logging
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.settings import Settings, settings as default_settings
from app.database.repository import Repository
from app.models.schemas import (
    ConfigUpdate,
    KnowledgeQuery,
    LegacyResearchRequest,
    LegacyResearchResponse,
    PlaygroundRequest,
    PromptCreate,
    ResearchRequest,
    StartResearchResponse,
    UserLogin,
    UserRegister,
)
from app.services.citations import CitationManager
from app.services.diagrams import mermaid_diagrams, research_graph
from app.services.events import EventBroker
from app.services.exporters import ExportService, ExportUnavailable
from app.services.knowledge import KnowledgeBase
from app.services.research import ResearchService
from config import get_llm


logger = logging.getLogger("research.api")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@dataclass(slots=True)
class Container:
    settings: Settings
    repository: Repository
    broker: EventBroker
    knowledge: KnowledgeBase
    exporter: ExportService
    research: ResearchService
    citations: CitationManager


def build_container(settings: Settings) -> Container:
    repository = Repository(settings.database_url)
    broker = EventBroker(repository)
    knowledge = KnowledgeBase(repository, settings.chunk_size)
    exporter = ExportService(settings.output_dir)
    research = ResearchService(repository, broker, knowledge, exporter, settings)
    return Container(
        settings=settings,
        repository=repository,
        broker=broker,
        knowledge=knowledge,
        exporter=exporter,
        research=research,
        citations=CitationManager(),
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or default_settings
    app_settings.prepare_directories()
    log_handlers = configure_logging(app_settings.log_dir)
    container = build_container(app_settings)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        app_settings.validate_production()
        await asyncio.to_thread(container.repository.create_schema)
        application.state.container = container
        logger.info("ResearchOS API started")
        try:
            yield
        finally:
            active = list(container.research._tasks.values())
            for task in active:
                task.cancel()
            if active:
                await asyncio.gather(*active, return_exceptions=True)
            close_logging_handlers(log_handlers)

    app = FastAPI(
        title="ResearchOS · Multi-Agent Research Platform",
        description=(
            "Enterprise research orchestration with live CrewAI agents, persistent "
            "memory, source scoring, analytics, and multi-format reporting."
        ),
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {"name": "Compatibility", "description": "Original stable API contracts."},
            {"name": "Research", "description": "Live research orchestration."},
            {"name": "Reports", "description": "History, citations, graphs, and exports."},
            {"name": "Knowledge", "description": "Long-term semantic memory."},
            {"name": "Platform", "description": "Configuration, prompts, and analytics."},
            {"name": "Authentication", "description": "JWT and OAuth provider discovery."},
        ],
    )
    app.state.container = container
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_container(request: Request) -> Container:
        return request.app.state.container

    async def current_user(
        request: Request,
        token: str | None = Depends(oauth2_scheme),
    ) -> dict[str, Any]:
        current: Container = request.app.state.container
        if not token:
            if current.settings.auth_required:
                raise HTTPException(status_code=401, detail="Authentication required")
            return {"id": "guest", "role": "researcher", "name": "Guest Researcher"}
        try:
            payload = decode_access_token(token, current.settings)
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
        user = await asyncio.to_thread(current.repository.get_user, payload["sub"])
        if not user or not user["active"]:
            raise HTTPException(status_code=401, detail="User is unavailable")
        return user

    @app.exception_handler(ExportUnavailable)
    async def export_error(_: Request, exc: ExportUnavailable):
        return JSONResponse(status_code=501, content={"detail": str(exc)})

    @app.get("/health", tags=["Compatibility"])
    async def health(request: Request):
        current: Container = request.app.state.container
        return {
            "status": "ok",
            "version": app.version,
            "database": current.settings.database_url.split(":", 1)[0],
            "vector_store": current.settings.vector_backend,
        }

    @app.get("/debug_model", tags=["Compatibility"])
    async def debug_model():
        return {"model": get_llm(), "llm": get_llm()}

    @app.post(
        "/research",
        response_model=LegacyResearchResponse,
        tags=["Compatibility"],
        summary="Run research using the original blocking contract",
    )
    async def legacy_research(
        payload: LegacyResearchRequest, current: Container = Depends(get_container)
    ):
        report = await current.research.run_and_wait(payload.topic)
        return LegacyResearchResponse(
            topic=payload.topic,
            result=report["result"],
            report_path=report["report_path"],
        )

    @app.post(
        "/api/v1/research",
        response_model=StartResearchResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["Research"],
    )
    async def start_research(
        payload: ResearchRequest,
        request: Request,
        user: dict = Depends(current_user),
    ):
        current: Container = request.app.state.container
        job_id = await current.research.start(
            payload.topic,
            model=payload.model,
            template=payload.template,
            options=payload.model_dump(),
            user_id=None if user["id"] == "guest" else user["id"],
        )
        return StartResearchResponse(
            job_id=job_id,
            status="queued",
            stream_url=f"/api/v1/research/{job_id}/events",
            websocket_url=f"/api/v1/research/{job_id}/ws",
        )

    @app.get("/api/v1/research/{job_id}", tags=["Research"])
    async def get_research(job_id: str, request: Request):
        current: Container = request.app.state.container
        report = await asyncio.to_thread(current.repository.get_report, job_id)
        if not report:
            raise HTTPException(status_code=404, detail="Research job not found")
        return report

    @app.delete("/api/v1/research/{job_id}", tags=["Research"])
    async def cancel_research(job_id: str, request: Request):
        current: Container = request.app.state.container
        if not await current.research.cancel(job_id):
            raise HTTPException(status_code=409, detail="Job is not running")
        return {"message": "Cancellation requested", "job_id": job_id}

    @app.get("/api/v1/research/{job_id}/events", tags=["Research"])
    async def stream_events(job_id: str, request: Request):
        current: Container = request.app.state.container
        report = await asyncio.to_thread(current.repository.get_report, job_id)
        if not report:
            raise HTTPException(status_code=404, detail="Research job not found")

        async def event_stream() -> AsyncIterator[str]:
            queue = await current.broker.subscribe(job_id)
            last_sequence = 0
            try:
                history = await asyncio.to_thread(current.repository.list_events, job_id)
                terminal_history = False
                for event in history:
                    last_sequence = max(last_sequence, event["sequence"])
                    yield _sse(event)
                    if event["type"] == "job" and event["status"] in {
                        "completed",
                        "failed",
                        "cancelled",
                    }:
                        terminal_history = True
                if terminal_history:
                    return
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=15)
                        if event["sequence"] <= last_sequence:
                            continue
                        last_sequence = event["sequence"]
                        yield _sse(event)
                        if event["type"] == "job" and event["status"] in {
                            "completed",
                            "failed",
                            "cancelled",
                        }:
                            break
                    except asyncio.TimeoutError:
                        latest = await asyncio.to_thread(
                            current.repository.get_report, job_id
                        )
                        yield ": heartbeat\n\n"
                        if latest and latest["status"] in {
                            "completed",
                            "failed",
                            "cancelled",
                        }:
                            break
            finally:
                await current.broker.unsubscribe(job_id, queue)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    @app.websocket("/api/v1/research/{job_id}/ws")
    async def websocket_events(websocket: WebSocket, job_id: str):
        current: Container = websocket.app.state.container
        report = await asyncio.to_thread(current.repository.get_report, job_id)
        if not report:
            await websocket.close(code=4404, reason="Research job not found")
            return
        await websocket.accept()
        queue = await current.broker.subscribe(job_id)
        try:
            history = await asyncio.to_thread(current.repository.list_events, job_id)
            terminal_history = False
            for event in history:
                await websocket.send_json(event)
                if event["type"] == "job" and event["status"] in {
                    "completed",
                    "failed",
                    "cancelled",
                }:
                    terminal_history = True
            if terminal_history:
                return
            while True:
                event = await queue.get()
                await websocket.send_json(event)
                if event["type"] == "job" and event["status"] in {
                    "completed",
                    "failed",
                    "cancelled",
                }:
                    break
        except WebSocketDisconnect:
            pass
        finally:
            await current.broker.unsubscribe(job_id, queue)

    @app.get("/api/v1/reports", tags=["Reports"])
    async def list_reports(
        request: Request,
        limit: int = Query(30, ge=1, le=100),
        saved: bool = False,
        query: str = "",
    ):
        current: Container = request.app.state.container
        reports = await asyncio.to_thread(
            current.repository.list_reports, limit, saved, query
        )
        return {"items": reports, "count": len(reports)}

    @app.get("/api/v1/reports/{report_id}", tags=["Reports"])
    async def report_detail(report_id: str, request: Request):
        current: Container = request.app.state.container
        report = await asyncio.to_thread(current.repository.get_report, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        sources, events = await asyncio.gather(
            asyncio.to_thread(current.repository.list_sources, report_id),
            asyncio.to_thread(current.repository.list_events, report_id),
        )
        return {
            **report,
            "sources": sources,
            "events": events,
            "citations": current.citations.format_all(sources),
            "diagrams": mermaid_diagrams(report["topic"]),
            "graph": research_graph(report["topic"], sources),
        }

    @app.patch("/api/v1/reports/{report_id}/saved", tags=["Reports"])
    async def save_report(report_id: str, request: Request, saved: bool = True):
        current: Container = request.app.state.container
        if not await asyncio.to_thread(current.repository.get_report, report_id):
            raise HTTPException(status_code=404, detail="Report not found")
        await asyncio.to_thread(
            current.repository.update_report, report_id, saved=saved
        )
        return {"id": report_id, "saved": saved}

    @app.delete("/api/v1/reports/{report_id}", tags=["Reports"])
    async def delete_report(report_id: str, request: Request):
        current: Container = request.app.state.container
        deleted = await asyncio.to_thread(current.repository.delete_report, report_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"message": "Report deleted"}

    @app.get("/api/v1/reports/{report_id}/logs", tags=["Reports"])
    async def download_logs(report_id: str, request: Request):
        current: Container = request.app.state.container
        events = await asyncio.to_thread(current.repository.list_events, report_id)
        if not events:
            raise HTTPException(status_code=404, detail="No logs found")
        path = current.settings.output_dir / f"logs_{report_id}.json"
        await asyncio.to_thread(
            path.write_text, json.dumps(events, indent=2), "utf-8"
        )
        return FileResponse(path, filename=path.name, media_type="application/json")

    @app.get("/api/v1/reports/{report_id}/export/{format_name}", tags=["Reports"])
    async def export_report(report_id: str, format_name: str, request: Request):
        current: Container = request.app.state.container
        report = await asyncio.to_thread(current.repository.get_report, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        sources = await asyncio.to_thread(current.repository.list_sources, report_id)
        path = await asyncio.to_thread(
            current.exporter.export, report, sources, format_name
        )
        return FileResponse(path, filename=path.name)

    @app.post("/api/v1/knowledge/search", tags=["Knowledge"])
    async def knowledge_search(payload: KnowledgeQuery, request: Request):
        current: Container = request.app.state.container
        items = await current.knowledge.search(payload.query, payload.limit)
        return {"query": payload.query, "items": items, "count": len(items)}

    @app.get("/api/v1/analytics", tags=["Platform"])
    async def analytics(request: Request):
        current: Container = request.app.state.container
        return await asyncio.to_thread(current.repository.analytics)

    @app.get("/api/v1/config", tags=["Platform"])
    async def get_config(request: Request, user: dict = Depends(current_user)):
        current: Container = request.app.state.container
        stored = await asyncio.to_thread(current.repository.get_config, user["id"])
        return {**_default_config(current.settings), **stored}

    @app.put("/api/v1/config", tags=["Platform"])
    async def set_config(
        payload: ConfigUpdate,
        request: Request,
        user: dict = Depends(current_user),
    ):
        current: Container = request.app.state.container
        return await asyncio.to_thread(
            current.repository.set_config, user["id"], payload.model_dump()
        )

    @app.get("/api/v1/models", tags=["Platform"])
    async def model_catalog():
        return {
            "providers": [
                {
                    "id": "openrouter",
                    "name": "OpenRouter",
                    "models": [
                        "openrouter/meta-llama/llama-3.3-70b-instruct",
                        "openrouter/openai/gpt-4.1",
                        "openrouter/anthropic/claude-sonnet-4",
                        "openrouter/google/gemini-2.5-pro",
                        "openrouter/deepseek/deepseek-chat-v3-0324",
                    ],
                },
                {"id": "openai", "name": "OpenAI", "models": ["openai/gpt-4.1"]},
                {"id": "gemini", "name": "Google Gemini", "models": ["gemini/gemini-2.5-pro"]},
                {"id": "anthropic", "name": "Anthropic", "models": ["anthropic/claude-sonnet-4"]},
                {"id": "groq", "name": "Groq", "models": ["groq/llama-3.3-70b-versatile"]},
                {"id": "ollama", "name": "Ollama", "models": ["ollama/llama3.2"]},
            ]
        }

    @app.get("/api/v1/prompts", tags=["Platform"])
    async def list_prompts(request: Request):
        current: Container = request.app.state.container
        return {"items": await asyncio.to_thread(current.repository.list_prompts)}

    @app.post("/api/v1/prompts", tags=["Platform"])
    async def create_prompt(payload: PromptCreate, request: Request):
        current: Container = request.app.state.container
        return await asyncio.to_thread(
            current.repository.create_prompt,
            payload.name,
            payload.agent,
            payload.content,
            payload.description,
        )

    @app.post("/api/v1/playground", tags=["Platform"])
    async def playground(payload: PlaygroundRequest):
        return await _run_playground(payload)

    @app.post("/api/v1/auth/register", tags=["Authentication"])
    async def register(payload: UserRegister, request: Request):
        current: Container = request.app.state.container
        try:
            user = await asyncio.to_thread(
                current.repository.create_user,
                payload.email,
                payload.name,
                hash_password(payload.password),
            )
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Email already registered") from exc
        token = create_access_token(user["id"], user["role"], current.settings)
        return {"access_token": token, "token_type": "bearer", "user": user}

    @app.post("/api/v1/auth/login", tags=["Authentication"])
    async def login(payload: UserLogin, request: Request):
        current: Container = request.app.state.container
        user = await asyncio.to_thread(
            current.repository.find_user_by_email, payload.email
        )
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = create_access_token(user["id"], user["role"], current.settings)
        user.pop("password_hash", None)
        return {"access_token": token, "token_type": "bearer", "user": user}

    @app.get("/api/v1/auth/me", tags=["Authentication"])
    async def me(user: dict = Depends(current_user)):
        return user

    @app.get("/api/v1/auth/oauth/providers", tags=["Authentication"])
    async def oauth_providers():
        return {
            "providers": [
                {
                    "id": "google",
                    "enabled": bool(os.getenv("GOOGLE_CLIENT_ID")),
                    "authorize_url": "/api/v1/auth/oauth/google",
                },
                {
                    "id": "github",
                    "enabled": bool(os.getenv("GITHUB_CLIENT_ID")),
                    "authorize_url": "/api/v1/auth/oauth/github",
                },
            ]
        }

    @app.get("/api/v1/auth/oauth/{provider}", tags=["Authentication"])
    async def oauth_authorize(provider: str, request: Request):
        config = _oauth_config(provider)
        client_id = os.getenv(config["client_id_env"])
        if not client_id:
            raise HTTPException(status_code=503, detail=f"{provider.title()} OAuth is not configured")
        redirect_uri = str(request.url_for("oauth_callback", provider=provider))
        state_token = jwt.encode(
            {"provider": provider, "exp": int(time.time()) + 600},
            app_settings.jwt_secret,
            algorithm=app_settings.jwt_algorithm,
        )
        from urllib.parse import urlencode

        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": config["scope"],
                "state": state_token,
                "response_type": "code",
            }
        )
        return RedirectResponse(f"{config['authorize_url']}?{query}")

    @app.get(
        "/api/v1/auth/oauth/{provider}/callback",
        name="oauth_callback",
        tags=["Authentication"],
    )
    async def oauth_callback(provider: str, code: str, state: str, request: Request):
        current: Container = request.app.state.container
        try:
            state_data = decode_access_token(state, current.settings)
            if state_data.get("provider") != provider:
                raise ValueError("Provider mismatch")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc
        profile = await _exchange_oauth(provider, code, request)
        user = await asyncio.to_thread(
            current.repository.find_user_by_email, profile["email"]
        )
        if not user:
            try:
                user = await asyncio.to_thread(
                    current.repository.create_user,
                    profile["email"],
                    profile.get("name") or profile["email"].split("@")[0],
                    hash_password(os.urandom(32).hex()),
                )
            except IntegrityError:
                user = await asyncio.to_thread(
                    current.repository.find_user_by_email, profile["email"]
                )
        assert user is not None
        token = create_access_token(user["id"], user["role"], current.settings)
        frontend = os.getenv("OAUTH_SUCCESS_URL", "http://localhost:4173")
        return RedirectResponse(f"{frontend}?token={token}")

    frontend_dist = app_settings.root_dir / "frontend" / "dist"
    if frontend_dist.exists():
        assets = frontend_dist / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

        @app.get("/", include_in_schema=False)
        async def frontend_index():
            return FileResponse(frontend_dist / "index.html")
    else:
        @app.get("/", include_in_schema=False)
        async def root():
            return {
                "name": app_settings.app_name,
                "version": app.version,
                "docs": "/docs",
                "dashboard": "Run `npm run dev` in frontend/",
            }

    return app


def _sse(event: dict[str, Any]) -> str:
    return (
        f"id: {event['sequence']}\n"
        f"event: {event['type']}\n"
        f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    )


def _default_config(settings: Settings) -> dict[str, Any]:
    return {
        "provider": "openrouter",
        "model": settings.default_model,
        "temperature": 0.3,
        "max_tokens": 4096,
        "top_p": 0.9,
        "search_depth": "advanced",
        "number_of_sources": settings.source_limit,
        "chunk_size": settings.chunk_size,
        "embedding_model": "local-hash-v1",
        "vector_db": settings.vector_backend,
        "retry_count": settings.max_retries,
        "timeout": settings.request_timeout,
    }


async def _run_playground(payload: PlaygroundRequest) -> dict[str, Any]:
    from crewai import Crew, Process, Task
    from agents import (
        create_examiner_agent,
        create_researcher_agent,
        create_simplifier_agent,
        create_student_agent,
        create_teacher_agent,
    )

    factories = {
        "researcher": create_researcher_agent,
        "teacher": create_teacher_agent,
        "simplifier": create_simplifier_agent,
        "student": create_student_agent,
        "examiner": create_examiner_agent,
    }
    agent = factories[payload.agent](payload.model)
    task = Task(
        description=(
            f"Work on this research topic: {payload.topic}\n\n"
            f"Custom context:\n{payload.context or 'No additional context provided.'}"
        ),
        expected_output="A clear, accurate response appropriate to your assigned agent role.",
        agent=agent,
    )
    started = time.perf_counter()
    result = await Crew(
        agents=[agent], tasks=[task], process=Process.sequential, verbose=False
    ).kickoff_async()
    return {
        "agent": payload.agent,
        "topic": payload.topic,
        "result": str(result),
        "duration_seconds": round(time.perf_counter() - started, 2),
    }


def _oauth_config(provider: str) -> dict[str, str]:
    configs = {
        "google": {
            "client_id_env": "GOOGLE_CLIENT_ID",
            "secret_env": "GOOGLE_CLIENT_SECRET",
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "profile_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scope": "openid email profile",
        },
        "github": {
            "client_id_env": "GITHUB_CLIENT_ID",
            "secret_env": "GITHUB_CLIENT_SECRET",
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "profile_url": "https://api.github.com/user",
            "scope": "read:user user:email",
        },
    }
    if provider not in configs:
        raise HTTPException(status_code=404, detail="OAuth provider not supported")
    return configs[provider]


async def _exchange_oauth(provider: str, code: str, request: Request) -> dict[str, str]:
    import httpx

    config = _oauth_config(provider)
    client_id = os.getenv(config["client_id_env"])
    secret = os.getenv(config["secret_env"])
    if not client_id or not secret:
        raise HTTPException(status_code=503, detail=f"{provider.title()} OAuth is not configured")
    redirect_uri = str(request.url_for("oauth_callback", provider=provider))
    async with httpx.AsyncClient(timeout=20) as client:
        token_response = await client.post(
            config["token_url"],
            data={
                "client_id": client_id,
                "client_secret": secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        profile_response = await client.get(
            config["profile_url"],
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        profile_response.raise_for_status()
        profile = profile_response.json()
        if provider == "github" and not profile.get("email"):
            emails = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            emails.raise_for_status()
            primary = next(
                (item for item in emails.json() if item.get("primary") and item.get("verified")),
                None,
            )
            profile["email"] = primary["email"] if primary else ""
    if not profile.get("email"):
        raise HTTPException(status_code=400, detail="OAuth provider did not return an email")
    return {"email": profile["email"], "name": profile.get("name") or profile.get("login", "")}
