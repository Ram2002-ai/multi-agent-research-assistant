"""API request and response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=500)
    model: str | None = None
    search_depth: Literal["basic", "advanced"] = "advanced"
    number_of_sources: int = Field(default=10, ge=3, le=50)
    template: str = "professional"

    @field_validator("topic")
    @classmethod
    def clean_topic(cls, value: str) -> str:
        return " ".join(value.split())


class LegacyResearchRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=500)


class LegacyResearchResponse(BaseModel):
    topic: str
    result: str
    report_path: str


class StartResearchResponse(BaseModel):
    job_id: str
    status: str
    stream_url: str
    websocket_url: str


class UserRegister(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=2, max_length=100)


class UserLogin(BaseModel):
    email: str
    password: str


class ConfigUpdate(BaseModel):
    provider: str = "openrouter"
    model: str
    temperature: float = Field(default=0.3, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=256, le=128_000)
    top_p: float = Field(default=0.9, gt=0, le=1)
    search_depth: str = "advanced"
    number_of_sources: int = Field(default=10, ge=3, le=50)
    chunk_size: int = Field(default=900, ge=200, le=4000)
    embedding_model: str = "local-hash-v1"
    vector_db: str = "local"
    retry_count: int = Field(default=2, ge=0, le=8)
    timeout: int = Field(default=300, ge=10, le=1800)


class PromptCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    agent: str
    content: str = Field(min_length=10)
    description: str = ""


class PlaygroundRequest(BaseModel):
    agent: Literal["researcher", "teacher", "simplifier", "student", "examiner"]
    topic: str = Field(min_length=2, max_length=500)
    context: str = Field(default="", max_length=50_000)
    model: str | None = None


class KnowledgeQuery(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)


class ApiMessage(BaseModel):
    message: str
    data: dict[str, Any] = {}
