"""Structured JSON logging with separate operational log files."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("job_id", "agent", "event", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_dir: Path) -> list[logging.Handler]:
    log_dir.mkdir(parents=True, exist_ok=True)
    formatter = JsonFormatter()
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    created: list[logging.Handler] = []

    if not any(getattr(handler, "_research_os", False) for handler in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        console._research_os = True  # type: ignore[attr-defined]
        root.addHandler(console)
        created.append(console)

    destinations = {
        "execution.log": "research.execution",
        "api.log": "research.api",
        "agent.log": "research.agent",
        "errors.log": "research.errors",
    }
    for filename, logger_name in destinations.items():
        logger = logging.getLogger(logger_name)
        if any(getattr(handler, "_research_os", False) for handler in logger.handlers):
            continue
        handler = RotatingFileHandler(
            log_dir / filename,
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        handler._research_os = True  # type: ignore[attr-defined]
        if filename == "errors.log":
            handler.setLevel(logging.ERROR)
        logger.addHandler(handler)
        created.append(handler)
    return created


def close_logging_handlers(handlers: list[logging.Handler]) -> None:
    for handler in handlers:
        for logger in [logging.getLogger(), *[
            logging.getLogger(name)
            for name in ("research.execution", "research.api", "research.agent", "research.errors")
        ]]:
            if handler in logger.handlers:
                logger.removeHandler(handler)
        handler.flush()
        handler.close()
