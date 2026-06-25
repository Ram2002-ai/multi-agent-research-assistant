from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import os
import pathlib
import sys

# Ensure repo root is on the import path when running from backend/
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import validate_env
from crew import build_crew

app = FastAPI(
    title="Multi-Agent Research Assistant API",
    description="API for topic research, explanation, simplification, and revision notes generation.",
    version="1.0.0",
)

class ResearchRequest(BaseModel):
    topic: str

class ResearchResponse(BaseModel):
    topic: str
    result: str
    report_path: str


def save_output(topic: str, result: str) -> str:
    os.makedirs("outputs", exist_ok=True)
    timestamp = asyncio.get_event_loop().time()
    filename = f"outputs/report_{int(timestamp)}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Research Report: {topic}\n\n")
        f.write(f"*Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("---\n\n")
        f.write(str(result))
    return filename


@app.on_event("startup")
def startup_event() -> None:
    validate_env()


@app.post("/research", response_model=ResearchResponse)
def research(request: ResearchRequest):
    try:
        crew = build_crew(request.topic)
        result = asyncio.run(crew.kickoff_async())
        report_path = save_output(request.topic, result)
        return ResearchResponse(topic=request.topic, result=result, report_path=report_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
