"""Thread-safe repository used by API, pipeline, analytics, and RAG services."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import (
    Base,
    Event,
    KnowledgeChunk,
    Prompt,
    Report,
    Source,
    User,
    UserConfig,
)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _loads(value: str | None, default: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, ValueError):
        return default


class Repository:
    def __init__(self, database_url: str):
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(
            database_url, pool_pre_ping=True, connect_args=connect_args
        )
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def create_report(
        self,
        report_id: str,
        topic: str,
        model: str,
        template: str,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self.sessions.begin() as session:
            report = Report(
                id=report_id,
                topic=topic,
                model=model,
                template=template,
                user_id=user_id,
                metadata_json=_json(metadata or {}),
            )
            session.add(report)
        return self.report_to_dict(report)

    def update_report(self, report_id: str, **values: Any) -> None:
        with self.sessions.begin() as session:
            report = session.get(Report, report_id)
            if not report:
                return
            for key, value in values.items():
                if hasattr(report, key):
                    setattr(report, key, value)
            report.updated_at = datetime.now(timezone.utc)

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            report = session.get(Report, report_id)
            return self.report_to_dict(report) if report else None

    def list_reports(
        self, limit: int = 30, saved_only: bool = False, query: str = ""
    ) -> list[dict[str, Any]]:
        with self.sessions() as session:
            statement = select(Report)
            if saved_only:
                statement = statement.where(Report.saved.is_(True))
            if query:
                statement = statement.where(Report.topic.ilike(f"%{query}%"))
            reports = session.scalars(
                statement.order_by(Report.created_at.desc()).limit(limit)
            ).all()
            return [self.report_to_dict(item) for item in reports]

    def delete_report(self, report_id: str) -> bool:
        with self.sessions.begin() as session:
            report = session.get(Report, report_id)
            if not report:
                return False
            session.delete(report)
            return True

    def next_event_sequence(self, report_id: str) -> int:
        with self.sessions() as session:
            current = session.scalar(
                select(func.max(Event.sequence)).where(Event.report_id == report_id)
            )
            return int(current or 0) + 1

    def add_event(self, report_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self.sessions.begin() as session:
            sequence = self.next_event_sequence(report_id)
            event = Event(
                report_id=report_id,
                sequence=sequence,
                event_type=payload.get("type", "log"),
                agent=payload.get("agent", ""),
                status=payload.get("status", ""),
                level=payload.get("level", "INFO"),
                message=payload.get("message", ""),
                progress=int(payload.get("progress", 0)),
                duration_seconds=float(payload.get("duration_seconds", 0)),
                retry_count=int(payload.get("retry_count", 0)),
                data_json=_json(payload.get("data", {})),
            )
            session.add(event)
        return self.event_to_dict(event)

    def list_events(self, report_id: str) -> list[dict[str, Any]]:
        with self.sessions() as session:
            events = session.scalars(
                select(Event)
                .where(Event.report_id == report_id)
                .order_by(Event.sequence.asc())
            ).all()
            return [self.event_to_dict(event) for event in events]

    def replace_sources(self, report_id: str, sources: list[dict[str, Any]]) -> None:
        with self.sessions.begin() as session:
            session.execute(delete(Source).where(Source.report_id == report_id))
            for item in sources:
                session.add(Source(report_id=report_id, **item))

    def list_sources(self, report_id: str) -> list[dict[str, Any]]:
        with self.sessions() as session:
            rows = session.scalars(
                select(Source)
                .where(Source.report_id == report_id)
                .order_by(Source.credibility_score.desc())
            ).all()
            return [
                {
                    "id": row.id,
                    "url": row.url,
                    "title": row.title,
                    "domain": row.domain,
                    "credibility_score": row.credibility_score,
                    "trust_score": row.trust_score,
                    "authority_score": row.authority_score,
                    "recency_score": row.recency_score,
                    "citation_count": row.citation_count,
                    "domain_rating": row.domain_rating,
                    "label": row.label,
                }
                for row in rows
            ]

    def replace_chunks(self, report_id: str, topic: str, chunks: list[dict[str, Any]]) -> None:
        with self.sessions.begin() as session:
            session.execute(
                delete(KnowledgeChunk).where(KnowledgeChunk.report_id == report_id)
            )
            for position, item in enumerate(chunks):
                session.add(
                    KnowledgeChunk(
                        report_id=report_id,
                        topic=topic,
                        content=item["content"],
                        embedding_json=_json(item["embedding"]),
                        position=position,
                    )
                )

    def all_chunks(self) -> list[dict[str, Any]]:
        with self.sessions() as session:
            rows = session.scalars(select(KnowledgeChunk)).all()
            return [
                {
                    "id": row.id,
                    "report_id": row.report_id,
                    "topic": row.topic,
                    "content": row.content,
                    "embedding": _loads(row.embedding_json, {}),
                    "position": row.position,
                }
                for row in rows
            ]

    def create_user(self, email: str, name: str, password_hash: str) -> dict[str, Any]:
        user = User(
            id=str(uuid.uuid4()),
            email=email.lower().strip(),
            name=name.strip(),
            password_hash=password_hash,
        )
        with self.sessions.begin() as session:
            session.add(user)
        return self.user_to_dict(user)

    def find_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            user = session.scalar(
                select(User).where(User.email == email.lower().strip())
            )
            return self.user_to_dict(user, include_hash=True) if user else None

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            user = session.get(User, user_id)
            return self.user_to_dict(user) if user else None

    def get_config(self, user_id: str) -> dict[str, Any]:
        with self.sessions() as session:
            config = session.get(UserConfig, user_id)
            return _loads(config.config_json, {}) if config else {}

    def set_config(self, user_id: str, value: dict[str, Any]) -> dict[str, Any]:
        with self.sessions.begin() as session:
            config = session.get(UserConfig, user_id)
            if config:
                config.config_json = _json(value)
                config.updated_at = datetime.now(timezone.utc)
            else:
                session.add(UserConfig(user_id=user_id, config_json=_json(value)))
        return value

    def create_prompt(
        self, name: str, agent: str, content: str, description: str = ""
    ) -> dict[str, Any]:
        with self.sessions.begin() as session:
            max_version = session.scalar(
                select(func.max(Prompt.version)).where(Prompt.name == name)
            )
            prompt = Prompt(
                id=str(uuid.uuid4()),
                name=name,
                agent=agent,
                content=content,
                description=description,
                version=int(max_version or 0) + 1,
            )
            session.add(prompt)
        return self.prompt_to_dict(prompt)

    def list_prompts(self) -> list[dict[str, Any]]:
        with self.sessions() as session:
            prompts = session.scalars(
                select(Prompt).order_by(Prompt.name, Prompt.version.desc())
            ).all()
            return [self.prompt_to_dict(item) for item in prompts]

    def analytics(self) -> dict[str, Any]:
        with self.sessions() as session:
            total = session.scalar(select(func.count(Report.id))) or 0
            completed = (
                session.scalar(
                    select(func.count(Report.id)).where(Report.status == "completed")
                )
                or 0
            )
            failed = (
                session.scalar(
                    select(func.count(Report.id)).where(Report.status == "failed")
                )
                or 0
            )
            aggregates = session.execute(
                select(
                    func.avg(Report.duration_seconds),
                    func.sum(Report.prompt_tokens),
                    func.sum(Report.completion_tokens),
                    func.sum(Report.estimated_cost),
                    func.sum(Report.source_count),
                )
            ).one()
            recent = session.scalars(
                select(Report).order_by(Report.created_at.desc()).limit(12)
            ).all()
            return {
                "total_reports": total,
                "completed": completed,
                "failed": failed,
                "success_rate": round((completed / total * 100) if total else 0, 1),
                "failure_rate": round((failed / total * 100) if total else 0, 1),
                "average_duration": round(float(aggregates[0] or 0), 2),
                "prompt_tokens": int(aggregates[1] or 0),
                "completion_tokens": int(aggregates[2] or 0),
                "estimated_cost": round(float(aggregates[3] or 0), 4),
                "sources": int(aggregates[4] or 0),
                "recent_runs": [
                    {
                        "id": item.id,
                        "topic": item.topic,
                        "status": item.status,
                        "duration": item.duration_seconds,
                        "sources": item.source_count,
                        "created_at": item.created_at.isoformat(),
                    }
                    for item in reversed(recent)
                ],
            }

    @staticmethod
    def report_to_dict(report: Report) -> dict[str, Any]:
        return {
            "id": report.id,
            "topic": report.topic,
            "status": report.status,
            "progress": report.progress,
            "result": report.result,
            "report_path": report.report_path,
            "error": report.error,
            "model": report.model,
            "template": report.template,
            "saved": report.saved,
            "source_count": report.source_count,
            "duration_seconds": report.duration_seconds,
            "prompt_tokens": report.prompt_tokens,
            "completion_tokens": report.completion_tokens,
            "estimated_cost": report.estimated_cost,
            "metadata": _loads(report.metadata_json, {}),
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
        }

    @staticmethod
    def event_to_dict(event: Event) -> dict[str, Any]:
        return {
            "id": event.id,
            "sequence": event.sequence,
            "job_id": event.report_id,
            "type": event.event_type,
            "agent": event.agent,
            "status": event.status,
            "level": event.level,
            "message": event.message,
            "progress": event.progress,
            "duration_seconds": event.duration_seconds,
            "retry_count": event.retry_count,
            "data": _loads(event.data_json, {}),
            "timestamp": event.created_at.isoformat(),
        }

    @staticmethod
    def user_to_dict(user: User, include_hash: bool = False) -> dict[str, Any]:
        payload = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "active": user.active,
            "created_at": user.created_at.isoformat(),
        }
        if include_hash:
            payload["password_hash"] = user.password_hash
        return payload

    @staticmethod
    def prompt_to_dict(prompt: Prompt) -> dict[str, Any]:
        return {
            "id": prompt.id,
            "name": prompt.name,
            "agent": prompt.agent,
            "description": prompt.description,
            "content": prompt.content,
            "version": prompt.version,
            "active": prompt.active,
            "created_at": prompt.created_at.isoformat(),
        }
