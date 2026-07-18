---
name: nmem-search-memory
description: Search the user's personal knowledge base when past insights would improve the response. Trigger proactively for continuity, recurring bugs, design rationale, and remembered workflows.
---

# Search Memory

Use Nowledge Mem proactively when prior knowledge would materially improve the answer.

## Strong Signals

Search when:

- the user references previous work, a prior fix, or an earlier decision
- the task resumes a named feature, bug, refactor, incident, or subsystem
- a debugging pattern resembles something solved earlier
- the user asks for rationale, preferences, procedures, or recurring workflow details
- the user uses implicit recall language: "that approach", "like before"

**Contextual signals — consider searching when:**

- complex debugging where prior context would narrow the search space
- architecture discussion that may intersect with past decisions
- domain-specific conventions the user has established before
- the current result is ambiguous and past context would make the answer sharper

## Token-Efficient Retrieval Routing & Graph Neighborhoods

To minimize token usage, avoid bloating the conversation context, and prevent terminal permission prompts, follow this interface hierarchy:

1. **Nowledge FS (MCP `mem_fs`) - Best for Unified File Actions**:
   - For listing, searching, checking size, or loading chunks of memories, threads, wiki pages, or documents, call the MCP `mem_fs` tool.
   - Use the **"Start broad, then narrow"** pattern:
     - Run `mem_fs` with `command: "recall", path: "/memories", query: "..."` for semantic searches.
     - Run `mem_fs` with `command: "grep", query: "..."` to search text across memories, threads, and library sources.
     - Run `mem_fs` with `command: "stat"` to check the file size and line counts cheaply before loading.
     - Run `mem_fs` with `command: "cat", path: "...", line: START, lines: COUNT` to fetch only the required window, avoiding context bloat.
2. **Specialized MCP Tools**:
   - Use `memory_search` for durable knowledge queries.
   - Use `thread_search` followed by `thread_fetch_messages` (always passing a small `limit` like `5` or `10`) to paginatedly check thread histories.
   - Use `memory_neighbors` or `explore_graph` to expand graph neighborhoods selectively.
3. **CLI Fallback (Only if MCP is unavailable)**:
   - For file actions: `nmem fs ls`, `nmem fs cat --line START --lines COUNT`, `nmem fs stat`, `nmem fs find`, `nmem fs grep`, `nmem fs recall`.
   - For direct question asking/synthesis across all sources: `nmem ask "question"` (use `--ephemeral` to avoid creating a Timeline entry, and `--json` for structured sources).
   - For memory/thread lookups: `nmem --json m search` or `nmem --json t search` (with pagination).

Prefer the smallest retrieval surface that answers the question.

If the runtime already knows the active project or agent lane, add `--space "<space name>"` to these commands.

Mention source threads when they add useful historical context.
