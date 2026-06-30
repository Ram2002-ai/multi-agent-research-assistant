"""Deterministic Mermaid and graph generation for every report."""

from __future__ import annotations

import re


def mermaid_diagrams(topic: str) -> dict[str, str]:
    safe_topic = re.sub(r'["\n\r]', "", topic)[:80]
    return {
        "pipeline": f"""flowchart LR
    U["{safe_topic}"] --> R[Research Agent]
    R --> T[Teacher Agent]
    T --> S[Simplifier Agent]
    S --> N[Student Agent]
    N --> E[Examiner Agent]
    E --> P[Research Report]""",
        "sequence": """sequenceDiagram
    actor User
    participant API
    participant Search
    participant Crew as Agent Crew
    participant KB as Knowledge Base
    User->>API: Start research
    API-->>User: Job ID + live stream
    API->>Search: Find credible sources
    Search-->>Crew: Ranked evidence
    Crew->>Crew: Teach, simplify, note, examine
    Crew->>KB: Store report chunks
    Crew-->>API: Final report
    API-->>User: Live report + exports""",
        "architecture": """flowchart TB
    UI[React Dashboard] <-->|REST / SSE / WebSocket| API[FastAPI]
    API --> ORCH[Research Orchestrator]
    ORCH --> AGENTS[CrewAI Agent Pipeline]
    AGENTS --> SEARCH[Serper / Tavily]
    AGENTS --> LLM[Multi-LLM Gateway]
    ORCH --> DB[(PostgreSQL)]
    ORCH --> VECTOR[(Vector Store)]
    ORCH --> EXPORT[Export Engine]
    API --> AUTH[JWT / OAuth]""",
    }


def research_graph(topic: str, sources: list[dict]) -> dict:
    nodes = [
        {"id": "topic", "label": topic, "type": "topic"},
        *[
            {"id": f"agent-{index}", "label": label, "type": "agent"}
            for index, label in enumerate(
                ["Researcher", "Teacher", "Simplifier", "Student", "Examiner"], 1
            )
        ],
    ]
    links = [{"source": "topic", "target": "agent-1", "type": "researched_by"}]
    links.extend(
        {
            "source": f"agent-{index}",
            "target": f"agent-{index + 1}",
            "type": "context",
        }
        for index in range(1, 5)
    )
    for index, source in enumerate(sources, 1):
        node_id = f"source-{index}"
        nodes.append(
            {
                "id": node_id,
                "label": source["domain"],
                "type": "source",
                "score": source["credibility_score"],
                "url": source["url"],
            }
        )
        links.append({"source": node_id, "target": "agent-1", "type": "evidence"})
    return {"nodes": nodes, "links": links}
