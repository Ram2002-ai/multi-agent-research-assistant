"""
agents/simplifier_agent.py
--------------------------
The Simplifier Agent takes the Teacher's explanation and strips it
down to the absolute essentials — plain language, no jargon.

Design decisions:
- This agent runs third in the pipeline, after research and teaching.
  Its input context will contain both the raw research and the
  structured explanation, giving it full information to simplify from.
- No tools needed: simplification is pure language reasoning.
"""

from crewai import Agent
from config import get_llm


def create_simplifier_agent() -> Agent:
    return Agent(
        role="Simplifier",
        goal="Rewrite complex explanations in the simplest possible language",
        backstory=(
            "You have a gift for breaking down complicated ideas into "
            "language that a 10-year-old could understand. You remove "
            "all jargon and technical terms, replacing them with everyday "
            "words and short sentences."
        ),
        llm=get_llm(),
        allow_delegation=False,
        verbose=True,
    )
