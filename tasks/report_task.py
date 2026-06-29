"""
tasks/report_task.py
--------------------
Defines the final report task assigned to the Reporter Agent.
Aggregates all previous outputs into a comprehensive, structured report
with clear sections for each agent and their outputs.
Runs last — reads all prior context and formats it into a complete document.
"""

from crewai import Task


def create_report_task(topic: str, reporter_agent) -> Task:
    return Task(
        description=(
            f"You have access to all the research, explanations, simplified content, "
            f"notes, and exam questions about '{topic}'. Your job is to compile "
            f"all of this information into ONE comprehensive, well-structured report. "
            f"\n\nIMPORTANT: Format the report EXACTLY as follows with clear section headers:\n\n"
            f"## RESEARCH FINDINGS (Researcher Agent)\n"
            f"[Include the research findings here]\n\n"
            f"## DETAILED EXPLANATION (Teacher Agent)\n"
            f"[Include the step-by-step explanation here]\n\n"
            f"## SIMPLIFIED SUMMARY (Simplifier Agent)\n"
            f"[Include the simplified version here]\n\n"
            f"## STUDY NOTES (Student Agent)\n"
            f"[Include the revision notes here]\n\n"
            f"## SELF-TEST QUESTIONS (Examiner Agent)\n"
            f"[Include the exam questions here]\n\n"
            f"Make sure each section is clearly labeled and contains the complete output from that agent."
        ),
        expected_output=(
            "A complete, well-formatted report with exactly 5 sections, each clearly labeled:\n"
            "1. RESEARCH FINDINGS (Researcher Agent output)\n"
            "2. DETAILED EXPLANATION (Teacher Agent output)\n"
            "3. SIMPLIFIED SUMMARY (Simplifier Agent output)\n"
            "4. STUDY NOTES (Student Agent output)\n"
            "5. SELF-TEST QUESTIONS (Examiner Agent output)\n"
            "Each section must be preceded by a ## header and contain the full output from that agent."
        ),
        agent=reporter_agent,
    )
