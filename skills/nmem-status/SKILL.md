---
name: nmem-status
description: Check the status of Nowledge Mem server connection, active workspace space, current conversation thread sync, and local offline sync queue. Use when the user requests status, diagnostics, or to verify if their session is being captured correctly.
---

# Nowledge Mem Status

Check connection status and inspect session synchronizations.

## Preferred Execution Hierarchy

To construct the status report, follow this sequence:

1. **Check Server Connection & API Configuration (MCP & CLI)**:
   - Call the MCP `graph_stats` tool or run `nmem status`.
   - Parse the outputs to determine the API URL, database status, and server reachability.
2. **Check Active Context & Environment**:
   - Read the active environment variables:
     - `NMEM_HOST_AGENT_ID`: The derived host agent fingerprint. If unset, read from the context bundle or use `hooks/nmem_shared.py` to check it.
     - `NMEM_SPACE` or `NMEM_SPACE_ID`: The active Nowledge Mem space.
3. **Verify Current Thread Sync State**:
   - Check if the current conversation (`conversationId`) has been created/synced in Nowledge Mem.
   - Run:
     ```bash
     nmem t show <conversationId>
     ```
     Or call MCP `thread_fetch_messages` with the current `conversationId` and a limit of 1.
   - Report if it exists, the number of messages, and sync status.
4. **Check Local Offline Sync Queue**:
   - Check if there are any failed/unsynced sessions queued locally in `~/.nowledge-mem/antigravity_unsynced.json` that are waiting for retry.
   - Print the queue status (number of pending sessions).

## Output Formatting

Synthesize the collected information into a beautiful, premium visual interface using standard markdown tables, GitHub-style alerts, and list blocks:

- **Server Connection**: Use `[!NOTE]` or `[!IMPORTANT]` alerts for connection state.
- **Active Context**: Use a Markdown Table for variables like space, host ID, and session directory.
- **Sync Status**: Use a `[!TIP]` alert or table to show thread messages and queue status.

Example structure of the printed rich status output:

> [!NOTE]
> **Nowledge Mem Server**: Connected to `http://127.0.0.1:14242` (Local)
> **Database Status**: Online
> **API Version**: 0.7.15

### Active Workspace Context

| Parameter | Value |
| :--- | :--- |
| **Active Space** | `Default` |
| **Host Agent ID** | `antigravity-3a2b1c` |
| **Conversation ID** | `ec33ebf9-0cba-4100-8142-c61503f6c587` |

### Conversation Sync Status

- **Synced Thread**: Yes (Thread contains 12 messages)
- **Local Unsynced Queue**: Empty (All sessions synced successfully)

---

<!-- nmem:skill-outcome-footer v1 -->
## Improving this skill

Nowledge Mem compiled this skill from the user's own experience. When you apply it, print one line so it keeps getting sharper (replace `<name>` with this skill's name from the frontmatter above):

    nmem-skill-used: nmem-status

If a step was wrong or missing, or it didn't work, also record that: call `report_skill_outcome` with `skill_id="nmem-status"`, `skill_version=1`, an `outcome` of `completed` / `completed_with_deviation` / `failed` / `abandoned`, and a one-line note on what was off. This is the user's own feedback loop, not telemetry.
(Or use CLI fallback: `nmem skills outcome nmem-status --version 1 --outcome <outcome> [--deviations "<note>" | --failure "<reason>"]`)
