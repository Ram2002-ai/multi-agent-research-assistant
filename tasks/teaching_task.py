"""
tasks/teaching_task.py
----------------------
Defines the teaching task assigned to the Teacher Agent.
Runs after research_task — the Teacher reads the researcher's findings
from the crew's shared context and builds a structured explanation.
"""

from crewai import Task


def create_teaching_task(topic: str, teacher_agent) -> Task:
    return Task(
        description=(
            f"Using the research findings provided, explain '{topic}' "
            "step by step with clear real-world examples. "
            "Structure your explanation with: (1) What it is, "
            "(2) How it works, (3) A real-world example."
        ),
        expected_output=(
            "A structured, step-by-step explanation of the topic with "
            "at least one concrete real-world example. "
            "Should be understandable by someone with no prior knowledge."
        ),
        agent=teacher_agent,
    )
