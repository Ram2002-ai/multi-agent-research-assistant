"""
tasks/exam_task.py
------------------
Defines the examination task assigned to the Examiner Agent.
Runs last — reads all prior context (research, explanation, simplified
version, student notes) and generates 3 questions to test understanding.

Output is included in the final report so users can self-test.
"""

from crewai import Task


def create_exam_task(topic: str, examiner_agent) -> Task:
    return Task(
        description=(
            f"Based on everything discussed about '{topic}', "
            "create 3 questions that test genuine understanding. "
            "Question 1: factual recall. "
            "Question 2: simple explanation. "
            "Question 3: real-world application."
        ),
        expected_output=(
            "3 numbered questions of increasing difficulty: "
            "1 recall question, 1 explanation question, 1 application question. "
            "Each question should be answerable from the material covered."
        ),
        agent=examiner_agent,
    )
