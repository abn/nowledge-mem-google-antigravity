---
name: nmem-distill-memory
description: Detect breakthrough moments, durable lessons, and decisions worth preserving. Suggest distillation sparingly, then store high-value knowledge as atomic memories.
---

# Distill Memory

Save proactively when the conversation produces a durable fact, preference, decision, plan, procedure, learning, event, or important context. Do not wait to be asked.

## Good Candidates

- decisions with rationale
- repeatable procedures
- lessons from debugging or incident work
- durable preferences or constraints
- plans that future sessions will need to resume cleanly

## Workflow

1. Scan the conversation history to identify candidates for distilled memories (facts, decisions, learnings, preferences, or repeatable procedures).
2. Draft a standalone memory card for each candidate with a clear title and context-complete description.
3. Present these draft memory cards to the user, categorized by unit type (`decision`, `learning`, `preference`, etc.), and ask for approval or edits.
4. For approved items, verify if a duplicate or similar memory exists:
   - If yes: update the existing memory (using MCP `memory_update` or CLI `nmem m update`).
   - If no: add it as a new memory (using MCP `memory_add` or CLI `nmem --json m add`).
5. Identify semantic relationships between the new memories and existing knowledge (e.g., a new decision superseding an older plan). Present the relationship edges to the user and, on approval, link them (using MCP `memory_relation_add` or CLI commands).

Always seek explicit confirmation before creating or updating memories. Do not perform write operations silently.
