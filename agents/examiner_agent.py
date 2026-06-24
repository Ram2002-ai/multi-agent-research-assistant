"""
agents/examiner_agent.py
------------------------
The Examiner Agent is the final agent in the pipeline.
It reads all previous outputs and generates 3 questions to test
understanding of the topic — acting as a quality gate.

Design decisions:
- Runs last: by the time Examiner runs, it has access to research,
  explanation, simplified version, and student notes. This gives it
  the full picture to write relevant, targeted questions.
- Output format: 3 numbered questions, ranging from factual recall
  to simple application — appropriate for a beginner audience.
"""

from crewai import Agent
from config import get_llm


def create_examiner_agent() -> Agent:
    return Agent(
        role="Examiner",
        goal="Create 3 questions that test genuine understanding of the topic",
        backstory=(
            "You are an experienced examiner who designs questions that "
            "test real comprehension, not just memorisation. Your questions "
            "range from basic recall to simple application, making them "
            "suitable for beginners learning the topic for the first time."
        ),
        llm=get_llm(),
        allow_delegation=False,
        verbose=True,
    )
