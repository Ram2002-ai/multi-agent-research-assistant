"""
agents/reporter_agent.py
------------------------
The Reporter Agent aggregates all outputs from previous agents
and formats them into a comprehensive, structured report.

Design decisions:
- Runs last in the pipeline
- Takes all previous context and organizes it
- No tools needed: pure text aggregation
"""

from crewai import Agent
from config import get_llm


def create_reporter_agent(llm: str | None = None) -> Agent:
    return Agent(
        role="Report Generator",
        goal="Compile all research, explanations, notes, and questions into a well-structured comprehensive report",
        backstory=(
            "You are an expert technical writer who specializes in creating "
            "clear, well-organized reports. You take complex information from "
            "multiple sources and format it into a professional, easy-to-read document."
        ),
        llm=llm or get_llm(),
        allow_delegation=False,
        verbose=True,
    )
