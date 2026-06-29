"""
config.py
---------
Central configuration for the Multi-Agent Research Assistant.
All LLM model names, API key loading, and shared settings live here.
Any agent that needs an LLM imports get_llm() from this file — so
switching models in future means changing one line, not five files.

IMPORTANT: All LLM requests are routed through OpenRouter only.
No direct API calls to Anthropic, OpenAI, or other providers.
"""

import os
import pathlib
from dotenv import load_dotenv


ROOT_DIR = pathlib.Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT_DIR / '.env')

# Validate required keys are present at startup
def validate_env():
    required = ["OPENROUTER_API_KEY", "SERPER_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {missing}\n"
            "Copy .env.example to .env and fill in your keys."
        )

# ============================================================================
# OPENROUTER CONFIGURATION - All LLM requests must go through OpenRouter
# ============================================================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Configure OpenRouter for OpenAI-compatible API usage
# CrewAI uses the OpenAI client under the hood, so we redirect it to OpenRouter
os.environ["OPENAI_API_BASE"] = OPENROUTER_BASE_URL
os.environ["OPENAI_BASE_URL"] = OPENROUTER_BASE_URL

# Disable direct provider API calls - force all routing through OpenRouter
# This prevents any accidental direct calls to Anthropic, Google, or OpenAI
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("GEMINI_API_KEY", None)

# ============================================================================
# LLM MODEL SELECTION
# ============================================================================
# Change DEFAULT_LLM here to switch all agents at once
# All models are accessed via OpenRouter (https://openrouter.ai/docs/models)
#
# High-token models via OpenRouter:
#   - "anthropic/claude-3-5-sonnet" (200k tokens) — Recommended
#   - "openai/gpt-4-turbo-preview" (128k tokens)
#   - "openai/gpt-4-1106-preview" (128k tokens)
#   - "meta-llama/llama-2-70b-chat" (4k tokens)
#
DEFAULT_LLM = "openrouter/meta-llama/llama-3.3-70b-instruct"


def get_llm() -> str:
    """Return the LLM model string for CrewAI agents.
    
    All requests are routed through OpenRouter with the configured
    base URL and API key. No direct provider calls are made.
    
    Returns:
        str: Model name in OpenRouter format (e.g. "anthropic/claude-3-5-sonnet")
    """
    return DEFAULT_LLM
