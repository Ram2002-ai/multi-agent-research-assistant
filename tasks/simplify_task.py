"""
tasks/simplify_task.py
----------------------
Defines the simplification task assigned to the Simplifier Agent.
Runs third — takes the Teacher's structured explanation and rewrites
it in plain language for a complete beginner.
"""

from crewai import Task


def create_simplify_task(topic: str, simplifier_agent) -> Task:
    return Task(
        description=(
            f"Take the step-by-step explanation of '{topic}' and rewrite it "
            "in the simplest possible language. "
            "Use short sentences. Remove all jargon. "
            "Write as if explaining to a 12-year-old."
        ),
        expected_output=(
            "A plain-language version of the explanation, using simple words "
            "and short sentences. No technical jargon. Maximum 150 words."
        ),
        agent=simplifier_agent,
    )
