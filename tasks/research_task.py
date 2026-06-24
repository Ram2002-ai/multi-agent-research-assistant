"""
tasks/research_task.py
----------------------
Defines the research task assigned to the Researcher Agent.
Task definitions are kept separate from agent definitions so you can
reassign tasks to different agents or reorder them in crew.py without
touching agent logic.
"""

from crewai import Task


def create_research_task(topic: str, researcher_agent) -> Task:
    """
    Args:
        topic: The research topic string passed in from main.py
        researcher_agent: The Agent instance that will execute this task

    Returns:
        Task: CrewAI Task object ready to be added to the Crew
    """
    return Task(
        description=(
            f"Search the web and find 3 important, accurate points about: '{topic}'. "
            "Focus on recent, credible sources. For each point, note the source URL."
        ),
        expected_output=(
            "A numbered list of exactly 3 key findings about the topic, "
            "each 2-3 sentences long, with a source reference for each."
        ),
        agent=researcher_agent,
    )
