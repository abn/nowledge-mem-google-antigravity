---
name: nmem-save-handoff
description: Save a concise Google Antigravity handoff summary only when the user explicitly asks. This is intentionally separate from full thread-save, which should use the native session importer script.
---

# Save Handoff

Only use this skill when the user explicitly asks to save progress as a handoff, leave a resumable summary, or create a lightweight restart point.

## Why This Is A Handoff

`nmem-save-thread` should mean saving the real session messages through the custom session importer script.

This skill intentionally creates a structured handoff summary thread instead of importing the full session.

## Workflow

1. Synthesize the session progress into the following structure:
   - **Goal**: The primary objective of the session.
   - **Decisions**: Key architectural, design, or logical decisions made.
   - **Files Touched**: Absolute paths of any files touched or modified.
   - **Risks & Open Questions**: Outstanding bugs, assumptions, or open issues.
   - **Next Steps**: Checklist of work remaining for the next session.
2. Format this summary as a clean, reader-friendly Markdown table or structured layout.
3. Present the draft handoff to the user and request confirmation or amendments.
4. Upon user approval, create the handoff thread (using MCP `thread_create` if available, or the CLI command `nmem --json t create -t "Antigravity Session - <topic>" -c "<content>" -s google-antigravity`).
5. If the user prefers a lossless transcript backup instead of a handoff summary, route to the `nmem-save-thread` skill.

Always get explicit approval before creating the handoff thread. Do not auto-save handoffs silently.
