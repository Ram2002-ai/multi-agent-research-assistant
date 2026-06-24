"""
config.py
---------
Central configuration for the Multi-Agent Research Assistant.
All LLM model names, API key loading, and shared settings live here.
Any agent that needs an LLM imports get_llm() from this file — so
switching models in future means changing one line, not five files.
"""

import os
from dotenv import load_dotenv

load_dotenv()

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
DEFAULT_LLM = "gemini/gemini-2.5-flash"

def get_llm() -> str:
    """Return the LLM model string for CrewAI agents."""
    return os.getenv("LLM_MODEL", DEFAULT_LLM)
