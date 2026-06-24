"""
tools/search_tool.py
--------------------
Wraps the CrewAI SerperDevTool for web search.
Only the Researcher agent uses this tool — keeping tools in a
separate folder makes it easy to swap or add tools later (e.g.
replace Serper with Tavily) without touching agent definitions.
"""

import os
from crewai_tools import SerperDevTool


def get_search_tool() -> SerperDevTool:
    """
    Return a configured SerperDevTool instance.
    Serper API key is loaded from environment — never hardcoded.
    Get a free key at: https://serper.dev
    """
    # SerperDevTool reads SERPER_API_KEY from env automatically
    return SerperDevTool()
