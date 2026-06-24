"""
agents/teacher_agent.py
-----------------------
The Teacher Agent receives the Researcher's findings and explains
the topic step-by-step with clear examples.

Design decisions:
- No tools: this agent reasons over text only — no web access needed.
  It works from the context passed by the Researcher task output.
- Role is specific ("Experienced Teacher") rather than generic ("Agent")
  because specificity in the role string improves CrewAI prompt quality.
"""

from crewai import Agent
from config import get_llm


def create_teacher_agent() -> Agent:
    return Agent(
        role="Teacher",
        goal="Explain concepts clearly, step by step, with real-world examples",
        backstory=(
            "You are an experienced teacher who has spent years making "
            "complex topics accessible to beginners. You always use "
            "analogies and examples to bring abstract ideas to life."
        ),
        llm=get_llm(),
        allow_delegation=False,
        verbose=True,
    )
