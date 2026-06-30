"""Fault-tolerant orchestration around the existing CrewAI pipeline."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.settings import Settings
from app.database.repository import Repository
from app.services.credibility import score_sources
from app.services.events import EventBroker
from app.services.exporters import ExportService
from app.services.knowledge import KnowledgeBase
from crew import build_crew


logger = logging.getLogger("research.execution")
AGENTS = [
    ("researcher", "Research Agent"),
    ("teacher", "Teacher Agent"),
    ("simplifier", "Simplifier Agent"),
    ("student", "Student Agent"),
    ("examiner", "Examiner Agent"),
    ("reporter", "Report Compiler"),
]


class ResearchService:
    def __init__(
        self,
        repository: Repository,
        broker: EventBroker,
        knowledge: KnowledgeBase,
        exporter: ExportService,
        settings: Settings,
    ):
        self.repository = repository
        self.broker = broker
        self.knowledge = knowledge
        self.exporter = exporter
        self.settings = settings
        self._tasks: dict[str, asyncio.Task] = {}

    async def start(
        self,
        topic: str,
        *,
        model: str | None = None,
        template: str = "professional",
        options: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        selected_model = model or self.settings.default_model
        await asyncio.to_thread(
            self.repository.create_report,
            job_id,
            topic,
            selected_model,
            template,
            user_id,
            options or {},
        )
        task = asyncio.create_task(
            self._execute(job_id, topic, selected_model), name=f"research-{job_id}"
        )
        self._tasks[job_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(job_id, None))
        return job_id

    async def run_and_wait(
        self, topic: str, model: str | None = None
    ) -> dict[str, Any]:
        job_id = await self.start(topic, model=model)
        await self._tasks[job_id]
        report = await asyncio.to_thread(self.repository.get_report, job_id)
        if not report:
            raise RuntimeError("Research report disappeared during execution")
        if report["status"] == "failed":
            raise RuntimeError(report["error"])
        return report

    async def cancel(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if not task or task.done():
            return False
        task.cancel()
        await asyncio.to_thread(
            self.repository.update_report,
            job_id,
            status="cancelled",
            error="Cancelled by user",
        )
        await self.broker.publish(
            job_id,
            {
                "type": "job",
                "status": "cancelled",
                "level": "WARNING",
                "message": "Research cancelled by user",
            },
        )
        return True

    async def _execute(self, job_id: str, topic: str, model: str) -> None:
        started = time.perf_counter()
        await asyncio.to_thread(
            self.repository.update_report, job_id, status="running", progress=2
        )
        await self.broker.publish(
            job_id,
            {
                "type": "job",
                "status": "running",
                "progress": 2,
                "message": "Research pipeline started",
                "data": {"agents": [item[0] for item in AGENTS], "model": model},
            },
        )
        await self.broker.publish(
            job_id,
            {
                "type": "agent",
                "agent": AGENTS[0][0],
                "status": "running",
                "progress": 5,
                "message": f"{AGENTS[0][1]} started",
            },
        )
        for key, label in AGENTS[1:]:
            await self.broker.publish(
                job_id,
                {
                    "type": "agent",
                    "agent": key,
                    "status": "waiting",
                    "message": f"{label} waiting for context",
                },
            )

        loop = asyncio.get_running_loop()
        completed = 0
        agent_started = [time.perf_counter(), *([0.0] * (len(AGENTS) - 1))]
        pending_announcements: set[asyncio.Task] = set()

        def schedule_announcement(coroutine) -> None:
            def create_task() -> None:
                task = asyncio.create_task(coroutine)
                pending_announcements.add(task)
                task.add_done_callback(pending_announcements.discard)

            loop.call_soon_threadsafe(create_task)

        def task_callback(output: Any) -> None:
            nonlocal completed
            index = min(completed, len(AGENTS) - 1)
            key, label = AGENTS[index]
            raw = str(getattr(output, "raw", output))
            completed += 1
            progress = min(92, round(completed / len(AGENTS) * 90))
            agent_duration = time.perf_counter() - (agent_started[index] or started)

            async def announce() -> None:
                await self.broker.publish(
                    job_id,
                    {
                        "type": "agent",
                        "agent": key,
                        "status": "completed",
                        "progress": progress,
                        "duration_seconds": round(agent_duration, 2),
                        "message": f"{label} completed",
                        "data": {"output": raw},
                    },
                )
                await asyncio.to_thread(
                    self.repository.update_report, job_id, progress=progress
                )
                if completed < len(AGENTS):
                    agent_started[completed] = time.perf_counter()
                    next_key, next_label = AGENTS[completed]
                    await self.broker.publish(
                        job_id,
                        {
                            "type": "agent",
                            "agent": next_key,
                            "status": "running",
                            "progress": progress,
                            "message": f"{next_label} started",
                        },
                    )

            schedule_announcement(announce())

        def step_callback(output: Any) -> None:
            tool = getattr(output, "tool", None)
            tool_name = getattr(tool, "name", None) or getattr(output, "tool_name", None)
            message = (
                f"Tool completed: {tool_name}"
                if tool_name
                else f"Agent step completed: {type(output).__name__}"
            )

            async def announce_step() -> None:
                await self.broker.publish(
                    job_id,
                    {
                        "type": "log",
                        "agent": AGENTS[min(completed, len(AGENTS) - 1)][0],
                        "status": "running",
                        "level": "INFO",
                        "progress": min(90, max(5, round(completed / len(AGENTS) * 90))),
                        "message": message,
                    },
                )

            schedule_announcement(announce_step())

        attempt = 0
        try:
            while True:
                try:
                    crew = build_crew(
                        topic,
                        task_callback=task_callback,
                        step_callback=step_callback,
                        llm=model,
                    )
                    result = await asyncio.wait_for(
                        crew.kickoff_async(), timeout=self.settings.request_timeout
                    )
                    break
                except Exception as exc:
                    if attempt >= self.settings.max_retries:
                        raise
                    attempt += 1
                    delay = min(2**attempt, 10)
                    await self.broker.publish(
                        job_id,
                        {
                            "type": "recovery",
                            "status": "retrying",
                            "level": "WARNING",
                            "retry_count": attempt,
                            "message": f"Provider call failed; retrying in {delay}s",
                            "data": {"error": str(exc)},
                        },
                    )
                    await asyncio.sleep(delay)

            # CrewAI callbacks are synchronous hooks and may originate in worker
            # threads. Let every scheduled callback enter the loop, then wait for
            # all timeline checkpoints before declaring the report complete.
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            while pending_announcements:
                await asyncio.gather(*list(pending_announcements))
            result_text = str(result)
            sources = score_sources(result_text)
            await asyncio.to_thread(self.repository.replace_sources, job_id, sources)
            chunks = await self.knowledge.add_report(job_id, topic, result_text)
            duration = time.perf_counter() - started
            prompt_tokens = max(1, len(topic) // 4)
            completion_tokens = max(1, len(result_text) // 4)
            report = await asyncio.to_thread(self.repository.get_report, job_id)
            assert report is not None
            report["result"] = result_text
            report["completed_at"] = datetime.now(timezone.utc).isoformat()
            path = await asyncio.to_thread(
                self.exporter.export, report, sources, "markdown"
            )
            await asyncio.to_thread(
                self.repository.update_report,
                job_id,
                status="completed",
                progress=100,
                result=result_text,
                report_path=str(path),
                completed_at=datetime.now(timezone.utc),
                source_count=len(sources),
                duration_seconds=duration,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            await self.broker.publish(
                job_id,
                {
                    "type": "job",
                    "status": "completed",
                    "progress": 100,
                    "duration_seconds": round(duration, 2),
                    "message": "Research report ready",
                    "data": {
                        "report_path": str(path),
                        "source_count": len(sources),
                        "knowledge_chunks": chunks,
                        "result": result_text,
                    },
                },
            )
            logger.info(
                "Research completed",
                extra={"job_id": job_id, "duration_ms": round(duration * 1000)},
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            duration = time.perf_counter() - started
            await asyncio.to_thread(
                self.repository.update_report,
                job_id,
                status="failed",
                error=str(exc),
                duration_seconds=duration,
                completed_at=datetime.now(timezone.utc),
            )
            await self.broker.publish(
                job_id,
                {
                    "type": "job",
                    "status": "failed",
                    "level": "ERROR",
                    "duration_seconds": round(duration, 2),
                    "message": "Research pipeline failed",
                    "data": {"error": str(exc)},
                },
            )
            logging.getLogger("research.errors").exception(
                "Research failed", extra={"job_id": job_id}
            )
