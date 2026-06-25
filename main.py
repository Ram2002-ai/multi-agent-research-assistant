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
    - Saved to outputs/report_<timestamp>.md
"""

import argparse
import asyncio
import os
from datetime import datetime

from config import validate_env
from crew import build_crew


def save_output(topic: str, result: str) -> str:
    """Save the crew output to a markdown file in outputs/."""
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/report_{timestamp}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Research Report: {topic}\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("---\n\n")
        f.write(str(result))

    return filename


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
        description="Multi-Agent Research Assistant — powered by CrewAI + Gemini"
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

    # Save to file
    output_file = save_output(args.topic, result)

    print(f"\n{'='*60}")
    print(f"  Done! Report saved to: {output_file}")
    print(f"{'='*60}\n")
    print(result)


if __name__ == "__main__":
    main()
