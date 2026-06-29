"""
main.py
-------
Entry point for the Multi-Agent Research Assistant.

Usage:
    # Default topic
    python main.py

    # Custom topic
    python main.py --topic "What is Machine Learning?"

    # Async mode (faster, runs tasks concurrently where possible)
    python main.py --topic "What is Deep Learning?" --async

Output:
    - Printed to terminal (verbose agent logs + final report)
    - Saved to outputs/report_<timestamp>.md (markdown format)
    - Saved to outputs/report_<timestamp>_structured.txt (structured format with all agents)
"""

import argparse
import asyncio
import os
from datetime import datetime

from config import validate_env
from crew import build_crew
from output_formatter import format_structured_output
from pdf_formatter import generate_pdf


def save_output(topic: str, result: str) -> tuple:
    """Save the crew output to markdown, text, and PDF files.
    
    Args:
        topic: The research topic
        result: The crew output result
        
    Returns:
        tuple: (markdown_file, structured_file, pdf_file)
    """
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as markdown
    md_filename = f"outputs/report_{timestamp}.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(f"# Research Report: {topic}\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("---\n\n")
        f.write(str(result))
    
    # Save as structured text with all agent outputs
    structured_filename = f"outputs/report_{timestamp}_structured.txt"
    structured_output = format_structured_output(str(result))
    with open(structured_filename, "w", encoding="utf-8") as f:
        f.write(f"MULTI-AGENT RESEARCH REPORT: {topic}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n{structured_output}\n")
    
    # Save as PDF
    pdf_filename = f"outputs/report_{timestamp}.pdf"
    generate_pdf(topic, str(result), pdf_filename)

    return md_filename, structured_filename, pdf_filename


def run_sync(topic: str):
    """Run the crew synchronously.

    This uses the async crew API under the hood because Crewai's sync
    kickoff wrapper may trigger nested event loop issues on some systems.
    """
    crew = build_crew(topic)
    return asyncio.run(crew.kickoff_async())


async def run_async(topic: str):
    """Run the crew asynchronously (non-blocking)."""
    crew = build_crew(topic)
    result = await crew.kickoff_async()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research Assistant — powered by CrewAI + OpenRouter"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="What is Artificial Intelligence?",
        help="The topic to research (default: 'What is Artificial Intelligence?')",
    )
    parser.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        help="Run in async mode",
    )
    args = parser.parse_args()

    # Validate API keys before starting
    validate_env()

    print(f"\n{'='*60}")
    print(f"  Multi-Agent Research Assistant")
    print(f"  Topic: {args.topic}")
    print(f"{'='*60}\n")

    if args.use_async:
        result = asyncio.run(run_async(args.topic))
    else:
        result = run_sync(args.topic)

    # Save to files
    md_file, struct_file, pdf_file = save_output(args.topic, result)

    print(f"\n{'='*60}")
    print(f"  Done! Reports saved to:")
    print(f"  - {md_file}")
    print(f"  - {struct_file}")
    print(f"  - {pdf_file}")
    print(f"{'='*60}\n")
    
    # Print structured output
    print(format_structured_output(str(result)))


if __name__ == "__main__":
    main()
