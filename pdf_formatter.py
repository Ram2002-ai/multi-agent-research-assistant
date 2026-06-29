"""
pdf_formatter.py
----------------
Generates a professional PDF report from the multi-agent output
with all agent tasks and their responses clearly formatted.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
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


def generate_pdf(topic: str, report: str, output_path: str):
    """
    Generate a professional PDF report with all agent outputs.
    
    Args:
        topic: The research topic
        report: The full report from the Reporter agent
        output_path: Where to save the PDF file
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    agent_header_style = ParagraphStyle(
        'AgentHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#ffffff'),
        backColor=colors.HexColor('#1565c0'),
        spaceAfter=12,
        spaceBefore=12,
        leftIndent=6,
        fontName='Helvetica-Bold'
    )
    
    task_style = ParagraphStyle(
        'TaskStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#424242'),
        spaceAfter=8,
        leftIndent=12,
        fontName='Helvetica-Oblique'
    )
    
    content_style = ParagraphStyle(
        'ContentStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#212121'),
        spaceAfter=12,
        leftIndent=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    normal_style = styles['Normal']
    
    # Parse report sections
    sections = parse_structured_report(report)
    
    # Build PDF content
    content = []
    
    # Title page
    content.append(Spacer(1, 0.3*inch))
    content.append(Paragraph(
        "Multi-Agent Research Report",
        title_style
    ))
    content.append(Spacer(1, 0.2*inch))
    content.append(Paragraph(
        f"Topic: {topic}",
        ParagraphStyle('Subtitle', parent=styles['Normal'], 
                      fontSize=16, alignment=TA_CENTER,
                      textColor=colors.HexColor('#424242'))
    ))
    content.append(Spacer(1, 0.1*inch))
    content.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        ParagraphStyle('Meta', parent=styles['Normal'],
                      fontSize=10, alignment=TA_CENTER,
                      textColor=colors.HexColor('#757575'))
    ))
    content.append(Spacer(1, 0.5*inch))
    
    # Table of Contents
    content.append(Paragraph("Table of Contents", styles['Heading2']))
    toc_items = [
        "1. Research Findings",
        "2. Detailed Explanation",
        "3. Simplified Summary",
        "4. Study Notes",
        "5. Self-Test Questions"
    ]
    for item in toc_items:
        content.append(Paragraph(item, ParagraphStyle('TOC', parent=normal_style,
                                                      leftIndent=12, fontSize=10)))
    content.append(Spacer(1, 0.3*inch))
    content.append(PageBreak())
    
    # Agent 1: Researcher
    content.append(Paragraph("1. Research Findings", styles['Heading2']))
    content.append(Paragraph(
        "<b>Agent:</b> Researcher<br/>"
        "<b>Task:</b> Search the web and find 3 important, accurate points about the topic with credible sources.",
        task_style
    ))
    content.append(Spacer(1, 0.1*inch))
    if sections["research"]:
        content.append(Paragraph(sections["research"], content_style))
    content.append(Spacer(1, 0.2*inch))
    content.append(PageBreak())
    
    # Agent 2: Teacher
    content.append(Paragraph("2. Detailed Explanation", styles['Heading2']))
    content.append(Paragraph(
        "<b>Agent:</b> Teacher<br/>"
        "<b>Task:</b> Explain the topic step-by-step with clear real-world examples.",
        task_style
    ))
    content.append(Spacer(1, 0.1*inch))
    if sections["explanation"]:
        content.append(Paragraph(sections["explanation"], content_style))
    content.append(Spacer(1, 0.2*inch))
    content.append(PageBreak())
    
    # Agent 3: Simplifier
    content.append(Paragraph("3. Simplified Summary", styles['Heading2']))
    content.append(Paragraph(
        "<b>Agent:</b> Simplifier<br/>"
        "<b>Task:</b> Rewrite complex explanations in the simplest possible language.",
        task_style
    ))
    content.append(Spacer(1, 0.1*inch))
    if sections["simplified"]:
        content.append(Paragraph(sections["simplified"], content_style))
    content.append(Spacer(1, 0.2*inch))
    content.append(PageBreak())
    
    # Agent 4: Student
    content.append(Paragraph("4. Study Notes", styles['Heading2']))
    content.append(Paragraph(
        "<b>Agent:</b> Student<br/>"
        "<b>Task:</b> Write concise, well-organized revision notes.",
        task_style
    ))
    content.append(Spacer(1, 0.1*inch))
    if sections["notes"]:
        content.append(Paragraph(sections["notes"], content_style))
    content.append(Spacer(1, 0.2*inch))
    content.append(PageBreak())
    
    # Agent 5: Examiner
    content.append(Paragraph("5. Self-Test Questions", styles['Heading2']))
    content.append(Paragraph(
        "<b>Agent:</b> Examiner<br/>"
        "<b>Task:</b> Create 3 questions that test genuine understanding (from basic recall to application).",
        task_style
    ))
    content.append(Spacer(1, 0.1*inch))
    if sections["questions"]:
        content.append(Paragraph(sections["questions"], content_style))
    content.append(Spacer(1, 0.3*inch))
    
    # Footer
    content.append(Spacer(1, 0.2*inch))
    content.append(Paragraph(
        "This report was generated by the Multi-Agent Research Assistant powered by CrewAI and OpenRouter.",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8,
                      textColor=colors.HexColor('#9e9e9e'),
                      alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(content)
