"""
agents/researcher_agent.py
--------------------------
The Researcher Agent is the first agent in the pipeline.
It uses the SerperDevTool to search the web for real, up-to-date
information on the given topic and returns 3 key findings.

Design decisions:
- allow_delegation=False: this agent owns information gathering.
  It should not hand off to another agent mid-task.
- tools=[search_tool]: only this agent gets web access. Other agents
  reason over the research output, they don't need to search.
- verbose=True: keeps logs readable during development.
"""

from crewai import Agent
from config import get_llm
from tools.search_tool import get_search_tool


def create_researcher_agent(llm: str | None = None) -> Agent:
    return Agent(
        role="Researcher",
        goal="Find the latest and most accurate information on the given topic",
        backstory=(
            "You are an expert researcher with deep experience in "
            "searching and evaluating real-world data from the web. "
            "You always verify facts from multiple sources before reporting."
        ),
        llm=llm or get_llm(),
        tools=[get_search_tool()],  # web search enabled for this agent only
        allow_delegation=False,
        verbose=True,
    )
