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

To minimize token usage and avoid bloating the conversation context:

1. **Be Precise**: Use specific keywords in search queries to find exact matches.
2. **Paging Thread Messages**:
   - If MCP tools are available, call `thread_search` to find relevant threads.
   - Do NOT load full threads. When calling `thread_fetch_messages`, always specify a small limit (e.g. `limit: 5` or `10`) to check recent context first. Page further using `offset` only if needed.
3. **Windowed File Reading**:
   - When navigating the virtual filesystem with `mem_fs` or CLI `nmem fs`:
     - Run `stat` to check the file size and line count before loading any file.
     - For large thread logs (`.jsonl`) or documents, do not call `cat` on the whole path. Use `cat` with `--line <start>` and `--lines <count>` to inspect only the required window.
4. **Graph Neighborhoods**:
   - When a relevant memory is found, use `memory_neighbors` or `explore_graph` to selectively load adjacent nodes/relationships rather than pulling large batches of unrelated memories.

If MCP tools are not available, use the CLI equivalents:
1. Start with `nmem --json m search` for durable knowledge.
2. Use `--mode deep` when the first pass is weak or the recall need is conceptual.
3. Use `nmem --json t search` for prior discussions or previous sessions.
4. If a memory result includes a `source_thread` or thread search returns a strong hit, inspect the conversation progressively with `nmem --json t show <thread_id> --limit 5 --offset 0 --content-limit 1200` to avoid dumping the entire thread.

Prefer the smallest retrieval surface that answers the question.

If the runtime already knows the active project or agent lane, add `--space "<space name>"` to these commands.

Mention source threads when they add useful historical context.
