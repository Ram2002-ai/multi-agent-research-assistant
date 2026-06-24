"""
tasks/notes_task.py
-------------------
Defines the note-taking task assigned to the Student Agent.
Runs fourth — synthesises all previous outputs (research findings,
step-by-step explanation, simplified summary) into compact revision notes.
"""

from crewai import Task


def create_notes_task(topic: str, student_agent) -> Task:
    return Task(
        description=(
            f"Review everything discussed about '{topic}' so far — "
            "the research findings, the explanation, and the simplified version. "
            "Write compact revision notes with clear headings and bullet points."
        ),
        expected_output=(
            "Well-organised revision notes with: "
            "a one-line definition, 3-5 key bullet points, "
            "and one 'remember this' summary sentence at the end."
        ),
        agent=student_agent,
    )
