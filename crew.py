"""
crew.py
-------
Assembles agents and tasks into a CrewAI Crew and runs the pipeline.

Pipeline order (sequential process):
  1. Researcher  → searches web, finds 3 key points
  2. Teacher     → explains step-by-step with examples
  3. Simplifier  → rewrites in plain language
  4. Student     → writes revision notes
  5. Examiner    → generates 3 test questions
  6. Reporter    → aggregates all outputs into structured report

Sequential process is used here (not hierarchical) because each agent
depends on the previous agent's output — research must complete before
teaching can begin, teaching before simplification, and so on.
"""

from crewai import Crew, Process

from agents import (
    create_researcher_agent,
    create_teacher_agent,
    create_simplifier_agent,
    create_student_agent,
    create_examiner_agent,
    create_reporter_agent,
)
from tasks import (
    create_research_task,
    create_teaching_task,
    create_simplify_task,
    create_notes_task,
    create_exam_task,
    create_report_task,
)


def build_crew(topic: str) -> Crew:
    """
    Build and return a configured Crew for the given topic.

    Args:
        topic: The research topic string (e.g. "What is Artificial Intelligence?")

    Returns:
        Crew: Ready-to-run CrewAI crew instance
    """
    # Instantiate agents
    researcher = create_researcher_agent()
    teacher = create_teacher_agent()
    simplifier = create_simplifier_agent()
    student = create_student_agent()
    examiner = create_examiner_agent()
    reporter = create_reporter_agent()

    # Instantiate tasks (each task is bound to its agent)
    research_task = create_research_task(topic, researcher)
    teaching_task = create_teaching_task(topic, teacher)
    simplify_task = create_simplify_task(topic, simplifier)
    notes_task = create_notes_task(topic, student)
    exam_task = create_exam_task(topic, examiner)
    report_task = create_report_task(topic, reporter)

    return Crew(
        agents=[researcher, teacher, simplifier, student, examiner, reporter],
        tasks=[research_task, teaching_task, simplify_task, notes_task, exam_task, report_task],
        # Sequential: tasks run in order, each agent sees prior outputs
        process=Process.sequential,
        verbose=True,
    )
