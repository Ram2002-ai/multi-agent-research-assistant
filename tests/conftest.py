from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.services.research as research_module
from app.core.settings import Settings
from app.factory import create_app


class FakeTaskOutput:
    def __init__(self, raw: str):
        self.raw = raw


class FakeCrew:
    def __init__(self, task_callback=None, step_callback=None):
        self.task_callback = task_callback
        self.step_callback = step_callback

    async def kickoff_async(self):
        outputs = [
            "Evidence from https://www.nasa.gov/research and https://www.nature.com/articles/example",
            "A structured explanation with a real-world example.",
            "A short plain-language summary.",
            "Definition and revision notes.",
            "1. What is it? 2. Explain it. 3. Apply it.",
            (
                "## RESEARCH FINDINGS\n"
                "Evidence is supported by https://www.nasa.gov/research.\n\n"
                "## DETAILED EXPLANATION\nA structured explanation.\n\n"
                "## SIMPLIFIED SUMMARY\nA simple summary.\n\n"
                "## STUDY NOTES\nConcise notes.\n\n"
                "## SELF-TEST QUESTIONS\n1. What is it?"
            ),
        ]
        for output in outputs:
            if self.step_callback:
                self.step_callback(type("Step", (), {"tool_name": "mock_search"})())
            if self.task_callback:
                self.task_callback(FakeTaskOutput(output))
            await asyncio.sleep(0)
        return outputs[-1]


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def fake_build_crew(topic: str, **kwargs):
        return FakeCrew(kwargs.get("task_callback"), kwargs.get("step_callback"))

    monkeypatch.setattr(research_module, "build_crew", fake_build_crew)
    settings = Settings(
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "outputs",
        log_dir=tmp_path / "logs",
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        jwt_secret="test-secret-with-at-least-thirty-two-bytes",
        max_retries=0,
        request_timeout=10,
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
