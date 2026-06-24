"""
agents/student_agent.py
-----------------------
The Student Agent synthesises everything produced so far into
compact, well-structured notes — the kind a good student would
write to revise from later.

Design decisions:
- This is the fourth agent in the pipeline. By the time it runs,
  the crew's shared context contains: raw research findings,
  step-by-step explanation, and simplified summary. The student
  agent distills all of this into a final set of notes.
- Output format: bullet-point notes with clear headings.
"""

from crewai import Agent
from config import get_llm


def create_student_agent() -> Agent:
    return Agent(
        role="Student",
        goal="Write concise, well-organised revision notes on the topic",
        backstory=(
            "You are a diligent student who takes excellent notes. "
            "You listen carefully to all the explanations and summaries, "
            "then write them up in a clear, structured format that is "
            "easy to revise from later."
        ),
        llm=get_llm(),
        allow_delegation=False,
        verbose=True,
    )
