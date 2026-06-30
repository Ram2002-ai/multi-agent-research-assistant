# Prompt engineering guide

The pipeline gets its quality from role clarity and context discipline.

## Role contract

Each agent should have:

- one observable goal;
- a backstory that adds useful expertise, not decorative prose;
- an expected output with length and structure constraints;
- only the tools needed for that role;
- no delegation unless the workflow explicitly supports it.

## Context contract

Research is the evidence boundary. Downstream agents transform the accumulated
context; they should not silently introduce unsupported current facts. The
examiner consumes the full teaching trail and acts as the comprehension gate.

## Version workflow

1. Add a prompt through `/api/v1/prompts`.
2. Reuse the same name to create another immutable version.
3. Exercise the agent in `/api/v1/playground` with representative context.
4. Compare correctness, citation retention, structure, latency, and tokens.
5. Promote the selected content into the task or agent definition in source.

## Review rubric

Score each candidate from 1–5:

- factual grounding;
- instruction adherence;
- citation preservation;
- audience fit;
- unnecessary verbosity;
- consistent Markdown structure;
- prompt-injection resistance.
