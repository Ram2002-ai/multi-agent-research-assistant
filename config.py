"""
config.py
---------
Central configuration for the Multi-Agent Research Assistant.
All LLM model names, API key loading, and shared settings live here.
Any agent that needs an LLM imports get_llm() from this file — so
switching models in future means changing one line, not five files.
"""

import os
import pathlib
from dotenv import load_dotenv

ROOT_DIR = pathlib.Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT_DIR / '.env')

# Validate required keys are present at startup
def validate_env():
    required = ["GEMINI_API_KEY", "SERPER_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {missing}\n"
            "Copy .env.example to .env and fill in your keys."
        )

# LLM model string — change here to switch all agents at once
# Set a sensible default that is supported by the Gemini API for generateContent
DEFAULT_LLM = "gemini/text-bison-001"
# You can override at runtime by setting LLM_MODEL in your .env
# Example: LLM_MODEL=gemini/text-bison-001

def get_llm() -> str:
    """Return the LLM model string for CrewAI agents."""
    # Forcing the use of DEFAULT_LLM to avoid environment inconsistencies
    # during debugging. This ensures the running process uses a supported
    # model. Revert this to `os.getenv("LLM_MODEL", DEFAULT_LLM)` when
    # environment loading is confirmed.
    return DEFAULT_LLM
