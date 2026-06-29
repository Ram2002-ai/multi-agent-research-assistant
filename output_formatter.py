"""
output_formatter.py
-------------------
Formats crew output into a structured, readable report showing
each agent's task and their response.
"""

import re


def parse_structured_report(report: str) -> dict:
    """
    Parse the structured report into sections by agent.
    
    Args:
        report: The full report from the Reporter agent
        
    Returns:
        dict: Structured report with agent sections
    """
    sections = {
        "research": "",
        "explanation": "",
        "simplified": "",
        "notes": "",
        "questions": "",
    }
    
    # Define patterns for each section
    patterns = {
        "research": r"## RESEARCH FINDINGS.*?\n(.*?)(?=##|$)",
        "explanation": r"## DETAILED EXPLANATION.*?\n(.*?)(?=##|$)",
        "simplified": r"## SIMPLIFIED SUMMARY.*?\n(.*?)(?=##|$)",
        "notes": r"## STUDY NOTES.*?\n(.*?)(?=##|$)",
        "questions": r"## SELF-TEST QUESTIONS.*?\n(.*?)(?=##|$)",
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, report, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()
    
    return sections


def format_structured_output(report: str) -> str:
    """
    Format the report into a beautiful, structured output.
    
    Args:
        report: The full report from the Reporter agent
        
    Returns:
        str: Beautifully formatted output
    """
    sections = parse_structured_report(report)
    
    output = []
    output.append("=" * 80)
    output.append("MULTI-AGENT RESEARCH REPORT - STRUCTURED OUTPUT")
    output.append("=" * 80)
    output.append("")
    
    # Agent 1: Researcher
    output.append("┌" + "─" * 78 + "┐")
    output.append("│ AGENT 1: RESEARCHER" + " " * 59 + "│")
    output.append("│ Task: Search web and find 3 important points with sources" + " " * 18 + "│")
    output.append("├" + "─" * 78 + "┤")
    output.append("│ OUTPUT:" + " " * 71 + "│")
    output.append("│" + " " * 78 + "│")
    for line in sections["research"].split("\n"):
        if line:
            # Wrap long lines
            wrapped = wrap_text(line, 76)
            for wl in wrapped:
                output.append(f"│ {wl:<76} │")
    output.append("└" + "─" * 78 + "┘")
    output.append("")
    
    # Agent 2: Teacher
    output.append("┌" + "─" * 78 + "┐")
    output.append("│ AGENT 2: TEACHER" + " " * 62 + "│")
    output.append("│ Task: Explain topic step-by-step with real-world examples" + " " * 18 + "│")
    output.append("├" + "─" * 78 + "┤")
    output.append("│ OUTPUT:" + " " * 71 + "│")
    output.append("│" + " " * 78 + "│")
    for line in sections["explanation"].split("\n"):
        if line:
            wrapped = wrap_text(line, 76)
            for wl in wrapped:
                output.append(f"│ {wl:<76} │")
    output.append("└" + "─" * 78 + "┘")
    output.append("")
    
    # Agent 3: Simplifier
    output.append("┌" + "─" * 78 + "┐")
    output.append("│ AGENT 3: SIMPLIFIER" + " " * 58 + "│")
    output.append("│ Task: Rewrite complex explanations in simplest language" + " " * 22 + "│")
    output.append("├" + "─" * 78 + "┤")
    output.append("│ OUTPUT:" + " " * 71 + "│")
    output.append("│" + " " * 78 + "│")
    for line in sections["simplified"].split("\n"):
        if line:
            wrapped = wrap_text(line, 76)
            for wl in wrapped:
                output.append(f"│ {wl:<76} │")
    output.append("└" + "─" * 78 + "┘")
    output.append("")
    
    # Agent 4: Student
    output.append("┌" + "─" * 78 + "┐")
    output.append("│ AGENT 4: STUDENT" + " " * 62 + "│")
    output.append("│ Task: Write concise, well-organized revision notes" + " " * 26 + "│")
    output.append("├" + "─" * 78 + "┤")
    output.append("│ OUTPUT:" + " " * 71 + "│")
    output.append("│" + " " * 78 + "│")
    for line in sections["notes"].split("\n"):
        if line:
            wrapped = wrap_text(line, 76)
            for wl in wrapped:
                output.append(f"│ {wl:<76} │")
    output.append("└" + "─" * 78 + "┘")
    output.append("")
    
    # Agent 5: Examiner
    output.append("┌" + "─" * 78 + "┐")
    output.append("│ AGENT 5: EXAMINER" + " " * 61 + "│")
    output.append("│ Task: Create 3 questions to test genuine understanding" + " " * 22 + "│")
    output.append("├" + "─" * 78 + "┤")
    output.append("│ OUTPUT:" + " " * 71 + "│")
    output.append("│" + " " * 78 + "│")
    for line in sections["questions"].split("\n"):
        if line:
            wrapped = wrap_text(line, 76)
            for wl in wrapped:
                output.append(f"│ {wl:<76} │")
    output.append("└" + "─" * 78 + "┘")
    output.append("")
    output.append("=" * 80)
    
    return "\n".join(output)


def wrap_text(text: str, width: int) -> list:
    """
    Wrap text to specified width.
    
    Args:
        text: Text to wrap
        width: Maximum width
        
    Returns:
        list: List of wrapped lines
    """
    if len(text) <= width:
        return [text]
    
    lines = []
    current_line = ""
    words = text.split()
    
    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.rstrip())
            current_line = word + " "
    
    if current_line:
        lines.append(current_line.rstrip())
    
    return lines
