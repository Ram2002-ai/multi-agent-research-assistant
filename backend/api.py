# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# import asyncio
# import logging
# import os
# import pathlib
# import sys

# # Ensure repo root is on the import path when running from backend/
# ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
# if str(ROOT_DIR) not in sys.path:
#     sys.path.insert(0, str(ROOT_DIR))

# from config import validate_env, get_llm
# from crew import build_crew

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="Multi-Agent Research Assistant API",
#     description="API for topic research, explanation, simplification, and revision notes generation.",
#     version="1.0.0",
# )

# class ResearchRequest(BaseModel):
#     topic: str

# class ResearchResponse(BaseModel):
#     topic: str
#     result: str
#     report_path: str


# def save_output(topic: str, result: str) -> str:
#     os.makedirs("outputs", exist_ok=True)
#     timestamp = asyncio.get_event_loop().time()
#     filename = f"outputs/report_{int(timestamp)}.md"
#     with open(filename, "w", encoding="utf-8") as f:
#         f.write(f"# Research Report: {topic}\n\n")
#         f.write(f"*Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
#         f.write("---\n\n")
#         f.write(str(result))
#     return filename


# @app.on_event("startup")
# def startup_event() -> None:
#     try:
#         validate_env()
#     except Exception as exc:
#         logger.exception("Startup validation failed")
#         raise


# @app.get("/health")
# def health_check():
#     return {"status": "ok"}


# @app.get("/debug_model")
# def debug_model():
#     """Return the resolved LLM model string for debugging."""
#     return {"llm": get_llm()}


# @app.post("/research", response_model=ResearchResponse)
# def research(request: ResearchRequest):
#     try:
#         logger.info("Received research request for topic: %s", request.topic)
#         logger.info("Resolved LLM model: %s", get_llm())
#         crew = build_crew(request.topic)
#         result = asyncio.run(crew.kickoff_async())
#         report_path = save_output(request.topic, result)
#         logger.info("Research completed for topic: %s", request.topic)
#         return ResearchResponse(topic=request.topic, result=result, report_path=report_path)
#     except Exception as exc:
#         logger.exception("Error while processing research request")
#         raise HTTPException(status_code=500, detail=str(exc))
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import os
import pathlib
import sys
import time
from datetime import datetime

# -----------------------------------------------------------------------------
# Add project root
# -----------------------------------------------------------------------------

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import validate_env, get_llm
from crew import build_crew

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Agent Research Assistant API",
    version="1.0.0"
)

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class ResearchRequest(BaseModel):
    topic: str


class ResearchResponse(BaseModel):
    topic: str
    result: str
    report_path: str


# -----------------------------------------------------------------------------
# Save report
# -----------------------------------------------------------------------------

def save_output(topic: str, result: str) -> str:

    os.makedirs("outputs", exist_ok=True)

    filename = f"outputs/report_{int(time.time())}.md"

    with open(filename, "w", encoding="utf-8") as f:

        f.write(f"# {topic}\n\n")

        f.write(
            f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        f.write(str(result))

    return filename


# -----------------------------------------------------------------------------
# Startup
# -----------------------------------------------------------------------------

@app.on_event("startup")
def startup():

    validate_env()

    logger.info("Application Started")


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------

@app.get("/health")
def health():

    return {"status": "ok"}


@app.get("/debug_model")
def debug():

    return {"model": get_llm()}


# -----------------------------------------------------------------------------
# Research Endpoint
# -----------------------------------------------------------------------------

@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):

    try:

        logger.info(f"Topic : {request.topic}")

        crew = build_crew(request.topic)

        # NO asyncio.run()
        result = await crew.kickoff_async()

        report = save_output(request.topic, result)

        return ResearchResponse(
            topic=request.topic,
            result=str(result),
            report_path=report
        )

    except Exception as e:

        logger.exception(e)

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )